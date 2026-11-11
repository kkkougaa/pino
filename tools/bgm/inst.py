"""Real instruments: drum-kit samples (Hydrogen kits), a sampled soundfont (FluidSynth),
and ZynAddSubFX presets hosted offline through DawDreamer.

apt: fluidsynth musescore-general-soundfont hydrogen-drumkits zynaddsubfx-vst zynaddsubfx-data
pip: pyfluidsynth dawdreamer python-osc soundfile
"""
import os, re, sys, tempfile, time
import numpy as np
import soundfile as sf
from engine import SR, rng, bq

KITS = '/usr/share/hydrogen/data/drumkits/'
SF3 = '/usr/share/sounds/sf3/MuseScore_General_Full.sf3'
ZBANK = '/usr/share/zynaddsubfx/banks/'
_hits = {}


def hit(name, pitch=1.0, dec=None, jit=0.0):
    """One drum sample as mono, optionally repitched and shortened."""
    if name not in _hits:
        fn = KITS + name + ('.flac' if os.path.exists(KITS + name + '.flac') else '.wav')
        x, sr = sf.read(fn)
        x = x.mean(1) if x.ndim == 2 else x
        if sr != SR:
            x = np.interp(np.arange(0, len(x) - 1, sr / SR), np.arange(len(x)), x)
        _hits[name] = x
    x = _hits[name]
    import engine
    p = pitch * (1 + jit * (engine.rng.random() * 2 - 1))
    if p != 1.0:
        x = np.interp(np.arange(0, len(x) - 1, p), np.arange(len(x)), x)
    if dec:
        x = x * np.exp(-np.arange(len(x)) / SR / dec)
    return x


class _Zyn:
    def __init__(self):
        self.e = None

    def boot(self):
        tmp = tempfile.TemporaryFile(mode='w+b')
        so, se = os.dup(1), os.dup(2)
        os.dup2(tmp.fileno(), 1)
        os.dup2(tmp.fileno(), 2)
        try:
            import dawdreamer as daw
            self.e = daw.RenderEngine(SR, 512)
            self.p = self.e.make_plugin_processor("zyn", "/usr/lib/vst/ZynAddSubFX.so")
        finally:
            sys.stdout.flush()
            os.dup2(so, 1)
            os.dup2(se, 2)
        tmp.seek(0)
        ports = [int(x) for x in re.findall(r'running on (\d+)', tmp.read().decode())]
        from pythonosc.udp_client import SimpleUDPClient
        self.c = SimpleUDPClient("127.0.0.1", ports[-1])
        self.cur = None

    def render(self, preset, notes, n):
        if self.e is None:
            self.boot()
        if preset != self.cur:
            self.c.send_message("/load_xiz", [0, ZBANK + preset + ".xiz"])
            time.sleep(0.7)
            self.cur = preset
        self.p.clear_midi()
        self.e.load_graph([(self.p, [])])
        self.e.render(0.8)
        for t, mid, dur, vel in notes:
            self.p.add_midi_note(int(mid), int(max(1, min(127, vel))), float(t), float(dur))
        self.e.load_graph([(self.p, [])])
        self.e.render(n / SR + 0.05)
        return np.asarray(self.e.get_audio(), float)[:, :n]


zyn = _Zyn()
_fs = {}


def soundfont(bank, preset, notes, n):
    import fluidsynth
    if 'fs' not in _fs:
        fs = fluidsynth.Synth(samplerate=float(SR), gain=0.6)
        fs.setting('synth.reverb.active', 0)
        fs.setting('synth.chorus.active', 0)
        _fs['fs'], _fs['id'] = fs, fs.sfload(SF3)
    fs = _fs['fs']
    fs.system_reset()
    fs.program_select(0, _fs['id'], bank, preset)
    ev = []
    for t, mid, dur, vel in notes:
        ev.append((int(t * SR), 1, int(mid), int(max(1, min(127, vel)))))
        ev.append((int((t + dur) * SR), 0, int(mid), 0))
    ev.sort(key=lambda x: (x[0], x[1]))
    out, pos = [], 0
    for s, on, mid, vel in ev:
        s = min(s, n)
        if s > pos:
            out.append(fs.get_samples(s - pos))
            pos = s
        (fs.noteon(0, mid, vel) if on else fs.noteoff(0, mid))
    if n > pos:
        out.append(fs.get_samples(n - pos))
    return np.concatenate(out).reshape(-1, 2).T.astype(float) / 32768


def norm(x, db):
    """Scale so the louder half of the active 50 ms blocks sits at `db` RMS."""
    b = int(0.05 * SR)
    k = x.shape[1] // b
    r = np.sqrt((x[:, :k * b].reshape(2, k, b) ** 2).mean((0, 2)))
    r = np.sort(r[r > 1e-5])
    if len(r) == 0:
        return x
    return x * 10 ** (db / 20) / r[len(r) // 2:].mean()
