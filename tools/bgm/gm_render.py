#!/usr/bin/env python3
"""BGM proposals played by sampled instruments (General MIDI, FluidR3_GM) instead of synth patches.
   usage: gm_render.py <outDir>   -> main.wav hard.wav rage.wav (seamless loops) + .mid files
   needs: fluidsynth, FluidR3_GM.sf2, numpy"""
import struct, subprocess, sys, wave, random, os
import numpy as np
SF2='/usr/share/sounds/sf2/FluidR3_GM.sf2'; PPQ=480; SR=44100

class Song:
    def __init__(s,bpm): s.bpm=bpm; s.ev=[]; s.rng=random.Random(5)
    def setup(s,ch,prog,pan=64,rev=40,cho=0,vol=100,bank=None):
        if bank is not None: s.ev.append((0,0,bytes([0xB0|ch,0,bank])))
        s.ev+= [(0,1,bytes([0xC0|ch,prog])),(0,1,bytes([0xB0|ch,10,pan])),(0,1,bytes([0xB0|ch,91,rev])),(0,1,bytes([0xB0|ch,93,cho])),(0,1,bytes([0xB0|ch,7,vol]))]
    def note(s,ch,beat,m,dur,vel,human=0.012):
        t=max(0,beat+(s.rng.random()-0.5)*human); v=max(1,min(127,int(vel*(0.93+0.14*s.rng.random()))))
        a=int(round(t*PPQ)); b=int(round((t+max(0.03,dur))*PPQ))
        s.ev.append((a,3,bytes([0x90|ch,m,v]))); s.ev.append((b,2,bytes([0x80|ch,m,0])))
    def write(s,path,end_beat):
        ev=sorted(s.ev+[(int(end_beat*PPQ),4,bytes([0xB9,120,0]))],key=lambda e:(e[0],e[1]))
        def vlq(n):
            b=[n&0x7F]; n>>=7
            while n: b.append((n&0x7F)|0x80); n>>=7
            return bytes(reversed(b))
        us=int(round(60e6/s.bpm)); trk=b'\x00\xFF\x51\x03'+us.to_bytes(3,'big'); last=0
        for t,_,d in ev: trk+=vlq(t-last)+d; last=t
        trk+=b'\x00\xFF\x2F\x00'
        open(path,'wb').write(b'MThd'+struct.pack('>IHHH',6,0,1,PPQ)+b'MTrk'+struct.pack('>I',len(trk))+trk)

CH={'Dm6':[62,65,69,71],'Bb7':[62,65,68,70],'A7':[61,64,67,69],'Gm7':[62,65,67,70],'F':[60,64,65,69],'Dm7':[60,62,65,69],'C7':[58,60,64,67]}
RT={'Dm6':38,'Dm7':38,'Bb7':46,'A7':45,'Gm7':43,'F':41,'C7':36}
M_CH=[['Dm6'],['Dm6'],['Bb7'],['A7'],['Dm6'],['Dm6'],['Gm7','A7'],['Dm6'],['F'],['Dm7'],['Gm7'],['C7'],['F'],['Dm7'],['Gm7','C7'],['A7']]
M_A=[[74,0,77,0,81,0,0,80],[81,0,0,77,0,74,0,0],[74,0,77,0,80,0,0,79],[76,0,73,0,69,0,0,0],[74,0,77,0,81,0,0,80],[81,0,84,0,86,0,0,0],[82,0,79,0,76,0,73,0],[74,0,0,0,0,0,69,72]]
M_B=[[77,0,81,0,84,0,81,0],[77,0,0,74,0,77,0,0],[79,0,82,0,86,0,82,0],[84,0,0,82,0,79,76,0],[77,0,81,0,84,0,88,0],[86,0,0,84,0,81,0,0],[82,0,79,0,82,0,84,0],[85,0,0,81,0,76,0,73]]
M_CTR={1:[(6,86),(7,89)],3:[(5,85),(6,88)],5:[(6,93),(7,89)]}

def main(hard=False):
    S=Song(104); BARS=24
    S.setup(0,0,58,45); S.setup(1,4,70,50,40,90); S.setup(2,32,64,15,0,112); S.setup(3,11,76,60); S.setup(4,9,90,70,0,80); S.setup(5,45,44,45,0,96); S.setup(9,32,64,35,0,104,bank=None)
    pos=lambda bar,p: bar*4+p//2+(0.62 if p%2 else 0)
    sec_of=lambda b: 'A' if b<8 else 'B' if b<16 else 'A2'
    for bar in range(BARS):
        sec=sec_of(bar); i=bar%8; chs=M_CH[8+i if sec=='B' else i]; chat=lambda p: CH[chs[1 if p>=4 and len(chs)>1 else 0]]
        mel=(M_B if sec=='B' else M_A)[i]
        for p,m in enumerate(mel):
            if not m: continue
            rest=1
            while p+rest<8 and not mel[p+rest]: rest+=1
            t=pos(bar,p); ln=min(1.6,rest*0.5)
            if hard: S.note(0,t,m-12,min(0.5,ln*0.6),78); continue
            if sec=='B': S.note(3,t,m,ln*1.3,96); S.note(1,t,m-12,ln,52)
            else:
                S.note(0,t,m,min(0.7,ln*0.7),100 if p%2==0 else 88); S.note(5,t,m,0.3,70)
                if sec=='A2': S.note(0,t,m+12,min(0.5,ln*0.5),62)
        if sec=='A2' and not hard and i in M_CTR:
            for p,m in M_CTR[i]: S.note(4,pos(bar,p),m-12,1.0,74)
        r0=RT[chs[0]]; r1=RT[chs[-1]]; nb=(bar+1)%BARS; ns=sec_of(nb); nr=RT[M_CH[8+nb%8 if ns=='B' else nb%8][0]]; fifth=lambda r: r-5 if r+7>50 else r+7
        S.note(2,pos(bar,0),r0,1.3,104); S.note(2,pos(bar,4),r1 if len(chs)>1 else fifth(r0),1.0,92 if not hard else 76)
        if sec!='A' and not hard: S.note(2,pos(bar,3),r0+12,0.3,70)
        if (sec!='A' or i%2) and not hard: S.note(2,pos(bar,7),nr-1,0.35,84)
        chord=lambda p,dur,vel: [S.note(1,pos(bar,p)+k*0.012,m,dur,vel) for k,m in enumerate(chat(p))]
        if hard: chord(3,0.3,54)
        elif sec=='B': chord(0,2.4,60); chord(5,0.7,56)
        else:
            chord(3,0.4,64); chord(6,0.35,58)
            if sec=='A2': chord(0,1.2,48)
        D=lambda p,n,v: S.note(9,pos(bar,p),n,0.2,v,0.006)
        D(0,36,96 if not hard else 84)
        if hard: D(2,42,48); D(6,42,48); D(6,37,70); continue
        if sec!='A': D(5,36,74)
        for p in (2,6):
            D(p,37,96)
            if sec!='A': D(p,39,52)
        for p in range(8):
            D(p,46 if (p==7 and bar%4==3) else 42,(66 if p%2 else 44)+(8 if sec!='A' else 0))
            if sec=='B' and p%2==0: D(p,51,46)
            if sec!='A' and p%2: D(p,70,44)
        if sec!='B':
            D(4,75,62)
            if bar%2: D(5,76,50)
        if i==7 and sec=='A2':
            for k,p in enumerate((5,6,7)): D(p,38,58+16*k)
    return S,BARS*4

R_TRI={'Dm':[62,65,69],'Bb':[62,65,70],'C':[60,64,67],'A':[61,64,69],'Gm':[62,67,70]}; R_RT={'Dm':38,'Bb':34,'C':36,'A':33,'Gm':31}
R_CH=['Dm','Dm','Bb','A','Dm','Dm','Bb','C','Dm','Dm','Bb','A','Gm','Dm','Bb','A','Gm','Dm','Bb','A','Dm','Dm','Bb','C','Dm','Dm','Bb','A']
R_LEAD=[[74,77,81,80,81,0,77,74],[74,77,81,80,81,0,84,86],[82,0,81,82,86,0,82,77],[84,0,82,84,88,0,84,79],[74,77,81,80,81,0,77,74],[86,0,84,81,0,77,81,0],[82,81,77,74,82,81,77,74],[73,76,81,85,88,0,85,81]]
R_LONG=[[79,82],[81,77],[82,86],[85,81],[86,82],[81,86],[89,86],[88,85]]

def rage():
    S=Song(168); BARS=28
    S.setup(0,1,60,35,0,110); S.setup(1,7,74,25,0,84); S.setup(2,33,64,10,0,118); S.setup(3,4,50,40,50,96); S.setup(4,61,80,45,0,84); S.setup(5,12,84,50,0,100); S.setup(6,53,56,70,0,86); S.setup(7,119,64,60,0,90); S.setup(9,0,64,30,0,112)
    at=lambda bar,s: bar*4+s/4.0
    for bar in range(BARS):
        sec='I' if bar<4 else 'A' if bar<12 else 'B' if bar<20 else 'A2'; ch=R_CH[bar]; r=R_RT[ch]; tri=R_TRI[ch]; i=bar-(4 if sec=='A' else 12 if sec=='B' else 20 if sec=='A2' else 0)
        D=lambda s,n,v: S.note(9,at(bar,s),n,0.1,v,0.004)
        if sec=='B':
            D(0,36,110); D(10,36,96); D(8,38,118); D(8,39,70)
            for s in range(0,16,2): D(s,42,62 if s%4 else 46)
            for g in (5,13): D(g,38,30)
            S.note(2,at(bar,0),r,2.2,104); S.note(2,at(bar,10),r,1.3,96)
            for k,m in enumerate(tri): S.note(3,at(bar,0)+k*0.01,m,3.6,62)
            up=[tri[0],tri[1],tri[2],tri[0]+12,tri[2],tri[1]]
            for s in range(16): S.note(5,at(bar,s),up[s%6]+12,0.22,58+(14 if i>=4 else 0)+(8 if s%4==0 else 0))
            for k,m in enumerate(R_LONG[i]): S.note(6,at(bar,k*8),m,1.9,84); S.note(0,at(bar,k*8),m,1.6,70)
            if i==6:
                for s in range(0,16,2): D(s,38,40+5*s)
                S.note(7,at(bar,0)+4.6,60,3.4,100)
            if i==7:
                for s in range(12): D(s,38,56+5*s)
                for k,(s,n) in enumerate(((12,48),(13,47),(14,45),(15,43))): D(s,n,112)
            continue
        full=sec!='I' or bar>=2; push=sec=='A2'
        if push:
            for s in (0,4,8,12): D(s,36,112)
            D(10,36,80)
        else:
            for s in (0,6,10): D(s,36,112)
            if bar%2: D(3,36,88)
        if full:
            D(4,38,116); D(12,38,116)
            for g in (7,9,15): D(g,38,34)
            if bar%4==3: D(13,38,70); D(14,38,92)
        for s in range(16):
            if push and s%2==0: D(s,51,70 if s%4==0 else 54)
            D(s,46 if s==14 else 42,78 if s%4==2 else (38 if s%2 else 58))
        if sec in('A','A2') and i==0: D(0,49,104); D(0,57,70)
        if sec=='I' and bar==0: D(0,49,92)
        for e in range(8): S.note(2,at(bar,e*2),r+(12 if e in(2,5,7) else 0),0.42,112 if e%2==0 else 96)
        for k,s in enumerate((0,6,12)):
            for q,m in enumerate(tri):
                S.note(3,at(bar,s)+q*0.006,m,0.55 if k==2 else 0.3,86)
                S.note(0,at(bar,s)+q*0.006,m-12,0.3,62)
                if push or sec=='I': S.note(4,at(bar,s),m,0.5 if k==2 else 0.28,86 if push else 70)
        if sec=='I':
            if bar==3: S.note(7,at(bar,0)+0.9,60,3.4,96)
            for s in (0,6,12): S.note(5,at(bar,s),tri[2]+12,0.25,80)
            continue
        mel=R_LEAD[i]
        for e,m in enumerate(mel):
            if not m: continue
            rest=1
            while e+rest<8 and not mel[e+rest]: rest+=1
            t=at(bar,e*2); d=min(1.2,rest*0.5*0.9)
            S.note(0,t,m,d,112); S.note(0,t,m-12,d,84); S.note(1,t,m-12,min(0.3,d),78 if push else 60)
            if push: S.note(5,t,m+12,0.25,70)
    return S,BARS*4

def render(name,song,beats,out,gain='0.55'):
    mid=os.path.join(out,name+'.mid'); raw=os.path.join(out,name+'_raw.wav'); tail=3.0
    song.write(mid,beats+tail*song.bpm/60)
    subprocess.run(['fluidsynth','-ni','-q','-g',gain,'-R','1','-C','1','-r',str(SR),'-O','s16','-F',raw,SF2,mid],check=True,stderr=subprocess.DEVNULL)
    w=wave.open(raw); a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float64)/32768; w.close()
    N=int(round(beats*60/song.bpm*SR)); T=min(len(a)-N,int(tail*SR)); o=a[:N].copy()
    if T>0: o[:T]+=a[N:N+T]
    pk=np.abs(o).max(); o*=min(1,0.98/pk)
    w=wave.open(os.path.join(out,name+'.wav'),'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((o*32767).astype('<i2').tobytes()); w.close(); os.remove(raw)
    print(name,'%.2fs'%(N/SR),'peak %.3f'%pk)

if __name__=='__main__':
    out=sys.argv[1] if len(sys.argv)>1 else '.'
    s,b=main(False); render('main',s,b,out)
    s,b=main(True); render('hard',s,b,out)
    s,b=rage(); render('rage',s,b,out,'0.36')
