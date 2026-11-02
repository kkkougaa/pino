// Real pixel art for the loading screen: the pino box sprite and the "코우가 챌린지" logo.
// Every cell is one square pixel; the page scales them up by whole numbers with image-rendering:pixelated.
// The logo letters are Galmuri11 Bold (the in-game pixel face) drawn at its native 12px and thresholded, so no cell is half-on.
window.PixelArt = (() => {
  const INK = '#3A2416';
  // the box top in cells (40 x 26, the package's 1.56 : 1): red lid, white oval, the pino wordmark, chocolate pinos, white dots
  function boxRows() {
    const W = 40, H = 26, g = Array.from({ length: H }, () => Array(W).fill('R'));
    const put = (x, y, ch) => { if (x >= 0 && y >= 0 && x < W && y < H) g[y][x] = ch; };
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const dx = (x + 0.5 - 20.5) / 17, dy = (y + 0.5 - 13.5) / 8.6; if (dx * dx + dy * dy <= 1) g[y][x] = 'W'; }
    const L = {
      p: ['#####.', '######', '##..##', '##..##', '######', '#####.', '##....', '##....'],
      i: ['##', '##', '..', '##', '##', '##', '##', '##', '##'],
      n: ['#####.', '######', '##..##', '##..##', '##..##', '##..##'],
      o: ['.####.', '######', '##..##', '##..##', '######', '.####.'],
    };
    const word = [['p', 0, 0], ['i', 7, -3], ['n', 10, 0], ['o', 17, 0]], x0 = 9, y0 = 11;
    for (const [k, dx, dy] of word) L[k].forEach((r, y) => [...r].forEach((c, x) => { if (c === '#') put(x0 + dx + x, y0 + dy + y, 'r'); }));
    const PINO = ['..cccc..', '.cCCCCc.', 'cCCCCCCC', 'CCCCCCCC', '.CCCCCC.', '..dddd..'];
    for (const [px, py] of [[30, 1], [2, 19]]) PINO.forEach((r, y) => [...r].forEach((c, x) => { if (c !== '.') put(px + x, py + y, c); }));
    for (const [x, y] of [[4, 3], [5, 3], [4, 4], [5, 4], [36, 21], [36, 22], [37, 21], [37, 22], [13, 2], [26, 23]]) put(x, y, 'W');
    for (let x = 0; x < W; x++) { g[0][x] = g[H - 1][x] = 'K'; } for (let y = 0; y < H; y++) { g[y][0] = g[y][W - 1] = 'K'; }
    return g.map(r => r.join(''));
  }
  const PAL = { K: INK, R: '#E2332B', r: '#D3241F', W: '#FFFFFF', C: '#5A3020', c: '#8A5434', d: '#3E1F14' };
  function boxCanvas() {
    const own = window.BOX_IMG;   // a hand-made sprite (assets/box.png, 1 cell = 1 pixel) wins over the drawn one
    if (own && own.complete && own.naturalWidth) { const c = document.createElement('canvas'); c.width = own.naturalWidth; c.height = own.naturalHeight; c.getContext('2d').drawImage(own, 0, 0); return c; }
    const rows = boxRows(), c = document.createElement('canvas'); c.width = rows[0].length; c.height = rows.length + 1;
    const g = c.getContext('2d');
    g.fillStyle = 'rgba(58,36,22,.35)'; g.fillRect(1, rows.length, rows[0].length - 1, 1);   // one-cell drop shadow
    rows.forEach((r, y) => [...r].forEach((ch, x) => { g.fillStyle = PAL[ch]; g.fillRect(x, y, 1, 1); }));
    return c;
  }
  // a line of Galmuri11 Bold as a 0/1 cell mask at its native size
  function mask(text, px = 12) {
    const c = document.createElement('canvas'), g = c.getContext('2d'); g.font = `700 ${px}px "Galmuri11"`;
    const w = Math.ceil(g.measureText(text).width) + 2, h = px + 4; c.width = w; c.height = h;
    g.font = `700 ${px}px "Galmuri11"`; g.fillStyle = '#000'; g.fillText(text, 1, px + 1);   // alphabetic baseline on a whole pixel: at 12px every cell is fully on or off
    const d = g.getImageData(0, 0, w, h).data, m = [];
    for (let y = 0; y < h; y++) { m.push([]); for (let x = 0; x < w; x++) m[y].push(d[(y * w + x) * 4 + 3] >= 128 ? 1 : 0); }
    // trim empty rows/cols
    let t = 0, b = h - 1, l = 0, r = w - 1; const rowE = y => m[y].every(v => !v), colE = x => m.every(row => !row[x]);
    while (t < b && rowE(t)) t++; while (b > t && rowE(b)) b--; while (l < r && colE(l)) l++; while (r > l && colE(r)) r--;
    return m.slice(t, b + 1).map(row => row.slice(l, r + 1));
  }
  // paint a mask with a two-tone fill, a one-cell ink outline and a one-cell drop under it
  function stamp(g, m, ox, oy, top, bot) {
    const H = m.length, W = m[0].length, on = (x, y) => y >= 0 && x >= 0 && y < H && x < W && m[y][x];
    const ring = (x, y) => !on(x, y) && [-1, 0, 1].some(a => [-1, 0, 1].some(b => on(x + a, y + b)));
    g.fillStyle = INK;
    for (let y = -1; y <= H + 1; y++) for (let x = -1; x <= W; x++) if (on(x, y) || ring(x, y) || ring(x, y - 1) || on(x, y - 1) || on(x, y - 2) || ring(x, y - 2)) g.fillRect(ox + x, oy + y, 1, 1);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (m[y][x]) { g.fillStyle = y < H * 0.55 ? top : bot; g.fillRect(ox + x, oy + y, 1, 1); }
  }
  function logoCanvas() {
    const a = mask('코우가'), b = mask('챌린지');
    const bw = b[0].length * 2, bh = b.length * 2;   // the big line is the 12px face doubled, cell for cell
    const big = b.flatMap(r => { const rr = r.flatMap(v => [v, v]); return [rr, rr.slice()]; });
    const tagW = a[0].length + 6, tagH = a.length + 5;
    const W = Math.max(bw, tagW) + 6, H = tagH + bh + 6, c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d');
    // the red tape behind "코우가": ink edge, red body, one shadow row
    const tx = Math.round((W - tagW) / 2), ty = 1;
    g.fillStyle = INK; g.fillRect(tx - 1, ty - 1, tagW + 2, tagH + 3);
    g.fillStyle = '#E2332B'; g.fillRect(tx, ty, tagW, tagH);
    g.fillStyle = '#F26A55'; g.fillRect(tx, ty, tagW, 1);
    stamp(g, a, tx + 3, ty + 2, '#FFFBEF', '#FFE6C8');
    stamp(g, big, Math.round((W - bw) / 2), tagH + 3, '#FFE14A', '#F2A821');
    return c;
  }
  return { boxRows, boxCanvas, logoCanvas };
})();
