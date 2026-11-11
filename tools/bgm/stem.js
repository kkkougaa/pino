// node stem.js <events.json> <out.f32>   events.json: {seconds, opt, ev:[[inst,t,...args],...]}  -> raw float32 stereo interleaved
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
(async()=>{ const j=JSON.parse(fs.readFileSync(process.argv[2],'utf8')), b=await chromium.launch(), p=await b.newPage();
  await p.setContent('<meta charset="utf-8">'); await p.addScriptTag({path:path.join(__dirname,'compose.js')});
  const b64=await p.evaluate(async j=>{ const x=await PinoBGM.renderEvents(j.ev,j.seconds,j.opt), n=x.length, f=new Float32Array(n*2); for(let i=0;i<n;i++){ f[i*2]=x.ch[0][i]; f[i*2+1]=x.ch[1][i]; }
    const u=new Uint8Array(f.buffer); let s=''; for(let i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000)); return btoa(s); },j);
  fs.writeFileSync(process.argv[3],Buffer.from(b64,'base64')); await b.close(); })();
