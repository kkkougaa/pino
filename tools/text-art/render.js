// "Ice-cream sticker" lettering for the Kouga challenge.
// Every word is a die-cut fridge sticker: a soft shadow, a fat cream paper border, a brown ink line,
// a flavour-coloured fill with a candy gloss, and the odd sparkle. Banners sit on paper/sticker plates.
(function () {
  const R = 3;                                   // drawn 3x for sharp phones
  const INK = '#3A2416', PAPER = '#FFFBEF', SHADOW = 'rgba(58,36,22,.30)';
  const FACE = {
    display: { ko: '"Do Hyeon"', ja: '"Mochiy Pop One"', x: '"Titan One","Do Hyeon"' },
    hand:    { ko: '700 1px "Gaegu"', ja: '"Hachi Maru Pop"', x: '700 1px "Gaegu"' },
    num:     { ko: '"Titan One"', ja: '"Titan One"', x: '"Titan One"' },
  };
  // fill: top -> bottom; sp = sparkles; paper/ink: border widths as a share of the font size
  const SKINS = {
    good:   { fill: ['#7EEBCF', '#20A98B'] },          // mint
    lucky:  { fill: ['#FFA6CB', '#EC3F86'] },          // strawberry
    bad:    { fill: ['#C9D5E2', '#7F90A6'] },                 // ice
    alert:  { fill: ['#FF7A5E', '#D81F1F'] },                 // Kouga red
    warn:   { fill: ['#FFEC6E', '#FFB000'] },                 // lemon
    hint:   { fill: ['#96D4FF', '#2F86E0'] },                 // soda
    combo:  { fill: ['#FF86A4', '#E02F5C'] },          // berry
    score:  { fill: ['#FFC766', '#F07A10'] },                 // caramel
    hush:   { fill: ['#D7C7FF', '#8D6BE3'], face: 'hand' },   // lavender, handwritten
    thud:   { fill: ['#9A6644', '#4A2A18'], tilt: 1.6 },      // chocolate, heavy
    ring:   { fill: ['#FFFFFF', '#FFEFCC'], paper: 0.0, ink: 0.11 },
    ringOn: { fill: ['#FFF27A', '#FFB300'], paper: 0.0, ink: 0.11 },
    go:     { fill: ['#FFFFFF', '#FFE6D2'] },
    fever:  { fill: ['#FFFFFF', '#FFF07A'] },          // white-gold letters on the hot band
    rage:   { fill: ['#FFFFFF', '#FFD9CF'] },
    nm:     { fill: ['#FFFFFF', '#EBD9FF'] },
    unlock: { fill: ['#FFFFFF', '#FFE7A8'] },
    melt:   { fill: ['#93603D', '#43230F'] },
    pizza:  { fill: ['#FF7350', '#C8261A'] },
    gS: { fill: ['#FFF07A', '#F2A400'], sp: 1 }, gA: { fill: ['#FFA6CB', '#EC3F86'] },
    gB: { fill: ['#FFC766', '#F07A10'] }, gC: { fill: ['#7EEBCF', '#20A98B'] }, gF: { fill: ['#C9D5E2', '#7F90A6'] },
    hud:    { fill: ['#FFFFFF', '#FFF0D4'], paper: 0.0, ink: 0.12 },
    hudLow: { fill: ['#FFE5DD', '#FF8D78'], paper: 0.0, ink: 0.12, inkC: '#9E1C14' },
  };
  const cv = (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, Math.ceil(w)); c.height = Math.max(1, Math.ceil(h)); return c; };
  const rngOf = s => { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507), h = Math.imul(h ^ (h >>> 13), 3266489909), (h ^= h >>> 16) >>> 0) / 4294967296); };
  const SCALE = {};   // some faces draw small for their size (Dongle): scale them up to match
  function setFace(face, lang, css, scale) { FACE[face][lang] = css; SCALE[face + lang] = scale || 1; }
  function fontOf(face, lang, fs) { fs = Math.round(fs * (SCALE[face + lang] || 1)); const f = FACE[face][lang] || FACE[face].x; return f.includes('1px') ? f.replace('1px', fs + 'px') : fs + 'px ' + f; }

  // ---------- one line of sticker lettering ----------
  // opts.tab: fixed advance (digits); returns {c, pad, edge} (pad = empty margin, edge = sticker border width), all in canvas px
  function letters(text, skinName, size, lang, opts) {
    opts = opts || {};
    const sk = SKINS[skinName], fs = size * R, face = sk.face || (opts.num ? 'num' : 'display');
    const font = fontOf(face, lang, fs), rnd = rngOf(skinName + text);
    // Hangul syllables are dense: thinner borders keep them readable, more so at small sizes
    const dense = lang === 'ko' && face === 'display' && /[가-힣]/.test(text) ? (size < 30 ? 0.8 : 0.9) : 1;
    const inkW = fs * (sk.ink != null ? sk.ink : 0.075) * dense, paperW = fs * (sk.paper != null ? sk.paper : 0.13) * dense;
    const edge = inkW + paperW, shOff = fs * 0.07, pad = edge + fs * 0.04;
    const m = cv(4, 4).getContext('2d'); m.font = font;
    const chars = Array.from(text);
    const adv = chars.map(ch => opts.tab && /[0-9]/.test(ch) ? opts.tab * fs : m.measureText(ch).width * (opts.num ? 0.96 : 0.94));
    const tw = adv.reduce((a, b) => a + b, 0);
    const W = tw + pad * 2, H = fs * 1.18 + pad * 2 + shOff, base = pad + fs * 0.92;
    const lay = []; let x = pad;
    const wave = opts.num ? 0 : 0.05, tilt = (sk.tilt || 1) * (opts.num ? 0 : 0.06);
    chars.forEach((ch, i) => {
      const live = ch.trim() ? 1 : 0;
      lay.push({ ch, x: x + adv[i] / 2, dy: live * (Math.sin(i * 1.7 + rnd() * 2) * fs * wave), rot: live * (rnd() - 0.5) * 2 * tilt });
      x += adv[i];
    });
    const c = cv(W, H), g = c.getContext('2d');
    const each = (gg, fn) => lay.forEach(L => { gg.save(); gg.translate(L.x, base + L.dy); gg.rotate(L.rot); fn(gg, L.ch); gg.restore(); });
    const setup = gg => { gg.font = font; gg.textAlign = 'center'; gg.lineJoin = 'round'; gg.lineCap = 'round'; };
    setup(g);
    // shadow, paper border, ink line
    g.save(); g.translate(0, shOff); g.strokeStyle = SHADOW; g.fillStyle = SHADOW; g.lineWidth = edge * 2; each(g, (gg, ch) => { gg.strokeText(ch, 0, 0); gg.fillText(ch, 0, 0); }); g.restore();
    if (paperW > 0) { g.strokeStyle = PAPER; g.lineWidth = edge * 2; each(g, (gg, ch) => gg.strokeText(ch, 0, 0)); }
    g.strokeStyle = sk.inkC || INK; g.lineWidth = inkW * 2; each(g, (gg, ch) => gg.strokeText(ch, 0, 0));
    // fill + gloss, built on a mask so the gloss stays inside the letters
    const f = cv(W, H), fg = f.getContext('2d'); setup(fg);
    const gr = fg.createLinearGradient(0, base - fs * 0.85, 0, base + fs * 0.05); gr.addColorStop(0, sk.fill[0]); gr.addColorStop(1, sk.fill[1]);
    fg.fillStyle = gr; each(fg, (gg, ch) => gg.fillText(ch, 0, 0));
    fg.globalCompositeOperation = 'source-atop';
    const gl = fg.createLinearGradient(0, base - fs * 0.9, 0, base - fs * 0.38); gl.addColorStop(0, 'rgba(255,255,255,.62)'); gl.addColorStop(1, 'rgba(255,255,255,0)');
    fg.fillStyle = gl; fg.beginPath(); fg.ellipse(W / 2, base - fs * 0.9, W * 0.62, fs * 0.5, 0, 0, Math.PI * 2); fg.fill();
    fg.fillStyle = 'rgba(58,36,22,.16)'; fg.fillRect(0, base - fs * 0.08, W, fs * 0.3);          // a little weight at the foot
    g.drawImage(f, 0, 0);
    // sparkles on the top edge of a letter or two
    for (let i = 0; i < (opts.num ? 0 : sk.sp || 0); i++) { const L = lay[Math.floor((i + 0.5) / (sk.sp) * lay.length)] || lay[0]; spark(g, L.x + fs * 0.3, base + L.dy - fs * 0.86, fs * 0.17); }
    return { c, pad, edge, fs };
  }
  function spark(g, x, y, s) {
    g.save(); g.translate(x, y); g.beginPath();
    for (let i = 0; i < 8; i++) { const r = i % 2 ? s * 0.28 : s, a = i * Math.PI / 4; g.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
    g.closePath(); g.lineJoin = 'round'; g.lineWidth = s * 0.34; g.strokeStyle = INK; g.stroke(); g.fillStyle = '#FFFFFF'; g.fill(); g.restore();
  }

  // ---------- sticker shapes for banners ----------
  // draw a closed path as a sticker: shadow, paper border, ink line, fill (a colour or a gradient factory)
  function sticker(g, path, fill, u, o) {
    o = o || {};
    const paperW = o.paper != null ? o.paper : u * 0.16, inkW = u * 0.08;
    g.save(); g.lineJoin = 'round'; g.lineCap = 'round';
    g.save(); g.translate(0, u * 0.09); path(g); g.fillStyle = SHADOW; g.fill(); g.lineWidth = (paperW + inkW) * 2; g.strokeStyle = SHADOW; g.stroke(); g.restore();
    if (paperW > 0) { path(g); g.lineWidth = (paperW + inkW) * 2; g.strokeStyle = PAPER; g.stroke(); }
    path(g); g.lineWidth = inkW * 2; g.strokeStyle = o.ink || INK; g.stroke();
    path(g); g.fillStyle = typeof fill === 'function' ? fill(g) : fill; g.fill();
    if (o.gloss !== false) { g.save(); path(g); g.clip(); const b = o.box; const gl = g.createLinearGradient(0, b[1], 0, b[1] + b[3] * 0.45); gl.addColorStop(0, 'rgba(255,255,255,.45)'); gl.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gl; g.fillRect(b[0], b[1], b[2], b[3] * 0.45); g.restore(); }
    g.restore();
  }
  const lin = (y0, y1, a, b) => g => { const gr = g.createLinearGradient(0, y0, 0, y1); gr.addColorStop(0, a); gr.addColorStop(1, b); return gr; };
  function vein(g, x, y, s, col) {   // the 💢 anger mark, drawn as four bold curls
    g.save(); g.translate(x, y); g.lineCap = 'round';
    const curls = () => { g.beginPath(); [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sy]) => { g.moveTo(sx * s * 0.22, sy * s); g.quadraticCurveTo(sx * s * 0.22, sy * s * 0.22, sx * s, sy * s * 0.22); }); };
    curls(); g.lineWidth = s * 0.62; g.strokeStyle = PAPER; g.stroke();
    curls(); g.lineWidth = s * 0.42; g.strokeStyle = INK; g.stroke();
    curls(); g.lineWidth = s * 0.24; g.strokeStyle = col; g.stroke();
    g.restore();
  }
  function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
  function torn(g, x, y, w, h, rnd, step) {   // paper ripped on all four sides
    g.beginPath(); const pts = [];
    const side = (x0, y0, x1, y1) => { const n = Math.max(3, Math.round(Math.hypot(x1 - x0, y1 - y0) / step)); for (let i = 0; i < n; i++) { const t = i / n, nx = -(y1 - y0), ny = x1 - x0, l = Math.hypot(nx, ny), j = (rnd() - 0.5) * step * 0.9; pts.push([x0 + (x1 - x0) * t + nx / l * j, y0 + (y1 - y0) * t + ny / l * j]); } };
    side(x, y, x + w, y); side(x + w, y, x + w, y + h); side(x + w, y + h, x, y + h); side(x, y + h, x, y);
    pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath();
  }
  function burst(g, cx, cy, rx, ry, n, k, rnd) { g.beginPath(); for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * Math.PI * 2 - Math.PI / 2, out = i % 2 === 0, q = out ? 1 + (rnd() - 0.5) * 0.12 : k; const x = cx + Math.cos(a) * rx * q, y = cy + Math.sin(a) * ry * q; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.closePath(); }
  function scallop(g, cx, cy, rx, ry, n) { g.beginPath(); for (let i = 0; i <= 160; i++) { const a = i / 160 * Math.PI * 2, w = 1 + 0.07 * Math.cos(a * n); const x = cx + Math.cos(a) * rx * w, y = cy + Math.sin(a) * ry * w; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.closePath(); }
  function sprinkles(g, x, y, w, h, n, rnd, u) {
    const cols = ['#FF5C8A', '#5ED6B8', '#FFFFFF', '#7FC8FF', '#B07CFF', '#FFE14A'];
    for (let i = 0; i < n; i++) { g.save(); g.translate(x + rnd() * w, y + rnd() * h); g.rotate(rnd() * Math.PI); rr(g, -u * 0.18, -u * 0.06, u * 0.36, u * 0.12, u * 0.06); g.fillStyle = cols[i % cols.length]; g.fill(); g.lineWidth = u * 0.03; g.strokeStyle = 'rgba(58,36,22,.5)'; g.stroke(); g.restore(); }
  }

  // each plate gets the rendered letters (t) and returns the finished canvas
  const PLATES = {
    tag(t) {          // a memo slip held by two bits of masking tape
      const u = t.fs, mx = u * 0.55, my = u * 0.4, W = t.c.width + mx * 2, H = t.c.height + my * 2, c = cv(W + u, H + u), g = c.getContext('2d');
      g.translate(u / 2, u / 2); g.translate(W / 2, H / 2); g.rotate(-0.04); g.translate(-W / 2, -H / 2);
      const box = [u * 0.25, u * 0.3, W - u * 0.5, H - u * 0.55];
      sticker(g, gg => rr(gg, box[0], box[1], box[2], box[3], u * 0.12), '#FFF7D1', u, { box, paper: u * 0.1 });
      g.save(); rr(g, box[0], box[1], box[2], box[3], u * 0.12); g.clip(); g.strokeStyle = 'rgba(80,140,200,.25)'; g.lineWidth = u * 0.03; for (let y = box[1] + u * 0.45; y < box[1] + box[3]; y += u * 0.42) { g.beginPath(); g.moveTo(box[0], y); g.lineTo(box[0] + box[2], y); g.stroke(); } g.restore();
      [[box[0] + u * 0.2, box[1], -0.5], [box[0] + box[2] - u * 0.2, box[1], 0.5]].forEach(([x, y, a]) => { g.save(); g.translate(x, y); g.rotate(a); g.fillStyle = 'rgba(247,196,160,.85)'; g.fillRect(-u * 0.45, -u * 0.14, u * 0.9, u * 0.3); g.restore(); });
      g.drawImage(t.c, mx, my); return c;
    },
    stamp(t, rnd) {   // a round scalloped badge
      const u = t.fs, W = t.c.width + u * 1.1, H = Math.max(t.c.height + u * 0.9, W * 0.62), c = cv(W + u, H + u), g = c.getContext('2d'), cx = c.width / 2, cy = c.height / 2;
      const box = [cx - W / 2, cy - H / 2, W, H];
      g.save(); g.translate(cx, cy); g.rotate(-0.05); g.translate(-cx, -cy);
      sticker(g, gg => scallop(gg, cx, cy, W / 2 - u * 0.15, H / 2 - u * 0.15, 14), lin(box[1], box[1] + H, '#FF7C93', '#D9214F'), u, { box });
      g.restore();
      spark(g, cx + W * 0.36, cy - H * 0.3, u * 0.2);
      g.drawImage(t.c, cx - t.c.width / 2, cy - t.c.height / 2); return c;
    },
    fever(t, rnd) {   // arcade jackpot: a gold sunburst, a slanted hot-pink band, speed lines either side
      const u = t.fs, W = t.c.width + u * 1.3, H = t.c.height + u * 0.35, sk = u * 0.45;
      const c = cv(W + sk * 2 + u * 3.2, H + u * 3), g = c.getContext('2d'), cx = c.width / 2, cy = c.height / 2;
      const rx = W * 0.5 + u * 0.9, ry = H * 0.5 + u * 1.15, br = rngOf('fever' + W);
      const sun = gg => burst(gg, cx, cy, rx, ry, 16, 0.74, rngOf('fever' + W));
      sticker(g, sun, lin(cy - ry, cy + ry, '#FFEB6B', '#FFAE00'), u, { box: [cx - rx, cy - ry, rx * 2, ry * 2], gloss: false });
      g.save(); sun(g); g.clip(); for (let i = 0; i < 16; i++) { const a0 = i / 16 * Math.PI * 2, a1 = a0 + Math.PI / 16; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a0) * rx * 2, cy + Math.sin(a0) * ry * 2); g.lineTo(cx + Math.cos(a1) * rx * 2, cy + Math.sin(a1) * ry * 2); g.closePath(); g.fillStyle = 'rgba(255,120,0,.28)'; g.fill(); } g.restore();
      // speed lines
      g.lineCap = 'round';
      [-1, 1].forEach(sd => [[-0.28, 1.0], [0, 1.25], [0.28, 0.85]].forEach(([fy, len]) => { const y = cy + fy * H, x0 = cx + sd * (W / 2 + sk + u * 0.25), x1 = x0 + sd * u * len;
        g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.lineWidth = u * 0.3; g.strokeStyle = INK; g.stroke(); g.lineWidth = u * 0.16; g.strokeStyle = '#FFFFFF'; g.stroke(); }));
      const x0 = cx - W / 2, y0 = cy - H / 2, box = [x0 - sk, y0, W + sk * 2, H];
      const band = gg => { gg.beginPath(); gg.moveTo(x0 + sk, y0); gg.lineTo(x0 + W + sk, y0); gg.lineTo(x0 + W - sk, y0 + H); gg.lineTo(x0 - sk, y0 + H); gg.closePath(); };
      sticker(g, band, lin(y0, y0 + H, '#FF5C9A', '#E0261B'), u, { box });
      g.save(); band(g); g.clip(); g.fillStyle = 'rgba(255,255,255,.14)'; for (let i = -2; i < 9; i++) { const x = x0 + i * u * 1.1; g.beginPath(); g.moveTo(x, y0 + H); g.lineTo(x + u * 0.45, y0 + H); g.lineTo(x + u * 0.95, y0); g.lineTo(x + u * 0.5, y0); g.closePath(); g.fill(); } g.restore();
      spark(g, cx + W * 0.5 + sk * 0.3, y0 - u * 0.1, u * 0.24);
      g.drawImage(t.c, cx - t.c.width / 2, cy - t.c.height / 2); return c;
    },
    rage(t, rnd) { return PLATES._torn(t, rnd, ['#FF5D4A', '#B5121B'], '#E0261B', false); },
    nm(t, rnd) { return PLATES._torn(t, rnd, ['#A66BFF', '#4B1690'], '#8A2BE2', true); },
    _torn(t, rnd, cols, veinC, glitch) {   // a strip of torn coloured paper with anger marks
      const u = t.fs, W = t.c.width + u * 1.1, H = t.c.height + u * 0.6, c = cv(W + u * 1.6, H + u * 1.6), g = c.getContext('2d'), x0 = u * 0.8, y0 = u * 0.8, box = [x0, y0, W, H];
      g.save(); g.translate(c.width / 2, c.height / 2); g.rotate(-0.035); g.translate(-c.width / 2, -c.height / 2);
      const path = gg => torn(gg, x0, y0, W, H, rngOf('t' + W), u * 0.32);
      sticker(g, path, lin(y0, y0 + H, cols[0], cols[1]), u, { box });
      if (glitch) { g.save(); path(g); g.clip(); for (let i = 0; i < 5; i++) { g.fillStyle = i % 2 ? 'rgba(255,255,255,.12)' : 'rgba(20,0,40,.18)'; g.fillRect(x0, y0 + rnd() * H, W, u * (0.06 + rnd() * 0.12)); } g.restore(); }
      g.restore();
      vein(g, x0 + W - u * 0.05, y0 + u * 0.05, u * 0.42, veinC); vein(g, x0 + u * 0.1, y0 + H - u * 0.05, u * 0.3, veinC);
      g.drawImage(t.c, x0 + (W - t.c.width) / 2, y0 + (H - t.c.height) / 2); return c;
    },
    ribbon(t, rnd) {   // a red ribbon with notched tails
      const u = t.fs, W = t.c.width + u * 0.8, H = t.c.height + u * 0.25, tail = u * 1.1, c = cv(W + tail * 2 + u, H + u * 1.4), g = c.getContext('2d'), x0 = tail + u / 2, y0 = u * 0.5, box = [x0, y0, W, H];
      [[-1, x0 + u * 0.2], [1, x0 + W - u * 0.2]].forEach(([s, x]) => sticker(g, gg => { gg.beginPath(); gg.moveTo(x, y0 + u * 0.35); gg.lineTo(x + s * tail, y0 + u * 0.35); gg.lineTo(x + s * tail * 0.7, y0 + H / 2 + u * 0.35); gg.lineTo(x + s * tail, y0 + H + u * 0.35); gg.lineTo(x, y0 + H + u * 0.35); gg.closePath(); }, '#A3141E', u, { box, gloss: false }));
      sticker(g, gg => rr(gg, x0, y0, W, H, u * 0.12), lin(y0, y0 + H, '#FF5A4A', '#C81D25'), u, { box });
      spark(g, x0 + W - u * 0.1, y0 - u * 0.05, u * 0.2);
      g.drawImage(t.c, x0 + (W - t.c.width) / 2, y0 + (H - t.c.height) / 2); return c;
    },
    cloud(t, rnd) {   // a hushed thought bubble
      const u = t.fs, W = t.c.width + u * 1.4, H = t.c.height + u * 0.9, c = cv(W + u * 1.6, H + u * 1.6), g = c.getContext('2d'), cx = c.width / 2, cy = c.height / 2 - u * 0.2, box = [cx - W / 2, cy - H / 2, W, H];
      const blobs = []; const n = 11; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2; blobs.push([cx + Math.cos(a) * W * 0.4, cy + Math.sin(a) * H * 0.34, H * (0.3 + rnd() * 0.06)]); }
      const path = gg => { gg.beginPath(); blobs.forEach(([x, y, r]) => { gg.moveTo(x + r, y); gg.arc(x, y, r, 0, Math.PI * 2); }); gg.moveTo(cx + W * 0.42, cy); gg.ellipse(cx, cy, W * 0.42, H * 0.36, 0, 0, Math.PI * 2); };
      sticker(g, path, '#F3EDFF', u, { box, gloss: false });
      [[0.38, 0.62, 0.16], [0.47, 0.8, 0.1]].forEach(([fx, fy, r]) => sticker(g, gg => { gg.beginPath(); gg.arc(cx + W * fx, cy + H * fy, u * r * 1.6, 0, Math.PI * 2); }, '#F3EDFF', u, { box, gloss: false, paper: u * 0.08 }));
      g.drawImage(t.c, cx - t.c.width / 2, cy - t.c.height / 2); return c;
    },
    caught(t, rnd) {   // a rubber stamp slammed on at an angle
      const u = t.fs, W = t.c.width + u * 0.9, H = t.c.height + u * 0.5, c = cv(W + u * 1.4, H + u * 1.8), g = c.getContext('2d'), cx = c.width / 2, cy = c.height / 2, box = [cx - W / 2, cy - H / 2, W, H];
      g.save(); g.translate(cx, cy); g.rotate(-0.09); g.translate(-cx, -cy);
      sticker(g, gg => rr(gg, box[0], box[1], W, H, u * 0.2), '#FFF4EE', u, { box, gloss: false });
      g.save(); rr(g, box[0] + u * 0.16, box[1] + u * 0.16, W - u * 0.32, H - u * 0.32, u * 0.12); g.lineWidth = u * 0.1; g.strokeStyle = '#D81F1F'; g.setLineDash([u * 0.5, u * 0.12, u * 0.9, u * 0.1]); g.stroke(); g.restore();
      g.drawImage(t.c, cx - t.c.width / 2, cy - t.c.height / 2); g.restore(); return c;
    },
    melt(t, rnd) {     // chocolate letters dripping onto the floor
      const u = t.fs, drip = u * 0.9, c = cv(t.c.width + u * 0.4, t.c.height + drip + u * 0.3), g = c.getContext('2d'), x0 = u * 0.2, base = x0 + t.c.height - u * 0.62;
      const n = Math.max(4, Math.round(t.c.width / (u * 0.8)));
      for (let i = 0; i < n; i++) { const x = x0 + t.c.width * (0.12 + 0.76 * (i + rnd() * 0.5) / n), r = u * (0.1 + rnd() * 0.06), d = drip * (0.35 + rnd() * 0.65);
        sticker(g, gg => { gg.beginPath(); gg.moveTo(x - r, base - u * 0.2); gg.lineTo(x - r, base + d - r); gg.arc(x, base + d - r, r, Math.PI, 0, true); gg.lineTo(x + r, base - u * 0.2); gg.closePath(); }, lin(base, base + d, '#7A4A2E', '#43230F'), u, { box: [x - r, base, r * 2, d], gloss: false, paper: u * 0.09 }); }
      g.drawImage(t.c, x0, x0 * 0.5); return c;
    },
    pizza(t, rnd) {    // a slice of pizza waving next to the words
      const u = t.fs, s = t.c.height * 0.95, c = cv(t.c.width + s * 0.9, t.c.height + u * 0.4), g = c.getContext('2d'), cx = s * 0.48, cy = c.height / 2;
      g.save(); g.translate(cx, cy); g.rotate(-0.3);
      const box = [-s / 2, -s / 2, s, s];
      sticker(g, gg => { gg.beginPath(); gg.moveTo(0, s * 0.42); gg.lineTo(-s * 0.36, -s * 0.3); gg.quadraticCurveTo(0, -s * 0.48, s * 0.36, -s * 0.3); gg.closePath(); }, lin(-s * 0.4, s * 0.4, '#FFE27A', '#FFB830'), u * 0.7, { box });
      g.beginPath(); g.moveTo(-s * 0.36, -s * 0.3); g.quadraticCurveTo(0, -s * 0.48, s * 0.36, -s * 0.3); g.lineWidth = s * 0.1; g.strokeStyle = '#C9803A'; g.stroke();
      [[-0.1, -0.12], [0.12, -0.05], [0, 0.15]].forEach(([x, y]) => { g.beginPath(); g.arc(x * s, y * s, s * 0.07, 0, Math.PI * 2); g.fillStyle = '#D8352A'; g.fill(); g.lineWidth = s * 0.02; g.strokeStyle = INK; g.stroke(); });
      g.restore(); g.drawImage(t.c, s * 0.82, (c.height - t.c.height) / 2); return c;
    },
  };

  function icon(kind, size) {   // a little heart or star sticker
    const u = size * R, s = u * 0.78, c = cv(s + u * 0.5, s + u * 0.55), g = c.getContext('2d'), cx = c.width / 2, cy = c.height / 2 - u * 0.03;
    const heart = gg => { gg.beginPath(); gg.moveTo(cx, cy + s * 0.42); gg.bezierCurveTo(cx - s * 0.62, cy, cx - s * 0.5, cy - s * 0.52, cx, cy - s * 0.2); gg.bezierCurveTo(cx + s * 0.5, cy - s * 0.52, cx + s * 0.62, cy, cx, cy + s * 0.42); gg.closePath(); };
    const star = gg => { gg.beginPath(); for (let i = 0; i < 10; i++) { const r = i % 2 ? s * 0.25 : s * 0.52, a = -Math.PI / 2 + i * Math.PI / 5; gg.lineTo(cx + Math.cos(a) * r, cy + s * 0.04 + Math.sin(a) * r); } gg.closePath(); };
    const box = [cx - s / 2, cy - s / 2, s, s];
    g.translate(cx, cy); g.rotate(kind === 'heart' ? -0.18 : 0.12); g.translate(-cx, -cy);
    sticker(g, kind === 'heart' ? heart : star, kind === 'heart' ? lin(box[1], box[1] + s, '#FF9BC2', '#EC3F86') : lin(box[1], box[1] + s, '#FFF07A', '#F2A400'), u * 0.75, { box });
    return c;
  }
  function withIcon(t, kind, size) {
    const ic = icon(kind, size), tuck = t.pad * 1.1, c = cv(ic.width + t.c.width - tuck, Math.max(ic.height, t.c.height)), g = c.getContext('2d');
    g.drawImage(t.c, ic.width - tuck, (c.height - t.c.height) / 2); g.drawImage(ic, 0, (c.height - ic.height) / 2 - size * R * 0.04);
    return c;
  }
  function renderItem(it, lang) {
    const text = it.x != null ? it.x : it[lang];
    const t = letters(text, it.style, it.size, lang);
    const c = it.plate ? PLATES[it.plate](t, rngOf(it.key + lang)) : it.icon ? withIcon(t, it.icon, it.size) : t.c;
    return { key: it.key, lang: it.x != null ? 'x' : lang, c, s: it.size, p: t.pad / R };
  }
  function renderDigits(set, chars, size) {
    const m = cv(4, 4).getContext('2d'); m.font = size * R + 'px "Titan One"';
    const tab = Math.max(...'0123456789'.split('').map(d => m.measureText(d).width)) / (size * R) * 0.95;
    return Array.from(chars).map(ch => { const t = letters(ch, set, size, 'x', { num: true, tab }); return { set, ch, c: t.c, s: size, p: t.pad / R, e: t.edge / R, o: (2 * (t.pad - t.edge) + t.edge) / R }; });   // o: how far the next glyph tucks in: the paper borders merge, the ink lines stay apart
  }
  async function fontsReady(cat) {
    const all = [...cat.feedback, ...cat.grades, ...cat.banners];
    const loads = [];
    for (const lang of ['ko', 'ja']) {
      const txt = all.map(i => i.x != null ? i.x : i[lang]).join('');
      for (const face of ['display', 'hand']) loads.push(document.fonts.load(fontOf(face, lang, 40), txt));
    }
    loads.push(document.fonts.load('40px "Titan One"', cat.digits.chars + 'SABCFPINO!?…'));
    await Promise.all(loads); await document.fonts.ready;
  }
  window.TextArt = { R, setFace, letters, renderItem, renderDigits, fontsReady, SKINS, PLATES };
})();
