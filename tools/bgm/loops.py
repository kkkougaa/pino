"""Render the four tracks of BGM set 3 as seamless loop WAVs (then: pack_set.py 3 normal.wav hard.wav rage.wav nightmare.wav).

The reverb/delay tail after the last bar is folded back onto the start, so the loop wraps without a gap.
Levels follow set 1, so the shared set gain (0.42) fits.
"""
import os, sys
import numpy as np
from scipy.io import wavfile
import engine, songs

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loops')
os.makedirs(OUT, exist_ok=True)
#        key          composition       mood         first bar  level (dB RMS)
PICK = [('normal',    songs.TIPTOE,     'normal',    0,         -16.7),
        ('hard',      songs.TIPTOE,     'hard',      0,         -18.6),
        ('rage',      songs.CAUGHT,     'super',     4,         -15.4),
        ('nightmare', songs.OVERDRIVE,  'nightmare', 4,         -15.0)]
for i, (key, comp, mood, first, db) in enumerate(PICK):
    engine.reseed(300 + i)
    y = songs.build(comp, mood)
    bar = 4 * 60 / (comp['bpm'] + (6 if mood == 'nightmare' else 0)) * engine.SR
    a, b = int(round(first * bar)), int(round(24 * bar))
    loop = y[:, a:b].copy()
    tail = y[:, b:]
    loop[:, :tail.shape[1]] += tail
    loop *= 10 ** (db / 20) / np.sqrt((loop ** 2).mean())
    wavfile.write(os.path.join(OUT, key + '.wav'), engine.SR, (np.clip(loop, -1, 1).T * 32767).astype(np.int16))
    print(f"{key}: {loop.shape[1] / engine.SR:.3f}s peak {np.abs(loop).max():.2f}")
