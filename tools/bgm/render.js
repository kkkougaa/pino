// node render.js <outDir>  -> main.wav, rage.wav (needs playwright)
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
(async()=>{ const out=process.argv[2]||'.', b=await chromium.launch(), p=await b.newPage();
  await p.setContent('<meta charset="utf-8">'); await p.addScriptTag({path:path.join(__dirname,'compose.js')});
  for(const k of ['main','rage']){
    const r=await p.evaluate(async k=>{ const x=await PinoBGM.compose(k), n=x.length, i16=new Int16Array(n*2); let pk=0;
      for(let c=0;c<2;c++) for(let i=0;i<n;i++) pk=Math.max(pk,Math.abs(x.ch[c][i]));
      const g=pk>0.98?0.98/pk:1; for(let i=0;i<n;i++){ i16[i*2]=x.ch[0][i]*g*32767; i16[i*2+1]=x.ch[1][i]*g*32767; }
      const u=new Uint8Array(i16.buffer); let s=''; for(let i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));
      return {b64:btoa(s),sec:x.seconds,pk}; },k);
    const pcm=Buffer.from(r.b64,'base64'), h=Buffer.alloc(44); h.write('RIFF',0); h.writeUInt32LE(36+pcm.length,4); h.write('WAVEfmt ',8); h.writeUInt32LE(16,16); h.writeUInt16LE(1,20); h.writeUInt16LE(2,22);
    h.writeUInt32LE(44100,24); h.writeUInt32LE(44100*4,28); h.writeUInt16LE(4,32); h.writeUInt16LE(16,34); h.write('data',36); h.writeUInt32LE(pcm.length,40);
    fs.writeFileSync(path.join(out,k+'.wav'),Buffer.concat([h,pcm])); console.log(k,r.sec.toFixed(2)+'s','peak',r.pk.toFixed(3)); }
  await b.close(); })();
