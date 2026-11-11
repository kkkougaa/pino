// BGM proposals, written as Web Audio scores. PinoBGM.compose(kind) renders one seamless stereo loop.
// kinds: 'main' (104 bpm swing, D minor / F major, 24 bars), 'hard' (main pressed down: octave lower, sparse, filtered),
//        'rage' (168 bpm, D minor, 28 bars)
// Patches follow common hardware designs: DX-style FM electric piano, Juno-style chorus poly, ladder-filter mono bass,
// supersaw lead, TR-808/909 style drums; chorus, ping-pong delay and a plate-like reverb on sends.
(function(root){
const SR=44100, NOTE=n=>440*Math.pow(2,(n-69)/12);
let seed=7; const rnd=()=>{ seed=(seed*1664525+1013904223)>>>0; return seed/4294967296; };
const curve=k=>{ const c=new Float32Array(2049); for(let i=0;i<2049;i++){ const x=i/1024-1; c[i]=Math.tanh(x*k)/Math.tanh(k); } return c; };

function kit(C,opt){
  opt=opt||{};
  const noise=C.createBuffer(1,SR*2,SR); { const d=noise.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=rnd()*2-1; }
  const ir=C.createBuffer(2,Math.floor(SR*2.3),SR);
  for(let c=0;c<2;c++){ const d=ir.getChannelData(c); let lp=0;
    for(let i=0;i<d.length;i++){ const k=i/d.length, damp=0.25+0.7*k; lp+=( (rnd()*2-1)-lp)*(1-damp*0.9); d[i]=lp*Math.pow(1-k,3)*(i<SR*0.004?i/(SR*0.004):1); }
    for(let e=0;e<9;e++){ const at=Math.floor(SR*(0.007+rnd()*0.05)); d[at]+=(rnd()<0.5?-1:1)*(0.5-e*0.04); } }
  const G=v=>{ const g=C.createGain(); g.gain.value=v; return g; };
  const out=G(1), tone=C.createBiquadFilter(), sat=C.createWaveShaper(), dcb=C.createBiquadFilter(), comp=C.createDynamicsCompressor();
  tone.type='lowpass'; tone.frequency.value=opt.cut||20000; tone.Q.value=0.6; sat.curve=curve(1.25); sat.oversample='2x'; dcb.type='highpass'; dcb.frequency.value=26;
  comp.threshold.value=-13; comp.knee.value=12; comp.ratio.value=2.5; comp.attack.value=0.012; comp.release.value=0.2;
  out.connect(tone); tone.connect(sat); sat.connect(dcb); dcb.connect(comp); comp.connect(C.destination);
  const music=G(1), drums=G(1); music.connect(out); drums.connect(out);
  const revIn=G(1), pre=C.createDelay(0.1), rhp=C.createBiquadFilter(), rev=C.createConvolver(), rlp=C.createBiquadFilter(), revOut=G(opt.rev||0.55);
  pre.delayTime.value=0.018; rhp.type='highpass'; rhp.frequency.value=260; rlp.type='lowpass'; rlp.frequency.value=6500; rev.buffer=ir;
  revIn.connect(pre); pre.connect(rhp); rhp.connect(rev); rev.connect(rlp); rlp.connect(revOut); revOut.connect(out);
  const D=opt.delay||0.3, dlyIn=G(1), dL=C.createDelay(1.5), dR=C.createDelay(1.5), dlp=C.createBiquadFilter(), fb=G(0.36), pL=C.createStereoPanner(), pR=C.createStereoPanner(), dOut=G(0.55), dRev=G(0.25);
  dL.delayTime.value=D; dR.delayTime.value=D; dlp.type='lowpass'; dlp.frequency.value=3200; pL.pan.value=-0.65; pR.pan.value=0.65;
  dlyIn.connect(dL); dL.connect(dlp); dlp.connect(dR); dR.connect(fb); fb.connect(dL); dL.connect(pL); dR.connect(pR); pL.connect(dOut); pR.connect(dOut); dOut.connect(music); dOut.connect(dRev); dRev.connect(revIn);
  const cho=G(1), choDry=G(0.72); cho.connect(choDry); choDry.connect(music);
  [[0.011,0.0028,0.53,-0.75],[0.017,0.0032,0.71,0.75]].forEach(([base,dep,hz,pan])=>{ const d=C.createDelay(0.05), l=C.createOscillator(), lg=G(dep), p=C.createStereoPanner(), g=G(0.5);
    d.delayTime.value=base; l.frequency.value=hz; l.connect(lg); lg.connect(d.delayTime); l.start(0); p.pan.value=pan; cho.connect(d); d.connect(p); p.connect(g); g.connect(music); });
  const BUS={music,drums,cho};
  function route(node,o){ o=o||{}; const p=C.createStereoPanner(); p.pan.value=o.pan||0; node.connect(p); p.connect(BUS[o.bus||'music']);
    if(o.rev){ const g=G(o.rev); p.connect(g); g.connect(revIn); } if(o.dly){ const g=G(o.dly); p.connect(g); g.connect(dlyIn); } return p; }
  function lp24(t,peak,end,dec,q){ const a=C.createBiquadFilter(), b=C.createBiquadFilter(); [a,b].forEach(f=>{ f.type='lowpass'; f.Q.value=q||1; const pk=Math.min(16000,peak), en=Math.max(60,Math.min(16000,end));
      f.frequency.setValueAtTime(pk,t); f.frequency.exponentialRampToValueAtTime(en,t+dec); }); b.Q.value=0.5; a.connect(b); return {in:a,out:b}; }
  function adsr(g,t,a,d,s,dur,r,vol){ g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+a); g.gain.exponentialRampToValueAtTime(Math.max(0.0002,vol*s),t+a+d);
    g.gain.setValueAtTime(Math.max(0.0002,vol*s),Math.max(t+a+d,t+dur)); g.gain.exponentialRampToValueAtTime(0.0001,Math.max(t+a+d,t+dur)+r); return Math.max(t+a+d,t+dur)+r+0.05; }
  const osc=(type,f,det,t,end)=>{ const o=C.createOscillator(); o.type=type; o.frequency.value=f; if(det) o.detune.value=det; o.start(t); o.stop(end); return o; };
  const nz=(t,dur)=>{ const s=C.createBufferSource(); s.buffer=noise; s.start(t,rnd()*1.5); s.stop(t+dur+0.05); return s; };
  const K={music,
    // DX-style electric piano: two detuned FM pairs + a short "tine"
    ep(t,m,dur,vol,o){ o=o||{}; const f=NOTE(m), g=G(0), end=adsr(g,t,0.004,0.5,0.4,dur,0.25,vol);
      [-4,4].forEach(dt=>{ const c=osc('sine',f,dt,t,end), mo=osc('sine',f,dt,t,end), mg=G(0); mg.gain.setValueAtTime(f*1.7,t); mg.gain.exponentialRampToValueAtTime(f*0.22,t+0.45); mo.connect(mg); mg.connect(c.frequency); c.connect(g); });
      const tc=osc('sine',f,0,t,t+0.4), tm=osc('sine',f*14,0,t,t+0.4), tmg=G(0), tg=G(0); tmg.gain.setValueAtTime(f*1.4,t); tmg.gain.exponentialRampToValueAtTime(1,t+0.07); tm.connect(tmg); tmg.connect(tc.frequency);
      tg.gain.setValueAtTime(vol*0.5,t); tg.gain.exponentialRampToValueAtTime(0.0001,t+0.3); tc.connect(tg); const p=route(tg,{pan:o.pan,bus:'cho',rev:0.2});
      const pp=route(g,{pan:o.pan,bus:'cho',rev:o.rev==null?0.3:o.rev,dly:o.dly}); const l=osc('sine',4.6,0,t,end), lg=G(0.3); l.connect(lg); lg.connect(pp.pan); },
    // Juno-style poly: 2 saws + sub square, 24 dB low-pass with envelope, chorus
    juno(t,m,o){ o=o||{}; const f=NOTE(m), dur=o.dur||0.2, vol=o.vol||0.1, g=G(0), end=adsr(g,t,o.att||0.004,o.dec||0.18,o.sus==null?0.3:o.sus,dur,o.rel||0.12,vol), F=lp24(t,f*(o.cut||8),f*(o.cutEnd||1.6),o.fdec||0.16,o.q||2.2);
      [[ 'sawtooth',-7,1],['sawtooth',7,1],['square',-1200,o.sub==null?0.45:o.sub]].forEach(([ty,dt,v])=>{ const x=osc(ty,f,dt,t,end), xg=G(v*0.5); x.connect(xg); xg.connect(F.in); });
      F.out.connect(g); route(g,{pan:o.pan,bus:'cho',rev:o.rev==null?0.25:o.rev,dly:o.dly}); },
    // mono bass: saw + sub square into a ladder-like low-pass
    bass(t,m,dur,vol,o){ o=o||{}; const f=NOTE(m), g=G(0), end=adsr(g,t,0.005,o.dec||0.22,o.sus==null?0.55:o.sus,dur,0.06,vol), F=lp24(t,f*(o.cut||7),f*(o.cutEnd||1.8),o.fdec||0.14,o.q||3.5), dr=C.createWaveShaper(), hp=C.createBiquadFilter();
      dr.curve=curve(o.drive||1.4); hp.type='highpass'; hp.frequency.value=34;
      const a=osc('sawtooth',f,0,t,end), b=osc('square',f/2,0,t,end), bg=G(0.5), ag=G(0.5); a.connect(ag); b.connect(bg); ag.connect(F.in); bg.connect(F.in); F.out.connect(dr); dr.connect(g); g.connect(hp); route(hp,{rev:0.02}); },
    sub(t,m,dur,vol){ const g=G(0), end=adsr(g,t,0.02,0.1,0.9,dur,0.08,vol); osc('sine',NOTE(m),0,t,end).connect(g); route(g,{}); },
    // supersaw lead with vibrato
    lead(t,m,dur,vol,o){ o=o||{}; const f=NOTE(m), l=osc('sine',5.8,0,t,t+dur+0.4), lg=G(0); lg.gain.setValueAtTime(0,t+0.12); lg.gain.linearRampToValueAtTime(f*0.011,t+0.3); l.connect(lg);
      [[[-19,-6,11],-0.55],[[-11,6,19],0.55]].forEach(([dets,pan])=>{ const g=G(0), end=adsr(g,t,0.006,0.12,0.75,dur,0.1,vol*0.5), F=lp24(t,f*9,f*4,0.25,1.4);
        dets.forEach(dt=>{ const x=osc('sawtooth',f,dt,t,end), xg=G(0.33); x.frequency.setValueAtTime(f*0.985,t); x.frequency.exponentialRampToValueAtTime(f,t+0.018); lg.connect(x.frequency); x.connect(xg); xg.connect(F.in); });
        F.out.connect(g); route(g,{pan:pan*(o.wide==null?1:o.wide),rev:0.22,dly:o.dly==null?0.22:o.dly}); });
      const sg=G(0), se=adsr(sg,t,0.006,0.1,0.7,dur,0.08,vol*0.3), sq=osc('square',f/2,0,t,se), sf=C.createBiquadFilter(); sf.type='lowpass'; sf.frequency.value=f*3; sq.connect(sf); sf.connect(sg); route(sg,{rev:0.1}); },
    // FM vibraphone / bell with motor tremolo
    vibe(t,m,dur,vol,o){ o=o||{}; const f=NOTE(m), g=G(0), tr=G(1), end=adsr(g,t,0.003,dur,0.05,dur,0.2,vol);
      [-3,3].forEach(dt=>{ const c=osc('sine',f,dt,t,end), mo=osc('sine',f*(o.ratio||4),dt,t,end), mg=G(0); mg.gain.setValueAtTime(f*(o.index||1.3),t); mg.gain.exponentialRampToValueAtTime(f*0.06,t+(o.idec||0.3)); mo.connect(mg); mg.connect(c.frequency); c.connect(g); });
      const l=osc('sine',5.4,0,t,end), lg=G(0.22); l.connect(lg); lg.connect(tr.gain); g.connect(tr); route(tr,{pan:o.pan,rev:o.rev==null?0.45:o.rev,dly:o.dly}); },
    /* drums */
    kick(t,vol,o){ o=o||{}; const f=o.f||48, g=G(0), dr=C.createWaveShaper(), x=C.createOscillator(); dr.curve=curve(1.6);
      x.frequency.setValueAtTime(f*(o.sweep||3.4),t); x.frequency.exponentialRampToValueAtTime(f,t+(o.st||0.07)); x.start(t); x.stop(t+(o.dec||0.34)+0.05);
      g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.002); g.gain.exponentialRampToValueAtTime(0.0001,t+(o.dec||0.34)); x.connect(dr); dr.connect(g); route(g,{bus:'drums'});
      const c=nz(t,0.02), cf=C.createBiquadFilter(), cg=G(0); cf.type='highpass'; cf.frequency.value=2500; cg.gain.setValueAtTime(vol*0.25,t); cg.gain.exponentialRampToValueAtTime(0.0001,t+0.012); c.connect(cf); cf.connect(cg); route(cg,{bus:'drums'}); },
    snare(t,vol,o){ o=o||{}; [[185,0.55],[330,0.3]].forEach(([f,v])=>{ const x=C.createOscillator(), g=G(0); x.type='triangle'; x.frequency.setValueAtTime(f*1.5,t); x.frequency.exponentialRampToValueAtTime(f,t+0.03); x.start(t); x.stop(t+0.2);
        g.gain.setValueAtTime(vol*v,t); g.gain.exponentialRampToValueAtTime(0.0001,t+0.11); x.connect(g); route(g,{bus:'drums',rev:o.rev||0.1}); });
      const n=nz(t,0.25), hp=C.createBiquadFilter(), g=G(0); hp.type='highpass'; hp.frequency.value=1500; g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol*0.8,t+0.002); g.gain.exponentialRampToValueAtTime(0.0001,t+(o.dec||0.17)); n.connect(hp); hp.connect(g); route(g,{bus:'drums',pan:0.04,rev:o.rev||0.18}); },
    clap(t,vol,o){ o=o||{}; const n=nz(t,0.4), bp=C.createBiquadFilter(), g=G(0); bp.type='bandpass'; bp.frequency.value=1150; bp.Q.value=1.3; g.gain.setValueAtTime(0.0001,t);
      [0,0.011,0.022].forEach(d=>{ g.gain.setValueAtTime(vol,t+d); g.gain.exponentialRampToValueAtTime(vol*0.12,t+d+0.009); }); g.gain.setValueAtTime(vol,t+0.033); g.gain.exponentialRampToValueAtTime(0.0001,t+0.033+(o.dec||0.16));
      n.connect(bp); bp.connect(g); route(g,{bus:'drums',pan:o.pan||0,rev:o.rev==null?0.35:o.rev}); },
    hat(t,vol,dec,pan){ const bp=C.createBiquadFilter(), hp=C.createBiquadFilter(), g=G(0); bp.type='bandpass'; bp.frequency.value=10000; bp.Q.value=0.8; hp.type='highpass'; hp.frequency.value=7000;
      [205.3,304.4,369.6,522.7,540,800].forEach(f=>osc('square',f*1.42,0,t,t+dec+0.05).connect(bp)); g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.001); g.gain.exponentialRampToValueAtTime(0.0001,t+dec);
      bp.connect(hp); hp.connect(g); route(g,{bus:'drums',pan:pan==null?0.25:pan,rev:0.04}); },
    rim(t,vol,pan){ [[1667,0.6],[455,0.4]].forEach(([f,v])=>{ const g=G(0); g.gain.setValueAtTime(vol*v,t); g.gain.exponentialRampToValueAtTime(0.0001,t+0.028); osc('triangle',f,0,t,t+0.06).connect(g); route(g,{bus:'drums',pan,rev:0.3}); }); },
    clave(t,f,vol,pan){ const g=G(0); g.gain.setValueAtTime(vol,t); g.gain.exponentialRampToValueAtTime(0.0001,t+0.05); osc('sine',f,0,t,t+0.08).connect(g); route(g,{bus:'drums',pan,rev:0.35,dly:0.12}); },
    shaker(t,vol,pan){ const n=nz(t,0.1), hp=C.createBiquadFilter(), g=G(0); hp.type='highpass'; hp.frequency.value=6500; g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+0.012); g.gain.exponentialRampToValueAtTime(0.0001,t+0.06); n.connect(hp); hp.connect(g); route(g,{bus:'drums',pan,rev:0.05}); },
    tom(t,f,vol,pan){ const x=C.createOscillator(), g=G(0); x.frequency.setValueAtTime(f*1.6,t); x.frequency.exponentialRampToValueAtTime(f,t+0.08); x.start(t); x.stop(t+0.3); g.gain.setValueAtTime(vol,t); g.gain.exponentialRampToValueAtTime(0.0001,t+0.24); x.connect(g); route(g,{bus:'drums',pan,rev:0.2}); },
    crash(t,vol){ const n=nz(t,1.6), hp=C.createBiquadFilter(), g=G(0); hp.type='highpass'; hp.frequency.value=4500; g.gain.setValueAtTime(vol,t); g.gain.exponentialRampToValueAtTime(0.0001,t+1.5); n.connect(hp); hp.connect(g); route(g,{bus:'drums',pan:-0.15,rev:0.5}); K.hat(t,vol*0.5,0.9,0.2); },
    riser(t,dur,vol){ const n=nz(t,Math.min(1.9,dur)), bp=C.createBiquadFilter(), g=G(0); n.loop=true; bp.type='bandpass'; bp.Q.value=1.2; bp.frequency.setValueAtTime(400,t); bp.frequency.exponentialRampToValueAtTime(8000,t+dur);
      g.gain.setValueAtTime(0.0001,t); g.gain.exponentialRampToValueAtTime(vol,t+dur); g.gain.linearRampToValueAtTime(0.0001,t+dur+0.03); n.stop(t+dur+0.1); n.connect(bp); bp.connect(g); route(g,{bus:'drums',rev:0.4}); },
    swell(t,dur,vol){ const n=nz(t,Math.min(1.9,dur+0.5)), hp=C.createBiquadFilter(), g=G(0); hp.type='highpass'; hp.frequency.value=6000; g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(vol,t+dur); g.gain.exponentialRampToValueAtTime(0.0001,t+dur+0.4); n.connect(hp); hp.connect(g); route(g,{bus:'drums',rev:0.5}); },
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
function scoreMain(K,T0,hard){
  const B=60/104, BARS=24, pos=(bar,p)=>T0+bar*4*B+Math.floor(p/2)*B+(p%2?B*0.62:0), kicks=[];
  for(let bar=0;bar<BARS;bar++){
    const sec=bar<8?'A':bar<16?'B':'A2', i=bar%8, chs=M_CH[sec==='B'?8+i:i], chAt=p=>CH[chs[p>=4&&chs.length>1?1:0]];
    const mel=(sec==='B'?M_B:M_A)[i];
    mel.forEach((m,p)=>{ if(!m) return; let rest=1; while(p+rest<8&&!mel[p+rest]) rest++; const t=pos(bar,p), len=Math.min(1.3,rest*B*0.5);
      if(hard){ K.juno(t,m-12,{dur:0.12,vol:0.13,dec:0.2,sus:0.12,cut:5,cutEnd:1.3,fdec:0.12,q:2.6,pan:-0.1,rev:0.3,dly:0.15}); return; }
      if(sec==='B'){ K.vibe(t,m,0.55+len,0.1,{pan:0.15,dly:0.18}); K.juno(t,m-12,{dur:len*0.6,vol:0.035,att:0.03,cut:3,cutEnd:2,sus:0.6,sub:0,pan:-0.2,rev:0.4}); }
      else { K.juno(t,m,{dur:0.1+len*0.2,vol:0.12,dec:0.2,sus:0.15,cut:9,cutEnd:1.5,fdec:0.15,q:3,pan:-0.15,rev:0.25,dly:0.3});
        K.vibe(t,m+12,0.35,sec==='A2'?0.035:0.02,{ratio:3.5,index:1.6,idec:0.12,pan:0.3,rev:0.5}); } });
    if(sec==='A2'&&!hard&&M_CTR[i]) M_CTR[i].forEach(([p,m])=>K.vibe(pos(bar,p),m,1.2,0.035,{ratio:3.5,index:1.8,idec:0.35,pan:0.5,rev:0.7,dly:0.3}));
    const r0=RT[chs[0]], r1=RT[chs[chs.length>1?1:0]], nb=(bar+1)%BARS, ns=nb<8?'A':nb<16?'B':'A2', nr=RT[M_CH[ns==='B'?8+nb%8:nb%8][0]], fifth=r=>r+7>50?r-5:r+7;
    const bo={cut:hard?3:4.5,cutEnd:1.3,fdec:0.16,q:2.4,sus:0.45,drive:1.1};
    K.bass(pos(bar,0),r0,B*0.75,0.2,bo); K.bass(pos(bar,4),chs.length>1?r1:fifth(r0),B*0.6,hard?0.13:0.17,bo);
    if(sec!=='A'&&!hard) K.bass(pos(bar,3),r0+12,0.1,0.09,bo);
    if((sec!=='A'||i%2)&&!hard) K.bass(pos(bar,7),nr-1,0.12,0.13,bo);
    const chord=(p,dur,vol)=>chAt(p).forEach((m,k)=>K.ep(pos(bar,p)+k*0.007,m,dur,vol,{pan:k%2?0.35:-0.35}));
    if(hard){ chord(3,0.18,0.03); }
    else if(sec==='B'){ chord(0,1.3,0.04); chord(5,0.4,0.034); }
    else { chord(3,0.22,0.04); chord(6,0.18,0.034); if(sec==='A2') chord(0,0.6,0.024); }
    K.kick(pos(bar,0),hard?0.3:sec==='A'?0.34:0.4,{f:46,dec:0.3}); kicks.push(pos(bar,0));
    if(sec!=='A'&&!hard){ K.kick(pos(bar,5),0.26,{f:46,dec:0.22}); kicks.push(pos(bar,5)); }
    if(hard){ [2,6].forEach(p=>K.hat(pos(bar,p),0.03,0.04,0.3)); K.rim(pos(bar,6),0.1,0.3); continue; }
    [2,6].forEach(p=>{ K.rim(pos(bar,p),0.2,p===2?-0.3:0.3); if(sec!=='A') K.clap(pos(bar,p),0.09,{pan:p===2?0.15:-0.15,dec:0.12}); });
    for(let p=0;p<8;p++){ K.hat(pos(bar,p),(p%2?0.05:0.028)*(sec==='A'?0.8:1.1),p===7&&bar%4===3?0.22:0.035,p%2?0.4:-0.35); if(sec!=='A'&&p%2) K.shaker(pos(bar,p),0.03,-0.5); }
    if(sec!=='B'){ K.clave(pos(bar,4),bar%2?2500:2100,0.05,-0.5); if(bar%2) K.clave(pos(bar,5),1900,0.035,-0.5); }
    if(i===7){ if(sec==='A2') [5,6,7].forEach((p,k)=>K.snare(pos(bar,p),0.06+0.035*k,{rev:0.3})); K.swell(pos(bar,4),2*B,0.035); }
  }
  K.duck(kicks,hard?0.9:0.86,0.16);
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
  const kick=(t,v)=>{ K.kick(t,v,{f:52,sweep:4.2,st:0.045,dec:0.24}); kicks.push(t); };
  for(let bar=0;bar<BARS;bar++){
    const sec=bar<4?'I':bar<12?'A':bar<20?'B':'A2', ch=R_CH[bar], r=R_RT[ch], tri=R_TRI[ch], i=sec==='A'?bar-4:sec==='B'?bar-12:sec==='A2'?bar-20:bar;
    if(sec==='B'){
      kick(at(bar,0),0.42); kick(at(bar,10),0.34); K.snare(at(bar,8),0.3,{rev:0.5,dec:0.22}); K.clap(at(bar,8),0.16,{rev:0.6,dec:0.25});
      for(let s=0;s<16;s+=2) K.hat(at(bar,s),s%4?0.035:0.02,0.035,0.3);
      K.sub(at(bar,0),r+12,4*B*0.9,0.1); K.bass(at(bar,0),r+12,B*1.7,0.1,{cut:5,drive:1.8}); K.bass(at(bar,10),r+12,B*1.1,0.085,{cut:5,drive:1.8});
      tri.forEach((m,k)=>K.juno(at(bar,0),m,{dur:B*3,vol:0.03,att:0.05,dec:0.6,sus:0.7,cut:5,cutEnd:3,fdec:1.2,sub:0.2,pan:k-1?0.3:-0.3,rev:0.4}));
      const up=[tri[0],tri[1],tri[2],tri[0]+12,tri[2],tri[1]];
      for(let s=0;s<16;s++) K.juno(at(bar,s),up[s%6]+12,{dur:0.05,vol:0.055+(i>=4?0.015:0),dec:0.1,sus:0.1,cut:4+i*0.9,cutEnd:1.5,fdec:0.09,q:3.5,sub:0,pan:s%2?0.5:-0.5,rev:0.3,dly:0.25});
      R_LONG[i].forEach((m,k)=>K.lead(at(bar,k*8),m,B*1.8,0.085,{wide:0.8}));
      if(i===6) for(let s=0;s<16;s+=2) K.snare(at(bar,s),0.05+0.011*s,{rev:0.2});
      if(i===7){ for(let s=0;s<12;s++) K.snare(at(bar,s),0.08+0.014*s,{rev:0.2}); [[12,150],[13,120],[14,95],[15,75]].forEach(([s,f],k)=>K.tom(at(bar,s),f,0.26,k*0.3-0.45)); }
      if(i===6) K.riser(at(bar,0),8*B,0.07);
      continue;
    }
    const full=sec!=='I'||bar>=2, push=sec==='A2';
    if(push){ [0,4,8,12].forEach(s=>kick(at(bar,s),0.42)); kick(at(bar,10),0.26); }
    else { [0,6,10].forEach(s=>kick(at(bar,s),0.42)); if(bar%2) kick(at(bar,3),0.3); }
    if(full){ [4,12].forEach(s=>{ K.snare(at(bar,s),0.3); K.clap(at(bar,s),0.11,{rev:0.25}); }); K.snare(at(bar,15),0.06); if(bar%4===3){ K.snare(at(bar,13),0.13); K.snare(at(bar,14),0.19); } }
    for(let s=0;s<16;s++) K.hat(at(bar,s),s%4===2?0.05:s%2?0.016:0.03,s===14?0.14:0.025,s%2?0.4:0.2);
    if((sec==='A'||sec==='A2')&&i===0){ K.crash(at(bar,0),0.11); K.sub(at(bar,0),r,B*2,0.14); }
    if(sec==='I'&&bar===0) K.crash(at(bar,0),0.09);
    for(let e=0;e<8;e++) K.bass(at(bar,e*2),r+12+([2,5,7].includes(e)?12:0),S*1.5,0.1,{cut:6,cutEnd:2,fdec:0.09,q:4,drive:2,sus:0.5});
    [0,6,12].forEach((s,k)=>tri.forEach((m,q)=>K.juno(at(bar,s),m+(push?12:0),{dur:S*(k===2?2.2:1.2),vol:0.055,dec:0.12,sus:0.5,cut:10,cutEnd:3,fdec:0.14,q:1.8,sub:0.2,pan:(k%2?0.4:-0.4)+(q-1)*0.15,rev:0.3})));
    if(sec==='I'){ if(bar===3) K.riser(at(bar,0),4*B,0.06); [0,6,12].forEach(s=>K.juno(at(bar,s),tri[2]+12,{dur:0.06,vol:0.05,cut:6,sub:0,pan:0.4,rev:0.35,dly:0.3})); continue; }
    const mel=R_LEAD[i];
    mel.forEach((m,e)=>{ if(!m) return; let rest=1; while(e+rest<8&&!mel[e+rest]) rest++; const t=at(bar,e*2), d=Math.min(0.5,rest*2*S*0.9);
      K.lead(t,m,d,0.14); if(push) K.vibe(t,m+12,0.3,0.03,{ratio:3.5,index:1.6,idec:0.1,pan:0.4,rev:0.5}); });
  }
  K.duck(kicks,0.68,0.13);
  return BARS*4*B;
}

async function compose(kind){
  seed=kind==='rage'?11:7;
  const rage=kind==='rage', B=rage?60/168:60/104, bars=rage?28:24, L=bars*4*B, N=Math.round(L*SR), TAIL=Math.round(3*SR);
  const C=new OfflineAudioContext(2,N+TAIL,SR), K=kit(C,{delay:rage?B*0.75:B*0.75,cut:kind==='hard'?2300:0,rev:rage?0.45:0.6});
  rage?scoreRage(K,0):scoreMain(K,0,kind==='hard');
  const buf=await C.startRendering(), ch=[0,1].map(c=>{ const d=buf.getChannelData(c), o=new Float32Array(N); o.set(d.subarray(0,N)); for(let i=0;i<TAIL;i++) o[i]+=d[N+i]; return o; });
  return {sr:SR,length:N,seconds:L,ch};
}
root.PinoBGM={compose};
})(typeof window!=='undefined'?window:globalThis);
