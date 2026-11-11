"""Pino BGM: six compositions, each rendered in two moods.

normal_N and hard_N share a composition (hard is the toned-down, tenser take);
super_N and nightmare_N share one (nightmare is the more anxious take).
Language throughout: light drum'n'bass / 2-step, jazzy 9th chords on electric piano,
a syncopated synth hook in place of a vocal.
"""
import numpy as np
from engine import *  # noqa

BRK = {
    'A': ("x.x.......xx....", "....X.......X...", ".......o.o.....o"),
    'B': ("x.x.......x.....", "....X.........X.", ".......o.o..o..."),
    'C': ("x.x...x...x.....", "....X..o.X..X.XX", "................"),
    'T': ("x.........x.....", "....X.......X...", ".......o.o.....o"),
    'U': ("x.........xx....", "....X.......X...", ".o....o..o...oo."),
    'V': ("x......x..x.....", "....X.......X...", "......o......o.o"),
    'F': ("x.........x.....", "....X..o.o..X.oX", "................"),
    'H': ("x.....x.........", "........X.......", "..............o."),
    'G': ("x.....x...x.....", "....X.......X...", ".......o.....o.o"),
    'J': ("x..x......x..x..", "....X.......X...", ".......o.o.....o"),
}
KICKS = {
    'light': dict(f0=200, f1=58, pt=0.018, dec=0.1, click=0.5, drive=1.6),
    'soft': dict(f0=130, f1=50, pt=0.03, dec=0.16, click=0.15, drive=1.3),
    'heavy': dict(f0=230, f1=55, pt=0.02, dec=0.13, click=0.6, drive=2.5),
}


def brk(m, bar, kinds, hats="x.x-x.xox.x-x.xo", kg=1.0, sg=0.8, hg=0.22, rd=False, sf=200, kp='heavy', sd=0.13):
    kt = []
    for i, k in enumerate(kinds):
        K, S, G = BRK[k]
        kt += m.D('kick', bar + i, K, kick, kg, **KICKS[kp])
        m.D('snare', bar + i, S, snare, sg, f=sf, dec=sd, nz=1.1)
        m.D('snare', bar + i, G, snare, sg * 0.9, f=sf * 1.1, dec=sd * 0.55, nz=0.8)
        m.D('hat', bar + i, hats, hat, hg, pan=0.25, dec=0.02)
        if rd:
            m.D('hat', bar + i, "x...x...x...x...", ride, hg * 0.9, pan=-0.3)
    return kt


def roll(m, bar, step0, steps, div=1, g0=0.25, g1=0.9, f0=190, f1=260):
    n = int(steps * div)
    for i in range(n):
        r = i / max(1, n - 1)
        m.add('snare', m.bt(bar, step0 + i / div), snare(f=f0 + (f1 - f0) * r, dec=0.07, nz=0.9), g0 + (g1 - g0) * r)


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
    x = comp(sat(x * 0.9, drive), thr, ratio, 0.004, 0.09, 1.2)
    return rev(x, t60, room, 0.005, 400, 9000, seed=3)


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
    for b, (sec, ch, hk) in enumerate(plan):
        q = b % 4
        main = sec in ('A', 'B')
        # ---- bass
        if sec == 'intro':
            for st, root, _ in ch:
                m.add('bass', m.bt(b, st), sub([root + tr], (16 - st if len(ch) == 1 or st else 8) * m.sl * 0.95), 0.6 if b >= 2 else 0.0)
        else:
            pat = BASS['garage' if garage and mood == 'normal' else mood]
            if sec == 'out' and not dark:
                pat = [(0, 6, 0), (10, 4, 0)]
            for st, ln, off in pat:
                if mood == 'nightmare' and b == 11 and st >= 8:
                    continue
                root = at(ch, st)[1] + tr
                d = ln * m.sl * 0.9
                if mood == 'normal':
                    x = rubber([root + off], d, cut=240, env=1700, fdec=0.08, sb=0.7)
                elif mood == 'hard':
                    x = rubber([root + off], d, cut=140, env=450 + 60 * (b % 8), fdec=0.06, res=2.8, sb=0.8)
                elif mood == 'super':
                    x = reese([root + off], d, cut=560 + 30 * (b % 8), lfo=bpm / 60 / (4 if q % 2 == 0 else 2))
                else:
                    x = reese([root + (off if off < 12 else 0)], d, cut=700 + 50 * (b % 8), lfo=3, det=0.28)
                m.add('bass', m.bt(b, st), x)
        # ---- chords
        if sec == 'intro':
            for st, _, v in ch:
                m.P('comp', b, ". " * st + v, keys, tr=tr, gt=(16 - st if len(ch) == 1 or st else 8) * 0.9, bright=0.5 + 0.15 * b)
        else:
            steps = COMP['garage' if garage and mood == 'normal' else mood][b % 2]
            if sec == 'out':
                steps = [0, 6] if not dark else [0]
            for st in steps:
                v = at(ch, st)[2]
                if mood == 'normal':
                    m.P('comp', b, ". " * st + v, keys, tr=tr, gt=1.6, bright=1.0)
                elif mood == 'hard':
                    m.P('comp', b, ". " * st + v, keys, tr=tr, gt=5.0, bright=0.4)
                elif mood == 'super':
                    m.P('comp', b, ". " * st + v, keys, tr=tr, gt=1.4, bright=1.25)
                    m.P('stab', b, ". " * st + v, stab, tr=tr, gt=1.2, cut=600, env=3600, fdec=0.06, adec=0.12)
                else:
                    m.P('comp', b, ". " * st + v, keys, tr=tr, gt=1.2, bright=0.7)
                    m.P('stab', b, ". " * st + v, stab, tr=tr, gt=1.4, cut=800, env=4500, fdec=0.07, adec=0.16, bend=-2 if st % 2 else 2)
            if not heavy:
                for i, (st, _, v) in enumerate(ch):
                    ln = (16 - st if i == len(ch) - 1 else ch[i + 1][0] - st)
                    m.P('pad', b, ". " * st + v + " -" * (ln - 1), pad, tr=tr, cut=1100 if not dark else 550, cut2=1700 if not dark else 1000,
                        att=0.15, rel=0.3, hp=250, gt=1.0)
        # ---- hook
        if sec == 'intro':
            if b < 2 or not heavy:
                m.P('bell', b, hk, bell, tr=tr + (0 if dark else 12), dec=0.5, idx=1.5 if not dark else 2.4, ratio=3.5 if not dark else 3.01)
        elif mood == 'normal':
            m.P('hook', b, hk, pluck, tr=tr, gt=1.4, cut=900, env=4500, fdec=0.08, adec=0.28)
            m.P('hook', b, hk, lead, 0.5, tr=tr, gt=1.2, cut=1000, env=1800, fdec=0.1)
            if sec == 'B':
                m.P('bell', b, hk, bell, tr=tr + 12, dec=0.45, idx=1.5)
        elif mood == 'hard':
            m.P('hook', b, hk, pluck, tr=tr - 12, gt=1.4, cut=380 + 25 * (b % 8), env=2300, fdec=0.07, adec=0.3)
            if sec == 'B':
                m.P('bell', b, hk, bell, tr=tr, dec=0.6, idx=2.4, ratio=3.01)
        elif mood == 'super':
            m.P('hook', b, hk, lead, tr=tr, gt=1.3, cut=1300, env=3500, fdec=0.1)
            m.P('hook', b, hk, pluck, 0.6, tr=tr + 12, gt=1.2, cut=900, env=5000, adec=0.2)
            if sec == 'B':
                m.P('bell', b, hk, bell, tr=tr + 12, dec=0.35, idx=2.0)
        else:
            if sec != 'A' or q < 2:
                m.P('hook', b, hk, lead, tr=tr, gt=1.3, cut=950, env=3200, fdec=0.1, vib=0.006)
                m.P('hook', b, hk, pluck, 0.6, tr=tr - 12, gt=1.2, cut=600, env=4000, adec=0.2)
            m.P('bell', b, ". " * (0 if b % 2 == 0 else 8) + "C4", bell, tr=key - 60 + (7 if b % 2 == 0 else 8) + 12, dec=0.45, idx=3.0, ratio=2.76)
        # ---- drums
        tk = dict(f=3400 if mood == 'hard' else 4200)
        if sec == 'intro':
            heart(m, 'kick', b, 0, 0.9, 4)
            if mood == 'nightmare':
                heart(m, 'kick', b, 8, 0.9, 4)
            if dark:
                m.D('tick', b, "x.x.x.x.x.x.x.x." if b < 2 else "xxxxxxxxxxxxxxxx", tick, 0.5, pan=0.3 if b % 2 else -0.3, **tk)
            else:
                m.D('hat', b, "x.x-x.xox.x-x.xo", hat, 0.15, pan=0.25, dec=0.02)
            if b == 3:
                roll(m, 3, 8, 8, 2 if heavy else 1, 0.15, 0.8 if heavy else 0.5)
        elif mood == 'normal':
            kinds = c.get('dn', "TUTVTUTF" + "UJUVUJUF" + "HHHF")[b - 4]
            if garage:
                kinds = "GGGFGGGF" [(b - 4) % 8] if sec != 'out' else "HHHF"[q]
            kt += brk(m, b, kinds, kg=0.85, sg=0.7, hg=0.2, sf=215, kp='light', sd=0.09)
            if sec == 'B':
                m.D('hat', b, "..x...x...x...x.", hat, 0.22, dec=0.06, pan=-0.2)
                m.D('hat', b, "x-xox-xox-xox-xo", shaker, 0.5, pan=0.5)
            if garage:
                m.D('rim', b, "..x......x......", rim, 0.6, pan=-0.3)
        elif mood == 'hard':
            hole = sec == 'A' and b == 11
            kt += m.D('kick', b, "x.........x." if hole else ("x.....x........." if sec == 'out' else "x.........x....."), kick, 0.9, **KICKS['soft'])
            m.D('rim', b, "....x......." if hole else ("........x......." if sec == 'out' else "....x.......x..."), rim, 0.9, f=1500)
            m.D('tick', b, "xxxxxxxxxxxx" if hole else "xxxxxxxxxxxxxxxx", tick, 0.5, pan=0.3 if b % 2 else -0.3, **tk)
            if not hole:
                m.D('snare', b, ".......o.o.....o" if q != 3 else ".......o.o..o.oo", snare, 0.45, f=220, dec=0.06, nz=0.8)
            if sec == 'B':
                m.D('hat', b, "..x...x...x...x.", hat, 0.2, dec=0.05, pan=-0.2)
                m.D('snare', b, "....x.......x...", snare, 0.35, f=210, dec=0.08)
            if hole:
                heart(m, 'kick', b, 12, 1.0, 2)
                holes.append((b, 12, 16))
            if q == 0:
                heart(m, 'tick', b, 0, 0.5, 4)
        elif mood == 'super':
            if sec == 'out':
                kinds = "HHAC"[q]
            else:
                kinds = ("ABACABAC" if sec == 'A' else "UBUCUBAC")[(b - 4) % 8]
            kt += brk(m, b, kinds, hats="x.xox.xox.xox.xo" if sec == 'A' else "xoxoxoxoxoxoxoxo", rd=sec == 'B', sf=205)
            if b in (11, 19):
                roll(m, b, 12, 4, 2, 0.3, 0.9, 210, 300)
        else:
            if b == 11:
                kt += m.D('kick', b, "x.x.....", kick, **KICKS['heavy'])
                m.D('snare', b, "....X...", snare, 0.8)
                m.D('tick', b, "........x.x.x.xx", tick, 0.7)
                heart(m, 'tick', b, 8, 1.0, 3)
                holes.append((b, 8, 16))
            elif b == 19:
                kt += m.D('kick', b, "x.x.....", kick, **KICKS['heavy'])
                m.D('snare', b, "....X...", snare, 0.8)
                for i in range(16):
                    t = m.bt(b, 8 + i * 0.5)
                    m.add('kick', t, kick(**KICKS['heavy']), 0.45 + 0.035 * i)
                    kt.append(t)
            elif b in (22, 23):
                kt += m.D('kick', b, "x...x...x...x..." if b == 22 else "x.x.x.x.xxxxxxxx", kick, **KICKS['heavy'])
                roll(m, b, 0, 16, 1 if b == 22 else 2, 0.12 if b == 22 else 0.5, 0.5 if b == 22 else 1.0, 190, 300)
            else:
                kinds = "HH"[q] if sec == 'out' else "UBUC"[q]
                kt += brk(m, b, kinds, hats="xoxoxoxoxoxoxoxo", rd=sec == 'B', sf=195)
                if sec == 'B' and q % 2:
                    for i in range(8):
                        m.add('hat', m.bt(b, 12 + i * 0.5), hat(dec=0.012), 0.16, 0.4)
    # ---- one-shots and long layers
    m.add('fx', m.bt(2, 0), riser(m.sl * 32, 300, 9000), 0.9 if heavy else 0.6)
    m.add('fx', m.bt(19, 0), riser(m.sl * 16, 500, 9000), 0.6)
    if heavy:
        for b_, f_ in ((4, 55), (12, 50), (20, 46)):
            m.add('fx', m.bt(b_, 0), impact(f_), 1.0)
    if dark:
        m.add('fx', m.bt(10, 0), riser(m.sl * 28 if mood == 'hard' else m.sl * 24, 250, 6000), 0.7)
        cl = [key - 12, key - 11, key - 6] if mood == 'nightmare' else [key - 12 + 7, key - 12 + 8]
        tone = "+".join(["C4"] * len(cl))
        for b0, ln, c1, c2, bd in ((0, 64, 400, 1500, 0), (12, 128, 800, 3200, 2.0 if mood == 'nightmare' else 0), (20, 64, 600, 2600, 0)):
            x = pad(cl, ln * m.sl, cut=c1, cut2=c2, att=m.sl * ln * 0.4, rel=0.2, hp=350, spread=0.3, bend=bd)
            m.add('tens', m.bt(b0, 0), x)
    if mood == 'nightmare':
        m.add('fx', m.bt(1, 8), clang(410, 0.6), 0.5, -0.5)
        m.add('fx', m.bt(3, 0), clang(290, 0.7), 0.5, 0.5)
        m.add('fx', m.bt(22, 0), riser(m.sl * 32, 300, 11000), 1.0)
    # ---- mix
    hole = mute(m, holes) if holes else 1.0
    dk = duck(m.n, kt, {'normal': 0.4, 'hard': 0.45, 'super': 0.5, 'nightmare': 0.5}[mood], 0.07)
    dr = m.get('kick') * 0.95 + m.get('snare') * 0.9 + m.get('hat') + m.get('rim') * 0.8
    d3 = m.sl * 3
    if mood == 'normal':
        y = (drumbus(dr, 1.3, 0.08) * 0.78 + 0.5 * m.get('bass') * dk + 0.6 * wide(rev(m.get('comp') * dk, 1.0, 0.2))
             + 0.72 * pan(rev(delay(m.get('hook'), d3, 0.35, 0.22), 1.2, 0.16), -0.08) + 0.3 * pan(rev(delay(m.get('bell'), d3, 0.3, 0.2), 1.8, 0.3), 0.2)
             + 0.3 * rev(m.get('pad') * dk, 1.8, 0.3) + 0.3 * m.get('fx'))
        return master(y, -13, 1.15, m.body)
    if mood == 'hard':
        y = (drumbus(dr, 1.2, 0.12, t60=0.6) * 0.7 + 0.52 * m.get('bass') * dk * hole + 0.5 * wide(rev(bq(m.get('comp'), 'lp', 2200) * dk, 1.8, 0.3)) * hole
             + 0.85 * rev(delay(m.get('hook'), d3, 0.45, 0.32, lp=2400), 1.6, 0.22) * hole + 0.2 * rev(delay(m.get('bell'), d3, 0.4, 0.3), 2.2, 0.4) * hole
             + 0.4 * rev(m.get('pad') * dk, 2.2, 0.35) * hole + 0.22 * rev(m.get('tens'), 2.0, 0.3) * hole
             + 0.4 * rev(m.get('tick'), 1.0, 0.25) + 0.32 * m.get('fx'))
        return master(shelf(y, 5000, -2), -14, 1.05, m.body)
    y = (drumbus(dr, 2.0 if mood == 'super' else 2.3, 0.1, -16, 4) * 0.8 + 0.42 * m.get('bass') * dk * hole
         + 0.5 * wide(rev(m.get('comp') * dk, 0.9, 0.18)) * hole + 0.42 * rev(m.get('stab') * dk, 1.0, 0.22) * hole
         + 0.55 * rev(delay(m.get('hook'), d3, 0.35, 0.22), 1.1, 0.16) * dk * hole + 0.26 * rev(delay(m.get('bell'), d3, 0.45, 0.35), 1.6, 0.3) * hole
         + 0.2 * rev(m.get('tens'), 2.0, 0.3) * dk * hole + 0.45 * rev(m.get('tick'), 1.2, 0.3) + 0.3 * rev(m.get('fx'), 1.5, 0.3))
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
