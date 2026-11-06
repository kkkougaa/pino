// glb -> a compact JSON the game unpacks: int16 positions, int8 normals, uint16 indices, node tree with local transforms, material colours
const fs=require('fs'); const d=fs.readFileSync(process.argv[2]); const jl=d.readUInt32LE(12), j=JSON.parse(d.slice(20,20+jl).toString()); const bin=d.slice(20+jl+8);
const acc=(i)=>{ const a=j.accessors[i], v=j.bufferViews[a.bufferView], off=(v.byteOffset||0)+(a.byteOffset||0); const n={5126:4,5123:2,5125:4}[a.componentType]*{SCALAR:1,VEC3:3,VEC4:4}[a.type]; return {a,buf:bin.slice(off,off+a.count*n)}; };
const b64=(b)=>Buffer.from(b).toString('base64');
const lin2s=c=>Math.round(255*(c<=0.0031308?c*12.92:1.055*Math.pow(c,1/2.4)-0.055));
const hex=(f)=>'#'+[0,1,2].map(i=>lin2s(f[i]).toString(16).padStart(2,'0')).join('');
const meshes=[], mmap=[];
j.meshes.forEach(m=>{ const ids=[]; m.primitives.forEach(p=>{ const P=acc(p.attributes.POSITION), N=acc(p.attributes.NORMAL), I=acc(p.indices);
  const pos=new Float32Array(P.buf.buffer,P.buf.byteOffset,P.a.count*3), nor=new Float32Array(N.buf.buffer,N.buf.byteOffset,N.a.count*3);
  const mn=[1e9,1e9,1e9], mx=[-1e9,-1e9,-1e9]; for(let i=0;i<pos.length;i++){ mn[i%3]=Math.min(mn[i%3],pos[i]); mx[i%3]=Math.max(mx[i%3],pos[i]); }
  const q=new Int16Array(pos.length); for(let i=0;i<pos.length;i++){ const e=(mx[i%3]-mn[i%3])||1; q[i]=Math.round((pos[i]-mn[i%3])/e*65534-32767); }
  const n8=new Int8Array(nor.length); for(let i=0;i<nor.length;i++) n8[i]=Math.round(Math.max(-1,Math.min(1,nor[i]))*127);
  const idx=I.a.componentType===5123?new Uint16Array(I.buf.buffer,I.buf.byteOffset,I.a.count):Uint16Array.from(new Uint32Array(I.buf.buffer,I.buf.byteOffset,I.a.count));
  const mat=j.materials[p.material]; ids.push(meshes.length); meshes.push({m:mat.name,c:hex(mat.pbrMetallicRoughness.baseColorFactor),mn,ex:mx.map((v,i)=>v-mn[i]),p:b64(Buffer.from(q.buffer)),n:b64(Buffer.from(n8.buffer)),i:b64(Buffer.from(idx.buffer,idx.byteOffset,idx.byteLength))}); }); mmap.push(ids); });
const nodes=j.nodes.map((n,i)=>({name:n.name,mesh:n.mesh==null?[]:mmap[n.mesh],t:n.translation||[0,0,0],r:n.rotation||[0,0,0,1],s:n.scale||[1,1,1],ch:n.children||[]}));
const kids=new Set(); nodes.forEach(n=>n.ch.forEach(c=>kids.add(c)));
const out={roots:nodes.map((n,i)=>i).filter(i=>!kids.has(i)),nodes,meshes};
fs.writeFileSync(process.argv[3],JSON.stringify(out)); console.log('meshes',meshes.length,'nodes',nodes.length,'bytes',JSON.stringify(out).length);
