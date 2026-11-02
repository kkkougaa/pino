// Text art builder.
//   npm run build  -> draws every entry of catalog.js into ../../assets/text/ (WebP) and embeds the set in pino.html
//   npm run embed  -> only re-embeds what is in assets/text/ (after you swap in your own picture with the same name)
// Needs Playwright with Chromium (preinstalled in Claude Code cloud sessions; elsewhere: npx playwright install chromium).
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '../..'), OUT = path.join(ROOT, 'assets/text'), GAME = path.join(ROOT, 'pino.html');
const CHAR_FILE = { '+': 'plus', '−': 'minus', '×': 'times', '.': 'dot', ',': 'comma' };
const fileOfChar = ch => CHAR_FILE[ch] || ch;

// the memo hand (Goding) lives inside pino.html as a data URL: lift it out for the renderer
function godingFont() {
  const m = fs.readFileSync(GAME, 'utf8').match(/font-family:"Goding";src:url\(data:font\/woff2;base64,([A-Za-z0-9+/=]+)\)/);
  if (!m) throw new Error('Goding font not found in pino.html');
  fs.mkdirSync(path.join(__dirname, '.cache'), { recursive: true }); fs.writeFileSync(path.join(__dirname, '.cache/goding.woff2'), Buffer.from(m[1], 'base64'));
}
async function draw() {
  godingFont();
  const { chromium } = require('playwright');
  const b = await chromium.launch(), p = await b.newPage();
  p.on('pageerror', e => console.error('render error:', e.message));
  await p.goto('file://' + path.join(__dirname, 'render.html'));
  const res = await p.evaluate(async () => {
    const C = CATALOG; await TextArt.fontsReady(C);
    const url = c => c.toDataURL('image/webp', 0.86), words = [], nums = [];
    for (const it of [...C.feedback, ...C.grades, ...C.banners]) for (const lang of it.x != null ? ['x'] : ['ko', 'ja']) {
      const r = TextArt.renderItem(it, lang === 'x' ? 'ko' : lang); words.push({ lang, key: it.key, s: r.s, p: r.p, u: url(r.c) });
    }
    for (const set of C.digits.sets) TextArt.renderDigits(set, C.digits.chars, C.digits.size).forEach(d => nums.push({ set, ch: d.ch, s: d.s, p: d.p, o: d.o, u: url(d.c) }));
    const big = (c, k) => { const o = document.createElement('canvas'); o.width = c.width * k; o.height = c.height * k; const g = o.getContext('2d'); g.imageSmoothingEnabled = false; g.drawImage(c, 0, 0, o.width, o.height); return o.toDataURL('image/png'); };
    const pix = { logo: PixelArt.logoCanvas(), box: PixelArt.boxCanvas() };
    return { R: TextArt.R, words, nums, pix: Object.fromEntries(Object.entries(pix).map(([k, c]) => [k, { u: big(c, 1), w: c.width, h: c.height }])) };
  });
  await b.close();
  fs.rmSync(OUT, { recursive: true, force: true });
  const man = { R: res.R, words: {}, nums: {} };
  const save = (rel, u) => { const f = path.join(OUT, rel); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, Buffer.from(u.split(',')[1], 'base64')); };
  for (const w of res.words) { save(`${w.lang}/${w.key}.webp`, w.u); (man.words[w.lang] = man.words[w.lang] || {})[w.key] = { s: w.s, p: +w.p.toFixed(2) }; }
  for (const n of res.nums) { save(`num/${n.set}/${fileOfChar(n.ch)}.webp`, n.u); const m = man.nums[n.set] = man.nums[n.set] || { s: n.s, p: +n.p.toFixed(2), o: +n.o.toFixed(2), chars: '' }; m.chars += n.ch; }
  for (const k in res.pix) save(`pixel/${k}.png`, res.pix[k].u);   // 1 cell = 1 pixel; the page scales them up
  fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(man, null, 1));
  console.log(`drew ${res.words.length} word images and ${res.nums.length} digits into ${path.relative(ROOT, OUT)}/`);
}

// image size straight from the file header (WebP or PNG), so a swapped-in picture needs no extra info
function sizeOf(buf) {
  if (buf.toString('ascii', 0, 4) === 'RIFF') {
    const kind = buf.toString('ascii', 12, 16);
    if (kind === 'VP8X') return [1 + buf.readUIntLE(24, 3), 1 + buf.readUIntLE(27, 3)];
    if (kind === 'VP8L') { const b = buf.readUInt32LE(21); return [1 + (b & 0x3FFF), 1 + ((b >> 14) & 0x3FFF)]; }
    if (kind === 'VP8 ') return [buf.readUInt16LE(26) & 0x3FFF, buf.readUInt16LE(28) & 0x3FFF];
  }
  if (buf.readUInt32BE(0) === 0x89504E47) return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
  throw new Error('not a WebP/PNG file');
}
function embed() {
  const man = JSON.parse(fs.readFileSync(path.join(OUT, 'manifest.json'), 'utf8')), R = man.R;
  const pick = (dir, name) => { for (const ext of ['webp', 'png']) { const f = path.join(OUT, dir, name + '.' + ext); if (fs.existsSync(f)) return [f, ext]; } throw new Error('missing ' + dir + '/' + name); };
  const data = (f, ext) => { const buf = fs.readFileSync(f), [w, h] = sizeOf(buf); return ['data:image/' + ext + ';base64,' + buf.toString('base64'), +(w / R).toFixed(1), +(h / R).toFixed(1)]; };
  // TEXT_ART.w[lang][key] = [url, width, height (CSS px at size s), s, pad]; TEXT_ART.n[set] = {s, p, o, c:{char:[url, w, h]}}
  const out = { w: {}, n: {} };
  for (const lang in man.words) { out.w[lang] = {}; for (const key in man.words[lang]) { const m = man.words[lang][key], [f, ext] = pick(lang, key); out.w[lang][key] = [...data(f, ext), m.s, m.p]; } }
  for (const set in man.nums) { const m = man.nums[set]; out.n[set] = { s: m.s, p: m.p, o: m.o, c: {} }; for (const ch of m.chars) { const [f, ext] = pick('num/' + set, fileOfChar(ch)); out.n[set].c[ch] = data(f, ext); } }
  const line = 'const TEXT_ART=' + JSON.stringify(out) + ';';
  let html = fs.readFileSync(GAME, 'utf8'); const re = /^const TEXT_ART=.*;$/m;
  if (!re.test(html)) throw new Error('pino.html has no "const TEXT_ART=" line to replace');
  html = html.replace(re, () => line);
  // the loading screen's pixel art: <img id="bootLogo|bootBox" ... src="..."> with its cell size as width/height
  for (const [id, name, k] of [['bootLogo', 'logo', 3], ['bootBox', 'box', 3]]) {   // k: CSS px per cell
    const own = path.join(ROOT, 'assets', name + '.png');   // a hand-made picture (1 cell = 1 pixel) wins over the drawn one: assets/logo.png
    const f = fs.existsSync(own) ? own : path.join(OUT, 'pixel', name + '.png'), buf = fs.readFileSync(f), [w, h] = sizeOf(buf), url = 'data:image/png;base64,' + buf.toString('base64');
    const tag = new RegExp(`<img id="${id}"[^>]*>`); if (!tag.test(html)) throw new Error(`pino.html has no <img id="${id}">`);
    html = html.replace(tag, () => `<img id="${id}" width="${w * k}" height="${h * k}" alt="" src="${url}">`);
  }
  fs.writeFileSync(GAME, html);
  console.log(`embedded text art into pino.html (${(line.length / 1024).toFixed(0)} KB)`);
}

(async () => {
  if (process.argv[2] !== 'embed') await draw();
  embed();
})().catch(e => { console.error(e.message); process.exit(1); });
