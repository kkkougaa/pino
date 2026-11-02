// Every piece of lettering the game shows, pre-rendered by build.js.
//   key   : the name the game asks for (pino.html: artOf(key))
//   ko/ja : the text per language; x = the same in both languages
//   style : the lettering skin (see SKINS in render.js)
//   size  : the size it is shown at, in CSS px (it is drawn 3x larger so it stays sharp)
//   plate : an optional banner drawn behind the letters (see PLATES in render.js)
// Edit a line here and run `npm run build` to redraw it. To use your own picture for one, drop it in
// assets/text/<lang>/<key>.webp (same name) and run `npm run embed`.
window.CATALOG = {
  // ---- judgement & feedback (word parts; numbers are added from the digit sets) ----
  feedback: [
    { key: 'w_perfect',   ko: '퍼펙트!',        ja: 'パーフェクト！',   style: 'good',  size: 24 },
    { key: 'fx_nice',     ko: '나이스!',        ja: 'ナイス！',         style: 'good',  size: 24 },
    { key: 'fx_miss',     ko: '미스 −1초',      ja: 'ミス −1秒',        style: 'bad',   size: 22 },
    { key: 'w_miss',      ko: '미스',           ja: 'ミス',             style: 'bad',   size: 22 },
    { key: 'w_speed',     ko: '스피드 보너스',  ja: 'スピードボーナス', style: 'good',  size: 24 },
    { key: 'fx_heart',    ko: '하트',           ja: 'ハート',           style: 'lucky', size: 28 },
    { key: 'fx_star',     ko: '별',             ja: 'ほし',             style: 'lucky', size: 28 },
    { key: 'w_combo',     ko: '콤보!',          ja: 'コンボ！',         style: 'combo', size: 40 },
    { key: 'fx_break',    ko: '콤보 끊김…',     ja: 'コンボきれた…',    style: 'bad',   size: 22 },
    { key: 'fx_snap',     ko: '띠 끊김!',       ja: '帯が切れた！',     style: 'alert', size: 34 },
    { key: 'w_safe',      ko: '안 들켰다!',     ja: 'バレなかった！',   style: 'good',  size: 24 },
    { key: 'w_streak',    ko: '연속!',          ja: '連続！',           style: 'good',  size: 24 },
    { key: 'w_calm',      ko: '침착!',          ja: '冷静！',           style: 'lucky', size: 28 },
    { key: 'w_close',     ko: '간발의 차!',     ja: 'ギリギリセーフ！', style: 'lucky', size: 28 },
    { key: 'patrol_fake', ko: '…기분 탓인가?',  ja: '…気のせいか？',    style: 'hush',  size: 26 },
    { key: 'w_pizzaOpen', ko: '앗, 피자잖아!',  ja: 'あっ、ピザだ！',   style: 'alert', size: 34 },
    { key: 'pizza_away',  ko: '휙!',            ja: 'ポイッ！',         style: 'good',  size: 24 },
    { key: 'recheck',     ko: '…응?!',          ja: '…ん？！',          style: 'warn',  size: 30 },
    { key: 'hint_film',   ko: '띠를 쭉 당겨요!', ja: '帯をひっぱって！', style: 'hint',  size: 20 },
    { key: 'hint_tear',   ko: '위로 쭉 열어요!', ja: '上にグイッとあけて！', style: 'hint', size: 20 },
    { key: 'hint_snap',   ko: '다시 잡기',      ja: 'つかみ直す',       style: 'hint',  size: 18 },
    { key: 'hint_cover',  ko: '↓ 쓸어서 상자 덮기!', ja: '↓ スワイプで箱をとじる！', style: 'warn', size: 22 },
    { key: 'thud',        ko: '쿵',             ja: 'ドスッ',           style: 'thud',  size: 58 },
    { key: 'q',           x: '…?',                                      style: 'bad',   size: 26 },
    { key: 'pino',        x: 'PINO!',                                   style: 'combo', size: 28 },
    // labels inside the combo / fever rings
    { key: 'comboWord',   ko: '콤보',           ja: 'コンボ',           style: 'ring',  size: 12 },
    { key: 'feverWord',   ko: '피버',           ja: 'フィーバー',       style: 'ring',  size: 15 },
    { key: 'feverWordOn', ko: '피버!',          ja: 'フィーバー！',     style: 'ringOn', size: 16 },
  ],
  // ---- grades on the result memo ----
  grades: ['S', 'A', 'B', 'C', 'F'].map(g => ({ key: 'g' + g, x: g, style: 'g' + g, size: 68 })),
  // ---- state-change banners ----
  banners: [
    { key: 'ready',         ko: '준비~',            ja: 'よーい…',             style: 'score', size: 40, plate: 'tag' },
    { key: 'go_',           ko: '시작!',            ja: 'ドン！',              style: 'go',    size: 54, plate: 'stamp' },
    { key: 'fx_fever',      ko: '피버 타임!',       ja: 'フィーバー！',        style: 'fever', size: 52, plate: 'fever' },
    { key: 'rage_on',       ko: '코우가가 화났다!', ja: 'コウガが怒った！',    style: 'rage',  size: 36, plate: 'rage' },
    { key: 'nm_on',         ko: '코우가가 폭주합니다!!!!', ja: 'コウガが暴走します!!!!', style: 'nm', size: 30, plate: 'nm' },
    { key: 'superUnlock',   ko: '초하드 모드 해금!', ja: '超ハードモード解放！', style: 'unlock', size: 26, plate: 'ribbon' },
    { key: 'patrol_warn',   ko: '코우가가 온다!',   ja: 'コウガが来る！',      style: 'warn',  size: 34 },
    { key: 'patrol_watch',  ko: '쉿…',              ja: 'しーっ…',             style: 'hush',  size: 28, plate: 'cloud' },
    { key: 'patrol_caught', ko: '들켰다!',          ja: 'バレた！',            style: 'alert', size: 42, plate: 'caught' },
    { key: 'melt_over',     ko: '피노가 녹았다!',   ja: 'ピノが溶けた！',      style: 'melt',  size: 36, plate: 'melt' },
    { key: 'pizza_hint',    ko: '피자?! 치워버려!', ja: 'ピザ？！どかしちゃえ！', style: 'pizza', size: 26, plate: 'pizza' },
  ],
  // ---- digit sets: one glyph per file, all digits the same width so numbers don't wobble ----
  digits: {
    chars: '0123456789+−×.,',
    size: 60,
    sets: ['score', 'good', 'lucky', 'bad', 'alert', 'combo', 'hud', 'hudLow'],
  },
};
