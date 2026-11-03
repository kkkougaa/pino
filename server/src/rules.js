// Plausibility rules for a submitted run. Two layers:
//   HARD limits: things the game cannot produce at all (more boxes than time allows, a stage reached too early,
//                a score above what perfect play with every bonus could give). Failing one -> 'rejected'.
//   SOFT limit:  the score compared with the autoplay reference (a run that never misses and keeps its combo),
//                with every bonus added on top. Above it -> 'review' (kept hidden until an admin approves it).
// Tune the numbers here; the game itself does not need to change.
import { REF_CURVE } from './ref_curve.js';

export const RULES = {
  MIN_BOX_SEC: 1.2,        // fastest possible box (peel, open, pick, six pinos, toss) in game seconds, fever included
  BONUS_SEC: { perfect: 0.5, lucky: 2 },   // normal mode: time a box can add to the 60 s clock
  STAGE_SEC: { hardRage: 30, nightmareAfterRage: 30 },   // the quickest a hard run can anger him / tip him into nightmare
  PATROL_MIN_GAP: 4,       // the shortest gap between his visits (nightmare at its limit)
  // per-item maxima, before the stage multiplier
  PINO_MAX: 100 * 4 * 2,   // combo tier x4, fever x2
  DARE_FACTOR: 2.4,        // at most ~35% of pinos can be eaten while he is on his way (x5): 0.65 + 0.35*5
  LUCKY_MAX: 1000 * 4 * 2, // heart / star at x4 combo in fever
  PERFECT: 200,
  SAFE: 500,               // "not caught" bonus per visit
  // autoplay reference: points per game second at x1 multiplier for a run that never misses and keeps its combo.
  // Measured with the game's autoplay: normal 88,500 in ~72 s of play (60 s + PERFECT time) = ~1,230/s;
  // hard 143,530 in 60 s (x1.7, then x2.5 after anger) = ~1,140/s at x1. Hearts / stars / visits are added on top.
  REF_RATE: { normal: 1300, hard: 1300, super: 1300 },
  REF_MARGIN: 1.3,        // the fallback formula's margin
  CURVE_MARGIN: 1.2,      // a run may beat the every-bonus autoplay curve by this much before it is held
  SM: { normal: 1, hard: 1.7, hardRage: 2.5, super: 5, nightmare: 6 },
};

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : NaN);

// s: the summary the game sends. wallSec: seconds between the start token and this submit.
export function judge(mode, score, s, wallSec) {
  const R = RULES, bad = (why) => ({ status: 'rejected', reason: why });
  const t = num(s.elapsed), eaten = num(s.eaten), boxes = num(s.boxes), combo = num(s.combo), lucky = num(s.lucky), patrols = num(s.patrols);
  const rage = !!s.rage, nightmare = !!s.nightmare;
  if (![score, t, eaten, boxes, combo, lucky, patrols].every((v) => v >= 0)) return bad('missing or negative numbers');
  if (!Number.isInteger(score) || !Number.isInteger(eaten) || !Number.isInteger(boxes)) return bad('non-integer counts');

  // time
  if (t > wallSec + 5) return bad(`game time ${t.toFixed(1)}s is longer than the real time ${wallSec.toFixed(1)}s`);
  if (mode === 'normal' && t > 60 + boxes * R.BONUS_SEC.perfect + lucky * R.BONUS_SEC.lucky + 5) return bad('normal run longer than its clock allows');

  // counts
  if (boxes > Math.floor(t / R.MIN_BOX_SEC) + 1) return bad(`${boxes} boxes in ${t.toFixed(1)}s`);
  if (eaten > boxes * 6 + 6 || eaten < boxes * 6) return bad('pinos eaten do not match the boxes');
  if (combo > eaten) return bad('combo longer than pinos eaten');
  if (lucky > boxes + 1) return bad('more hearts / stars than boxes');
  if (patrols > Math.floor(t / R.PATROL_MIN_GAP) + 2) return bad('more visits than time allows');

  // stages
  if (mode === 'normal' && (rage || nightmare)) return bad('normal mode cannot anger him');
  if (nightmare && !rage) return bad('nightmare without rage');
  if (mode === 'hard' && rage && t < R.STAGE_SEC.hardRage) return bad('angered too early');
  if (mode === 'hard' && nightmare && t < R.STAGE_SEC.hardRage + R.STAGE_SEC.nightmareAfterRage) return bad('nightmare too early');
  if (mode === 'super' && nightmare && t < R.STAGE_SEC.nightmareAfterRage) return bad('nightmare too early');

  // score: the absolute ceiling (every pino at x4 in fever, the dare share at x5, every bonus) at the highest multiplier reached
  const sm = nightmare ? R.SM.nightmare : mode === 'super' ? R.SM.super : rage ? R.SM.hardRage : mode === 'hard' ? R.SM.hard : R.SM.normal;
  const dare = mode === 'normal' ? 1 + 4 * 0.2 : R.DARE_FACTOR;
  const ceiling = sm * (eaten * R.PINO_MAX * dare + lucky * R.LUCKY_MAX + boxes * R.PERFECT + patrols * R.SAFE);
  if (score > ceiling * 1.05) return bad(`score ${score} above the possible ${Math.round(ceiling)}`);

  // the softer check: the score autoplay reached at this second while taking every bonus (ref_curve.js),
  // past the end of the recording it carries on at the last 30 s' pace; without a recording, a formula
  const ref = curveAt(mode, t) * R.CURVE_MARGIN || (sm * (R.REF_RATE[mode] || 1300) * t + sm * (lucky * R.LUCKY_MAX + patrols * R.SAFE)) * R.REF_MARGIN;
  if (score > ref) return { status: 'review', reason: `score ${score} above the reference ${Math.round(ref)} for ${t.toFixed(0)}s` };
  return { status: 'ok', reason: '' };
}

// the every-bonus autoplay score at second t (0 when there is no recording for the mode)
export function curveAt(mode, t) {
  const c = REF_CURVE && REF_CURVE[mode]; if (!c || c.length < 2) return 0;
  const i = Math.max(0, Math.floor(t)), n = c.length - 1;
  if (i <= n) return c[i];
  const back = Math.min(30, n), pace = (c[n] - c[n - back]) / back;   // points per second near the end
  return c[n] + pace * (i - n);
}
