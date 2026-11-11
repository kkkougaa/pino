"""Pino BGM: six compositions, each rendered in two moods.

normal_N and hard_N share a composition (hard is the toned-down, tenser take);
super_N and nightmare_N share one (nightmare is the more anxious take).
Language throughout: light drum'n'bass / 2-step, jazzy 9th chords on electric piano,
a syncopated synth hook in place of a vocal. Drums are kit samples, the electric piano
and vibes come from a soundfont, drums are electronic kit samples, hooks/bass/pads are ZynAddSubFX presets (see inst.py).
"""
import numpy as np
from engine import *  # noqa
from inst import hit, zyn, soundfont, norm

BRK = {  # kick, snare, ghost snare: kept sparse on purpose
    'A': ("x.........x.....", "....X.......X...", ".........o......"),
    'B': ("x.........x.....", "....X.......X...", "..............o."),
    'C': ("x.........x.....", "....X.......X.x.", "................"),
    'T': ("x.........x.....", "....X.......X...", "................"),
    'U': ("x.........xx....", "....X.......X...", "................"),
    'V': ("x......x..x.....", "....X.......X...", "................"),
    'F': ("x.........x.....", "....X.......X..x", "................"),
    'H': ("x.....x.........", "........X.......", "................"),
    'G': ("x.....x...x.....", "....X.......X...", "...............o"),
    'J': ("x.........x..x..", "....X.......X...", "................"),
}
V, E = 'VariBreaks/VP ', 'ElectricEmpireKit/EE_'


def lay(*xs):
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


H = 'HardElectro1/'


def k_light():
    return sat(lay(hit(E + 'Kick_Power') * 0.9, hit(H + 'HardHse_K_02') * 0.55, hit(E + 'Click') * 0.25), 1.3)


def k_soft():
    return lay(hit(E + 'Kick_Low_2') * 0.9, bq(hit(E + 'Kick_Lite_1'), 'lp', 2500) * 0.5)


def k_heavy():
    return sat(lay(hit(E + 'Kick_Hard_2') * 0.9, hit(H + 'HardHse_K_03_B') * 0.6, hit(E + 'Kick_Dist') * 0.25), 1.4) * 0.9


KICKS = {'light': k_light, 'soft': k_soft, 'heavy': k_heavy}


def sn(p=1.0, big=True):
    """Electronic snare: body, crack and a clap on top."""
    if big:
        return sat(lay(hit(E + 'Snare_3', p, jit=0.01), hit(V + 'Snare 2', p) * 0.7, hit(H + 'PowR_SN_1', p) * 0.5,
                       hit(H + 'Clap_1', 1.0, dec=0.08) * 0.35), 1.5) * 0.9
    return lay(hit(E + 'Snare_3', p * 1.05, jit=0.01), hit(V + 'Snare 2', p * 1.05) * 0.5, hit(E + 'Clap', 1.0, dec=0.05) * 0.25) * 0.85


def gs(p=1.25):
    return hit(V + 'Snare 1', p, dec=0.05, jit=0.03) * 0.9


def hc():
    return hit(H + ('CHH_1' if rng.random() < 0.6 else 'Hard_CHH_01'), 1.0, dec=0.04, jit=0.03)


def oh(dec=0.1):
    return hit(H + 'Hard_Hse_OHH_1', 1.0, dec=dec) * 1.1


def rd():
    return hit(E + 'Hat_Cl_Dirty', 1.2, dec=0.05) * 0.8


def crash():
    n = int(1.6 * SR)
    return bq(noise(n), 'hp', 3500) * np.exp(-tarr(n) / 0.35) * 0.5


def rimc(p=1.0):
    return hit(E + 'Click', p) * 1.0


def tck(p=1.4):
    return hit(E + 'Click', p, jit=0.02) * 0.5


def brk(m, bar, kinds, hats="x.x.x.x.x.x.x.x.", kg=1.0, sg=0.9, hg=0.3, ride=False, sf=1.0, kp='heavy', big=True):
    kt = []
    for i, k in enumerate(kinds):
        K, S, G = BRK[k]
        kt += m.D('kick', bar + i, K, KICKS[kp], kg)
        m.D('snare', bar + i, S, sn, sg, p=sf, big=big)
        m.D('snare', bar + i, G, gs, sg * 0.75, p=sf * 1.08)
        m.D('hat', bar + i, hats, hc, hg, pan=0.25)
        if ride:
            m.D('hat', bar + i, "..x...x...x...x.", oh, hg * 0.8, pan=-0.3)
    return kt


def roll(m, bar, step0, steps, div=1, g0=0.25, g1=0.9, f0=190, f1=260):
    step0, steps, div = step0 + max(0, steps - 4), min(steps, 4), 1
    n = int(steps * div)
    for i in range(n):
        r = i / max(1, n - 1)
        m.add('snare', m.bt(bar, step0 + i / div), gs(1.0 + 0.4 * r), (g0 + (g1 - g0) * r) * 1.2)


def heart(m, bus, bar, step=0, g=1.0, gap=4.0):
    m.add(bus, m.bt(bar, step), thud(62, 0.11), g)
    m.add(bus, m.bt(bar, step + gap), thud(74, 0.08), g * 0.7)


def mute(m, spans, fade=0.004):
    e = np.ones(m.n)
    f = int(fade * SR)
    for bar, a, b in spans:
        i, j = int(m.bt(bar, a) * SR), int(m.bt(bar, b) * SR)
        e[i:j] = 0
        e[i - f:i] = np.minimum(e[i - f:i], np.linspace(1, 0, f))
        e[j:j + f] = np.minimum(e[j:j + f], np.linspace(0, 1, f))
    return e


def drumbus(x, drive=1.4, room=0.1, thr=-14, ratio=3, t60=0.35):
    x = norm(x, -14)
    x = comp(sat(x * 1.6, drive), thr, ratio, 0.006, 0.09, 1.2) + 0.5 * comp(x, -30, 8, 0.001, 0.06, 4.0)
    return rev(shelf(x, 5000, -3.5), t60, room, 0.005, 400, 9000, seed=3)


def chord_bar(spec):
    """'Bb1:D4+F4+A4 / F2:A3+Eb4' -> [(step, root midi, voicing)]"""
    parts = [p.strip() for p in spec.split('/')]
    return [(i * 16 // len(parts), nn(p.split(':')[0]), p.split(':')[1]) for i, p in enumerate(parts)]


def at(ch, step):
    cur = ch[0]
    for c in ch:
        if c[0] <= step:
            cur = c
    return cur


BASS = {
    'normal': [(0, 3, 0), (6, 2, 0), (10, 3, 12), (14, 1.5, 0)],
    'garage': [(0, 2, 0), (3, 1.5, 0), (7, 2, 12), (10, 3, 0), (14, 1.5, 7)],
    'hard': [(i, 1.3, 0) for i in range(0, 14, 2)] + [(14, 1, 0), (15, 1, 12)],
    'super': [(0, 5.5, 0), (6, 3.5, 0), (10, 2.5, 12), (13, 2.8, 0)],
    'nightmare': [(0, 1, 0), (1, 1.5, 0), (3, 1, 0), (4, 1.5, 0), (6, 1.5, 0), (8, 1, 0), (9, 1.5, 0), (11, 1, 0), (12, 1.5, 1), (14, 1.5, 3)],
}
COMP = {
    'normal': ([0, 3, 6, 11, 14], [2, 6, 9, 12]),
    'garage': ([3, 6, 11, 14], [0, 3, 8, 11]),
    'hard': ([0, 10], [3]),
    'super': ([0, 3, 6, 9, 12, 14], [0, 3, 6, 10, 13]),
    'nightmare': ([3, 6, 12], [3, 9, 12, 14]),
}


def ratio(stem, y):
    """Set the drum bus `over` dB above the rest of the mix, measured above 300 Hz."""
    import os
    d = stem['d']
    r = y - d
    f = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    g = 10 ** ((f(bq(r, 'hp', 300)) + stem['over'] - f(bq(d, 'hp', 300))) / 20)
    if os.environ.get('BGM_DEBUG'):
        for lo, hi in ((30, 150), (150, 600), (600, 3000), (3000, 16000)):
            print(f"   {lo:5d}-{hi:5d} Hz  drums-rest {f(bq(d * g, 'bp', (lo, hi))) - f(bq(r, 'bp', (lo, hi))):+.1f} dB")
    return r + d * g


EP = lambda q, n: soundfont(0, 4, q, n)
VIBES = lambda q, n: soundfont(0, 11, q, n)
Z = lambda preset: (lambda q, n: zyn.render(preset, q, n))
SOUND = {
    'normal': dict(hook='Plucked/0001-Plucked 1', bass='Bass/0035-FM Bass 1'),
    'hard': dict(hook='Plucked/0003-Plucked 3', bass='Bass/0006-Analogue Bass'),
    'super': dict(hook='Collection/0034-Hard Saw', hook2='Plucked/0001-Plucked 1', bass='Collection/0047-Distorted Bass'),
    'nightmare': dict(hook='Collection/0042-Sharp Synth', hook2='Collection/0034-Hard Saw', bass='Collection/0047-Distorted Bass'),
}


def build(c, mood):
    dark = mood in ('hard', 'nightmare')
    heavy = mood in ('super', 'nightmare')
    bpm = c['bpm'] + (6 if mood == 'nightmare' else 0)
    tr = {'normal': 0, 'hard': -2, 'super': 0, 'nightmare': -1}[mood]
    garage = c.get('swing', 0) > 0
    m = Mix(bpm, 24, swing=c.get('swing', 0))
    A = [chord_bar(x) for x in c['A']]
    B = [chord_bar(x) for x in c['B']]
    hA, hB = c['hA'], c['hB']
    plan = ([('intro', A[i], hA[i]) for i in range(4)] + [('A', A[i], hA[i]) for i in range(8)]
            + [('B', B[i], hB[i]) for i in range(8)] + [('out', A[4 + i], hA[4 + i]) for i in range(4)])
    key = c['key'] + tr
    kt = []
    holes = []
    note = lambda bus, t, mid, dur, vel=100: m.b.setdefault('~' + bus, []).append((t, mid, dur, vel))
    for b, (sec, chd, hk) in enumerate(plan):
        q = b % 4
        # ---- bass
        if sec == 'intro':
            for st, root, _ in chd:
                if b >= 2:
                    m.add('sub', m.bt(b, st), sub([root + tr], (16 - st if len(chd) == 1 or st else 8) * m.sl * 0.95), 0.6)
        else:
            pat = BASS['garage' if garage and mood == 'normal' else mood]
            if sec == 'out' and not dark:
                pat = [(0, 6, 0), (10, 4, 0)]
            for st, ln, off in pat:
                if mood == 'nightmare' and b == 11 and st >= 8:
                    continue
                root = at(chd, st)[1] + tr
                d = ln * m.sl * 0.9
                t = m.bt(b, st)
                if not heavy:
                    note('bass', t, root + off + 12, d, 110 if st == 0 else 96)
                    m.add('sub', t, sub([root + (off if off < 12 else 0)], d), 0.5)
                else:
                    if mood == 'super':
                        x = reese([root + off], d, cut=560 + 30 * (b % 8), lfo=bpm / 60 / (4 if q % 2 == 0 else 2))
                    else:
                        x = reese([root + (off if off < 12 else 0)], d, cut=700 + 50 * (b % 8), lfo=3, det=0.28)
                    m.add('reese', t, x)
                    note('bass', t, root + off + 12, d, 105)
        # ---- chords
        if sec == 'intro':
            for st, _, v in chd:
                m.N('comp', b, ". " * st + v, tr=tr, gt=(16 - st if len(chd) == 1 or st else 8) * 0.9, vel=60 + 10 * b)
        else:
            steps = COMP['garage' if garage and mood == 'normal' else mood][b % 2]
            if sec == 'out':
                steps = [0, 6] if not dark else [0]
            for i, st in enumerate(steps):
                v = at(chd, st)[2]
                acc = 1.0 if i % 2 == 0 else 0.85
                if mood == 'normal':
                    m.N('comp', b, ". " * st + v, tr=tr, gt=1.6, vel=100 * acc)
                elif mood == 'hard':
                    m.N('comp', b, ". " * st + v, tr=tr, gt=5.0, vel=62)
                elif mood == 'super':
                    m.N('comp', b, ". " * st + v, tr=tr, gt=1.4, vel=118 * acc)
                    m.N('stab', b, ". " * st + v, tr=tr, gt=1.2, vel=105 * acc)
                else:
                    m.N('comp', b, ". " * st + v, tr=tr, gt=1.2, vel=90)
                    m.N('stab', b, ". " * st + v, tr=tr + (1 if st == 12 else 0), gt=1.4, vel=110)
            if not heavy:
                for i, (st, _, v) in enumerate(chd):
                    ln = (16 - st if i == len(chd) - 1 else chd[i + 1][0] - st)
                    m.N('pad', b, ". " * st + v + " -" * (ln - 1), tr=tr, gt=1.0, vel=80)
        # ---- hook
        if sec == 'intro':
            if b < 2 or not heavy:
                m.N('bell', b, hk, tr=tr + (0 if dark else 12), gt=1.5, vel=80)
        elif mood == 'normal':
            m.N('hook', b, hk, tr=tr, gt=1.4, vel=108)
            if sec == 'B':
                m.N('bell', b, hk, tr=tr + 12, gt=1.5, vel=90)
        elif mood == 'hard':
            m.N('hook', b, hk, tr=tr - 12, gt=1.4, vel=92)
            if sec == 'B':
                m.N('bell', b, hk, tr=tr, gt=1.5, vel=70)
        elif mood == 'super':
            m.N('hook', b, hk, tr=tr, gt=1.3, vel=112)
            m.N('hook2', b, hk, tr=tr, gt=1.2, vel=110)
            if sec == 'B':
                m.N('bell', b, hk, tr=tr + 12, gt=1.5, vel=100)
        else:
            if sec != 'A' or q < 2:
                m.N('hook', b, hk, tr=tr, gt=1.3, vel=112)
                m.N('hook2', b, hk, tr=tr - 12, gt=1.2, vel=105)
            note('bell', m.bt(b, 0 if b % 2 == 0 else 8), key + (7 if b % 2 == 0 else 8), m.sl * 3, 100)
        # ---- drums
        if sec == 'intro':
            heart(m, 'kick', b, 0, 0.9, 4)
            if mood == 'nightmare':
                heart(m, 'kick', b, 8, 0.9, 4)
            if dark:
                m.D('tick', b, "x...x...x...x..." if b < 2 else "x.x.x.x.x.x.x.x.", tck, 0.5, pan=0.3 if b % 2 else -0.3)
            else:
                m.D('hat', b, "x.x.x.x.x.x.x.x.", hc, 0.3, pan=0.25)
            if b >= 2:
                kt += brk(m, b, 'T' if b == 2 else 'F', kg=0.9, sg=0.75, hg=0.25, kp='heavy' if heavy else ('soft' if dark else 'light'), big=heavy)
            if b == 3:
                roll(m, 3, 12, 4, 2, 0.3, 0.9)
        elif mood == 'normal':
            kinds = c.get('dn', "TUTVTUTF" + "UJUVUJUF" + "HHHF")[b - 4]
            if garage:
                kinds = "GGGFGGGF" [(b - 4) % 8] if sec != 'out' else "HHHF"[q]
            kt += brk(m, b, kinds, kg=0.9, sg=0.75, hg=0.2, sf=1.0, kp='light', big=False, ride=sec == 'B')
            if garage:
                m.D('rim', b, "..x......x......", rimc, 0.6, pan=-0.3)
        elif mood == 'hard':
            hole = sec == 'A' and b == 11
            m.D('tick', b, "x.x.x.x.x.x." if hole else "x.x.x.x.x.x.x.x.", tck, 0.5, pan=0.3 if b % 2 else -0.3)
            if hole:
                kt += m.D('kick', b, "x.........x.", k_soft, 0.9)
                m.D('snare', b, "....x.......", sn, 0.7, p=0.94, big=False)
                heart(m, 'kick', b, 12, 1.0, 2)
                holes.append((b, 12, 16))
            else:
                kinds = "HHHF"[q] if sec == 'out' else ("TUTVTUTF" if sec == 'A' else "UJUVUJUF")[(b - 4) % 8]
                if garage and sec != 'out':
                    kinds = "GGGFGGGF"[(b - 4) % 8]
                kt += brk(m, b, kinds, hats="x.x.x.x.x.x.x.x.", kg=0.95, sg=0.7, hg=0.2, sf=0.94, kp='soft', big=False)
                m.D('rim', b, "..x......x......" if q % 2 == 0 else ".....x.....x....", rimc, 0.5, pan=-0.3)
            if q == 0:
                heart(m, 'tick', b, 0, 0.5, 4)
        elif mood == 'super':
            if sec == 'out':
                kinds = "HHAC"[q]
            else:
                kinds = ("ABACABAC" if sec == 'A' else "UBUCUBAC")[(b - 4) % 8]
            kt += brk(m, b, kinds, hats="x.x.x.x.x.x.x.x.", ride=sec == 'B', sf=1.0)
            if b in (11, 19):
                roll(m, b, 12, 4, 2, 0.3, 0.9)
        else:
            if b == 11:
                kt += m.D('kick', b, "x.x.....", k_heavy)
                m.D('snare', b, "....X...", sn, 0.8)
                m.D('tick', b, "........x...x...", tck, 0.7)
                heart(m, 'tick', b, 8, 1.0, 3)
                holes.append((b, 8, 16))
            elif b == 19:
                kt += m.D('kick', b, "x.x.....", k_heavy)
                m.D('snare', b, "....X...", sn, 0.8)
                kt += m.D('kick', b, "........x.x.x.x.", k_heavy, 0.8)
            elif b in (22, 23):
                kt += m.D('kick', b, "x.......x......." if b == 22 else "x...x...x...x...", k_heavy)
                roll(m, b, 0, 16, 1 if b == 22 else 2, 0.12 if b == 22 else 0.5, 0.5 if b == 22 else 1.0)
            else:
                kinds = "HH"[q] if sec == 'out' else "UBUC"[q]
                kt += brk(m, b, kinds, hats="x.x.x.x.x.x.x.x.", ride=sec == 'B', sf=0.95)
    # ---- one-shots and long layers
    for b_ in (4, 12, 20):
        m.add('hat', m.bt(b_, 0), crash(), 0.5 if mood != 'hard' else 0.25, -0.2)
    m.add('fx', m.bt(2, 0), riser(m.sl * 32, 300, 9000), 0.9 if heavy else 0.6)
    m.add('fx', m.bt(19, 0), riser(m.sl * 16, 500, 9000), 0.6)
    if heavy:
        for b_, f_ in ((4, 55), (12, 50), (20, 46)):
            m.add('fx', m.bt(b_, 0), impact(f_), 1.0)
    if dark:
        m.add('fx', m.bt(10, 0), riser(m.sl * 28 if mood == 'hard' else m.sl * 24, 250, 6000), 0.7)
        cl = [key - 12, key - 11, key - 6] if mood == 'nightmare' else [key - 12 + 7, key - 12 + 8]
        for b0, ln, c1, c2, bd in ((0, 64, 400, 1500, 0), (12, 128, 800, 3200, 2.0 if mood == 'nightmare' else 0), (20, 64, 600, 2600, 0)):
            x = pad(cl, ln * m.sl, cut=c1, cut2=c2, att=m.sl * ln * 0.4, rel=0.2, hp=350, spread=0.3, bend=bd)
            m.add('tens', m.bt(b0, 0), x)
    if mood == 'nightmare':
        m.add('fx', m.bt(1, 8), clang(410, 0.6), 0.5, -0.5)
        m.add('fx', m.bt(3, 0), clang(290, 0.7), 0.5, 0.5)
        m.add('fx', m.bt(22, 0), riser(m.sl * 32, 300, 11000), 1.0)
    # ---- render the hosted instruments
    S = SOUND[mood]
    comp_ = m.part('comp', EP, -20)
    hook = m.part('hook', Z(S['hook']), -18)
    hook2 = m.part('hook2', Z(S['hook2']), -22) if 'hook2' in S else 0
    bassz = sat(m.part('bass', Z(S['bass']), -12 if not heavy else -16), 2.0) * (0.2 if not heavy else 0.13)
    bell_ = m.part('bell', VIBES if mood != 'nightmare' else Z('SynthPiano/0004-Fantasy Bell'), -25)
    pad_ = m.part('pad', Z('Pads/0065-Soft Pad'), -26) if not heavy else 0
    stab_ = m.part('stab', Z('Rhodes/0008-Synth Rhodes1'), -21) if heavy else 0
    # ---- mix
    hole = mute(m, holes) if holes else 1.0
    stem = {}

    def DR(x, over):
        stem['d'], stem['over'] = x, over
        return x
    dk = duck(m.n, kt, {'normal': 0.4, 'hard': 0.45, 'super': 0.5, 'nightmare': 0.5}[mood], 0.07)
    dr = (norm(bq(m.get('kick'), 'hp', 35), -17) + norm(m.get('snare'), -12.5) + norm(bq(m.get('hat'), 'lp', 11000), -28)
          + norm(m.get('rim'), -24))
    d3 = m.sl * 3
    fx = norm(m.get('fx'), -22)
    low = bq(bassz, 'hp', 60) + norm(m.get('sub'), -17) if not heavy else norm(m.get('reese'), -14.5) + bq(bassz, 'hp', 120)
    if mood == 'normal':
        y = (DR(drumbus(dr, 1.3, 0.08), 3.0) + low * dk + wide(rev(comp_ * dk, 1.0, 0.2))
             + pan(rev(delay(hook, d3, 0.35, 0.2), 1.2, 0.16), -0.08) + pan(rev(delay(bell_, d3, 0.3, 0.2), 1.8, 0.3), 0.2)
             + rev(pad_ * dk, 1.8, 0.3) + fx)
        y = ratio(stem, y)
        return master(y, -13, 1.15, m.body)
    if mood == 'hard':
        y = (DR(drumbus(dr, 1.2, 0.14, t60=0.6), 1.5) + bq(low, 'lp', 900) * dk * hole + wide(rev(bq(comp_, 'lp', 2200) * 0.7 * dk, 1.8, 0.3)) * hole
             + rev(delay(bq(hook, 'lp', 3500), d3, 0.45, 0.32, lp=2400), 1.6, 0.22) * hole + rev(delay(bell_, d3, 0.4, 0.3), 2.2, 0.4) * 0.8 * hole
             + rev(pad_ * dk, 2.2, 0.35) * 1.2 * hole + norm(m.get('tens'), -29) * hole
             + norm(rev(m.get('tick'), 1.0, 0.25), -27) + fx)
        y = ratio(stem, y)
        return master(shelf(y, 5000, -2), -14, 1.05, m.body)
    y = (DR(drumbus(dr, 1.7 if mood == 'super' else 2.0, 0.1, -16, 4), 4.0) + low * dk * hole
         + wide(rev(comp_ * dk, 0.9, 0.18)) * hole + rev(stab_ * dk, 1.0, 0.22) * hole
         + rev(delay(hook + hook2, d3, 0.35, 0.22), 1.1, 0.16) * dk * hole + rev(delay(bell_, d3, 0.45, 0.35), 1.6, 0.3) * hole
         + (norm(m.get('tens'), -26) * dk * hole if dark else 0) + (norm(rev(m.get('tick'), 1.2, 0.3), -22) if dark else 0) + rev(fx, 1.5, 0.3))
    y = ratio(stem, y)
    return master(y, -10.5 if mood == 'super' else -10, 1.5 if mood == 'super' else 1.6, m.body)


# ============================ compositions ============================
Bb9, A7s, Dm9, Cm9, F13 = "Bb1:D4+F4+A4+C5", "A1:C#4+G4+C5", "D2:C4+E4+F4+A4", "C2:Bb3+D4+Eb4+G4", "F2:A3+Eb4+G4"
Gm9, C9, Fma9, A7b = "G1:Bb3+D4+F4+A4", "C2:Bb3+D4+E4+G4", "F2:A3+C4+E4+G4", "A1:C#4+G4+Bb4"

TIPTOE = dict(  # D minor, light two-step dnb
    bpm=172, key=74,
    A=[Bb9, A7s, Dm9, Cm9 + " / " + F13] * 2,
    B=[Gm9, C9, Fma9, A7s] * 2,
    hA=["A4 . D5 . . F5 . E5 . . D5 . A4 . . .", "C5 . . Bb4 . . A4 . . . G4 . A4 . C#5 .",
        "D5 . . . . . F5 . E5 . D5 . . A4 . .", "G4 . Bb4 . D5 . . Eb5 . . D5 . C5 . A4 .",
        "A4 . D5 . . F5 . E5 . . D5 . A4 . . .", "C5 . . Bb4 . . A4 . . . G4 . A4 . C#5 .",
        "D5 . . . . . F5 . A5 . G5 . . F5 . .", "E5 . . D5 . . C5 . . A4 . . D5 - - ."],
    hB=["Bb4 . . D5 . . F5 . . . G5 . F5 . D5 .", "E5 . . G5 . . Bb5 . A5 . . G5 . . E5 .",
        "A5 . . . G5 . E5 . . C5 . . E5 . G5 .", "G5 . . F5 . . E5 . C#5 . . . A4 . C5 .",
        "Bb4 . . D5 . . F5 . . . G5 . F5 . D5 .", "E5 . . G5 . . Bb5 . A5 . . G5 . . E5 .",
        "A5 . . . G5 . E5 . . C5 . . A4 . C5 .", "C#5 . . E5 . . G5 . Bb5 . A5 . . . . ."])

SNACK = dict(  # E minor, swung 2-step
    bpm=138, swing=0.26, key=76,
    A=["A1:C4+E4+G4+B4", "D2:C4+E4+F#4+A4", "G1:B3+D4+F#4+A4", "C2:B3+D4+E4+G4",
       "F#2:A3+C4+E4", "B1:A3+C4+D#4+F#4", "E2:B3+D4+F#4+G4", "E2:B3+D4+F#4+G4"],
    B=["C2:B3+D4+E4+G4", "B1:A3+D4+F#4", "A1:C4+E4+G4+B4", "B1:A3+D#4+G4"] * 2,
    hA=["E5 . . G5 . . E5 . . D5 . . B4 . . .", "C5 . . E5 . . F#5 . . . A5 . . . . .",
        "D5 . . F#5 . . D5 . . B4 . . A4 . . .", "B4 . . D5 . . E5 . . . G5 . . . . .",
        "C5 . . E5 . . C5 . . A4 . . . . C5 .", "D#5 . . F#5 . . A5 . . . C6 . B5 . A5 .",
        "G5 . . F#5 . . D5 . . B4 . . E5 - - -", ". . . . . . . . B4 . D5 . E5 . G5 ."],
    hB=["G5 . E5 . . D5 . E5 . . G5 . . . B5 .", "A5 . F#5 . . D5 . F#5 . . A5 . . . . .",
        "G5 . E5 . . C5 . E5 . . B5 . . A5 . .", "G5 . . F#5 . . D#5 . . . B4 . D#5 . F#5 .",
        "G5 . E5 . . D5 . E5 . . G5 . . . B5 .", "A5 . F#5 . . D5 . F#5 . . A5 . . . . .",
        "G5 . E5 . . C5 . E5 . . B5 . . A5 . .", "B5 . . A5 . . F#5 . . D#5 . . F#5 - - ."])

CREEP = dict(  # G minor, bass creeping down a step at a time
    bpm=166, key=79, dn="HHHHHHHF" + "TUTVTUTF" + "HHHF",
    A=["G2:Bb3+D4+F4+A4", "F#2:A3+C4+Eb4", "F2:Bb3+D4+G4", "E2:G3+Bb3+D4",
       "Eb2:G3+Bb3+D4+F4", "D2:A3+C4+F4", "C2:Bb3+D4+Eb4+G4", "D2:F#3+C4+F4"],
    B=["C2:Bb3+D4+Eb4+G4", "F2:A3+Eb4+G4", "Bb1:A3+C4+D4+F4", "Eb2:G3+Bb3+D4+F4",
       "A1:G3+C4+Eb4", "D2:F#3+C4+Eb4", "G2:Bb3+D4+F4+A4", "D2:F#3+C4+F4"],
    hA=["D5 . . . Bb4 . D5 . . G5 . . F5 . D5 .", "C5 . . . A4 . C5 . . Eb5 . . D5 . C5 .",
        "Bb4 . . . G4 . Bb4 . . D5 . . C5 . Bb4 .", "A4 . . . G4 . . Bb4 . . D5 . . . . .",
        "G5 . . . F5 . D5 . . Bb4 . . D5 . F5 .", "F5 . . . D5 . C5 . . A4 . . C5 . D5 .",
        "Eb5 . . . D5 . C5 . . G4 . . Bb4 . C5 .", "D5 . . C5 . . A4 . F#4 . . A4 . C5 . Eb5"],
    hB=["G5 . . Eb5 . . D5 . . C5 . . D5 . Eb5 .", "G5 . . Eb5 . . C5 . . A4 . . C5 . Eb5 .",
        "F5 . . D5 . . C5 . . A4 . . Bb4 . D5 .", "G5 . . . F5 . D5 . . Bb4 . . . . . .",
        "Eb5 . . C5 . . A4 . . G4 . . A4 . C5 .", "Eb5 . . D5 . . C5 . . F#4 . . A4 . C5 .",
        "Bb4 . . D5 . . G5 . . . A5 . G5 . . .", "F5 . . . D5 . . C5 . . A4 . F#4 . . ."])

Fm9, Db9, C7s, C7b = "F2:Ab3+C4+Eb4+G4", "Db2:F3+Ab3+C4+Eb4", "C2:E4+Bb4+Eb5", "C2:E4+Bb4+Db5"
CAUGHT = dict(  # F minor, breakbeat hardcore
    bpm=174, key=77,
    A=[Fm9, Fm9, Db9, C7s, Fm9, "Ab1:Gb3+C4+Eb4+Bb4", Db9, "G1:F3+Bb3+Db4 / C2:E4+G4+Bb4"],
    B=["Bb1:Ab3+C4+Db4+F4", "C2:E4+G4+Bb4", Fm9, "Eb2:Ab3+C4+Eb4+G4", Db9, C7s, Fm9, C7b],
    hA=["C5 . C5 Eb5 . F5 . . G5 . F5 . Eb5 . C5 .", "Bb4 . C5 . . . . . . . Ab4 Bb4 C5 . Eb5 .",
        "F5 . F5 Ab5 . G5 . . F5 . Eb5 . C5 . Ab4 .", "G4 . Bb4 . . E5 . . Eb5 . . Db5 . . C5 .",
        "C5 . C5 Eb5 . F5 . . G5 . F5 . Eb5 . C5 .", "Bb4 . C5 . . . Eb5 . . Gb5 . . Eb5 . C5 .",
        "F5 . F5 Ab5 . C6 . . Bb5 . Ab5 . G5 . F5 .", "G5 . . F5 . Db5 . Bb4 . E5 . . G5 . Bb5 ."],
    hB=["Db5 . C5 . Bb4 . . F5 . . Db5 . C5 . Bb4 .", "C5 . Bb4 . G4 . . E5 . . C5 . Bb4 . G4 .",
        "Ab4 . C5 . Eb5 . . G5 . . F5 . . . . .", ". . . . C5 Eb5 F5 . G5 . Ab5 . G5 . Eb5 .",
        "F5 . . Ab5 . . C6 . . . Bb5 . Ab5 . F5 .", "E5 . . G5 . . Bb5 . . . Ab5 . G5 . E5 .",
        "F5 . . . . . C5 . Eb5 . F5 . . C5 . .", "Db5 . . C5 . . Bb4 . G4 . . E4 . G4 Bb4 C5"])

FREEZER = dict(  # A minor
    bpm=176, key=81,
    A=["F2:A3+C4+E4+G4", "E2:G#3+D4+G4", "A1:G3+B3+C4+E4", "G1:F3+A3+Bb3+D4 / C2:Bb3+E4+A4",
       "F2:A3+C4+E4+G4", "E2:G#3+D4+F4", "A1:G3+B3+C4+E4", "A1:G3+B3+C4+E4"],
    B=["D2:F3+A3+C4+E4", "G1:F3+B3+E4", "C2:B3+D4+E4+G4", "F2:A3+C4+E4+G4",
       "B1:A3+D4+F4", "E2:G#3+D4+G4", "A1:G3+B3+C4+E4", "E2:G#3+D4+F4"],
    hA=["E5 . . C5 . . A4 . C5 . E5 . . G5 . .", "G#5 . . E5 . . D5 . . C5 . B4 . . G#4 .",
        "A4 . C5 . E5 . . A5 . . G5 . E5 . . .", "D5 . . Bb4 . . D5 . E5 . . G5 . . A5 .",
        "E5 . . C5 . . A4 . C5 . E5 . . G5 . .", "F5 . . E5 . . D5 . . B4 . . G#4 . B4 D5",
        "C5 . . . . . E5 . . A5 . . . G5 . E5", "A5 - - . . . . . E5 . G5 . A5 . C6 ."],
    hB=["F5 . E5 . . D5 . . A4 . . D5 . E5 F5 .", "E5 . D5 . . B4 . . G4 . . B4 . D5 E5 .",
        "E5 . D5 . . C5 . . G4 . . C5 . D5 E5 .", "G5 . . . E5 . . C5 . . A4 . . . . .",
        "D5 . . F5 . . A5 . . . F5 . D5 . B4 .", "D5 . . E5 . . G5 . . . G#5 . B5 . . .",
        "A5 . . E5 . . C5 . . A4 . . C5 . E5 .", "F5 . . D5 . . B4 . G#4 . . . E5 . G#5 ."])

OVERDRIVE = dict(  # D minor, cousin of Tiptoe
    bpm=170, key=74,
    A=[Dm9, "C2:C4+E4+F4+A4", Bb9, A7s, Gm9, A7b, Dm9, A7s],
    B=[Bb9, C9, Dm9, Dm9, Gm9, C9, Fma9, A7b],
    hA=["D5 . F5 . A5 . . G5 . . F5 . D5 . . .", "E5 . F5 . A5 . . G5 . . E5 . C5 . . .",
        "D5 . F5 . A5 . . C6 . . A5 . F5 . . .", "E5 . . C#5 . . Bb4 . . G4 . . A4 . C#5 E5",
        "D5 . . Bb4 . . G4 . Bb4 . D5 . . F5 . .", "E5 . . C#5 . . Bb4 . C#5 . E5 . . G5 . .",
        "F5 . . . E5 . D5 . . A4 . . D5 . . .", ". . C#5 . E5 . G5 . Bb5 . A5 . . . . ."],
    hB=["A5 . . F5 . . D5 . F5 . . A5 . . . .", "G5 . . E5 . . D5 . E5 . . G5 . . Bb5 .",
        "A5 . . . . . F5 . E5 . D5 . . . . .", ". . . . A4 C5 D5 . F5 . E5 . D5 . C5 .",
        "Bb4 . D5 . F5 . . A5 . . G5 . F5 . D5 .", "Bb4 . D5 . E5 . . G5 . . E5 . D5 . C5 .",
        "A4 . C5 . E5 . . G5 . . A5 . . . . .", "Bb5 . . A5 . . G5 . E5 . . C#5 . . A4 ."])

SONGS = []
for i, (nm, c) in enumerate([('tiptoe', TIPTOE), ('midnight_snack', SNACK), ('creep', CREEP)], 1):
    SONGS.append((f'normal_{i}_{nm}', lambda c=c: build(c, 'normal')))
for i, (nm, c) in enumerate([('tiptoe', TIPTOE), ('midnight_snack', SNACK), ('creep', CREEP)], 1):
    SONGS.append((f'hard_{i}_{nm}', lambda c=c: build(c, 'hard')))
for i, (nm, c) in enumerate([('caught', CAUGHT), ('freezer_burn', FREEZER), ('overdrive', OVERDRIVE)], 1):
    SONGS.append((f'super_{i}_{nm}', lambda c=c: build(c, 'super')))
for i, (nm, c) in enumerate([('caught', CAUGHT), ('freezer_burn', FREEZER), ('overdrive', OVERDRIVE)], 1):
    SONGS.append((f'nightmare_{i}_{nm}', lambda c=c: build(c, 'nightmare')))
