#!/usr/bin/env python3
"""BGM v4: layered stems.
   - instruments: MuseScore_General soundfont (sampled) through fluidsynth
   - drums: one-shot samples (hydrogen kits VariBreaks / HardElectro1 / ElectricEmpireKit, GPL; ForzeeStereo crash) placed by a small sampler
   - synth layer (reese/sub bass, supersaw, risers): compose.js via stem.js
   usage: v4.py <outDir> [main,hard,rage,nightmare]"""
import os, sys, json, subprocess, wave, random
import numpy as np
from gm_render import Song, main as main_score
HERE=os.path.dirname(os.path.abspath(__file__)); SR=44100; TAIL=3.0
SF='/usr/share/sounds/sf3/MuseScore_General_Full.sf3'; KIT='/usr/share/hydrogen/data/drumkits/'
rng=random.Random(9)

def decode(path):
    raw=subprocess.run(['ffmpeg','-v','error','-i',path,'-f','f32le','-ac','2','-ar',str(SR),'-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw,dtype='<f4').reshape(-1,2).astype(np.float64)
_cache={}
def smp(rel):
    if rel not in _cache:
        a=decode(KIT+rel); pk=np.abs(a).max() or 1; _cache[rel]=a/pk
    return _cache[rel]

class Stem:
    def __init__(s,seconds): s.N=int(round(seconds*SR)); s.buf=np.zeros((s.N+int(TAIL*SR),2))
    def hit(s,t,rel,gain=1.0,rate=1.0,pan=0.0,cut=None):
        a=smp(rel)
        if rate!=1.0:
            n=int(len(a)/rate); idx=np.arange(n)*rate; i0=np.floor(idx).astype(int); fr=(idx-i0)[:,None]; i1=np.minimum(i0+1,len(a)-1); a=a[i0]*(1-fr)+a[i1]*fr
        if cut: n=int(cut*SR); a=a[:n].copy(); f=min(len(a),int(0.01*SR)); a[-f:]*=np.linspace(1,0,f)[:,None]
        i=int(round(max(0,t)*SR)); n=min(len(a),len(s.buf)-i)
        if n<=0: return
        l=np.cos((pan+1)*np.pi/4)*1.414; r=np.sin((pan+1)*np.pi/4)*1.414
        s.buf[i:i+n,0]+=a[:n,0]*gain*l; s.buf[i:i+n,1]+=a[:n,1]*gain*r
    def fold(s):
        o=s.buf[:s.N].copy(); T=len(s.buf)-s.N; o[:T]+=s.buf[s.N:]; return o

def fluid(song,beats,out,name,room=0.6,level=0.5,gain=0.5):
    mid=os.path.join(out,name+'.mid'); raw=os.path.join(out,name+'_sf.wav'); song.write(mid,beats+TAIL*song.bpm/60)
    subprocess.run(['fluidsynth','-ni','-q','-g',str(gain),'-R','1','-C','0','-o','synth.reverb.room-size=%s'%room,'-o','synth.reverb.level=%s'%level,'-o','synth.reverb.damp=0.25','-o','synth.reverb.width=1',
                    '-r',str(SR),'-O','s16','-F',raw,SF,mid],check=True,stderr=subprocess.DEVNULL)
    w=wave.open(raw); a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float64)/32768; w.close(); os.remove(raw)
    N=int(round(beats*60/song.bpm*SR)); T=int(TAIL*SR); b=np.zeros((N+T,2)); n=min(len(a),N+T); b[:n]=a[:n]; o=b[:N].copy(); o[:T]+=b[N:]; return o

def synth(ev,seconds,out,name,opt):
    j=os.path.join(out,name+'_ev.json'); f=os.path.join(out,name+'_syn.f32'); json.dump({'seconds':seconds,'opt':opt,'ev':ev},open(j,'w'))
    subprocess.run(['node',os.path.join(HERE,'stem.js'),j,f],check=True,env=dict(os.environ,NODE_PATH=subprocess.run(['npm','root','-g'],capture_output=True,text=True).stdout.strip()))
    a=np.fromfile(f,dtype='<f4').reshape(-1,2).astype(np.float64); os.remove(f); os.remove(j)
    N=int(round(seconds*SR)); o=a[:N].copy(); T=len(a)-N; o[:T]+=a[N:]; return o

def pump(x,times,depth,rel):
    g=np.ones(len(x)); 
    for t in times:
        i=int(t*SR); n=min(len(x)-i,int(rel*4*SR))
        if n>0: g[i:i+n]=np.minimum(g[i:i+n],1-depth*np.exp(-np.arange(n)/(rel*SR)))
    return x*g[:,None]

def room(x,sec=0.9,seed=1):
    r=np.random.RandomState(seed); n=int(sec*SR); ir=r.randn(n,2)*np.exp(-np.arange(n)/(sec*SR/5))[:,None]; ir[:int(0.004*SR)]*=0.2
    L=len(x)+n; F=1<<(L-1).bit_length(); y=np.stack([np.fft.irfft(np.fft.rfft(x[:,c],F)*np.fft.rfft(ir[:,c],F),F)[:L] for c in range(2)],1)
    o=y[:len(x)].copy(); o[:n]+=y[len(x):len(x)+n]; return o/np.sqrt(n/20)

def drive(x,k): return np.tanh(x*k)/np.tanh(k)

def master(mix,out,name,target=-14.0,lowpass=None):
    pk=np.abs(mix).max(); mix=mix/pk*0.7; tmp=os.path.join(out,name+'_pre.wav')
    w=wave.open(tmp,'wb'); w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR); d=(np.clip(mix,-1,1)*8388607).astype('<i4'); w.writeframes(b''.join(int(v).to_bytes(3,'little',signed=True) for v in d.reshape(-1))); w.close()
    chain='highpass=f=28,equalizer=f=280:t=q:w=1.2:g=-1.5,treble=g=2.2:f=9500,acompressor=threshold=-17dB:ratio=2.2:attack=18:release=160:makeup=1,extrastereo=m=1.12'
    if lowpass: chain='lowpass=f=%d,'%lowpass+chain
    t2=os.path.join(out,name+'_t2.wav'); subprocess.run(['ffmpeg','-y','-v','error','-i',tmp,'-af',chain,'-c:a','pcm_s24le',t2],check=True)
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',t2,'-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
    I=float([l for l in r.splitlines() if ' I:' in l][-1].split()[1]); g=target-I
    subprocess.run(['ffmpeg','-y','-v','error','-i',t2,'-af','volume=%.2fdB,alimiter=limit=0.89:attack=2:release=50:level=disabled'%g,'-c:a','pcm_s16le',os.path.join(out,name+'.wav')],check=True)
    subprocess.run(['ffmpeg','-y','-v','error','-i',os.path.join(out,name+'.wav'),'-b:a','192k',os.path.join(out,'pino_bgm_v4_%s.mp3'%name)],check=True)
    os.remove(tmp); os.remove(t2); print(name,'%.2fs'%(len(mix)/SR),'gain %.1f dB'%g)

VB='VariBreaks/VP '; HE='HardElectro1/'; EE='ElectricEmpireKit/'; FZ='ForzeeStereo/'

# ---------------------------------------------------------------- main / hard
def do_main(out,hard):
    s,beats=main_score(hard); mix=fluid(s,beats,out,'hard' if hard else 'main',room=0.55,level=0.45,gain=0.6)
    master(mix,out,'hard' if hard else 'main',target=-17.0 if hard else -14.5,lowpass=2300 if hard else None)

# ---------------------------------------------------------------- rage
R_ROOT=[38,38,39,33, 38,38,34,33, 38,38,39,33, 34,36,38,33, 43,38,39,33, 43,38,34,33, 38,39,34,33]
R_CHD=[[62,65,69,74],[62,65,68,74],[63,67,70,74],[61,64,69,73],[62,65,69,74],[62,65,71,74],[58,62,65,70],[61,64,69,73]]
RIFF_A=[[74,.75],[77,.75],[81,.5],[80,.5],[81,.5],[77,.5],[74,.5],[74,.75],[77,.75],[81,.5],[82,.5],[81,.5],[84,.5],[86,.5],
        [87,.75],[86,.75],[84,.5],[81,.5],[82,.5],[80,.5],[77,.5],[76,.5],[77,.5],[80,.5],[81,.75],[73,.75],[74,1.0]]
RIFF_B=[[86,1.5],[84,.5],[82,1],[81,1],[82,1.5],[81,.5],[77,1],[74,1],[86,1.5],[87,.5],[89,1],[88,1],[86,.75],[84,.75],[82,.5],[80,1],[81,1]]
def do_rage(out):
    bpm=174; B=60/bpm; BARS=28; beats=BARS*4; sec=beats*B
    S=Song(bpm); S.setup(0,1,58,35,0,112); S.setup(1,2,72,40,0,96); S.setup(2,12,84,45,0,92)
    D=Stem(sec); ev=[]; kicks=[]
    def K(t,g=1.0,hard=False):
        kicks.append(t); ev.append(['duckAt',t])
        if hard: D.hit(t,HE+'HardHse_K_02.flac',0.95*g); D.hit(t,VB+'Kick 2.flac',0.4*g)
        else: D.hit(t,VB+'Kick %d.flac'%(1 if rng.random()<0.7 else 3),0.95*g); D.hit(t,EE+'EE_Kick_Power.flac',0.35*g,cut=0.18)
    def SN(t,g=1.0,rate=1.0): D.hit(t,VB+'Snare 1.flac',0.9*g,rate,0.04); D.hit(t,VB+'Snare 2.flac',0.45*g,rate*1.06,-0.04)
    def GH(t,g=0.3): D.hit(t+rng.uniform(-0.004,0.004),VB+'Snare 3.flac',g*rng.uniform(0.8,1.15),1.12,0.1)
    def HH(t,g,op=False,pan=0.25): D.hit(t,VB+('Hat 1 Op.flac' if op else 'Hat %d Cl.flac'%rng.choice([1,2,3])),g*rng.uniform(0.85,1.1),1.0,pan,cut=None if op else 0.09)
    for bar in range(BARS):
        t0=bar*4*B; st=lambda s: t0+s*B/4; bt=lambda b: t0+b*B
        sec_='I' if bar<4 else 'A' if bar<12 else 'B' if bar<20 else 'A2'; r=R_ROOT[bar]; ch=R_CHD[bar%8]
        if bar in(4,12,20): D.hit(t0,FZ+'Crash18-3.wav',0.55,1.0,-0.2); ev.append(['boom',t0,0.3])
        # drums
        if sec_=='I' and bar<2:
            K(st(0),0.9); K(st(10),0.8)
            for s in range(0,16,2): HH(st(s),0.22 if s%4 else 0.14)
            for g_ in (7,9,15): GH(st(g_),0.2)
        elif sec_=='B':
            for b_ in range(4): K(bt(b_),1.0,True); HH(bt(b_)+B/2,0.4,True,0.3)
            SN(st(4)); SN(st(12)); D.hit(st(4),HE+'Clap_1.flac',0.5); D.hit(st(12),HE+'Clap_1.flac',0.5)
            for g_ in (7,10,15): GH(st(g_),0.28)
            for s in range(16): HH(st(s),0.16 if s%2 else 0.24,False,-0.3)
            if bar%4==3:
                for k_ in range(8): SN(st(8+k_),0.35+0.08*k_,1.0+0.03*k_)
        else:
            fill=bar%4==3
            pat=[[0,2,10],[0,2,10,11]][bar%2]
            for s in pat: K(st(s),1.0 if s in(0,10) else 0.8)
            if sec_=='A2': K(st(8),0.9,True); 
            SN(st(4))
            if fill:
                for k_,s in enumerate((8,9,10,11,12,13,14,15)): SN(st(s),0.4+0.08*k_,1.0+0.04*k_)
                D.hit(st(12),VB+'Tom Hi.flac',0.6,1.0,-0.4); D.hit(st(14),VB+'Tom Low.flac',0.7,1.0,0.4)
            else:
                SN(st(12) if bar%2==0 else st(13),1.0)
                for g_ in (7,9,15): GH(st(g_),0.3)
                if bar%2: GH(st(6),0.22)
            for s in range(16):
                if s%2==0 or sec_=='A2': HH(st(s),(0.34 if s%4==2 else 0.24) if s%2==0 else 0.13,s==14 and not fill)
            D.hit(st(0),VB+'Hat 1 Pd.flac',0.2,1.0,-0.3)
        # bass (reese + sub)
        if sec_=='I':
            ev.append(['reese',t0,r,B*2.3,0.2,{'cut':700,'cutEnd':1400}]); ev.append(['reese',bt(2.5),r,B*1.4,0.2,{'cut':900,'cutEnd':1800}])
        elif sec_=='B':
            for b_ in range(4): ev.append(['reese',bt(b_+0.5),r+12,B*0.42,0.22,{'cut':1800,'cutEnd':700,'drive':3}]); ev.append(['sub',bt(b_+0.5),r+12,B*0.4,0.1])
        else:
            for (b_,n,d) in ((0,r,1.4),(1.5,r+12,0.9),(2.5,r,0.95),(3.5,r+7 if bar%2==0 else r+1,0.46)): ev.append(['reese',bt(b_),n,B*d,0.22,{'cut':1500,'cutEnd':600,'drive':2.8}])
        # stabs: rave piano + supersaw
        if sec_!='I':
            for (b_,up,d) in ((0,0,0.45),(1.5,0,0.4))+(((3.25,12,0.3),) if bar%2 else ()):
                for q,m in enumerate(ch):
                    S.note(1,bar*4+b_+q*0.004,m+up,d,96); 
                    if q>0: ev.append(['lead',bt(b_),m+up,B*d*0.8,0.035,{'dly':0.05,'wide':1}])
            arp=[ch[0]+12,ch[1]+12,ch[2]+12,ch[3]+12,ch[0]+24,ch[2]+12,ch[1]+12,ch[2]+12]
            for s in range(8): S.note(2,bar*4+s*0.5,arp[s],0.3,74 if sec_=='A2' else 60)
        else:
            for q,m in enumerate(ch): S.note(1,bar*4+q*0.004,m,0.5,84); S.note(1,bar*4+1.5+q*0.004,m,0.4,78)
            if bar==3: ev.append(['riser',t0,4*B,0.07])
        if bar in(11,19): ev.append(['riser',bt(2),2*B,0.06])
    def riff(bar0,seq,full,syn):
        cur=bar0*4.0
        for n,d in seq:
            v=[n-12,n-5,n] if (full and d>=1.0) else [n-12,n]
            for m in v: S.note(0,cur,m,d*0.92,116 if m==n else 96)
            if syn: ev.append(['lead',cur*B,n,d*B*0.85,syn,{'dly':0.2}])
            else: ev.append(['juno',cur*B,n,{'dur':0.08,'vol':0.07,'cut':7,'sub':0,'pan':0.3,'dly':0.25}])
            cur+=d
    riff(4,RIFF_A,False,0); riff(8,RIFF_A,False,0); riff(12,RIFF_B,True,0.07); riff(16,RIFF_B,True,0.07); riff(20,RIFF_A,True,0.06); riff(24,RIFF_B,True,0.08)
    mus=fluid(S,beats,out,'rage',room=0.45,level=0.35,gain=0.55); syn=synth(ev,sec,out,'rage',{'delay':B*0.75,'rev':0.35,'duck':0.55,'duckRel':0.12,'seed':5})
    dr=D.fold(); dr=drive(dr*1.5,1.8)*0.62+room(dr,0.5)*0.05
    mix=pump(mus,kicks,0.35,0.07)*1.0+syn*0.95+dr*1.0
    master(mix,out,'rage',target=-13.5)

# ---------------------------------------------------------------- nightmare
N_PROG=[(38,[57,62,65,69,74]),(36,[57,60,65,69,76]),(34,[58,62,65,70,74]),(33,[57,61,64,69,73]),(31,[55,58,62,67,70]),(38,[57,62,65,69,74]),(39,[58,63,67,70,75]),(33,[57,61,64,68,73])]
N_A=[[74,1.5],[77,.5],[81,1],[80,1],[81,1.5],[82,.5],[81,1],[77,1],[74,1.5],[77,.5],[81,1],[86,1],[85,1.5],[81,.5],[80,1],[79,1],
     [74,1.5],[77,.5],[81,1],[80,1],[82,1.5],[86,.5],[84,1],[81,1],[87,1.5],[86,.5],[82,1],[81,1],[80,1.5],[76,.5],[73,1],[74,1]]
N_BR=[[86,1],[81,.5],[77,.5],[88,1],[89,1],[86,1.5],[84,.5],[81,2],[82,1],[77,.5],[74,.5],[86,1],[84,1],[81,1.5],[77,.5],[80,2],
      [86,1],[81,.5],[86,.5],[89,1],[91,1],[88,1.5],[85,.5],[86,2],[87,1],[86,.5],[82,.5],[81,1],[77,1],[85,1.5],[88,.5],[86,2]]
N_FIN=[[86,1],[88,1],[89,1],[93,1],[91,1.5],[89,.5],[86,1],[82,1],[87,1],[86,1],[82,1],[81,1],[85,1.5],[88,.5],[86,2]]
def do_nightmare(out):
    bpm=162; B=60/bpm; BARS=32; beats=BARS*4; sec=beats*B
    S=Song(bpm)
    S.setup(0,0,60,60,0,108)    # piano lead
    S.setup(1,6,70,55,0,84)     # harpsichord layer
    S.setup(2,52,64,110,0,104)  # choir aahs
    S.setup(3,19,64,90,0,84)    # church organ
    S.setup(4,48,54,80,0,96)    # strings
    S.setup(5,47,64,70,0,112)   # timpani
    S.setup(6,14,76,100,0,96)   # tubular bells
    S.setup(7,61,48,75,0,88)    # brass section
    D=Stem(sec); ev=[]; kicks=[]
    def K(t,g=1.0): kicks.append(t); ev.append(['duckAt',t]); D.hit(t,HE+'PowR_BD_1.flac',0.9*g); D.hit(t,EE+'EE_Kick_Hard_1.flac',0.45*g)
    def SN(t,g=1.0,rate=0.92): D.hit(t,VB+'Snare 2.flac',0.85*g,rate,0.03); D.hit(t,HE+'PowR_SN_1.flac',0.55*g,rate)
    def HH(t,g,op=False): D.hit(t,VB+('Hat 1 Op.flac' if op else 'Hat 2 Cl.flac'),g*rng.uniform(0.85,1.1),1.0,0.25,cut=None if op else 0.08)
    for bar in range(BARS):
        t0=bar*4*B; bt=lambda b: t0+b*B; bb=bar*4.0; r,ch=N_PROG[bar%8]
        intro=bar<4; bridge=12<=bar<20; climax=bar>=20
        # holy voices: sustained choir chords, organ under, bells on cadences
        cv=96 if climax else 84 if intro else 70 if bridge else 76
        for m in ch[1:]: S.note(2,bb,m,3.9,cv,0)
        if climax or intro: S.note(2,bb,ch[4]+12 if climax else ch[3]+12,3.9,cv-10,0)
        S.note(3,bb,r,3.95,84,0); S.note(3,bb,r+12,3.95,74,0)
        if intro or climax:
            for m in ch[:3]: S.note(3,bb,m,3.9,64,0)
        if bar%4==0: S.note(6,bb,r+36,3.6,100)
        if bar%4==3: S.note(6,bb+2,r+36,1.8,88)
        S.note(0,bb,r,3.5,96); S.note(0,bb,r+12,3.5,84)
        S.note(5,bb,r+12 if r<36 else r,0.9,112 if not intro else 96)
        if intro:
            K(bt(0),0.9); ev.append(['reese',t0,r,B*3.8,0.16,{'cut':500,'cutEnd':900}])
            if bar==3:
                for k_ in range(8): S.note(5,bb+2+k_*0.25,r+12 if r<36 else r,0.2,60+8*k_); SN(bt(2+k_*0.25),0.35+0.07*k_,0.9+0.02*k_)
                ev.append(['riser',bt(0),4*B,0.07])
            continue
        if bar in(4,12,20,28): D.hit(t0,FZ+'Crash18-3.wav',0.6,0.94,-0.2); ev.append(['boom',t0,0.36])
        # strings ostinato (8ths) + sustained tremolo in the climax
        ost=[ch[1],ch[2],ch[3],ch[4],ch[1]+12,ch[3],ch[2],ch[3]]
        for s_ in range(8): S.note(4,bb+s_*0.5,ost[s_]+12,0.28,(96 if climax else 82)+(8 if s_%4==0 else 0))
        if climax:
            for m in ch[1:4]: S.note(7,bb,m-12,3.8,84,0)
        # bass
        for (b_,n,d) in ((0,r,1.4),(1.5,r+12,0.45),(2.0,r,1.4),(3.5,r+7,0.45)): ev.append(['reese',bt(b_),n,B*d,0.2,{'cut':1300,'cutEnd':520,'drive':2.8}])
        S.note(5,bb+3.5,r+12 if r<36 else r,0.3,84)
        # drums
        if climax:
            for b_ in range(4): K(bt(b_))
            K(bt(1.5),0.8); K(bt(3.5),0.85)
        else:
            K(bt(0)); K(bt(1.5),0.85); K(bt(2.0),0.95)
            if bar%2: K(bt(3.5),0.82)
        SN(bt(1)); SN(bt(3)); D.hit(bt(1.75),VB+'Snare 3.flac',0.28,1.05,0.1)
        if bar%4==3:
            for k_,p in enumerate((3.25,3.5,3.75,3.875)): SN(bt(p),0.55+0.1*k_,0.95+0.04*k_)
            D.hit(bt(3.5),VB+'Tom Mid.flac',0.6,0.9,-0.4); D.hit(bt(3.75),VB+'Tom Low.flac',0.7,0.9,0.4)
            if bar in(11,19,27): ev.append(['riser',bt(0),4*B,0.06])
        for s_ in range(8): HH(bt(s_*0.5),0.3 if s_%2 else 0.18,s_%2==1 and climax)
        if climax:
            for s_ in range(16): D.hit(bt(s_*0.25),VB+'Hat 3 Cl.flac',0.1,1.0,-0.3,cut=0.05)
    def lead(bar0,seq,octs,vel,choir=False,brass=False):
        cur=bar0*4.0
        for n,d in seq:
            for o in octs: S.note(0,cur,n+o,d*0.92,vel if o==0 else vel-16); 
            S.note(1,cur,n,min(0.6,d*0.9),88); S.note(1,cur,n-12,min(0.6,d*0.9),76)
            if choir and d>=1.0: S.note(2,cur,n-12,d*0.98,92,0)
            if brass and d>=1.0: S.note(7,cur,n-12,d*0.9,100,0)
            cur+=d
    lead(4,N_A,(-12,0),112); lead(12,N_BR,(0,),108,choir=True); lead(20,N_A,(-12,0,12),118,brass=True); lead(28,N_FIN,(-12,0,12),120,choir=True,brass=True)
    cur=12*4.0
    for n,d in N_BR:
        if d>=1.5: S.note(6,cur,n,1.6,84)
        cur+=d
    mus=fluid(S,beats,out,'nightmare',room=0.88,level=0.75,gain=0.5); syn=synth(ev,sec,out,'nightmare',{'delay':B*0.75,'rev':0.5,'duck':0.6,'duckRel':0.14,'seed':8})
    dr=D.fold(); dr=drive(dr*1.3,1.5)*0.6+room(dr,1.4,3)*0.16
    mix=pump(mus,kicks,0.3,0.08)*1.15+syn*0.85+dr*0.95
    master(mix,out,'nightmare',target=-13.5)

if __name__=='__main__':
    out=sys.argv[1] if len(sys.argv)>1 else '.'; kinds=(sys.argv[2] if len(sys.argv)>2 else 'main,hard,rage,nightmare').split(',')
    os.makedirs(out,exist_ok=True)
    if 'main' in kinds: do_main(out,False)
    if 'hard' in kinds: do_main(out,True)
    if 'rage' in kinds: do_rage(out)
    if 'nightmare' in kinds: do_nightmare(out)
