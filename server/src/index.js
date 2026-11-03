// Kouga challenge ranking server (Cloudflare Worker + D1). One board for a limited event (EVENT_START..EVENT_END):
// each player (X handle) counts once, with their best approved run.
//   GET  /api/event                                   -> {start,end,now,open}
//   POST /api/start   {mode,xid,nick}                 -> {token}           one token per run (event open only)
//   POST /api/submit  {token,score,summary}           -> {status,rank,best}
//   GET  /api/board?xid=<handle>                      -> {event,players,top:[10],me}
//   admin (header X-Admin-Key: <ADMIN_KEY>):
//   GET  /api/admin/scores?status=review|ok|rejected|deleted&limit=100
//   POST /api/admin/scores/<id>  {status:'ok'|'review'|'deleted'}
//   GET  /admin   -> the admin page
import { judge } from './rules.js';
import { ADMIN_HTML } from './admin.js';

const MODES = ['normal', 'hard', 'super'];
const TOKEN_TTL_MS = 3 * 60 * 60 * 1000;
const LIMIT_START_PER_HOUR = 120, LIMIT_SUBMIT_PER_HOUR = 60;

const cors = (env) => ({ 'access-control-allow-origin': env.ALLOWED_ORIGIN || '*', 'access-control-allow-headers': 'content-type, x-admin-key', 'access-control-allow-methods': 'GET, POST, OPTIONS' });
const json = (data, status, env, extra) => new Response(JSON.stringify(data), { status: status || 200, headers: { 'content-type': 'application/json; charset=utf-8', ...cors(env), ...(extra || {}) } });
const ipOf = (req) => req.headers.get('cf-connecting-ip') || req.headers.get('x-forwarded-for') || 'local';
const newId = () => [...crypto.getRandomValues(new Uint8Array(16))].map((b) => b.toString(16).padStart(2, '0')).join('');

export function eventOf(env, now) {
  const start = Date.parse(env.EVENT_START || ''), end = Date.parse(env.EVENT_END || '');
  return { start: start || null, end: end || null, now, open: !!start && !!end && now >= start && now < end };
}
export const cleanXid = (x) => { x = String(x || '').trim().replace(/^@/, ''); return /^[A-Za-z0-9_]{1,15}$/.test(x) ? x.toLowerCase() : ''; };
export const cleanNick = (n) => { n = String(n || '').normalize('NFC').replace(/[\u0000-\u001f\u007f<>]/g, '').trim(); return Array.from(n).slice(0, 12).join(''); };

async function countSince(env, table, ip, since) {
  const r = await env.DB.prepare(`SELECT COUNT(*) AS n FROM ${table} WHERE ip = ? AND created > ?`).bind(ip, since).first();
  return r ? r.n : 0;
}

// each player's best approved run inside the event, best first
const BEST_SQL = `SELECT b.xid, p.nick, b.score, b.mode, b.nightmare, b.created FROM
  (SELECT xid, score, mode, nightmare, created, ROW_NUMBER() OVER (PARTITION BY xid ORDER BY score DESC, created ASC) AS rn
     FROM scores WHERE status = 'ok' AND created >= ? AND created < ?) b
  JOIN players p ON p.xid = b.xid WHERE b.rn = 1 ORDER BY b.score DESC, b.created ASC`;

async function myRank(env, ev, xid) {
  const mine = await env.DB.prepare("SELECT MAX(score) AS s FROM scores WHERE xid = ? AND status = 'ok' AND created >= ? AND created < ?").bind(xid, ev.start, ev.end).first();
  if (!mine || mine.s == null) return null;
  const r = await env.DB.prepare(`SELECT COUNT(*) + 1 AS r FROM (SELECT xid, MAX(score) AS s FROM scores WHERE status = 'ok' AND created >= ? AND created < ? GROUP BY xid) WHERE s > ?`)
    .bind(ev.start, ev.end, mine.s).first();
  return { rank: r.r, score: mine.s };
}

async function start(req, env) {
  const b = await req.json().catch(() => ({})), ip = ipOf(req), now = Date.now(), ev = eventOf(env, now);
  if (!ev.open) return json({ error: 'closed', event: ev }, 403, env);
  if (!MODES.includes(b.mode)) return json({ error: 'bad mode' }, 400, env);
  const xid = cleanXid(b.xid), nick = cleanNick(b.nick);
  if (!xid || !nick) return json({ error: 'nickname and X handle needed' }, 400, env);
  if (await countSince(env, 'tokens', ip, now - 3600e3) >= LIMIT_START_PER_HOUR) return json({ error: 'too many runs' }, 429, env);
  await env.DB.prepare('INSERT INTO players (xid, nick, created, updated) VALUES (?, ?, ?, ?) ON CONFLICT(xid) DO UPDATE SET nick = excluded.nick, updated = excluded.updated').bind(xid, nick, now, now).run();
  const token = newId();
  await env.DB.prepare('INSERT INTO tokens (id, xid, mode, ip, created, used) VALUES (?, ?, ?, ?, ?, 0)').bind(token, xid, b.mode, ip, now).run();
  return json({ token }, 200, env);
}

async function submit(req, env) {
  const b = await req.json().catch(() => null), ip = ipOf(req), now = Date.now();
  if (!b || typeof b.token !== 'string') return json({ error: 'bad request' }, 400, env);
  if (await countSince(env, 'scores', ip, now - 3600e3) >= LIMIT_SUBMIT_PER_HOUR) return json({ error: 'too many submits' }, 429, env);
  const tk = await env.DB.prepare('SELECT * FROM tokens WHERE id = ?').bind(b.token).first();
  if (!tk) return json({ error: 'unknown token' }, 400, env);
  if (tk.used) return json({ error: 'token already used' }, 409, env);
  if (now - tk.created > TOKEN_TTL_MS) return json({ error: 'token expired' }, 410, env);
  const ev = eventOf(env, tk.created);   // a run started inside the event counts, even if it ends just after
  if (!ev.open) return json({ error: 'closed' }, 403, env);
  const spent = await env.DB.prepare('UPDATE tokens SET used = 1 WHERE id = ? AND used = 0').bind(b.token).run();
  if (!spent.meta || spent.meta.changes !== 1) return json({ error: 'token already used' }, 409, env);
  const s = b.summary || {}, score = b.score;
  const verdict = judge(tk.mode, score, s, (now - tk.created) / 1000);
  await env.DB.prepare(`INSERT INTO scores (id, token, xid, mode, score, elapsed, eaten, boxes, combo, lucky, patrols, rage, nightmare, status, reason, ip, created)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .bind(newId(), b.token, tk.xid, tk.mode, Number.isInteger(score) ? score : 0, +s.elapsed || 0, s.eaten | 0, s.boxes | 0, s.combo | 0, s.lucky | 0, s.patrols | 0,
      s.rage ? 1 : 0, s.nightmare ? 1 : 0, verdict.status, verdict.reason, ip, tk.created).run();
  const me = await myRank(env, ev, tk.xid);
  return json({ status: verdict.status === 'ok' ? 'ok' : 'held', rank: me ? me.rank : null, best: me ? me.score : null }, 200, env);   // why a run was held stays on the server
}

async function board(url, env) {
  const ev = eventOf(env, Date.now());
  if (!ev.start) return json({ event: ev, players: 0, top: [], me: null }, 200, env);
  const all = (await env.DB.prepare(BEST_SQL).bind(ev.start, ev.end).all()).results || [];
  const top = all.slice(0, 10).map((r, i) => ({ rank: i + 1, nick: r.nick, score: r.score, mode: r.nightmare ? 'nightmare' : r.mode }));
  const xid = cleanXid(url.searchParams.get('xid'));
  let me = null;
  if (xid) { const i = all.findIndex((r) => r.xid === xid); if (i >= 0) me = { rank: i + 1, nick: all[i].nick, score: all[i].score, mode: all[i].nightmare ? 'nightmare' : all[i].mode }; }
  const cut = all[10] ? all[10].score : null;   // the 11th best: with the player in the top 10, the 10th of everyone else
  return json({ event: ev, players: all.length, top, me, cut }, 200, env, { 'cache-control': 'no-store' });
}

const isAdmin = (req, env) => !!env.ADMIN_KEY && req.headers.get('x-admin-key') === env.ADMIN_KEY;
async function adminList(url, env) {
  const status = url.searchParams.get('status') || 'review', limit = Math.max(1, Math.min(500, parseInt(url.searchParams.get('limit') || '100', 10)));
  const r = await env.DB.prepare(`SELECT s.*, p.nick FROM scores s LEFT JOIN players p ON p.xid = s.xid WHERE s.status = ? ORDER BY ${status === 'ok' ? 's.score DESC' : 's.created DESC'} LIMIT ?`).bind(status, limit).all();
  return json({ rows: r.results || [], event: eventOf(env, Date.now()) }, 200, env);
}
async function adminSet(req, id, env) {
  const b = await req.json().catch(() => ({}));
  if (!['ok', 'review', 'deleted'].includes(b.status)) return json({ error: 'bad status' }, 400, env);
  const r = await env.DB.prepare('UPDATE scores SET status = ? WHERE id = ?').bind(b.status, id).run();
  return json({ changed: r.meta ? r.meta.changes : 0 }, 200, env);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), p = url.pathname;
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(env) });
    try {
      if (p === '/api/event') return json(eventOf(env, Date.now()), 200, env);
      if (p === '/api/start' && req.method === 'POST') return await start(req, env);
      if (p === '/api/submit' && req.method === 'POST') return await submit(req, env);
      if (p === '/api/board' && req.method === 'GET') return await board(url, env);
      if (p === '/admin') return new Response(ADMIN_HTML, { headers: { 'content-type': 'text/html; charset=utf-8' } });
      if (p.startsWith('/api/admin/')) {
        if (!isAdmin(req, env)) return json({ error: 'not allowed' }, 401, env);
        if (p === '/api/admin/scores' && req.method === 'GET') return await adminList(url, env);
        const m = p.match(/^\/api\/admin\/scores\/([0-9a-f]{32})$/);
        if (m && req.method === 'POST') return await adminSet(req, m[1], env);
      }
      return json({ error: 'not found' }, 404, env);
    } catch (e) {
      return json({ error: 'server error' }, 500, env);
    }
  },
};
