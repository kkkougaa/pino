#!/usr/bin/env python3
"""Packs four seamless loop WAVs into a BGM_SETS entry for pino.html.
   usage: pack_set.py <n> normal.wav hard.wav rage.wav nightmare.wav > entry.txt
   Each file gets LEAD seconds of wrap-around audio before and after the loop, so the game can loop any
   `len`-second window without depending on the MP3 encoder's padding. Paste the printed line into BGM_SETS."""
import sys, wave, subprocess, base64, tempfile, os
import numpy as np
LEAD=0.25; n=sys.argv[1]; keys=['normal','hard','rage','nightmare']; ln={}; src={}
for key,path in zip(keys,sys.argv[2:6]):
    w=wave.open(path); sr=w.getframerate(); ch=w.getnchannels(); a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,ch); w.close()
    k=int(LEAD*sr); b=np.concatenate([a[-k:],a,a[:k]])
    with tempfile.TemporaryDirectory() as d:
        t=os.path.join(d,'p.wav'); o=wave.open(t,'wb'); o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr); o.writeframes(b.tobytes()); o.close()
        m=os.path.join(d,'p.mp3'); subprocess.run(['ffmpeg','-y','-v','error','-i',t,'-b:a','96k','-ar','44100',m],check=True)
        src[key]=base64.b64encode(open(m,'rb').read()).decode()
    ln[key]=round(len(a)/sr,5)
print("%s:{lead:%s,gain:0.42,len:{%s},src:{%s}}"%(n,LEAD,",".join("%s:%s"%(k,ln[k]) for k in keys),",".join("%s:'data:audio/mpeg;base64,%s'"%(k,src[k]) for k in keys)))
