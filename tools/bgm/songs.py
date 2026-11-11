"""Twelve BGM sketches for Pino: three per difficulty. Run make.py to render."""
import numpy as np
from engine import *  # noqa


def seqs(m, bus, bar, pats, inst, **kw):
    for i, p in enumerate(pats):
        m.P(bus, bar + i, p, inst, **kw)


def chords(m, bus, bar, rhythm, names, inst, **kw):
    for i, c in enumerate(names):
        m.P(bus, bar + i, rhythm.replace('X', c), inst, **kw)


def drumbus(x, drive=1.4, room=0.1, thr=-14, ratio=3, t60=0.4):
    x = comp(sat(x * 0.9, drive), thr, ratio, 0.004, 0.09, 1.2)
    return rev(x, t60, room, 0.005, 400, 8000, seed=3)


def mute(m, spans, fade=0.004):
    """Gain curve that drops to zero inside each (bar, step0, step1) span."""
    e = np.ones(m.n)
    f = int(fade * SR)
    for bar, a, b in spans:
        i, j = int(m.bt(bar, a) * SR), int(m.bt(bar, b) * SR)
        e[i:j] = 0
        e[max(0, i - f):i] = np.minimum(e[max(0, i - f):i], np.linspace(1, 0, f)[-(i - max(0, i - f)):])
        e[j:j + f] = np.minimum(e[j:j + f], np.linspace(0, 1, f)[:len(e[j:j + f])])
    return e


def heart(m, bus, bar, step=0, g=1.0, gap=3.0):
    m.add(bus, m.bt(bar, step), thud(62, 0.11), g)
    m.add(bus, m.bt(bar, step + gap), thud(74, 0.08), g * 0.7)


BRK = {
    'A': ("x.x.......xx....", "....X.......X...", ".......o.o.....o"),
    'B': ("x.x.......x.....", "....X.........X.", ".......o.o..o..."),
    'C': ("x.x...x...x.....", "....X..o.X..X.XX", "................"),
    'T': ("x.........x.....", "....X.......X...", "......o..o....o."),
    'U': ("x.........xx....", "....X.......X...", ".o....o..o...oo."),
    'H': ("x.....x.........", "........X.......", "..............o."),
}


def brk(m, bar, kinds, hats="x.xox.xox.xox.xo", kg=1.0, sg=0.8, hg=0.22, rd=True, sf=200):
    kt = []
    for i, k in enumerate(kinds):
        K, S, G = BRK[k]
        kt += m.D('kick', bar + i, K, kick, kg, f0=230, f1=55, pt=0.02, dec=0.13, click=0.6, drive=2.5)
        m.D('snare', bar + i, S, snare, sg, f=sf, dec=0.13, nz=1.1)
        m.D('snare', bar + i, G, snare, sg * 0.9, f=sf * 1.1, dec=0.07, nz=0.8)
        m.D('hat', bar + i, hats, hat, hg, pan=0.25, dec=0.022)
        if rd:
            m.D('hat', bar + i, "x...x...x...x...", ride, hg * 0.9, pan=-0.3)
    return kt


def roll(m, bar, step0, steps, div=1, g0=0.25, g1=0.9, f0=190, f1=260):
    n = int(steps * div)
    for i in range(n):
        r = i / max(1, n - 1)
        m.add('snare', m.bt(bar, step0 + i / div), snare(f=f0 + (f1 - f0) * r, dec=0.07, nz=0.9), g0 + (g1 - g0) * r)


# ======================= NORMAL =======================
def n1():
    """Tiptoe: swung, plucky, a heartbeat kick under a sneaking bass."""
    m = Mix(104, 16, swing=0.24)
    Dm, Bb, A7, Em = "F3+A3+C4+E4", "F3+A3+Bb3+D4", "G3+Bb3+C#4+E4", "G3+Bb3+D4+E4"
    bA = ["D2 . . D2 . . F2 . G2 . . G#2 A2 . . .", "D2 . . D2 . . C2 . . . A1 . C2 . C#2 .",
          "Bb1 . . Bb1 . . D2 . F2 . . . Bb1 . . .", "A1 . . A1 . . C#2 . E2 . G2 . A2 . C#2 ."]
    bB = ["G1 . . G1 . . Bb1 . D2 . . . G2 . . .", "D2 . . D2 . . F2 . A2 . . . D2 . C2 .",
          "E2 . . E2 . . G2 . Bb2 . . . E2 . . .", "A1 . . A1 . . C#2 . E2 . G2 . A2 - - ."]
    lA = ["A4 . . D5 . . . . F5 . E5 . D5 . . .", ". . A4 . C5 . D5 . . . . . . . . .",
          "A4 . . D5 . . . . F5 . G5 . A5 . . .", ". . G5 . F5 . E5 . C#5 . . . . . . ."]
    lB = ["D5 . . Bb4 . . G4 . . . A4 . Bb4 . D5 .", "F5 - - . E5 . D5 . . . A4 . . . . .",
          "G5 . . E5 . . Bb4 . . . D5 . E5 . G5 .", "A5 . G5 . F5 . E5 . C#5 . . . A4 . . ."]
    for r in (0, 4):
        seqs(m, 'bass', r, bA, rubber, cut=260, env=1500, fdec=0.1, tr=12, gt=0.8)
        seqs(m, 'lead', r, lA, pluck, cut=700, env=3800, fdec=0.06, adec=0.22)
        chords(m, 'ep', r, ". . . . . . X . . . . . X . . .", [Dm, Dm, Bb, A7], epiano, gt=1.6)
    seqs(m, 'bell', 4, lA, bell, tr=12, dec=0.5, idx=1.4)
    for r in (8, 12):
        seqs(m, 'bass', r, bB, rubber, cut=260, env=1500, fdec=0.1, tr=12, gt=0.8)
        seqs(m, 'lead', r, lB, pluck, cut=700, env=3800, fdec=0.06, adec=0.22)
        chords(m, 'ep', r, ". . . X . . . . . . X . . . X .", [Bb, Dm, Em, A7], epiano, gt=1.6)
    seqs(m, 'bell', 12, lB, bell, tr=12, dec=0.5, idx=1.4)
    kt = m.D('kick', 0, "X..x....X..x....|X..x....X.x..x..", kick, rep=8, f0=120, f1=48, dec=0.17, click=0.15, drive=1.4)
    m.D('snap', 0, "....x.......x...", snap, rep=16)
    m.D('hat', 0, "x.xox.xox.xox.xo", hat, rep=16, pan=0.2, dec=0.018)
    m.D('hat', 8, "..x...x...x...x.", shaker, rep=8, pan=-0.3)
    m.D('snap', 7, "..........x.x.xx", rim)
    m.D('snap', 15, "........x..x.x.x", rim)
    dk = duck(m.n, kt, 0.35, 0.1)
    ld = rev(delay(m.get('lead'), m.sl * 3, 0.35, 0.22), 1.3, 0.16)
    bl = rev(delay(m.get('bell'), m.sl * 3, 0.3, 0.2), 2.0, 0.3)
    y = (0.6 * m.get('kick') + 0.5 * m.get('bass') * dk + 0.8 * pan(ld, -0.12) + 0.34 * pan(bl, 0.25)
         + 0.62 * wide(rev(m.get('ep') * dk, 1.2, 0.25)) + 0.6 * rev(m.get('snap'), 0.7, 0.25) + 0.7 * m.get('hat'))
    return master(y, -14.5, 1.05, m.body)


def n2():
    """Midnight Snack: straight four-on-the-floor, rubber octave bass, chopped stabs."""
    m = Mix(118, 16)
    oct_ = lambda a, b, c, d, e, f: f"{a}2 . {a}3 . . {a}2 . {b} {a}2 . {a}3 . {c} . {d} {e}".replace('~', f)
    bE = "E2 . E3 . . E2 . D3 E2 . E3 . G2 . A2 B2"
    bC = "C2 . C3 . . C2 . B2 C2 . C3 . E2 . G2 C3"
    bB = "B1 . B2 . . B1 . A2 B1 . B2 . D#2 . F#2 A2"
    bA = "A1 . A2 . . A1 . G2 A1 . A2 . C2 . E2 G2"
    bBm = "B1 . B2 . . B1 . A2 B1 . B2 . D2 . F#2 A2"
    bD = "D2 . D3 . . D2 . C3 B1 . B2 . D#2 . F#2 B2"
    Em, C, B7, Am, Bm, D = "G3+B3+D4+F#4", "G3+B3+C4+E4", "A3+B3+D#4+F#4", "G3+A3+C4+E4", "A3+B3+D4+F#4", "A3+D4+F#4"
    lA = ["B4 . D5 E5 . . . . . . G5 . F#5 . E5 .", "D5 . . B4 . . . . . . . . . . . .",
          "E5 . G5 B5 . . . . . . A5 . G5 . E5 .", "F#5 . . D#5 . . B4 . . . . . . . . ."]
    lB = ["C5 . E5 . A5 . . G5 . . E5 . . . . .", "D5 . F#5 . B5 . . A5 . . F#5 . . . . .",
          "E5 . G5 . C6 . . B5 . . G5 . E5 . . .", "A5 . F#5 . D5 . . . D#5 . F#5 . B5 . . ."]
    for r in (0, 4):
        seqs(m, 'bass', r, [bE, bE, bC, bB], rubber, cut=220, env=2400, fdec=0.07, res=3.2, tr=12, gt=0.7)
        chords(m, 'stab', r, ". . X . . X . . . . X . . X . .", [Em, Em, C, B7], stab, cut=500, env=3200, fdec=0.06, adec=0.12, gt=0.7)
        seqs(m, 'lead', r, lA, pluck, cut=900, env=4200, fdec=0.08, adec=0.25)
    for r in (8, 12):
        seqs(m, 'bass', r, [bA, bBm, bC, bD], rubber, cut=220, env=2400, fdec=0.07, res=3.2, tr=12, gt=0.7)
        chords(m, 'stab', r, ". . X . . X . . . . X . . X . .", [Am, Bm, C, D if r == 8 else B7], stab, cut=500, env=3200, fdec=0.06, adec=0.12, gt=0.7)
        seqs(m, 'lead', r, lB, pluck, cut=900, env=4200, fdec=0.08, adec=0.25)
    seqs(m, 'bell', 4, lA, bell, tr=12, dec=0.45, idx=1.5)
    seqs(m, 'bell', 12, lB, bell, dec=0.45, idx=1.5)
    kt = m.D('kick', 0, "x...x...x...x...", kick, rep=16, f0=150, f1=50, dec=0.18, click=0.3)
    m.D('clap', 0, "....x.......x...", clap, rep=16, dec=0.09)
    m.D('hat', 0, "..x...x...x...x.", hat, 1.3, rep=16, dec=0.07, pan=-0.2)
    m.D('hat', 0, "xo.oxo.oxo.oxo.o", hat, 0.7, rep=16, dec=0.015, pan=0.3)
    m.D('hat', 4, "x.xxx.xxx.xxx.xx", shaker, 0.6, rep=12, pan=0.5)
    m.D('clap', 7, ".............xxx", rim)
    m.add('fx', m.bt(7, 0), riser(m.sl * 16, 400, 7000), 0.5)
    m.add('fx', m.bt(15, 0), riser(m.sl * 16, 400, 7000), 0.5)
    dk = duck(m.n, kt, 0.55, 0.13)
    ld = rev(delay(m.get('lead'), m.sl * 3, 0.4, 0.25), 1.4, 0.18)
    bl = rev(delay(m.get('bell'), m.sl * 3, 0.3, 0.2), 2.0, 0.3)
    y = (0.62 * m.get('kick') + 0.5 * m.get('bass') * dk + 0.75 * pan(ld, -0.12) + 0.32 * pan(bl, 0.25) + 0.3 * m.get('fx') * dk
         + 0.6 * rev(m.get('stab') * dk, 0.9, 0.22) + 0.6 * rev(m.get('clap'), 0.9, 0.25) + 0.6 * m.get('hat'))
    return master(y, -13.5, 1.1, m.body)


def n3():
    """Fridge Light: slow and cold, glass bells over a lub-dub kick."""
    m = Mix(92, 12, swing=0.2)
    F, E, D, E7 = "F3+A3+C4+E4", "E3+G3+B3+D4", "D3+F3+A3+C4+E4", "E3+G#3+B3+D4"
    bF, bE = "F2 . . . . . . F2 . . C3 . . . . .", "E2 . . . . . . E2 . . B2 . . . D2 ."
    bD, b7 = "D2 . . . . . . D2 . . A2 . . . . .", "E2 . . . . . . E2 . . G#2 . B2 . D3 ."
    mA = ["E5 . . . C5 . . A4 . . B4 . C5 . . .", "D5 . . . B4 . . G4 . . . . . . E4 G4",
          "A4 . . . F4 . . E4 . . F4 . A4 . . .", "G#4 . . . B4 . . . E5 - - - . . . ."]
    mB = ["F5 . E5 . D5 . . A4 . . . . D5 . E5 .", "G5 . E5 . D5 . . B4 . . . . . . . .",
          "A5 . G5 . E5 . . C5 . . E5 . . . . .", "G#5 . . . E5 . . B4 . . G#4 . . . . ."]
    cA = [". . C4 . . . E4 . . . . . . . A3 .", ". . B3 . . . D4 . . . G3 . . . . .",
          ". . A3 . . . D4 . . . . . . . F3 .", ". . B3 . . . G#3 . . . D4 . E4 . . ."]
    for r in (0, 4):
        seqs(m, 'bass', r, [bF, bE, bD, b7], rubber, cut=200, env=900, fdec=0.14, res=1.5, sb=0.9, gt=1.4)
        seqs(m, 'bell', r, mA, bell, dec=0.9, idx=1.8)
        for i, c in enumerate([F, E, D, E7]):
            m.P('pad', r + i, c + " - - - - - - - - - - - - - - -", pad, cut=900, cut2=1900, att=0.4, rel=0.6, gt=1.0)
    seqs(m, 'pl', 4, cA, pluck, cut=600, env=2600, fdec=0.09, adec=0.3)
    seqs(m, 'bass', 8, [bD, bE, bF, b7], rubber, cut=200, env=900, fdec=0.14, res=1.5, sb=0.9, gt=1.4)
    seqs(m, 'bell', 8, mB, bell, dec=0.9, idx=1.8)
    seqs(m, 'pl', 8, [cA[2], cA[1], cA[0], cA[3]], pluck, cut=600, env=2600, fdec=0.09, adec=0.3)
    for i, c in enumerate([D, E, F, E7]):
        m.P('pad', 8 + i, c + " - - - - - - - - - - - - - - -", pad, cut=1100, cut2=2400, att=0.4, rel=0.6)
    kt = m.D('kick', 0, "X..x......X..x..", kick, rep=12, f0=110, f1=46, dec=0.2, click=0.12, drive=1.3)
    m.D('rim', 0, "....x.......x...", rim, rep=12, pan=-0.15)
    m.D('rim', 4, "............x...", snap, 0.7, rep=8)
    m.D('hat', 0, "x.x.x.x.x.x.x.xo", hat, rep=12, pan=0.25, dec=0.02)
    m.D('hat', 4, "..x...x...x...x.", shaker, 0.8, rep=8, pan=-0.35)
    dk = duck(m.n, kt, 0.4, 0.14)
    bl = rev(delay(m.get('bell'), m.sl * 3, 0.4, 0.28), 2.4, 0.35)
    y = (0.6 * m.get('kick') + 0.48 * m.get('bass') * dk + 0.75 * bl + 0.5 * rev(m.get('pad') * dk, 2.0, 0.3)
         + 0.5 * pan(rev(delay(m.get('pl'), m.sl * 6, 0.3, 0.2, lp=2500), 1.4, 0.2), -0.25)
         + 0.6 * rev(m.get('rim'), 0.9, 0.3) + 0.6 * m.get('hat'))
    return master(y, -15, 1.0, m.body)


# ======================= HARD (toned down, tense) =======================
def h1():
    """Lights Out: the Tiptoe motif an octave down over a closed, pulsing bass."""
    m = Mix(108, 16)
    pulse8 = lambda a, b="": f"{a} . {a} . {a} . {a} . {a} . {a} . {a} . {b or a + ' .'}"
    bs = [pulse8("D2", "F2 E2"), pulse8("D2", "C2 C#2"), pulse8("Bb1", "A1 Bb1"), pulse8("A1", "C#2 E2"),
          pulse8("D2", "F2 E2"), pulse8("Eb2", "D2 Eb2"), pulse8("G1", "Bb1 D2"), pulse8("A1", "G2 C#2")]
    lA = ["A3 . . D4 . . . . F4 . E4 . D4 . . .", ". . A3 . C4 . D4 . . . . . . . . .",
          "A3 . . D4 . . . . F4 . G4 . A4 . . .", ". . G4 . F4 . E4 . C#4 . . . . . . ."]
    lB = ["D4 . . Eb4 . . . . D4 . . . A3 . . .", "Bb3 . . A3 . . . . G3 . . Bb3 . . D4 .",
          "G4 . . F4 . . D4 . . . Bb3 . . . . .", "C#4 . . E4 . . G4 . Bb4 . . . A4 . . ."]
    pads = ["D3+A3+E4", "D3+A3+F4", "Bb2+F3+D4", "A2+G3+C#4", "D3+A3+E4", "Eb3+Bb3+D4+A4", "G2+D3+Bb3", "A2+G3+Bb3+C#4"]
    for r in (0, 8):
        seqs(m, 'bass', r, bs, rubber, cut=150, env=650 if r == 0 else 1100, fdec=0.08, res=2.8, tr=12, gt=0.75)
        for i, c in enumerate(pads):
            m.P('pad', r + i, c + " - - - - - - - - - - - - - - -", pad, cut=600, cut2=1300, att=0.5, rel=0.7, hp=200)
    seqs(m, 'lead', 0, lA + lB, pluck, cut=350, env=2200, fdec=0.07, adec=0.3, tr=12)
    seqs(m, 'lead', 8, lA + lB, pluck, cut=450, env=3000, fdec=0.07, adec=0.3, tr=12)
    seqs(m, 'bell', 12, lB, bell, tr=24, dec=0.6, idx=2.4, ratio=3.01)
    kt = []
    for b in range(16):
        if b == 7:
            kt += m.D('kick', b, "X..x........", kick, f0=110, f1=45, dec=0.2, click=0.1, drive=1.3)
        else:
            kt += m.D('kick', b, "X..x....x..x...." if b >= 8 else "X..x............", kick, f0=110, f1=45, dec=0.2, click=0.1, drive=1.3)
            m.D('rim', b, "............x..." if b < 8 else "....x.......x...", rim, f=1500)
        m.D('hat', b, "xxxxxxxxxxxxxxxx" if b != 7 else "xxxxxxxxxxxx....", tick, 0.5, pan=0.3 if b % 2 else -0.3, f=3400)
        if b >= 8:
            m.D('hat', b, "..x...x...x...x.", hat, 0.9, dec=0.03, pan=0.2)
    m.add('fx', m.bt(7, 0), riser(m.sl * 16, 250, 5000), 0.7)
    m.add('fx', m.bt(15, 4), riser(m.sl * 12, 250, 5000), 0.6)
    dk = duck(m.n, kt, 0.45, 0.14)
    ld = rev(delay(m.get('lead'), m.sl * 3, 0.45, 0.3, lp=2400), 1.8, 0.22)
    y = (0.62 * m.get('kick') + 0.5 * m.get('bass') * dk + 0.8 * ld + 0.55 * rev(m.get('pad') * dk, 2.4, 0.35)
         + 0.2 * rev(delay(m.get('bell'), m.sl * 3, 0.4, 0.3), 2.4, 0.4) + 0.55 * rev(m.get('rim'), 1.4, 0.35)
         + 0.45 * m.get('hat') + 0.35 * m.get('fx'))
    return master(y, -15, 1.0, m.body)


def h2():
    """Hold Your Breath: minimal pulse, a rolling low F and far-off stabs."""
    m = Mix(122, 16)
    roll_b = ". F2 F2 F2 . F2 F2 F2 . F2 F2 F2 . F2 F2 Gb2"
    roll_c = ". F2 F2 F2 . F2 F2 F2 . Eb2 Eb2 Eb2 . Gb2 Gb2 Gb2"
    kt = []
    for b in range(16):
        m.P('bass', b, roll_c if b % 4 == 3 else roll_b, rubber, cut=140, env=500 + 60 * b, fdec=0.05, res=2.5, sb=0.9, gt=0.6)
        full = b >= 8
        if b == 7:
            kt += m.D('kick', b, "x...x...x...", kick, f0=130, f1=47, dec=0.2, click=0.2)
            heart(m, 'kick', 7, 12, 0.9, 2)
        else:
            kt += m.D('kick', b, "x...x...x...x.x." if b % 4 == 3 else "x...x...x...x...", kick, f0=130, f1=47, dec=0.2, click=0.2)
            m.D('hat', b, "xoxoxoxoxoxoxoxo", tick, 0.6, pan=0.25, f=4200)
            m.D('hat', b, "..x...x...x...x.", hat, 1.0 if full else 0.5, dec=0.05 if full else 0.02, pan=-0.2)
        if b >= 4 and b != 7:
            m.D('clap', b, "....x.......x...", clap, dec=0.1, f=1100)
        if full:
            m.D('rim', b, ".......x..x....x" if b % 2 else "..x....x.....x..", rim, 0.8, pan=0.4, f=2100)
    st = [(0, 3, "F4+Ab4+C5"), (1, 10, "Gb4+Bb4+Db5"), (2, 6, "Eb4+Ab4+C5"), (3, 3, "Gb4+A4+C5"), (3, 11, "Gb4+A4+C5")]
    for r in (0, 4, 8, 12):
        for b, s, c in st:
            m.P('stab', r + b, ". " * s + c, stab, cut=400, env=2600, fdec=0.12, adec=0.3, gt=1.5)
    for r in (4, 12):
        m.P('lead', r, "C5 . . . . . Db5 . . . C5 . . . Ab4 . | . . . . . . . . . . . . . . . .", bell, dec=0.7, idx=2.6, ratio=2.99)
        m.P('lead', r + 2, "F5 . . . . . Gb5 . . . F5 . . . Eb5 Db5", bell, dec=0.7, idx=2.6, ratio=2.99)
    acid = "F3 F3 Ab3 F3 C4 F3 Gb3 F3 F3 Eb4 F3 C4 F3 Ab3 Gb3 F3"
    for b in range(8, 16):
        m.P('acid', b, acid, pluck, cut=250 + 140 * (b - 8), env=900 + 420 * (b - 8), fdec=0.05, res=4.0, adec=0.15, gt=0.6)
    m.P('pad', 0, "F2+C3+F3" + " -" * 127, pad, cut=500, cut2=900, att=1.5, rel=1.0, hp=120, gt=1.0)
    m.P('pad', 8, "Gb4+C5+F5" + " -" * 127, pad, cut=700, cut2=2600, att=4.0, rel=0.5, hp=400, gt=1.0)
    m.add('fx', m.bt(6, 0), riser(m.sl * 32, 200, 6000), 0.8)
    m.add('fx', m.bt(14, 0), riser(m.sl * 32, 200, 8000), 0.8)
    dk = duck(m.n, kt, 0.6, 0.12)
    cut = mute(m, [(7, 12, 16)])
    y = (0.62 * m.get('kick') + 0.5 * m.get('bass') * dk * cut
         + 0.62 * rev(delay(m.get('stab'), m.sl * 3, 0.55, 0.45, lp=2500), 2.2, 0.4)
         + 0.34 * rev(delay(m.get('lead'), m.sl * 6, 0.4, 0.3), 2.4, 0.4) + 0.5 * delay(m.get('acid'), m.sl * 3, 0.4, 0.3) * dk
         + 0.45 * rev(m.get('pad'), 2.4, 0.3) * dk + 0.55 * rev(m.get('clap'), 1.6, 0.35) + 0.5 * m.get('hat') * cut
         + 0.4 * rev(m.get('rim'), 1.0, 0.3) + 0.36 * m.get('fx'))
    return master(y, -14, 1.05, m.body)


def h3():
    """Footsteps: a broken ostinato through a resonant filter, steps in the dark."""
    m = Mix(114, 16)
    osC = "C4 . G3 C4 . Eb4 . G3 C4 . G3 D4 . Eb4 . G3"
    osA = "C4 . Ab3 C4 . Eb4 . Ab3 C4 . Ab3 D4 . Eb4 . Ab3"
    osF = "C4 . Ab3 C4 . F4 . Ab3 C4 . Ab3 Db4 . F4 . Ab3"
    osG = "B3 . G3 B3 . D4 . G3 B3 . G3 F4 . D4 . Ab3"
    bC, bA = "C2 - - . . . C2 . . . C2 - . . Bb1 B1", "Ab1 - - . . . Ab1 . . . Ab1 - . . G1 Ab1"
    bF, bG = "F2 - - . . . F2 . . . F2 - . . Eb2 F2", "G1 - - . . . G1 . . . G2 - . . B1 D2"
    ld = ["G4 - - - - - Ab4 - G4 - - - Eb4 - - -", "C5 - - - - - Bb4 - Ab4 - - - - - - -",
          "Ab4 - - - - - Bb4 - Ab4 - - - F4 - - -", "D5 - - - - - - - B4 - - - G4 - - -"]
    pd = ["C4+Eb4+G4", "C4+Eb4+Ab4", "C4+F4+Ab4", "B3+D4+G4"]
    kt = []
    for b in range(16):
        q = b % 4
        sw = 0.5 - 0.5 * np.cos(np.pi * b / 8)
        m.P('arp', b, [osC, osA, osF, osG][q], pluck, cut=280 + 500 * sw, env=1500 + 2500 * sw, fdec=0.06, res=3.5, adec=0.2, gt=0.7)
        m.P('pad', b, pd[q] + " -" * 15, pad, cut=700, cut2=1500, att=0.4, rel=0.6, hp=250, gt=1.0)
        if b == 7:
            m.D('step', b, "x...x...x...x...", thud, f=85, dec=0.07)
            m.D('step', b, "..x...x...x...x.", rim, 0.5, f=900)
            continue
        m.P('bass', b, [bC, bA, bF, bG][q], rubber, cut=170, env=1200, fdec=0.1, res=2.2, tr=12 if q != 2 else 0, gt=0.85)
        kt += m.D('kick', b, "x.....x...x....." if b % 2 == 0 else "x.....x...x..x..", kick, f0=160, f1=50, dec=0.16, click=0.35)
        m.D('snare', b, "....x.......x...", snare, f=215, dec=0.08, nz=0.9, tone=0.5)
        m.D('hat', b, "x.x.x.xox.x.x.xo", hat, dec=0.018, pan=0.25)
        if b >= 8:
            m.D('hat', b, "..x...x...x...x.", hat, 1.1, dec=0.06, pan=-0.2)
            m.P('lead', b, ld[q], lead, cut=700, env=1400, fdec=0.4, glide=-2 if q == 0 else 0, vib=0.004)
    m.add('fx', m.bt(7, 0), riser(m.sl * 16, 250, 6000), 0.8)
    m.add('fx', m.bt(15, 8), riser(m.sl * 8, 400, 8000), 0.6)
    dk = duck(m.n, kt, 0.5, 0.12)
    stp = m.get('step') * np.linspace(0.3, 1, m.n)
    stp = stp * np.stack([np.linspace(1, 0.3, m.n), np.linspace(0.3, 1, m.n)])
    y = (0.65 * m.get('kick') + 0.5 * m.get('bass') * dk + 0.6 * rev(delay(m.get('arp'), m.sl * 3, 0.45, 0.35), 1.2, 0.15)
         + 0.4 * rev(m.get('pad') * dk, 2.2, 0.3) + 0.6 * rev(m.get('snare'), 0.9, 0.22) + 0.5 * m.get('hat')
         + 0.55 * rev(delay(m.get('lead'), m.sl * 6, 0.3, 0.25), 2.0, 0.3) + 0.8 * rev(stp, 1.6, 0.5) + 0.3 * m.get('fx'))
    return master(y, -14, 1.05, m.body)


# ======================= SUPER (breakbeat hardcore) =======================
def hardmix(m, kt, parts, rms=-10.5, clip=1.5, dr=2.0):
    d = drumbus(m.get('kick') * 0.95 + m.get('snare') * 0.9 + m.get('hat'), dr, 0.1, -16, 4, 0.35)
    dk = duck(m.n, kt, 0.5, 0.07)
    y = d * 0.8
    for g, x, side in parts:
        y = y + g * (x * dk if side else x)
    return master(y, rms, clip, m.body)


def x1():
    """Caught: 170 breakbeat, reese on F, dark minor stabs."""
    m = Mix(170, 24)
    kt = []
    heart(m, 'kick', 0, 0, 0.9, 4)
    heart(m, 'kick', 1, 0, 0.9, 4)
    kt += brk(m, 2, "AB", kg=0.0, sg=0.45, hg=0.16, rd=False)
    roll(m, 3, 8, 8, 2)
    kt += brk(m, 4, "ABAC" * 4)
    kt += brk(m, 20, "HHAC")
    rs = ["F2 - - - - - - - - - F2 - Ab2 - - -", "F2 - - - - - Eb2 - - - - - Gb2 - - -"]
    for b in range(4, 24, 2):
        m.P('bass', b, rs[0], reese, cut=500 + 40 * (b - 4), lfo=170 / 60 / 4, gt=0.97)
        m.P('bass', b + 1, rs[1] if b % 4 == 0 else "F2 - - - - - - - Ab2 - - - C3 - Bb2 -", reese, cut=650, lfo=170 / 60 / 2, gt=0.97)
    m.P('bass', 0, "F2" + " -" * 63, reese, cut=180, lfo=0.2, depth=0.2, gt=1.0)
    Fm, Gb, Db = "F4+Ab4+C5", "Gb4+Bb4+Db5", "F4+Ab4+Db5"
    s1, s2 = ". . . X . . X . . . . . X . . .", ". . . X . . X . . X . . Y . . ."
    for b in range(4, 20, 2):
        m.P('stab', b, s1.replace('X', Fm if b % 8 < 4 else Db), stab, cut=600, env=4200, fdec=0.07, adec=0.14, bend=-1, gt=0.8)
        m.P('stab', b + 1, s2.replace('X', Fm if b % 8 < 4 else Db).replace('Y', Gb), stab, cut=600, env=4200, fdec=0.07, adec=0.14, bend=-1, gt=0.8)
    m.P('stab', 0, Fm + " . . . . . . . " * 2 + "| " + Gb + " . . . . . . . . . . . . . . .", stab, cut=400, env=2500, fdec=0.2, adec=0.6, gt=3)
    ld = ["C5 . . C5 . . Db5 . C5 . . Ab4 . . Bb4 .", "C5 . . C5 . . Eb5 . Db5 . . C5 . . Ab4 .",
          "F5 . . F5 . . Gb5 . F5 . . Db5 . . Eb5 .", "F5 . . Eb5 . . Db5 . C5 . . Bb4 . Ab4 G4 ."]
    seqs(m, 'lead', 12, ld, lead, cut=900, env=3000, fdec=0.12, gt=0.8)
    seqs(m, 'lead', 16, ld, lead, cut=1200, env=3500, fdec=0.12, gt=0.8)
    seqs(m, 'lead', 20, ld[2:] + ld[2:], pluck, cut=700, env=4000, adec=0.2)
    m.add('fx', m.bt(2, 0), riser(m.sl * 32, 300, 9000), 0.9)
    m.add('fx', m.bt(4, 0), impact(), 1.0)
    m.add('fx', m.bt(19, 0), riser(m.sl * 16, 500, 9000), 0.6)
    m.add('fx', m.bt(20, 0), impact(48), 0.9)
    return hardmix(m, kt, [(0.42, m.get('bass'), 1), (0.55, rev(m.get('stab'), 1.0, 0.22), 1),
                           (0.48, rev(delay(m.get('lead'), m.sl * 3, 0.35, 0.25), 1.2, 0.18), 1), (0.3, rev(m.get('fx'), 1.5, 0.3), 0)])


def x2():
    """Freezer Burn: 174 two-step, growling bass, cold bells."""
    m = Mix(174, 24)
    kt = []
    m.D('hat', 0, "x.xox.xox.xox.xo", hat, 0.14, rep=4, dec=0.02, pan=0.3)
    heart(m, 'kick', 2, 0, 0.9, 4)
    heart(m, 'kick', 3, 0, 0.9, 4)
    roll(m, 3, 8, 8, 2)
    kt += brk(m, 4, "TUTC" * 4, hats="xoxoxoxoxoxoxoxo", sf=215)
    kt += brk(m, 20, "HHTC", sf=215)
    riff = [[("E2", 3, 8), ("E2", 1, 16), ("G2", 3, 4), ("E2", 1, 16), ("F2", 2, 6), ("E2", 1, 12)],
            [("E2", 3, 8), ("E2", 1, 16), ("B1", 3, 3), ("D2", 3, 12), ("F2", 1, 16)]]
    pos = [[0, 4, 6, 10, 12, 14], [0, 4, 6, 10, 14]]
    for b in range(4, 24):
        r = b % 2
        for (note, ln, rate), st in zip(riff[r], pos[r]):
            hz = 174 / 60 * rate / 4
            x = growl([nn(note) + 12], ln * m.sl * 0.95, rate=hz / 2, idx=3 + (b % 4), hi=1800 + 250 * (b % 4), ratio=1 if st % 4 == 0 else 2)
            m.add('bass', m.bt(b, st), x)
    be = ["B5 . . . . . G5 . . . . . F#5 . . .", ". . E5 . . . . . B4 . . . . . . .",
          "B5 . . . . . G5 . . . . . A5 . . .", ". . F#5 . . . . . D5 . . . E5 . . ."]
    for r in (0, 4, 12, 20):
        seqs(m, 'bell', r, be, bell, dec=0.6, idx=2.2, ratio=3.01)
    m.P('pad', 0, "E3+B3+E4+G4" + " -" * 63, pad, cut=500, cut2=3000, att=1.0, rel=0.3, hp=200, gt=1.0)
    for r in (8, 16):
        m.P('pad', r, "E4+G4+B4" + " -" * 63 + " | F4+A4+C5" + " -" * 31 + " | E4+G4+B4" + " -" * 31, pad, cut=1200, att=0.2, rel=0.3, hp=300, gt=1.0)
    for b in range(8, 20, 4):
        m.P('stab', b + 3, ". . . . . . . . E4+G4+B4 . . F4+A4+C5 . . . .", stab, cut=700, env=5000, fdec=0.06, adec=0.12, bend=2)
    m.add('fx', m.bt(2, 0), riser(m.sl * 32, 300, 9000), 0.9)
    m.add('fx', m.bt(4, 0), impact(), 1.0)
    m.add('fx', m.bt(19, 0), riser(m.sl * 16, 500, 9000), 0.6)
    m.add('fx', m.bt(20, 0), impact(46), 0.9)
    return hardmix(m, kt, [(0.42, m.get('bass'), 1), (0.34, rev(delay(m.get('bell'), m.sl * 3, 0.45, 0.35), 2.0, 0.3), 0),
                           (0.3, rev(m.get('pad'), 2.0, 0.25), 1), (0.45, rev(m.get('stab'), 1.0, 0.25), 1), (0.3, rev(m.get('fx'), 1.5, 0.3), 0)])


def x3():
    """Heartbeat Overdrive: the Tiptoe motif at 165 over a hardcore kick and breaks."""
    m = Mix(165, 24)
    mot = ["A4 . . D5 . . . . F5 . E5 . D5 . . .", ". . A4 . C5 . D5 . . . . . . . . .",
           "A4 . . D5 . . . . F5 . G5 . A5 . . .", ". . G5 . F5 . E5 . C#5 . . . . . . ."]
    rf = ["D4 . . D4 . F4 . D4 . . A4 . G4 . F4 E4", "D4 . . D4 . F4 . D4 . . Bb4 . A4 . G4 A4",
          "Bb3 . . Bb3 . D4 . Bb3 . . F4 . E4 . D4 C4", "A3 . . A3 . C#4 . E4 . G4 . Bb4 A4 . . ."]
    seqs(m, 'pl', 0, mot, pluck, cut=450, env=3000, adec=0.3)
    for b in range(4):
        heart(m, 'kick', b, 0, 0.9, 4)
    roll(m, 3, 0, 16, 1, 0.15, 0.9)
    kt = []
    roots = ["D", "D", "Bb", "A"]
    for b in range(4, 24):
        brkonly = 12 <= b < 16
        q = b % 4
        if not brkonly:
            kt += m.D('kick', b, "x...x...x...x..." if q != 3 else "x...x...x...x.xx", hkick, 0.85)
            m.D('snare', b, "....x.......x...", snare, 0.6, f=205, dec=0.12)
            m.D('hat', b, "..x...x...x...x.", hat, 0.3, dec=0.07, pan=-0.2)
            m.D('hat', b, "xoxoxoxoxoxoxoxo", hat, 0.16, dec=0.015, pan=0.3)
            rt = roots[q] + ("1" if roots[q] != "D" else "2")
            m.P('bass', b, f". . {rt} . . . {rt} . . . {rt} . . . {rt} .", rubber, cut=300, env=1500, fdec=0.06, tr=12, gt=1.6)
            m.P('lead', b, rf[q], lead, cut=800 + 60 * (b - 4), env=3000, fdec=0.1, gt=0.75)
            if b >= 16:
                m.P('pl', b, mot[q], stab, cut=900, env=5000, fdec=0.08, adec=0.16, tr=12, gt=1.0)
        else:
            kt += brk(m, b, "ABAC"[q], sf=205)
            rt = roots[q] + "2" if roots[q] == "D" else roots[q] + "1"
            m.P('bass', b, rt + " -" * 15, reese, cut=700, lfo=165 / 60 / 2, tr=12 if roots[q] != "D" else 0, gt=0.97)
            m.P('pl', b, mot[q], pluck, cut=600, env=4500, adec=0.25)
    m.add('fx', m.bt(2, 0), riser(m.sl * 32, 300, 9000), 0.9)
    m.add('fx', m.bt(4, 0), impact(), 1.0)
    m.add('fx', m.bt(15, 0), riser(m.sl * 16, 500, 9000), 0.7)
    m.add('fx', m.bt(16, 0), impact(46), 1.0)
    return hardmix(m, kt, [(0.42, m.get('bass'), 1), (0.46, rev(m.get('lead'), 0.9, 0.15), 1),
                           (0.5, rev(delay(m.get('pl'), m.sl * 3, 0.4, 0.3), 1.4, 0.22), 1), (0.3, rev(m.get('fx'), 1.5, 0.3), 0)], dr=1.8)


# ======================= NIGHTMARE =======================
def m1():
    """Don't Look Back: 176, tritone stabs, sudden holes of silence."""
    m = Mix(176, 28)
    kt = []
    for b in range(4):
        heart(m, 'kick', b, 0, 0.9, 4)
        m.D('tick', b, "x...x...x...x...", tick, 0.6, pan=0.4 if b % 2 else -0.4)
    m.add('fx', m.bt(1, 8), clang(410, 0.6), 0.5, -0.5)
    m.add('fx', m.bt(3, 0), clang(290, 0.7), 0.5, 0.5)
    kt += brk(m, 4, "ABAB" + "ABA")
    kt += m.D('kick', 11, "x.x.....", kick, f0=230, f1=55, dec=0.13, click=0.6, drive=2.5)
    m.D('snare', 11, "....X...", snare, 0.8)
    m.D('tick', 11, "........x.x.x.xx", tick, 0.7)
    heart(m, 'tick', 11, 8, 1.0, 3)
    kt += brk(m, 12, "UBUC" + "UBUB", hats="xoxoxoxoxoxoxoxo")
    kt += brk(m, 20, "HH", rd=False)
    roll(m, 22, 0, 32, 1, 0.12, 0.95, 180, 290)
    kt += m.D('kick', 22, "x...x...x...x...x.x.x.x.xxxxxxxx", kick, f0=230, f1=55, dec=0.1, click=0.6, drive=2.5)
    kt += brk(m, 24, "UBUC", hats="xoxoxoxoxoxoxoxo")
    m.P('bass', 0, "C2" + " -" * 63, reese, cut=160, lfo=0.15, depth=0.3, gt=1.0)
    rb = ["C2 - - - - - - - - - - - Db2 - - -", "C2 - - - - - - - Gb2 - - - F2 - Eb2 -"]
    for b in range(4, 11, 2):
        m.P('bass', b, rb[0], reese, cut=600, lfo=176 / 60 / 4, gt=0.97)
        if b + 1 < 11:
            m.P('bass', b + 1, rb[1], reese, cut=800, lfo=176 / 60 / 2, gt=0.97)
    m.P('bass', 11, "C2 - - - - - - -", reese, cut=700, glide=-12, gt=1.0)
    pb = "C2 C2 . C2 C2 . C2 . C2 C2 . C2 Db2 . Eb2 ."
    for b in list(range(12, 20)) + list(range(24, 28)):
        m.P('bass', b, pb if b % 4 != 3 else "C2 C2 . C2 Gb2 - - . F2 F2 . F2 Eb2 . Db2 .", reese, cut=700 + 50 * (b % 8), lfo=3, gt=0.8)
    m.P('bass', 20, "C2" + " -" * 31, reese, cut=500, lfo=176 / 60, glide=-5, gt=1.0)
    scr = "C4+Gb4+B4"
    for b, s in [(4, 6), (5, 11), (6, 3), (7, 14), (8, 6), (9, 9), (10, 3), (13, 6), (15, 11), (17, 3), (18, 14), (19, 6), (25, 6), (26, 11), (27, 3), (27, 9)]:
        m.P('stab', b, ". " * s + scr, stab, cut=900, env=5000, fdec=0.09, adec=0.2, bend=3 if s % 2 else -3, tr=(b % 3 == 2), gt=1.5)
    m.P('pad', 0, "C4+Db4+Gb4" + " -" * 63, pad, cut=400, cut2=1600, att=2.0, rel=0.3, hp=300, gt=1.0)
    m.P('pad', 12, "G4+Ab4+Db5" + " -" * 127, pad, cut=900, cut2=3500, att=1.0, rel=0.1, hp=400, bend=2.0, spread=0.3, gt=1.0)
    m.P('pad', 20, "C5+Db5+Gb5" + " -" * 63, pad, cut=600, cut2=5000, att=3.0, rel=0.05, hp=500, bend=3.0, spread=0.35, gt=1.0)
    m.P('pad', 24, "G4+Ab4+Db5+Gb5" + " -" * 63, pad, cut=2500, att=0.05, rel=0.2, hp=400, spread=0.3, gt=1.0)
    al = "G5 . . . . . Gb5 . . . . . . . . . | G5 . . . . . Gb5 . . . F5 . . . . ."
    for r in (12, 16, 24):
        m.P('bell', r, al, bell, dec=0.5, idx=3.0, ratio=2.76, rep=2)
    m.add('fx', m.bt(2, 0), riser(m.sl * 32, 300, 9000), 0.9)
    m.add('fx', m.bt(4, 0), impact(), 1.0)
    m.add('fx', m.bt(12, 0), impact(50), 1.0)
    m.add('fx', m.bt(22, 0), riser(m.sl * 32, 300, 11000), 1.0)
    m.add('fx', m.bt(24, 0), impact(44), 1.0)
    hole = mute(m, [(11, 8, 16)])
    return hardmix(m, kt, [(0.42, m.get('bass') * hole, 1), (0.55, rev(m.get('stab'), 1.4, 0.3) * hole, 1),
                           (0.34, rev(m.get('pad'), 2.0, 0.3) * hole, 1), (0.3, rev(delay(m.get('bell'), m.sl * 3, 0.5, 0.4), 1.6, 0.3) * hole, 0),
                           (0.5, rev(m.get('tick'), 1.2, 0.3), 0), (0.3, rev(m.get('fx'), 1.5, 0.3), 0)], rms=-10, clip=1.6)


def m2():
    """Eyes in the Dark: 170 industrial, clanging metal, something passing behind you."""
    m = Mix(170, 24)
    kt = []
    kp = ["x..x..x...x..x..", "x..x..x...x.x.x.", "x..x..x...x..x..", "x.x...x..x..xxxx"]
    for b in range(24):
        q = b % 4
        if b < 2:
            heart(m, 'kick', b, 0, 0.9, 4)
            heart(m, 'kick', b, 8, 0.9, 4)
            continue
        if b == 16:
            for s in (0, 4, 8, 11, 14):
                heart(m, 'tick', b, s, 1.0, 1.5)
            m.D('tick', b, "x.x.x.x.x.xxxxxx", tick, 0.6)
            continue
        if b in (7, 15) :
            kt += m.D('kick', b, "x..x..x.", hkick, 0.85)
            for i in range(16):
                t = m.bt(b, 8 + i * 0.5)
                m.add('kick', t, hkick(dur=0.09, tail=0.05), 0.5 + 0.03 * i)
                kt.append(t)
            m.D('snare', b, "....X...", snare, 0.8, f=180, dec=0.2)
            continue
        kt += m.D('kick', b, kp[q], hkick, 0.85, tail=0.14, dur=0.22)
        m.D('snare', b, "....X.......X...", snare, 0.8, f=180, dec=0.2, nz=1.3)
        m.D('hat', b, "xoxoxoxoxoxoxoxo" if b >= 8 else "x.x.x.x.x.x.x.x.", hat, 0.2, dec=0.02, pan=0.3)
        if b >= 4:
            m.D('fx', b, "..x.......x....." if q % 2 == 0 else "......x.......x.", clang, 0.35, pan=-0.6 if q < 2 else 0.6, f=330 + 90 * q, dec=0.25)
        if b >= 2:
            notes = [("E2", 0, 6), ("E2", 6, 4), ("F2", 10, 3), ("E2", 13, 3)] if q != 3 else [("E2", 0, 6), ("Bb2", 6, 4), ("G2", 10, 3), ("F2", 13, 3)]
            for nt, st, ln in notes:
                m.add('bass', m.bt(b, st), growl([nn(nt) + 12], ln * m.sl * 0.95, rate=170 / 60 * (1 if st == 0 else 2), idx=5, hi=2200, ratio=2 if st else 1, drive=5))
    m.P('pad', 0, "E4+F4+B4" + " -" * 31, pad, cut=500, cut2=2500, att=1.5, rel=0.2, hp=300, spread=0.3, gt=1.0)
    m.P('pad', 8, "E4+F4+B4" + " -" * 127, pad, cut=1200, cut2=2600, att=0.3, rel=0.1, hp=400, spread=0.3, gt=1.0)
    m.P('pad', 17, "F4+Gb4+C5" + " -" * 111, pad, cut=1500, cut2=4500, att=0.1, rel=0.2, hp=400, spread=0.35, bend=1.0, gt=1.0)
    al = "B5 . . . . . . . C6 . . . . . . . | B5 . . . . . . . F5 . . . E5 . . ."
    for r in (8, 12, 17, 20):
        m.P('bell', r, al, bell, dec=0.45, idx=3.2, ratio=2.41)
    for b in range(17, 24):
        m.P('stab', b, ". . . E4+B4+F5 . . . . . . E4+B4+F5 . . . . .", stab, cut=900, env=5000, fdec=0.07, adec=0.14, bend=-2)
    for i, b in enumerate((3, 6, 10, 13, 16, 19, 22)):
        w = riser(m.sl * 24, 500, 5000, 3.0, down=i % 2 == 1)
        w = w * np.stack([np.linspace(1, 0, w.shape[1]), np.linspace(0, 1, w.shape[1])])[::(1 if i % 2 else -1)]
        m.add('whoosh', m.bt(b, 0), w, 1.0)
    m.add('fx', m.bt(2, 0), impact(), 1.0)
    m.add('fx', m.bt(8, 0), impact(48), 1.0)
    m.add('fx', m.bt(17, 0), impact(44), 1.1)
    hole = mute(m, [(16, 0, 16)])
    return hardmix(m, kt, [(0.4, m.get('bass'), 1), (0.34, rev(m.get('pad'), 2.0, 0.3) * hole, 1),
                           (0.3, rev(delay(m.get('bell'), m.sl * 3, 0.5, 0.4), 1.6, 0.3) * hole, 0), (0.45, rev(m.get('stab'), 1.2, 0.3), 1),
                           (0.4, rev(m.get('whoosh'), 1.5, 0.3), 0), (0.5, rev(m.get('tick'), 1.2, 0.3), 0), (0.3, rev(m.get('fx'), 1.8, 0.35), 0)],
                   rms=-10, clip=1.6, dr=1.8)


def m3():
    """Last Bite: 180, the floor rises a semitone every four bars until it cuts."""
    m = Mix(180, 24)
    kt = []
    ost = "A4+Bb4! . A4+Bb4? A4+Bb4 . A4+Bb4? A4+Bb4! . A4+Bb4? A4+Bb4 . A4+Bb4! A4+Bb4? . A4+Bb4 A4+Bb4?"
    al = "E5 . . . . . . . F5 . . . . . . . | E5 . . . . . . . F5 . . . G#5 . . ."
    rb = ["A1 - - - - - A1 - - - A1 - C2 - - -", "A1 - - - - - A1 - Bb1 - - - G#1 - - -"]
    for b in range(4):
        heart(m, 'kick', b, 0, 0.9, 3)
        heart(m, 'kick', b, 8, 0.9, 3)
        m.P('ost', b, ost, stab, cut=250 + 100 * b, env=900 + 500 * b, fdec=0.05, adec=0.1, gt=0.7, voices=3)
    m.P('pad', 0, "A3+E4+Bb4" + " -" * 63, pad, cut=400, cut2=2500, att=2.0, rel=0.1, hp=250, gt=1.0)
    roll(m, 3, 8, 8, 2)
    for sec in range(5):
        b0 = 4 + sec * 4
        tr = sec
        kt += brk(m, b0, "ABAC" if sec % 2 == 0 else "UBUC", hats="xoxoxoxoxoxoxoxo" if sec >= 2 else "x.xox.xox.xox.xo", sf=200 + 8 * sec)
        for i in range(4):
            m.P('ost', b0 + i, ost, stab, tr=tr, cut=500 + 150 * sec, env=2500 + 600 * sec, fdec=0.05, adec=0.1, gt=0.7, voices=3)
            m.P('bass', b0 + i, rb[i % 2], reese, tr=tr + 12, cut=550 + 80 * sec, lfo=180 / 60 / (4 if i % 2 == 0 else 2), gt=0.95)
        m.P('bell', b0, al, bell, tr=tr, dec=0.4, idx=3.0, ratio=2.76, rep=2)
        m.P('pad', b0, "A4+C5+E5" + " -" * 63, pad, tr=tr, cut=900 + 300 * sec, att=0.05, rel=0.1, hp=350, bend=1.0, gt=1.0)
        m.add('fx', m.bt(b0, 0), impact(55 - 2 * sec), 1.0)
        m.add('fx', m.bt(b0 + 3, 0), riser(m.sl * 16, 400, 9000 + 500 * sec), 0.7)
        if sec >= 3:
            m.P('lead', b0, "A5 - - . A5 - - . Bb5 - - . A5 - G5 - | A5 - - . A5 - - . C6 - - . Bb5 - A5 -", lead, tr=tr, cut=1500, env=3000, fdec=0.1, rep=2, gt=0.85)
    roll(m, 23, 0, 16, 2, 0.2, 1.0, 200, 320)
    return hardmix(m, kt, [(0.42, m.get('bass'), 1), (0.5, rev(m.get('ost'), 0.8, 0.15), 1), (0.3, rev(m.get('pad'), 1.8, 0.3), 1),
                           (0.3, rev(delay(m.get('bell'), m.sl * 3, 0.5, 0.4), 1.6, 0.3), 0), (0.36, rev(m.get('lead'), 1.0, 0.2), 1),
                           (0.3, rev(m.get('fx'), 1.5, 0.3), 0)], rms=-10, clip=1.6)


SONGS = [
    ('normal_1_tiptoe', n1), ('normal_2_midnight_snack', n2), ('normal_3_fridge_light', n3),
    ('hard_1_lights_out', h1), ('hard_2_hold_your_breath', h2), ('hard_3_footsteps', h3),
    ('super_1_caught', x1), ('super_2_freezer_burn', x2), ('super_3_heartbeat_overdrive', x3),
    ('nightmare_1_dont_look_back', m1), ('nightmare_2_eyes_in_the_dark', m2), ('nightmare_3_last_bite', m3),
]
