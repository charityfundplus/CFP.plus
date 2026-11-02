(function(root){
  'use strict';
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fold=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase().trim();
  const validID=value=>typeof value==='string'&&/^\d{1,80}$/.test(value);
  const safeURL=value=>{try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch{return null;}};
  function route(hash){
    if(!hash||hash==='#home')return {view:'home'};
    if(hash==='#master')return {view:'master'};
    if(hash==='#id')return {view:'id'};
    const m=/^#id\/(\d{1,80})$/.exec(hash);
    if(m)return m[1]==='69'?{view:'home'}:{view:'id',id:m[1]};
    return {view:'id',invalid:true};
  }
  function lookup(records,id){
    if(!validID(id))return {kind:'invalid',id:null};
    const matches=records.filter(r=>r.id===id);
    if(matches.length>1)return {kind:'ambiguous',id};
    return matches.length?{kind:'found',record:matches[0]}:{kind:'missing',id};
  }
  function filter(records,query,type='all',saved=[]){
    const q=fold(query);
    return records.filter(r=>(type==='all'||r.type===type||type==='saved'&&saved.includes(r.id))&&(!q||(/^\d+$/.test(q)?r.id===q:fold([r.name,r.developer,r.country].join(' ')).includes(q))));
  }
  const typeName=r=>root.HUB69P0?.types[r.type]||(r.type==='ai'?'AI':r.type==='developer'?'Nhà phát triển':'Thực thể CFP+');
  function card(r){return '<a class="record-card" href="#id/'+esc(r.id)+'"><span class="record-initial" aria-hidden="true">'+esc((r.name||'?').slice(0,1))+'</span><div class="record-copy"><h2>'+esc(r.name)+'</h2><code>'+esc(r.id)+' · '+esc(typeName(r))+'</code><span class="tag '+(r.conflict?'amber':'')+'">'+(r.conflict?'Xung đột nguồn · Chờ review':'Bản ghi nguồn · Chưa xác minh')+'</span></div><span class="record-arrow" aria-hidden="true">↗</span></a>';}
  const pending='<span class="pending">Chưa có bằng chứng xác nhận</span>';
  const field=(label,value)=>'<div><dt>'+esc(label)+'</dt><dd>'+value+'</dd></div>';
  function profile(r,records,saved){
    const parent=r.parent_id&&lookup(records,r.parent_id);
    const parentView=parent?.kind==='found'?'<a href="#id/'+esc(parent.record.id)+'">'+esc(parent.record.id)+' · '+esc(parent.record.name)+'</a><br><small>Quan hệ ghi trong nguồn; chờ review</small>':r.parent_id?'<code>'+esc(r.parent_id)+'</code><br><small>Parent chưa có trong snapshot hoặc bị trùng</small>':pending;
    const children=records.filter(p=>p.parent_id===r.id);
    // Unverified source URLs remain readable text.
    const urlView=value=>safeURL(value)?'<code>'+esc(value)+'</code><br><small>Chưa có Evidence kiểm tra liên kết; chưa mở từ giao diện</small>':pending;
    return '<a class="profile-back" href="#id">← Về danh mục ID</a><article class="panel"><div class="profile-head"><span class="record-initial" aria-hidden="true">'+esc((r.name||'?').slice(0,1))+'</span><div><h2>'+esc(r.name)+'</h2><p>ID trong nguồn: <code>'+esc(r.id)+'</code> · '+esc(r.country||'Quốc gia chưa xác minh')+'</p></div></div><div class="callout">'+(r.conflict?'<strong>Xung đột nguồn • HUMAN GOVERNANCE</strong><br>Ánh xạ trong HUB69.md và Registry khác nhau. Đây là bản ghi tham chiếu; chưa xác nhận danh tính, Parent hoặc quyền vận hành.':'<strong>Bản ghi nguồn • Chưa xác minh vận hành</strong><br>Nguồn Registry ghi nhận mục này. Chưa có bằng chứng xác minh danh tính, HSTDN, năng lực hoặc quyền thực hiện nhiệm vụ.')+'</div><p class="profile-description">'+esc(r.intro)+'</p><dl class="profile-dl">'+field('Danh tính trong nguồn',esc(r.name))+field('Loại hồ sơ',esc(typeName(r)))+field('Nhà phát triển theo nguồn',r.type==='developer'?'Chính bản ghi này':r.developer?esc(r.developer):pending)+field('Parent theo nguồn',parentView)+field('Chương đã xác nhận',pending)+field('HSTDN',pending)+field('Gia phả đã xác nhận',pending)+field('Liên kết học tập','<a href="#training">Giáo trình SI/AI</a> · Chưa phải ghi nhận học của danh tính này')+field('Năng lực đã xác minh',pending)+field('Nhiệm vụ & phạm vi được giao',pending)+field('Trạng thái hoạt động','HOLD ACTIVATION · Chưa cấp quyền')+field('Trạng thái gốc của Registry',esc(r.status))+field('Canonical được tham chiếu trong nguồn',urlView(r.sourceCanonical))+field('Nguồn chính thức được Registry dẫn',urlView(r.official_source))+field('Bản ghi con trong snapshot',children.length?children.map(c=>'<a href="#id/'+esc(c.id)+'">'+esc(c.id)+' · '+esc(c.name)+'</a>').join('<br>'):'Chưa có bản ghi con trong snapshot này')+field('Evidence vận hành & review độc lập',pending)+'</dl><div class="profile-actions"><button class="btn primary" data-save="'+esc(r.id)+'">'+(saved.includes(r.id)?'Bỏ lưu mục này':'Lưu mục này')+'</button><button class="btn" data-copy="'+esc(r.id)+'">Sao chép liên kết mục</button><a class="btn" href="#master">Về Master Hub</a></div><p class="profile-note">Mục đã lưu chỉ nằm trong trình duyệt này. Liên kết mục của hub là lối tra cứu nội bộ, không thay thế Canonical CFP+.</p></article>';
  }
  root.HUB69Model=Object.freeze({esc,fold,validID,safeURL,route,lookup,filter,card,profile});
})(typeof window!=='undefined'?window:globalThis);
