// The admin page, served at /admin. The key is kept in this browser only and sent as a header.
export const ADMIN_HTML = `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>랭킹 관리</title><style>
body{margin:0;font:14px/1.4 system-ui,sans-serif;background:#f6f1e7;color:#3a2416}
header{position:sticky;top:0;background:#3a2416;color:#fffbef;padding:10px 14px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
header input,header select,header button{font:inherit;padding:5px 8px;border-radius:6px;border:0}
main{padding:12px}table{width:100%;border-collapse:collapse;background:#fff}
th,td{padding:6px 8px;border-bottom:1px solid #eadfcc;text-align:left;vertical-align:top}th{background:#efe5d3;position:sticky;top:48px}
td.n{text-align:right;font-variant-numeric:tabular-nums}.why{color:#b0101a;font-size:12px}
button.a{padding:4px 8px;margin:2px;border:1px solid #3a2416;border-radius:6px;background:#fffbef;cursor:pointer}
button.ok{background:#2f9e5b;color:#fff;border-color:#2f9e5b}button.del{background:#c0141c;color:#fff;border-color:#c0141c}
.msg{padding:8px 0;color:#7a5a40}
</style></head><body>
<header><b>🏆 랭킹 관리</b>
<input id="key" type="password" placeholder="관리자 키" size="14">
<select id="status"><option value="review">검토 대기</option><option value="ok">공개 중</option><option value="rejected">자동 거절</option><option value="deleted">삭제됨</option></select>
<button id="load">불러오기</button></header>
<main><div class="msg" id="msg">관리자 키를 넣고 불러오기를 누르세요.</div><table id="t" hidden><thead><tr>
<th>닉네임</th><th>X 아이디</th><th>모드</th><th class="n">점수</th><th class="n">시간(초)</th><th class="n">먹은 알</th><th class="n">상자</th><th class="n">콤보</th><th>단계</th><th>사유</th><th>시각</th><th>처리</th></tr></thead><tbody></tbody></table></main>
<script>
const $=id=>document.getElementById(id); try{ $('key').value=localStorage.getItem('rank-admin-key')||''; }catch(e){}
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path,opt){ const r=await fetch(path,Object.assign({headers:{'content-type':'application/json','x-admin-key':$('key').value}},opt||{})); if(!r.ok) throw new Error(r.status+' '+(await r.text())); return r.json(); }
async function load(){ try{ localStorage.setItem('rank-admin-key',$('key').value); }catch(e){}
  const q='?status='+$('status').value;
  try{ const d=await api('/api/admin/scores'+q); const tb=$('t').querySelector('tbody'); tb.innerHTML='';
    d.rows.forEach(r=>{ const tr=document.createElement('tr'); const stage=r.nightmare?'폭주':r.rage?'화남':'-';
      tr.innerHTML='<td>'+esc(r.nick||'')+'</td><td><a href="https://x.com/'+esc(r.xid)+'" target="_blank" rel="noopener">@'+esc(r.xid)+'</a></td><td>'+r.mode+'</td><td class="n">'+r.score.toLocaleString()+'</td><td class="n">'+r.elapsed.toFixed(1)+'</td><td class="n">'+r.eaten+'</td><td class="n">'+r.boxes+'</td><td class="n">'+r.combo+'</td><td>'+stage+'</td><td class="why">'+esc(r.reason||'')+'</td><td>'+new Date(r.created).toLocaleString()+'</td>'
        +'<td><button class="a ok" data-s="ok">공개</button><button class="a" data-s="review">보류</button><button class="a del" data-s="deleted">삭제</button></td>';
      tr.querySelectorAll('button').forEach(b=>b.onclick=async()=>{ await api('/api/admin/scores/'+r.id,{method:'POST',body:JSON.stringify({status:b.dataset.s})}); tr.remove(); });
      tb.appendChild(tr); });
    $('t').hidden=!d.rows.length; $('msg').textContent=d.rows.length?d.rows.length+'건':'해당하는 기록이 없어요.'; }
  catch(e){ $('msg').textContent='불러오지 못했어요: '+e.message; $('t').hidden=true; } }
$('load').onclick=load; $('status').onchange=load;
</script></body></html>`;
