"""Render the BGM sketches to mp3.  python3 make.py [name-filter ...]  (needs numpy, scipy, numba, ffmpeg and the packages listed in inst.py)"""
import os, subprocess, sys, time
import numpy as np
from scipy.io import wavfile
import engine
from songs import SONGS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'samples')
os.makedirs(OUT, exist_ok=True)
for i, (name, fn) in enumerate(SONGS):
    if sys.argv[1:] and not any(a in name for a in sys.argv[1:]):
        continue
    engine.reseed(100 + i)
    t0 = time.time()
    y = fn()
    f = int(0.4 * engine.SR)
    y[:, -f:] *= np.linspace(1, 0, f)
    wav = os.path.join(OUT, name + '.wav')
    wavfile.write(wav, engine.SR, (y.T * 32767).astype(np.int16))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libmp3lame', '-q:a', '2', os.path.join(OUT, name + '.mp3')], check=True)
    if not os.environ.get('KEEP_WAV'):
        os.remove(wav)
    print(f"{name}: {y.shape[1] / engine.SR:.1f}s peak {np.abs(y).max():.2f} rms {20 * np.log10(np.sqrt((y ** 2).mean())):.1f}dB ({time.time() - t0:.1f}s)")
