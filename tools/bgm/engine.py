"""Small offline synth: oscillators, filters, drums, effects, a step sequencer."""
import math
import numpy as np
from numba import njit
from scipy import signal
from scipy.ndimage import maximum_filter1d, uniform_filter1d

SR = 44100
TAU = 2 * math.pi
rng = np.random.default_rng(7)


def reseed(s):
    global rng
    rng = np.random.default_rng(s)


NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nn(s):
    p = NAMES[s[0]]
    i = 1
    while s[i] in '#b':
        p += 1 if s[i] == '#' else -1
        i += 1
    return p + 12 * (int(s[i:]) + 1)


def mtof(m):
    return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def parse(pat):
    """'D2 . - F2+A2!' -> [(step, [midi...], length, vel)]"""
    ev = []
    i = 0
    for tok in pat.replace('|', ' ').split():
        if tok == '-':
            if ev:
                ev[-1][2] += 1
        elif tok != '.':
            vel = 1.0
            if tok.endswith('!'):
                vel, tok = 1.3, tok[:-1]
            elif tok.endswith('?'):
                vel, tok = 0.55, tok[:-1]
            ev.append([i, [nn(x) for x in tok.split('+')], 1, vel])
        i += 1
    return ev, i


# ---------- oscillators ----------
def _blep(p, dt):
    out = np.zeros_like(p)
    m = p < dt
    t = p[m] / dt[m]
    out[m] = t + t - t * t - 1
    m = p > 1 - dt
    t = (p[m] - 1) / dt[m]
    out[m] = t * t + t + t + 1
    return out


def saw(f, n, ph=None):
    ph = rng.random() if ph is None else ph
    dt = np.broadcast_to(np.asarray(f, float) / SR, (n,)).copy()
    p = (ph + np.cumsum(dt)) % 1
    return 2 * p - 1 - _blep(p, dt)


def pulse(f, n, pw=0.5, ph=None):
    ph = rng.random() if ph is None else ph
    return saw(f, n, ph) - saw(f, n, ph + pw)


def sine(f, n, ph=0.0):
    f = np.broadcast_to(np.asarray(f, float), (n,))
    return np.sin(TAU * (np.cumsum(f) / SR + ph))


def noise(n):
    return rng.standard_normal(n)


def tarr(n):
    return np.arange(n) / SR


# ---------- filters ----------
@njit(cache=True)
def _svf(x, fc, q, mode):
    n = len(x)
    y = np.empty(n)
    ic1 = 0.0
    ic2 = 0.0
    k = 1.0 / q
    for i in range(n):
        f = fc[i]
        if f > 19000.0:
            f = 19000.0
        if f < 20.0:
            f = 20.0
        g = math.tan(math.pi * f / 44100.0)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x[i] - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        if mode == 0:
            y[i] = v2
        elif mode == 1:
            y[i] = v1
        else:
            y[i] = x[i] - k * v1 - v2
    return y


def svf(x, fc, q=0.8, mode='lp'):
    n = x.shape[-1]
    fc = np.ascontiguousarray(np.broadcast_to(np.asarray(fc, float), (n,)))
    md = {'lp': 0, 'bp': 1, 'hp': 2}[mode]
    if x.ndim == 2:
        return np.stack([_svf(np.ascontiguousarray(c), fc, q, md) for c in x])
    return _svf(np.ascontiguousarray(x), fc, q, md)


def bq(x, kind, f, order=2):
    if kind == 'bp':
        sos = signal.butter(order, [f[0], min(f[1], SR * 0.45)], 'bandpass', fs=SR, output='sos')
    else:
        sos = signal.butter(order, min(f, SR * 0.45), {'lp': 'lowpass', 'hp': 'highpass'}[kind], fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=-1)


def shelf(x, f, db, hi=True):
    A = 10 ** (db / 40)
    w = TAU * f / SR
    c, s = math.cos(w), math.sin(w) / 2 * math.sqrt(2)
    r = 2 * math.sqrt(A) * s
    if hi:
        b = [A * ((A + 1) + (A - 1) * c + r), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - r)]
        a = [(A + 1) - (A - 1) * c + r, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - r]
    else:
        b = [A * ((A + 1) - (A - 1) * c + r), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - r)]
        a = [(A + 1) + (A - 1) * c + r, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - r]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=-1)


def gate(n, dur, att=0.003, rel=0.03):
    t = tarr(n)
    return np.clip(t / att, 0, 1) * np.clip((dur + rel - t) / rel, 0, 1)


def sat(x, d=1.5):
    return np.tanh(x * d) / math.tanh(d)


# ---------- drums ----------
def kick(f0=170, f1=50, pt=0.03, dec=0.22, click=0.4, drive=1.8):
    n = int((dec * 5 + 0.02) * SR)
    t = tarr(n)
    body = sine(f1 + (f0 - f1) * np.exp(-t / pt), n) * np.exp(-t / dec)
    ck = bq(noise(n), 'hp', 2000) * np.exp(-t / 0.002) * click
    return sat(body + ck, drive) * np.clip((t[-1] - t) / 0.01, 0, 1)


def hkick(f1=52, drive=7, tail=0.2, dur=0.3):
    n = int(dur * SR)
    t = tarr(n)
    f = f1 + 330 * np.exp(-t / 0.011) + 70 * np.exp(-t / 0.055)
    env = np.minimum(1, 1.7 * np.exp(-t / tail))
    y = np.tanh(drive * sine(f, n) * env)
    y = bq(y, 'lp', 4200) + 0.25 * bq(y, 'hp', 3000)
    return y * 0.8 * np.clip((t[-1] - t) / 0.02, 0, 1)


def snare(f=190, dec=0.14, nz=1.0, tone=0.7, lo=1200):
    n = int((dec * 5 + 0.02) * SR)
    t = tarr(n)
    pe = 1 + 0.8 * np.exp(-t / 0.008)
    body = sine(f * pe, n) * np.exp(-t / (dec * 0.45)) + 0.5 * sine(f * 1.58 * pe, n) * np.exp(-t / (dec * 0.3))
    w = noise(n)
    w = (bq(w, 'hp', lo) * 0.5 + bq(w, 'bp', (2200, 7500)) * 0.8) * np.exp(-t / dec)
    return sat(tone * body + nz * 0.55 * w + 0.5 * np.exp(-t / 0.0015), 1.6) * 0.6


def hat(dec=0.03, tone=9000):
    n = int((dec * 6 + 0.01) * SR)
    t = tarr(n)
    x = noise(n) * 0.7
    for fr in (2051, 3044, 3696, 5227, 5400, 8000):
        x += 0.22 * np.sign(np.sin(TAU * fr * t + rng.random() * 6))
    x = bq(bq(x, 'hp', tone * 0.75), 'lp', min(17000, tone * 1.9), 1)
    return x * np.exp(-t / dec) * np.clip(t / 0.0005, 0, 1) * 0.3


def ride(dec=0.18):
    n = int(dec * 5 * SR)
    t = tarr(n)
    x = noise(n) * 0.3
    for fr in (3170, 4410, 5230, 6730, 8150, 9900):
        x += 0.3 * np.sin(TAU * fr * t + 2.5 * np.sin(TAU * fr * 1.414 * t))
    x = bq(x, 'hp', 4500)
    return x * (0.6 * np.exp(-t / dec) + 0.4 * np.exp(-t / 0.02)) * 0.2


def clap(dec=0.12, f=1300, bursts=(0, 0.011, 0.023), tail=0.03):
    n = int((dec * 5 + 0.05) * SR)
    t = tarr(n)
    w = bq(noise(n), 'bp', (f * 0.7, f * 2.3))
    env = np.zeros(n)
    for d in bursts:
        env += (t >= d) * np.exp(-np.maximum(t - d, 0) / 0.006)
    env += (t >= tail) * np.exp(-np.maximum(t - tail, 0) / dec) * 0.8
    return w * env * 0.5


def snap():
    return clap(dec=0.045, f=2300, bursts=(0, 0.007), tail=0.012) * 1.2


def rim(f=1750):
    n = int(0.12 * SR)
    t = tarr(n)
    return (np.sin(TAU * f * t) * np.exp(-t / 0.012) + 0.5 * np.sin(TAU * f * 0.247 * t) * np.exp(-t / 0.02)
            + 0.3 * noise(n) * np.exp(-t / 0.001)) * 0.5


def shaker(dec=0.035):
    n = int(0.2 * SR)
    t = tarr(n)
    return bq(noise(n), 'bp', (5000, 11000)) * np.clip(t / 0.012, 0, 1) * np.exp(-np.maximum(t - 0.012, 0) / dec) * 0.25


def tick(f=3200):
    n = int(0.05 * SR)
    t = tarr(n)
    return (np.sin(TAU * f * t) * np.exp(-t / 0.004) + 0.4 * np.sin(TAU * f * 1.51 * t) * np.exp(-t / 0.002)) * 0.4


def thud(f=70, dec=0.1):
    return kick(f0=f * 1.6, f1=f * 0.7, pt=0.02, dec=dec, click=0.05, drive=1.2)


def clang(f=520, dec=0.5):
    n = int(dec * 5 * SR)
    t = tarr(n)
    y = np.sin(TAU * f * t + 3.5 * np.exp(-t / (dec * 0.6)) * np.sin(TAU * f * 2.76 * t))
    y += 0.6 * np.sin(TAU * f * 1.48 * t + 2 * np.sin(TAU * f * 3.9 * t))
    return y * np.exp(-t / dec) * 0.4


# ---------- tonal voices ----------
def sub(m, dur, drive=1.3, **_):
    n = int((dur + 0.04) * SR)
    f = mtof(m[0])
    return sat(sine(f, n) + 0.15 * sine(f * 2, n), drive) * gate(n, dur, 0.006, 0.03)


def rubber(m, dur, cut=250, env=1800, fdec=0.09, res=2.5, sb=0.4, drive=1.5, **_):
    n = int((dur + 0.04) * SR)
    f = mtof(m[0])
    t = tarr(n)
    x = saw(f, n) + 0.5 * pulse(f, n, 0.3)
    y = sat(svf(x, cut + env * np.exp(-t / fdec), res) * 0.6, drive)
    return (y + sb * sine(f, n)) * np.exp(-t / 0.9) * gate(n, dur, 0.003, 0.025)


def reese(m, dur, cut=700, lfo=0.35, det=0.2, drive=2.2, sb=0.5, glide=None, depth=0.6, res=1.6, **_):
    n = int((dur + 0.04) * SR)
    t = tarr(n)
    f = mtof(m[0])
    if glide is not None:
        f = mtof(m[0] + glide * np.clip(t / max(dur, 1e-3), 0, 1) ** 2)
    fc = cut * (1 + depth * np.sin(TAU * lfo * t + rng.random() * 6))
    L = saw(f * 2 ** (-det / 12), n) + saw(f * 2 ** (det * 0.6 / 12), n)
    R = saw(f * 2 ** (det / 12), n) + saw(f * 2 ** (-det * 0.5 / 12), n)
    st = np.stack([svf(L, fc, res), svf(R, fc, res)])
    mid = st.mean(0)
    st = sat(bq(st, 'hp', 140) * 0.8 + 0.35 * bq(mid, 'hp', 140), drive)
    low = bq(mid, 'lp', 140) * 0.5 + sb * sine(f, n)
    return (st + sat(low, 1.4)) * gate(n, dur, 0.006, 0.03)


def growl(m, dur, rate=8.0, idx=4.0, ratio=1.0, lo=250, hi=2600, drive=4.0, sb=0.7, ph=0.0, **_):
    n = int((dur + 0.03) * SR)
    t = tarr(n)
    f = mtof(m[0])
    l = 0.5 - 0.5 * np.cos(TAU * (rate * t + ph))
    car = np.sin(TAU * f * t + idx * (0.25 + l) * np.sin(TAU * f * ratio * t))
    y = svf(car + 0.5 * saw(f, n), lo * (hi / lo) ** l, 3.0, 'bp') * 1.6 + 0.35 * car
    y = bq(np.tanh(drive * y), 'lp', 7000)
    y = bq(y, 'hp', 120) * 0.6 + sb * sine(f, n)
    return y * gate(n, dur, 0.004, 0.02)


def pluck(m, dur, cut=500, env=4500, fdec=0.07, res=1.8, adec=0.3, det=6, **_):
    out = 0
    for mm in m:
        n = int((dur + 0.08) * SR)
        f = mtof(mm)
        t = tarr(n)
        x = saw(f, n) + 0.6 * pulse(f * 2 ** (det / 1200), n, 0.35)
        out = out + svf(x, cut + env * np.exp(-t / fdec), res) * np.exp(-t / adec) * gate(n, dur, 0.0015, 0.03)
    return out * 0.5


def epiano(m, dur, bright=1.0, **_):
    out = 0
    for mm in m:
        n = int((dur + 0.35) * SR)
        f = mtof(mm)
        t = tarr(n)
        I = 1.3 * bright * np.exp(-t / 0.35) + 0.2
        y = np.sin(TAU * f * t + I * np.sin(TAU * f * t)) * np.exp(-t / 1.4)
        y += 0.1 * bright * np.sin(TAU * f * 7 * t) * np.exp(-t / 0.04)
        out = out + y * gate(n, dur, 0.003, 0.3)
    return out * 0.4


def keys(m, dur, bright=1.0, **_):
    """Electric piano, two slightly detuned voices left and right."""
    n = int((dur + 0.3) * SR)
    t = tarr(n)
    out = np.zeros((2, n))
    for mm in m:
        f0 = mtof(mm)
        for ch, dt in ((0, -4), (1, 4)):
            f = f0 * 2 ** (dt / 1200)
            I = 2.0 * bright * np.exp(-t / 0.16) + 0.35 * bright
            y = np.sin(TAU * f * t + I * np.sin(TAU * f * t)) * np.exp(-t / 0.9)
            y += 0.12 * bright * np.sin(TAU * f * 4 * t) * np.exp(-t / 0.03)
            out[ch] += y
    return out * gate(n, dur, 0.002, 0.25) * 0.3


def bell(m, dur, ratio=3.5, idx=2.0, dec=0.8, **_):
    out = 0
    for mm in m:
        n = int(min(dur + dec * 3, 5) * SR)
        f = mtof(mm)
        t = tarr(n)
        y = np.sin(TAU * f * t + idx * np.exp(-t / 0.22) * np.sin(TAU * f * ratio * t)) * np.exp(-t / dec)
        y += 0.25 * np.sin(TAU * f * 2 * t) * np.exp(-t / (dec * 0.5))
        out = out + y * np.clip(t / 0.002, 0, 1) * np.clip((t[-1] - t) / 0.05, 0, 1)
    return out * 0.4


def supersaw(fs, n, voices=5, spread=0.14):
    L = np.zeros(n)
    R = np.zeros(n)
    for f in fs:
        for v in range(voices):
            p = v / (voices - 1) * 2 - 1 if voices > 1 else 0
            s = saw(f * 2 ** (spread * p / 12), n)
            a = (p * 0.8 + 1) * math.pi / 4
            L += s * math.cos(a)
            R += s * math.sin(a)
    return np.stack([L, R]) / math.sqrt(len(fs) * voices)


def pad(m, dur, cut=1800, cut2=None, att=0.3, rel=0.5, res=0.8, voices=5, spread=0.16, hp=150, bend=0.0, **_):
    n = int((dur + rel) * SR)
    t = tarr(n)
    fs = [mtof(mm + bend * np.clip(t / dur, 0, 1)) for mm in m] if bend else [mtof(mm) for mm in m]
    x = supersaw(fs, n, voices, spread)
    fc = cut if cut2 is None else cut * (cut2 / cut) ** np.clip(t / dur, 0, 1)
    y = bq(svf(x, fc, res), 'hp', hp)
    return y * np.clip(t / att, 0, 1) * np.clip((dur + rel - t) / rel, 0, 1) * 0.5


def stab(m, dur, cut=700, env=5000, fdec=0.1, res=1.4, adec=0.25, voices=5, spread=0.18, bend=0.0, **_):
    n = int((dur + 0.1) * SR)
    t = tarr(n)
    pb = 2 ** (bend * np.exp(-t / 0.03) / 12) if bend else 1
    x = supersaw([mtof(mm) * pb for mm in m], n, voices, spread)
    y = svf(x, cut + env * np.exp(-t / fdec), res)
    return bq(y, 'hp', 160) * np.exp(-t / adec) * gate(n, dur, 0.002, 0.05) * 0.6


def lead(m, dur, cut=1500, env=2500, fdec=0.25, res=1.3, glide=0.0, vib=0.0, **_):
    n = int((dur + 0.1) * SR)
    t = tarr(n)
    f = mtof(m[0] + glide * np.exp(-t / 0.035))
    if vib:
        f = f * (1 + vib * np.clip((t - 0.15) / 0.3, 0, 1) * np.sin(TAU * 5.5 * t))
    x = saw(f * 1.004, n) + saw(f * 0.996, n) + 0.4 * pulse(f / 2, n, 0.5)
    y = svf(x, cut + env * np.exp(-t / fdec), res)
    return y * gate(n, dur, 0.006, 0.08) * 0.35


# ---------- one-shots ----------
def riser(dur, f0=300, f1=9000, q=2.0, down=False):
    n = int(dur * SR)
    r = np.linspace(0, 1, n)
    if down:
        r = 1 - r
    x = np.stack([noise(n), noise(n)])
    return svf(x, f0 * (f1 / f0) ** r, q, 'bp') * r ** 2 * 0.5


def impact(f=55, dec=0.7):
    n = int(dec * 4 * SR)
    t = tarr(n)
    y = sine(f * 0.6 + f * 1.4 * np.exp(-t / 0.05), n) * np.exp(-t / dec)
    y = sat(y, 2.5) + bq(noise(n), 'lp', 1400) * np.exp(-t / 0.12) * 0.6
    return y * 0.9


# ---------- effects ----------
def pan(x, p):
    return x * np.array([[min(1, 1 - p)], [min(1, 1 + p)]])


def wide(x, ms=11, amt=0.35):
    d = int(ms / 1000 * SR)
    s = np.zeros(x.shape[1])
    s[d:] = bq(x.mean(0), 'hp', 300)[:-d]
    return x + amt * np.stack([s, -s])


_IR = {}


def rev(x, t60=1.6, wet=0.25, pre=0.015, lo=250, hi=7000, seed=1):
    key = (t60, lo, hi, seed)
    if key not in _IR:
        r = np.random.default_rng(seed)
        n = int(t60 * 1.3 * SR)
        ir = r.standard_normal((2, n)) * np.exp(-6.9 * tarr(n) / t60)
        ir = bq(bq(ir, 'hp', lo), 'lp', hi)
        _IR[key] = ir / np.sqrt((ir ** 2).sum(1))[:, None]
    ir = _IR[key]
    N = x.shape[1]
    d = int(pre * SR)
    w = np.stack([signal.fftconvolve(x[c], ir[c])[:N] for c in range(2)])
    out = x.copy()
    out[:, d:] += wet * w[:, :N - d]
    return out


def delay(x, time, fb=0.4, wet=0.3, pp=True, lp=3500, reps=6):
    d = int(time * SR)
    N = x.shape[1]
    out = x.copy()
    cur = x
    for k in range(1, reps + 1):
        if k * d >= N:
            break
        cur = bq(cur, 'lp', lp, 1)
        if pp:
            cur = cur[::-1]
        out[:, k * d:] += wet * fb ** (k - 1) * cur[:, :N - k * d]
    return out


def duck(n, times, depth=0.6, rel=0.15, att=0.004):
    env = np.ones(n)
    a = int(att * SR)
    L = int(rel * 5 * SR)
    shape = np.concatenate([np.linspace(1, 1 - depth, a), 1 - depth * np.exp(-tarr(L) / rel)])
    for tk in times:
        i = max(0, int(tk * SR) - a)
        seg = env[i:i + len(shape)]
        np.minimum(seg, shape[:len(seg)], out=seg)
    return env


@njit(cache=True)
def _cgain(e_in, thr, ratio, att, rel):
    n = len(e_in)
    g = np.empty(n)
    e = 0.0
    for i in range(n):
        x = e_in[i]
        c = att if x > e else rel
        e = c * e + (1 - c) * x
        g[i] = (e / thr) ** (1.0 / ratio - 1.0) if e > thr else 1.0
    return g


def comp(x, thr_db=-18, ratio=4, att=0.005, rel=0.12, makeup=1.0):
    g = _cgain(np.abs(x).max(0), 10 ** (thr_db / 20), ratio, math.exp(-1 / (att * SR)), math.exp(-1 / (rel * SR)))
    return x * g * makeup


def limiter(x, ceil=0.9, look=0.004):
    L = int(look * SR)
    env = maximum_filter1d(np.abs(x).max(0), size=2 * L + 1)
    g = uniform_filter1d(np.minimum(1, ceil / np.maximum(env, 1e-9)), size=L)
    return np.clip(x * g, -ceil, ceil)


def master(x, rms_db=-13.0, clip=1.15, body=None):
    x = shelf(shelf(bq(x, 'hp', 30), 75, -4, hi=False), 4500, 2.5)
    x = comp(x, -16, 2.0, 0.02, 0.2)
    ref = x if body is None else x[:, :body]
    x = x * 10 ** (rms_db / 20) / math.sqrt(float((ref ** 2).mean()))
    x = np.tanh(x * clip)
    return limiter(x * 0.92 / np.abs(x).max())


# ---------- sequencer ----------
class Mix:
    def __init__(self, bpm, bars, swing=0.0, tail=1.6):
        self.sl = 60 / bpm / 4
        self.swing = swing
        self.bars = bars
        self.body = int(bars * 16 * self.sl * SR)
        self.n = self.body + int(tail * SR)
        self.b = {}

    def tt(self, step):
        return step * self.sl + (self.swing * self.sl if int(step) % 2 == 1 else 0)

    def add(self, bus, t, x, g=1.0, pan=0.0):
        buf = self.b.setdefault(bus, np.zeros((2, self.n)))
        i = int(t * SR)
        if i >= self.n or i < 0:
            return
        if x.ndim == 1:
            a = (pan + 1) * math.pi / 4
            x = np.stack([x * math.cos(a), x * math.sin(a)]) * 1.414
        elif pan:
            x = x * np.array([[min(1, 1 - pan)], [min(1, 1 + pan)]])
        L = min(x.shape[1], self.n - i)
        buf[:, i:i + L] += g * x[:, :L]

    def P(self, bus, bar, pat, inst, g=1.0, pan=0.0, gt=0.9, tr=0, rep=1, **kw):
        ev, L = parse(pat)
        for r in range(rep):
            for st, ms, ln, vel in ev:
                s = bar * 16 + r * L + st
                self.add(bus, self.tt(s), inst([x + tr for x in ms], ln * self.sl * gt, **kw), g * vel, pan)

    def D(self, bus, bar, pat, fn, g=1.0, pan=0.0, rep=1, hum=0.08, **kw):
        pat = pat.replace('|', '').replace(' ', '')
        times = []
        for r in range(rep):
            for i, c in enumerate(pat):
                if c == '.':
                    continue
                v = {'X': 1.25, 'x': 1.0, 'o': 0.42, '-': 0.7}[c] * (1 + hum * (rng.random() * 2 - 1))
                t = self.tt(bar * 16 + r * len(pat) + i)
                self.add(bus, t, fn(**kw), g * v, pan)
                times.append(t)
        return times

    def N(self, bus, bar, pat, g=1.0, gt=0.9, tr=0, vel=96):
        """Queue notes for a hosted instrument (rendered later with Mix.part)."""
        ev, _ = parse(pat)
        q = self.b.setdefault('~' + bus, [])
        for st, ms, ln, v in ev:
            for mm in ms:
                q.append((self.tt(bar * 16 + st), mm + tr, ln * self.sl * gt, vel * v * g))

    def part(self, bus, fn, db):
        from inst import norm
        q = self.b.get('~' + bus)
        return norm(fn(q, self.n), db) if q else np.zeros((2, self.n))

    def get(self, bus):
        return self.b.get(bus, np.zeros((2, self.n)))

    def bt(self, bar, step=0):
        return self.tt(bar * 16 + step)
