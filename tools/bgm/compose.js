// BGM proposals, written as Web Audio scores. compose(kind) renders one seamless stereo loop.
// kinds: 'main' (104 bpm swing, D minor / F major, 24 bars), 'rage' (168 bpm, D minor, 28 bars)
(function(root){
const SR=44100, NOTE=n=>440*Math.pow(2,(n-69)/12);
let seed=7; const rnd=()=>{ seed=(seed*1664525+1013904223)>>>0; return seed/4294967296; };

function kit(C){
  const noise=C.createBuffer(1,SR*2,SR); { const d=noise.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=rnd()*2-1; }
  const ir=C.createBuffer(2,Math.floor(SR*1.7),SR);
  for(let c=0;c<2;c++){ const d=ir.getChannelData(c); for(let i=0;i<d.length;i++){ const k=i/d.length; d[i]=(rnd()*2-1)*Math.pow(1-k,3.4)*(i<SR*0.006?i/(SR*0.006):1); } }
  const comp=C.createDynamicsCompressor(); comp.threshold.value=-15; comp.knee.value=10; comp.ratio.value=3; comp.attack.value=0.006; comp.release.value=0.16;
  const music=C.createGain(), drums=C.createGain(), rev=C.createConvolver(), revIn=C.createGain(), revHp=C.createBiquadFilter(), revOut=C.createGain();
  rev.buffer=ir; revHp.type='highpass'; revHp.frequency.value=280; revOut.gain.value=0.75;
  revIn.connect(revHp); revHp.connect(rev); rev.connect(revOut); revOut.connect(comp);
  music.connect(comp); drums.connect(comp); comp.connect(C.destination);
  const SAT=new Float32Array(1024); for(let i=0;i<1024;i++){ const x=i/512-1; SAT[i]=Math.tanh(x*2.4); }
  function send(node,pan,sv,bus){ const p=C.createStereoPanner(); p.pan.value=pan||0; node.connect(p); p.connect(bus||music);
    if(sv){ const g=C.createGain(); g.gain.value=sv; p.connect(g); g.connect(revIn); } }
  const K={music,drums,
    fm(t,m,o){ o=o||{}; const f=NOTE(m), dur=o.dur||0.4, car=C.createOscillator(), mod=C.createOscillator(), mg=C.createGain(), g=C.createGain();
      car.frequency.value=f; mod.frequency.value=f*(o.ratio||2); const idx=f*(o.index||1);
      mg.gain.setValueAtTime(idx,t); mg.gain.exponentialRampToValueAtTime(Math.max(0.5,idx*0.02),t+(o.idecay||0.1));
      mod.connect(mg); mg.connect(car.frequency);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(o.vol||0.1,t+(o.att||0.004)); g.gain.exponentialRampToValueAtTime(0.0001,t+dur);
      car.connect(g); send(g,o.pan,o.send==null?0.3:o.send,o.bus); car.start(t); mod.start(t); car.stop(t+dur+0.05); mod.stop(t+dur+0.05); },
    pluck(t,m,o){ o=o||{}; const f=NOTE(m), dur=o.dur||0.3, a=C.createOscillator(), b=C.createOscillator(), lp=C.createBiquadFilter(), g=C.createGain();
      a.type='sawtooth'; b.type='square'; a.frequency.value=f; b.frequency.value=f; b.detune.value=7;
      lp.type='lowpass'; lp.Q.value=o.q||2.5; lp.frequency.setValueAtTime(Math.min(12000,f*(o.cut||7)),t); lp.frequency.exponentialRampToValueAtTime(Math.max(200,f*1.1),t+dur*0.6);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(o.vol||0.1,t+0.003); g.gain.exponentialRampToValueAtTime(0.0001,t+dur);
      const bg=C.createGain(); bg.gain.value=0.5; a.connect(lp); b.connect(bg); bg.connect(lp); lp.connect(g); send(g,o.pan,o.send==null?0.25:o.send,o.bus);
      a.start(t); b.start(t); a.stop(t+dur+0.05); b.stop(t+dur+0.05); },
    upright(t,m,dur,vol){ const f=NOTE(m), s=C.createOscillator(), tr=C.createOscillator(), tg=C.createGain(), lp=C.createBiquadFilter(), g=C.createGain();
      tr.type='triangle'; s.frequency.setValueAtTime(f*1.04,t); s.frequency.exponentialRampToValueAtTime(f,t+0.03); tr.frequency.value=f*2; tg.gain.value=0.32;
      lp.type='lowpass'; lp.frequency.setValueAtTime(1400,t); lp.frequency.exponentialRampToValueAtTime(380,t+dur*0.7);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.008); g.gain.exponentialRampToValueAtTime(0.0001,t+dur);
      s.connect(lp); tr.connect(tg); tg.connect(lp); lp.connect(g); send(g,0,0.06); s.start(t); tr.start(t); s.stop(t+dur+0.05); tr.stop(t+dur+0.05); },
    rhodes(t,notes,dur,vol,pan){ notes.forEach((m,i)=>{ K.fm(t+i*0.006,m,{ratio:1,index:1.3,idecay:0.25,dur,vol,pan:(pan||0)+(i%2?0.5:-0.5),send:0.4,att:0.006});
      K.fm(t+i*0.006,m,{ratio:14,index:0.25,idecay:0.03,dur:0.12,vol:vol*0.35,pan:(pan||0),send:0.2}); }); },
    nz(t,type,freq,q,vol,dur,pan,sv,att){ const s=C.createBufferSource(), f=C.createBiquadFilter(), g=C.createGain(); s.buffer=noise; f.type=type; f.frequency.value=freq; f.Q.value=q;
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+(att||0.002)); g.gain.exponentialRampToValueAtTime(0.0001,t+(att||0)+dur);
      s.connect(f); f.connect(g); send(g,pan,sv,drums); s.start(t,rnd()*1.2); s.stop(t+(att||0)+dur+0.05); return f; },
    kick(t,vol,f0){ const o=C.createOscillator(), g=C.createGain(), f=f0||52; o.frequency.setValueAtTime(f*3.2,t); o.frequency.exponentialRampToValueAtTime(f,t+0.06);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.002); g.gain.exponentialRampToValueAtTime(0.0001,t+0.26);
      o.connect(g); send(g,0,0,drums); o.start(t); o.stop(t+0.3); K.nz(t,'bandpass',3200,0.8,vol*0.18,0.012,0,0); },
    snare(t,vol,sv){ K.nz(t,'bandpass',2000,0.8,vol,0.13,0.05,sv==null?0.2:sv); K.nz(t,'highpass',5500,0.7,vol*0.5,0.09,0.05,0.1);
      K.fm(t,55,{ratio:1.6,index:1.4,idecay:0.02,dur:0.09,vol:vol*0.5,send:0,bus:drums}); },
    brush(t,vol){ K.nz(t,'bandpass',3400,0.6,vol,0.11,-0.1,0.25,0.012); },
    hat(t,vol,dur,pan){ K.nz(t,'highpass',8800,0.8,vol,dur||0.03,pan==null?0.25:pan,0.05); },
    snap(t,vol,pan){ [0,0.011,0.021].forEach((d,i)=>K.nz(t+d,'bandpass',1700+i*260,3.2,vol*(i===2?1:0.55),i===2?0.07:0.012,pan||0,0.45)); },
    wood(t,m,vol,pan){ K.fm(t,m,{ratio:1.5,index:3,idecay:0.012,dur:0.08,vol,pan,send:0.3,bus:drums}); },
    swell(t,dur,vol,up){ const f=K.nz(t,'highpass',up?900:6000,0.7,vol,0.5,0,0.5,dur); if(up){ f.type='bandpass'; f.frequency.setValueAtTime(500,t); f.frequency.exponentialRampToValueAtTime(7000,t+dur); } },
    crash(t,vol){ K.nz(t,'highpass',5200,0.6,vol,1.3,-0.2,0.6); K.nz(t,'bandpass',9000,2,vol*0.6,0.9,0.3,0.4); },
    sawBass(t,m,dur,vol){ const f=NOTE(m), a=C.createOscillator(), b=C.createOscillator(), s=C.createOscillator(), w=C.createWaveShaper(), lp=C.createBiquadFilter(), g=C.createGain(), pre=C.createGain();
      a.type='sawtooth'; b.type='sawtooth'; a.frequency.value=f; b.frequency.value=f; b.detune.value=11; s.frequency.value=f; w.curve=SAT; pre.gain.value=0.3;
      lp.type='lowpass'; lp.Q.value=4; lp.frequency.setValueAtTime(1900,t); lp.frequency.exponentialRampToValueAtTime(420,t+dur);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.004); g.gain.setValueAtTime(vol,t+dur*0.7); g.gain.linearRampToValueAtTime(0.0001,t+dur);
      const sg=C.createGain(), hp=C.createBiquadFilter(); sg.gain.value=0.45; hp.type='highpass'; hp.frequency.value=38; a.connect(pre); b.connect(pre); pre.connect(w); w.connect(lp); s.connect(sg); sg.connect(g); lp.connect(g); g.connect(hp); send(hp,0,0.03);
      [a,b,s].forEach(o=>{ o.start(t); o.stop(t+dur+0.03); }); },
    stab(t,notes,dur,vol,pan){ const lp=C.createBiquadFilter(), g=C.createGain(); lp.type='lowpass'; lp.Q.value=1.6;
      lp.frequency.setValueAtTime(500,t); lp.frequency.linearRampToValueAtTime(4200,t+0.025); lp.frequency.exponentialRampToValueAtTime(1300,t+dur);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.012); g.gain.setValueAtTime(vol*0.8,t+dur*0.7); g.gain.linearRampToValueAtTime(0.0001,t+dur);
      notes.forEach(m=>[-9,8].forEach(dt=>{ const o=C.createOscillator(); o.type='sawtooth'; o.frequency.setValueAtTime(NOTE(m)*0.97,t); o.frequency.exponentialRampToValueAtTime(NOTE(m),t+0.03); o.detune.value=dt; o.connect(lp); o.start(t); o.stop(t+dur+0.03); }));
      lp.connect(g); send(g,pan,0.3); },
    lead(t,m,dur,vol,pan){ const f=NOTE(m), a=C.createOscillator(), b=C.createOscillator(), bg=C.createGain(), lp=C.createBiquadFilter(), g=C.createGain(), l=C.createOscillator(), lg=C.createGain();
      a.type='square'; b.type='sawtooth'; b.detune.value=-12; bg.gain.value=0.6; [a,b].forEach(o=>{ o.frequency.setValueAtTime(f*0.985,t); o.frequency.exponentialRampToValueAtTime(f,t+0.02); });
      l.frequency.value=6.2; lg.gain.setValueAtTime(0,t); lg.gain.setValueAtTime(0,t+0.14); lg.gain.linearRampToValueAtTime(f*0.012,t+0.3); l.connect(lg); lg.connect(a.frequency); lg.connect(b.frequency);
      lp.type='lowpass'; lp.Q.value=1.2; lp.frequency.setValueAtTime(5200,t); lp.frequency.exponentialRampToValueAtTime(2600,t+dur);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.008); g.gain.setValueAtTime(vol*0.85,t+dur*0.8); g.gain.linearRampToValueAtTime(0.0001,t+dur);
      a.connect(lp); b.connect(bg); bg.connect(lp); lp.connect(g); send(g,pan,0.32);
      [a,b,l].forEach(o=>{ o.start(t); o.stop(t+dur+0.03); }); },
    sub(t,m,dur,vol){ const o=C.createOscillator(), g=C.createGain(); o.frequency.value=NOTE(m);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.02); g.gain.setValueAtTime(vol,t+dur*0.8); g.gain.linearRampToValueAtTime(0.0001,t+dur); o.connect(g); send(g,0,0); o.start(t); o.stop(t+dur+0.03); },
    duck(times,depth,rel){ times.slice().sort((a,b)=>a-b).forEach(t=>{ music.gain.setValueAtTime(depth,t); music.gain.linearRampToValueAtTime(1,t+rel); }); }
  };
  return K;
}

/* ---- main: "midnight tiptoe" ---- */
const CH={Dm6:[62,65,69,71],Bb7:[62,65,68,70],A7:[61,64,67,69],Gm7:[62,65,67,70],F:[60,64,65,69],Dm7:[60,62,65,69],C7:[58,60,64,67]};
const RT={Dm6:38,Dm7:38,Bb7:46,A7:45,Gm7:43,F:41,C7:36};
const M_CH=[['Dm6'],['Dm6'],['Bb7'],['A7'],['Dm6'],['Dm6'],['Gm7','A7'],['Dm6'],
            ['F'],['Dm7'],['Gm7'],['C7'],['F'],['Dm7'],['Gm7','C7'],['A7']];
const M_A=[[74,0,77,0,81,0,0,80],[81,0,0,77,0,74,0,0],[74,0,77,0,80,0,0,79],[76,0,73,0,69,0,0,0],
           [74,0,77,0,81,0,0,80],[81,0,84,0,86,0,0,0],[82,0,79,0,76,0,73,0],[74,0,0,0,0,0,69,72]];
const M_B=[[77,0,81,0,84,0,81,0],[77,0,0,74,0,77,0,0],[79,0,82,0,86,0,82,0],[84,0,0,82,0,79,76,0],
           [77,0,81,0,84,0,88,0],[86,0,0,84,0,81,0,0],[82,0,79,0,82,0,84,0],[85,0,0,81,0,76,0,73]];
const M_CTR={1:[[6,86],[7,89]],3:[[5,85],[6,88]],5:[[6,93],[7,89]]};
function scoreMain(K,T0){
  const B=60/104, BARS=24, pos=(bar,p)=>T0+bar*4*B+Math.floor(p/2)*B+(p%2?B*0.62:0);
  for(let bar=0;bar<BARS;bar++){
    const sec=bar<8?'A':bar<16?'B':'A2', i=bar%8, chs=M_CH[sec==='B'?8+i:i], chAt=p=>CH[chs[p>=4&&chs.length>1?1:0]];
    const mel=(sec==='B'?M_B:M_A)[i];
    mel.forEach((m,p)=>{ if(!m) return; let rest=1; while(p+rest<8&&!mel[p+rest]) rest++; const t=pos(bar,p), len=Math.min(1.4,rest*B*0.5);
      if(sec==='B'){ K.fm(t,m,{ratio:4,index:0.9,idecay:0.12,dur:0.5+len,vol:0.11,pan:0.18,send:0.55}); K.fm(t,m-12,{ratio:1,index:0.4,idecay:0.2,dur:0.4+len,vol:0.03,pan:0.1,send:0.4}); }
      else { K.pluck(t,m,{dur:0.22+len*0.25,vol:0.11,pan:-0.25,cut:7,send:0.35}); K.fm(t,m,{ratio:4,index:1.1,idecay:0.04,dur:0.3,vol:sec==='A2'?0.09:0.055,pan:0.25,send:0.4}); } });
    if(sec==='A2'&&M_CTR[i]) M_CTR[i].forEach(([p,m])=>K.fm(pos(bar,p),m,{ratio:3.5,index:1.6,idecay:0.3,dur:1.1,vol:0.03,pan:0.55,send:0.7}));
    // bass
    const r0=RT[chs[0]], r1=RT[chs[chs.length>1?1:0]], nb=(bar+1)%BARS, ns=nb<8?'A':nb<16?'B':'A2', nr=RT[M_CH[ns==='B'?8+nb%8:nb%8][0]], fifth=r=>r+7>50?r-5:r+7;
    K.upright(pos(bar,0),r0,0.5,0.22); K.upright(pos(bar,4),chs.length>1?r1:fifth(r0),0.45,0.19);
    if(sec!=='A') K.upright(pos(bar,3),r0+12,0.2,0.12);
    if(sec!=='A'||i%2) K.upright(pos(bar,7),nr-1,0.2,0.15);
    // keys
    if(sec==='B'){ K.rhodes(pos(bar,0),chAt(0),1.5,0.042,0); K.rhodes(pos(bar,5),chAt(5),0.5,0.036,0); }
    else { K.rhodes(pos(bar,3),chAt(3),0.32,0.042,0); K.rhodes(pos(bar,6),chAt(6),0.26,0.036,0); if(sec==='A2') K.rhodes(pos(bar,0),chAt(0),0.7,0.022,0); }
    // drums
    K.kick(pos(bar,0),sec==='A'?0.2:0.26); if(sec!=='A'){ K.kick(pos(bar,5),0.16); }
    [2,6].forEach(p=>{ K.snap(pos(bar,p),sec==='B'?0.1:0.16,p===2?-0.3:0.3); if(sec!=='A') K.brush(pos(bar,p),0.1); });
    for(let p=0;p<8;p++) K.hat(pos(bar,p),(p%2?0.05:0.026)*(sec==='A'?0.8:1.2),p%2?0.035:0.02,p%2?0.4:-0.35);
    if(sec!=='B'){ K.wood(pos(bar,4),bar%2?86:81,0.05,-0.45); if(bar%2) K.wood(pos(bar,5),79,0.035,-0.45); }
    if(i===7){ K.brush(pos(bar,7),0.09); if(sec==='A2'){ [5,6,7].forEach((p,k)=>K.snare(pos(bar,p),0.07+0.035*k,0.3)); } K.swell(pos(bar,4),2*B,0.035); }
  }
  return BARS*4*B;
}

/* ---- rage: "caught!" ---- */
const R_TRI={Dm:[62,65,69],Bb:[62,65,70],C:[60,64,67],A:[61,64,69],Gm:[62,67,70]}, R_RT={Dm:38,Bb:34,C:36,A:33,Gm:31};
const R_CH=['Dm','Dm','Bb','A', 'Dm','Dm','Bb','C','Dm','Dm','Bb','A', 'Gm','Dm','Bb','A','Gm','Dm','Bb','A', 'Dm','Dm','Bb','C','Dm','Dm','Bb','A'];
const R_LEAD=[[74,77,81,80,81,0,77,74],[74,77,81,80,81,0,84,86],[82,0,81,82,86,0,82,77],[84,0,82,84,88,0,84,79],
              [74,77,81,80,81,0,77,74],[86,0,84,81,0,77,81,0],[82,81,77,74,82,81,77,74],[73,76,81,85,88,0,85,81]];
const R_LONG=[[79,82],[81,77],[82,86],[85,81],[86,82],[81,86],[89,86],[88,85]];
function scoreRage(K,T0){
  const B=60/168, S=B/4, BARS=28, at=(bar,s)=>T0+bar*4*B+s*S, kicks=[];
  const kick=(t,v)=>{ K.kick(t,v*0.62,56); kicks.push(t); };
  for(let bar=0;bar<BARS;bar++){
    const sec=bar<4?'I':bar<12?'A':bar<20?'B':'A2', ch=R_CH[bar], r=R_RT[ch], tri=R_TRI[ch], i=sec==='A'?bar-4:sec==='B'?bar-12:sec==='A2'?bar-20:bar;
    if(sec==='B'){
      kick(at(bar,0),0.5); kick(at(bar,10),0.42); K.snare(at(bar,8),0.3,0.55);
      for(let s=0;s<16;s+=2) K.hat(at(bar,s),s%4?0.03:0.018,0.03,0.3);
      K.sub(at(bar,0),r+12,4*B*0.96,0.1); K.sawBass(at(bar,0),r+12,B*1.8,0.07); K.sawBass(at(bar,10),r+12,B*1.2,0.06);
      K.stab(at(bar,0),tri,B*3.2,0.03,0);
      const up=[tri[0],tri[1],tri[2],tri[0]+12,tri[2],tri[1]];
      for(let s=0;s<16;s++) K.pluck(at(bar,s),up[s%6]+12,{dur:0.16,vol:0.04+(i>=4?0.012:0),pan:s%2?0.5:-0.5,cut:5+i*0.6,send:0.4});
      R_LONG[i].forEach((m,k)=>K.lead(at(bar,k*8),m,B*1.9,0.05,0.1));
      if(i===6) for(let s=0;s<16;s+=2) K.snare(at(bar,s),0.06+0.012*s,0.25);
      if(i===7){ for(let s=0;s<16;s++) K.snare(at(bar,s),0.08+0.014*s,0.25); }
      if(i===6) K.swell(at(bar,0),8*B,0.09,true);
      continue;
    }
    const full=sec!=='I'||bar>=2, push=sec==='A2';
    if(push){ [0,4,8,12].forEach(s=>kick(at(bar,s),0.5)); kick(at(bar,10),0.3); }
    else { [0,6,10].forEach(s=>kick(at(bar,s),0.5)); if(bar%2) kick(at(bar,3),0.34); }
    if(full){ K.snare(at(bar,4),0.3); K.snare(at(bar,12),0.3); K.snare(at(bar,15),0.07); if(bar%4===3){ K.snare(at(bar,13),0.14); K.snare(at(bar,14),0.2); } }
    for(let s=0;s<16;s++) K.hat(at(bar,s),s%4===2?0.045:s%2?0.014:0.026,s===14?0.12:0.022,s%2?0.4:0.2);
    if((sec==='A'||sec==='A2')&&i===0) K.crash(at(bar,0),0.12);
    if(sec==='I'&&bar===0) K.crash(at(bar,0),0.1);
    for(let e=0;e<8;e++) K.sawBass(at(bar,e*2),r+12+([2,5,7].includes(e)?12:0),S*1.7,0.085);
    [0,6,12].forEach((s,k)=>K.stab(at(bar,s),tri.map(m=>m+(push?12:0)),S*(k===2?2.6:1.5),0.05,k%2?0.45:-0.45));
    if(sec==='I'){ if(bar===3) K.swell(at(bar,0),4*B,0.08,true); [0,6,12].forEach(s=>K.pluck(at(bar,s),tri[2]+12,{dur:0.18,vol:0.04,pan:0.4,send:0.4})); continue; }
    const mel=R_LEAD[i];
    mel.forEach((m,e)=>{ if(!m) return; let rest=1; while(e+rest<8&&!mel[e+rest]) rest++; const t=at(bar,e*2), d=Math.min(0.5,rest*2*S*0.92);
      K.lead(t,m,d,0.085,-0.08); if(push) K.fm(t,m+12,{ratio:3.5,index:1.5,idecay:0.12,dur:0.35,vol:0.03,pan:0.4,send:0.5}); });
  }
  K.duck(kicks,0.7,0.13);
  return BARS*4*B;
}

async function compose(kind){
  seed=kind==='rage'?11:7;
  const B=kind==='rage'?60/168:60/104, bars=kind==='rage'?28:24, L=bars*4*B, N=Math.round(L*SR), TAIL=Math.round(2.2*SR);
  const C=new OfflineAudioContext(2,N+TAIL,SR), K=kit(C);
  (kind==='rage'?scoreRage:scoreMain)(K,0);
  const buf=await C.startRendering(), ch=[0,1].map(c=>{ const d=buf.getChannelData(c), o=new Float32Array(N); o.set(d.subarray(0,N)); for(let i=0;i<TAIL;i++) o[i]+=d[N+i]; return o; });
  return {sr:SR,length:N,seconds:L,ch};
}
root.PinoBGM={compose};
})(typeof window!=='undefined'?window:globalThis);
