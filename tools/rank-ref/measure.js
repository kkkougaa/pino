// Score reference curve for the ranking checks: autoplay a mode taking every bonus, and record the score at each second.
//   node tools/rank-ref/measure.js <normal|hard|super> [seconds]      (needs Playwright with Chromium)
// "Every bonus": every box has a heart / star, and when Kouga is on his way
// it keeps eating (the x5 dare) until the last moment before hiding. The result is merged into server/src/ref_curve.js.
// Runs in a headless browser in game time, so it is slow (a minute of game time can take 10-20 minutes): leave it running.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '../..'), OUT = path.join(ROOT, 'server/src/ref_curve.js'), CACHE = path.join(__dirname, '.cache');
const mode = process.argv[2], secs = +(process.argv[3] || (mode === 'normal' ? 80 : 300));
if (!['normal', 'hard', 'super'].includes(mode)) { console.error('mode: normal | hard | super'); process.exit(1); }

// a copy of the game with the "every bonus" changes and a per-second recorder
fs.mkdirSync(CACHE, { recursive: true });
let html = fs.readFileSync(path.join(ROOT, 'pino.html'), 'utf8');
const swap = (a, b) => { if (!html.includes(a)) throw new Error('pino.html changed; update measure.js: ' + a.slice(0, 60)); html = html.replace(a, b); };
swap("const lr=rnd(); if(lr<0.11)", "const lr=rnd()*0.11; if(lr<0.11)");   // every box lucky
swap("  if(kouga&&exposed()){ if(boxShowing()) coverBox(); else preHide(); return; }",
     "  if(kouga&&exposed()&&!(patrol.phase==='warn'&&patrol.t>0.35&&state==='eat')){ if(boxShowing()) coverBox(); else preHide(); return; }");   // eat on while he comes
swap("    if(state!=='swat'&&!held){ runT+=dt;", "    if(state!=='swat'&&!held){ runT+=dt; while(window.__rec&&runT>=window.__rec.length) window.__rec.push(score);");
swap("const RANK_API='local';", "const RANK_API='';");   // no ranking event in the copy: its start popup would hold the run
swap("fontsReady.then(init,init);", "window.__rec=[]; window.__st=()=>({state,score,runT});fontsReady.then(init,init);");
const page = path.join(CACHE, 'measure.html'); fs.writeFileSync(page, html);

(async () => {
  const { chromium } = require('playwright');
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 360, height: 640 } });
  p.on('pageerror', (e) => console.error('page error:', e.message));
  // offline copies, when present (a sandbox without CDN access): .cache/three.min.js, .cache/gfonts.css
  const local = (f) => path.join(CACHE, f);
  if (fs.existsSync(local('three.min.js'))) await p.route('**/three.min.js', (r) => r.fulfill({ path: local('three.min.js'), contentType: 'application/javascript' }));
  if (fs.existsSync(local('gfonts.css'))) await p.route('https://fonts.googleapis.com/**', (r) => r.fulfill({ path: local('gfonts.css'), contentType: 'text/css' }));
  await p.addInitScript((m) => { const L = localStorage; L.setItem('kouga-tut', '1'); ['hard', 'super', 'nm'].forEach((k) => L.setItem('kouga-intro-' + k, '1'));
    ['sus', 'warn', 'watch', 'melt', 'snap', 'pizza', 'fake', 'rage', 'silent', 'recheck', 'feint'].forEach((k) => L.setItem('kouga-coach-' + k, '1'));
    L.setItem('kouga-mode', m); L.setItem('kouga-bgm', '0'); L.setItem('kouga-sfx', '0'); L.setItem('kouga-super', '1'); }, mode);
  await p.goto('file://' + page + '?auto'); await p.waitForSelector('#boot', { state: 'detached', timeout: 120000 });
  await p.click('#go');
  let last = 0;
  for (;;) { await p.waitForTimeout(3000); const s = await p.evaluate(() => window.__st());
    if (s.runT - last >= 10) { last = s.runT; console.log(mode, Math.floor(s.runT) + 's', s.score); }
    if (s.state === 'over' || s.runT >= secs) break; }
  const rec = await p.evaluate(() => window.__rec); await b.close();
  // merge into server/src/ref_curve.js
  let cur = {}; try { cur = JSON.parse(fs.readFileSync(OUT, 'utf8').replace(/^[\s\S]*?=\s*/, '').replace(/;\s*$/, '')); } catch (e) {}
  cur[mode] = rec;
  fs.writeFileSync(OUT, '// Score at each game second for autoplay taking every bonus (tools/rank-ref/measure.js). Index = second.\n// Used by rules.js: a run scoring well above this for its play time waits for review.\nexport const REF_CURVE = ' + JSON.stringify(cur) + ';\n');
  console.log(mode, 'recorded', rec.length, 'seconds, final', rec[rec.length - 1]);
})().catch((e) => { console.error(e.message); process.exit(1); });
