// Runs the worker against an in-memory SQLite (Node 22+), with a tiny stand-in for Cloudflare D1.
//   node --no-warnings server/test/local.mjs          -> runs the checks below
//   node --no-warnings server/test/local.mjs serve    -> serves it on http://localhost:8787 (event open now, for 3 days)
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import worker from '../src/index.js';

const db = new DatabaseSync(':memory:');
db.exec(readFileSync(new URL('../schema.sql', import.meta.url), 'utf8'));
const D1 = { prepare(sql) { const st = db.prepare(sql); let args = [];
  const q = { bind(...a) { args = a; return q; }, first() { return Promise.resolve(st.get(...args) ?? null); },
    all() { return Promise.resolve({ results: st.all(...args) }); }, run() { const r = st.run(...args); return Promise.resolve({ meta: { changes: Number(r.changes) } }); } };
  return q; } };
const t0 = Date.now();
const env = { DB: D1, ADMIN_KEY: 'test-admin', ALLOWED_ORIGIN: '*', EVENT_START: new Date(t0 - 3600e3).toISOString(), EVENT_END: new Date(t0 + 3 * 86400e3).toISOString() };
const call = async (method, path, body, headers) => {
  const r = await worker.fetch(new Request('http://x' + path, { method, headers: { 'content-type': 'application/json', ...(headers || {}) }, body: body ? JSON.stringify(body) : undefined }), env);
  return { status: r.status, body: r.headers.get('content-type')?.includes('json') ? await r.json() : await r.text() };
};

if (process.argv[2] === 'serve') {
  if (process.argv[3] === 'demo') {   // sample players for trying the board
    const P = [['폭주의신','nm_god','super',301500,1],['コウガ推し','kougaoshi','super',142000,0],['피노헌터','hunter01','hard',58400,0],['ピノ大好き','pino_suki','hard',39700,0],
      ['콤보장인','combo_m','hard',33300,0],['다이후쿠','daifuku','hard',27100,0],['냉동실털이','freezer','normal',21300,0],['몰래먹기','sneaky','normal',18800,0],
      ['밤의 피노','night_p','normal',15200,0],['きつね','kitsune','normal',12900,0],['도둑고양이','neko','normal',9800,0],['초보','newbie','normal',4100,0]];
    P.forEach(([nick, xid, mode, score, nm], i) => { const at = t0 - 1800e3 + i * 1000;
      db.prepare('INSERT INTO players VALUES (?,?,?,?)').run(xid, nick, at, at);
      db.prepare("INSERT INTO scores VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'ok','',?,?)").run('d' + String(i).padStart(31, '0'), 'demo' + i, xid, mode, score, 120, 60, 10, 30, 1, 5, mode === 'normal' ? 0 : 1, nm, 'demo', at); });
  }
  createServer(async (req, res) => {
    let data = ''; req.on('data', (c) => (data += c)); await new Promise((r) => req.on('end', r));
    const r = await worker.fetch(new Request('http://localhost:8787' + req.url, { method: req.method, headers: req.headers, body: ['GET', 'HEAD', 'OPTIONS'].includes(req.method) ? undefined : data }), env);
    res.writeHead(r.status, Object.fromEntries(r.headers)); res.end(Buffer.from(await r.arrayBuffer()));
  }).listen(8787, () => console.log('ranking server on http://localhost:8787 (admin key: test-admin)'));
} else {
  const ok = (cond, msg) => { console.log((cond ? 'PASS ' : 'FAIL ') + msg); if (!cond) process.exitCode = 1; };
  const sum = (o) => Object.assign({ elapsed: 60, eaten: 60, boxes: 10, combo: 60, lucky: 1, patrols: 0, rage: false, nightmare: false }, o);
  const realNow = Date.now; const travel = (sec) => { const a = realNow(); Date.now = () => a + sec * 1000; };
  const run = async (who, mode, score, s, sec) => { const st = await call('POST', '/api/start', { mode, xid: who.xid, nick: who.nick });
    if (st.status !== 200) return st; travel(sec || 65); const r = await call('POST', '/api/submit', { token: st.body.token, score, summary: sum(s || {}) }); Date.now = realNow; return r; };
  const A = { xid: '@Pino_Lover', nick: '피노도둑' }, B = { xid: 'kouga_fan', nick: 'コウガ推し' }, C = { xid: 'cheater', nick: '치터' };

  let r = await call('POST', '/api/start', { mode: 'normal', xid: 'not a handle!', nick: 'x' }); ok(r.status === 400, 'a bad X handle is refused');
  r = await call('POST', '/api/start', { mode: 'normal', xid: 'ok', nick: '' }); ok(r.status === 400, 'a nickname is required');
  r = await run(A, 'normal', 15000); ok(r.body.status === 'ok' && r.body.rank === 1, 'a normal run is accepted and ranked 1st');
  r = await run(A, 'normal', 9000); ok(r.body.rank === 1 && r.body.best === 15000, 'a lower run keeps the player\'s best');
  r = await run(B, 'hard', 40000, { elapsed: 150, boxes: 20, eaten: 120, combo: 120, rage: true, patrols: 10 }, 200); ok(r.body.status === 'ok' && r.body.rank === 1, 'a better player takes 1st');
  r = await run(C, 'normal', 99999999); ok(r.body.status === 'held', 'an impossible score is held back (the reason stays on the server)');
  r = await run({ xid: 'too_good', nick: '수상해' }, 'hard', 850000, { elapsed: 150, boxes: 30, eaten: 180, combo: 180, rage: true, patrols: 12 }, 200);
  ok(r.body.status === 'held', 'a possible but far-above-autoplay score waits for review');
  const st = await call('POST', '/api/start', { mode: 'normal', xid: A.xid, nick: A.nick }); travel(65);
  await call('POST', '/api/submit', { token: st.body.token, score: 100, summary: sum({}) });
  r = await call('POST', '/api/submit', { token: st.body.token, score: 100, summary: sum({}) }); Date.now = realNow;
  ok(r.status === 409, 'the same token cannot be used twice');

  let b = await call('GET', '/api/board?xid=pino_lover');
  ok(b.body.players === 2 && b.body.top.length === 2, 'the board counts each player once');
  ok(b.body.top[0].nick === 'コウガ推し' && b.body.top[0].mode === 'hard' && !('xid' in b.body.top[0]), 'board rows show nickname and mode, never the X handle');
  ok(b.body.me && b.body.me.rank === 2 && b.body.me.score === 15000, 'my rank comes back');
  ok(b.body.event.open === true && b.body.event.start && b.body.event.end, 'the event window comes back');

  r = await run({ xid: 'nm_player', nick: '폭주왕' }, 'super', 300000, { elapsed: 120, boxes: 20, eaten: 120, combo: 120, rage: true, nightmare: true, patrols: 15 }, 150);
  b = await call('GET', '/api/board');
  ok(b.body.top.some((x) => x.mode === 'super' && x.nm), 'a run that reached nightmare keeps its mode and carries the nightmare mark');

  for (let i = 0; i < 12; i++) await run({ xid: 'p' + i, nick: '플레이어' + i }, 'normal', 1000 + i);
  b = await call('GET', '/api/board?xid=p0');
  ok(b.body.top.length === 10 && b.body.me.rank > 10, 'only the top 10 are listed, my rank still shows below them');

  let a = await call('GET', '/api/admin/scores?status=rejected'); ok(a.status === 401, 'admin needs the key');
  a = await call('GET', '/api/admin/scores?status=rejected', null, { 'x-admin-key': 'test-admin' });
  ok(a.body.rows.length === 1 && a.body.rows[0].xid === 'cheater', 'admin sees the rejected run with the X handle');
  const rv = await call('GET', '/api/admin/scores?status=review', null, { 'x-admin-key': 'test-admin' });
  await call('POST', '/api/admin/scores/' + rv.body.rows[0].id, { status: 'ok' }, { 'x-admin-key': 'test-admin' });
  b = await call('GET', '/api/board'); ok(b.body.top[0].nick === '수상해', 'approving a held run puts it on the board');
  const okRow = (await call('GET', '/api/admin/scores?status=ok', null, { 'x-admin-key': 'test-admin' })).body.rows.find((x) => x.xid === 'kouga_fan');
  await call('POST', '/api/admin/scores/' + okRow.id, { status: 'deleted' }, { 'x-admin-key': 'test-admin' });
  b = await call('GET', '/api/board'); ok(!b.body.top.some((x) => x.nick === 'コウガ推し'), 'deleting takes a run off the board');

  const closed = { ...env, EVENT_START: new Date(t0 - 5 * 86400e3).toISOString(), EVENT_END: new Date(t0 - 86400e3).toISOString() };
  r = await worker.fetch(new Request('http://x/api/start', { method: 'POST', body: JSON.stringify({ mode: 'normal', xid: 'late', nick: 'late' }) }), closed);
  ok(r.status === 403, 'no runs start once the event is over');
  const page = await call('GET', '/admin'); ok(page.status === 200 && String(page.body).includes('랭킹 관리'), 'the admin page is served');
}
