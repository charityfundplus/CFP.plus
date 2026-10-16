(function(root){
  'use strict';
  const M=root.HUB69Model, esc=M.esc;
  const source='https://github.com/charityfundplus/CFP.plus/blob/835616308111f6851c0387fa9f5eda60c9ffa624/registry/ai-entity-registry.json';
  const types=Object.freeze({pair:'Siêu Bộ Đôi',super_pair:'Siêu Bộ Đôi',software:'Siêu Phần Mềm',super_software:'Siêu Phần Mềm',si:'SI',ai:'AI',robot:'Robot',developer:'Nhà phát triển',hstdn:'HSTDN',enterprise:'Doanh nghiệp',country:'Quốc gia',organization:'Tổ chức',entity:'Thực thể CFP+'});
  const groups=Object.freeze([
    {id:'V',name:'Điều phối tổng thể',chapters:[]},
    {id:'000',name:'Nền tảng',chapters:['0']},
    {id:'135',name:'Sự Sống · Ba Quỹ · Cộng Đồng',chapters:['1','3','5']},
    {id:'246',name:'Con Người · Tôn Giáo · Công Nghệ',chapters:['2','4','6']},
    {id:'789',name:'Doanh Nghiệp · Tổ Chức · Quốc Gia',chapters:['7','8','9']}
  ]);
  const names=['Nền Tảng','Sự Sống','Con Người','Bộ Tam và Ba Quỹ','Tôn Giáo và Tín Ngưỡng','Bộ Ngũ và Cộng Đồng','SI · AI · Robot · Siêu Phần Mềm','Doanh Nghiệp','Tổ Chức và Quỹ','Quốc Gia và Vùng Lãnh Thổ'];
  const chapters=Object.freeze(names.map((name,i)=>({id:String(i),name,group:groups.find(g=>g.chapters.includes(String(i))).id})));
  function route(hash){
    if(hash==='#chapters')return {view:'chapters'};
    if(hash==='#vaults')return {view:'vaults'};
    if(hash==='#openai')return {view:'openai'};
    if(hash==='#template')return {view:'template'};
    const group=/^#group\/(V|000|135|246|789)$/.exec(hash);
    if(group)return {view:'chapters',group:group[1]};
    const chapter=/^#chapter\/([0-9])$/.exec(hash);
    if(chapter)return {view:'chapters',chapter:chapter[1]};
    return M.route(hash);
  }
  function validate(records){
    const issues=[],byID=new Map();
    for(const r of records){
      if(!M.validID(r.id)){issues.push({code:'INVALID_ID',id:r.id});continue;}
      if(byID.has(r.id))issues.push({code:'DUPLICATE_ID',id:r.id});else byID.set(r.id,r);
    }
    for(const r of records){
      if(r.parent_id&&!byID.has(r.parent_id))issues.push({code:'PARENT_MISSING',id:r.id,parent:r.parent_id});
      if(r.chapter!=null&&r.chapter!==r.id?.[0])issues.push({code:'CHAPTER_CONFLICT',id:r.id});
      if(r.parent_id&&byID.has(r.parent_id)&&r.id[0]!==r.parent_id[0])issues.push({code:'CROSS_CHAPTER_PARENT',id:r.id,parent:r.parent_id});
      const seen=new Set([r.id]);let current=r;
      while(current?.parent_id&&byID.has(current.parent_id)){
        if(seen.has(current.parent_id)){issues.push({code:'PARENT_CYCLE',id:r.id});break;}
        seen.add(current.parent_id);current=byID.get(current.parent_id);
      }
    }
    return issues;
  }
  function verifiedLink(link){
    if(!link||link.verified!==true||link.visibility!=='public'||!/^\d{4}-\d{2}-\d{2}T/.test(link.checkedAt||'')||!Number.isFinite(Date.parse(link.checkedAt))||!M.safeURL(link.evidenceURL))return null;
    return M.safeURL(link.url);
  }
  function linkView(link,label){const url=verifiedLink(link);return url?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label||url)+' ↗</a>':'<span class="pending">Chưa có liên kết được xác minh</span>';}
  function children(records,id){return records.filter(r=>r.parent_id===id);}
  function treeNode(r,records,seen=new Set(),depth=0){
    if(seen.has(r.id)||depth>20)return '<li class="tree-warning">Chuỗi Parent cần review: '+esc(r.id)+'</li>';
    const path=new Set(seen);path.add(r.id);
    const descendants=children(records,r.id);
    const row='<a href="#id/'+esc(r.id)+'"><code>'+esc(r.id)+'</code> '+esc(r.name)+'</a><small>'+esc(types[r.type]||'Thực thể CFP+')+' · '+(r.parent_id?'Parent nguồn: '+esc(r.parent_id):'Parent chưa có trong nguồn')+'</small>';
    return '<li>'+(descendants.length?'<details open><summary>'+row+'</summary><ul>'+descendants.map(c=>treeNode(c,records,path,depth+1)).join('')+'</ul></details>':row)+'</li>';
  }
  function chapterView(chapter,records){
    const rows=records.filter(r=>M.validID(r.id)&&r.id[0]===chapter.id);
    const ids=new Set(rows.map(r=>r.id));
    const roots=rows.filter(r=>!r.parent_id||!ids.has(r.parent_id));
    const seen=new Set();const visit=r=>{if(seen.has(r.id))return;seen.add(r.id);children(rows,r.id).forEach(visit);};roots.forEach(visit);
    const unresolved=rows.filter(r=>!seen.has(r.id));
    return '<article class="panel chapter-panel" id="chapter-'+chapter.id+'"><div class="section-top"><h2><a href="#chapter/'+chapter.id+'">Chương '+chapter.id+' · '+esc(chapter.name)+'</a></h2><span class="tag">'+rows.length+' bản ghi nguồn</span></div><p class="muted">Nhóm '+chapter.group+' · Chương được phân loại theo chữ số đầu; không tạo quan hệ Parent mới.</p>'+(roots.length?'<ul class="id-tree">'+roots.map(r=>treeNode(r,rows)).join('')+'</ul>':'<p class="empty">Chưa có bản ghi con đủ nguồn trong snapshot này.</p>')+(unresolved.length?'<p class="callout">'+unresolved.length+' bản ghi có vòng lặp hoặc chưa dựng được cây; xem lại Parent. Không tự sửa lineage.</p>':'')+'</article>';
  }
  function mapView(records,state={}){
    const selected=state.chapter?chapters.filter(c=>c.id===state.chapter):state.group?chapters.filter(c=>c.group===state.group):chapters;
    const nav='<div class="group-nav" aria-label="5 nhóm">'+groups.map(g=>'<a class="btn '+(state.group===g.id?'primary':'')+'" href="#group/'+g.id+'"'+(state.group===g.id?' aria-current="page"':'')+'><strong>'+g.id+'</strong><span>'+esc(g.name)+'</span></a>').join('')+'</div>';
    const chapterNav='<div class="chapter-nav" aria-label="10 chương">'+chapters.map(c=>'<a class="btn" href="#chapter/'+c.id+'"'+(state.chapter===c.id?' aria-current="page"':'')+'>Chương '+c.id+'</a>').join('')+'</div>';
    return nav+chapterNav+'<p class="muted">V và 000 là nhóm điều hướng. ID 0 và ID 000 vẫn là hai chuỗi khác nhau. Cây hiển thị Chương → bản ghi Con → bản ghi Cháu khi có Parent trong nguồn; các nhóm không cấp ID.</p>'+(state.group==='V'?'<article class="panel"><h2>V · Điều phối tổng thể</h2><p>HUB 69 giữ vai trò cổng chính. Các quyết định dữ liệu và vận hành thuộc Human Governance.</p><div class="profile-actions"><a class="btn" href="#master">Master Hub</a><a class="btn" href="#vaults">6 Kho</a><a class="btn" href="#chapters">Toàn bộ 10 chương</a></div></article>':selected.map(c=>chapterView(c,records)).join(''));
  }
  function projectsView(record){
    const pair=['pair','super_pair'].includes(record.type);
    const projects=Array.isArray(record.chatgptProjects)?record.chatgptProjects.filter(p=>p&&p.visibility==='public'):[];
    if(!pair)return '';
    return '<section class="project-section"><h3>Làm Dự Án tại ChatGPT</h3><p class="muted">Dự án dùng ID '+esc(record.id)+' và Link Mẫu hiện hữu của Siêu Bộ Đôi.</p>'+(projects.length?projects.map(p=>'<dl class="profile-dl">'+field('Tên dự án',esc(p.name||'Chưa có tên'))+field('Phạm vi công việc',esc(p.scope||'Chưa khai báo'))+field('Trạng thái',esc(p.status||'PENDING'))+field('Liên kết thực tế',linkView(p.link))+ '</dl>').join(''):'<p class="empty">Tên dự án: chưa khai báo · Phạm vi: chưa khai báo · Trạng thái: chờ dữ liệu. Chưa có liên kết dự án được xác minh.</p>')+'</section>';
  }
  const field=(label,value)=>'<div><dt>'+esc(label)+'</dt><dd>'+value+'</dd></div>';
  function profileExtra(r,records){
    const evidence=Array.isArray(r.evidence)?r.evidence:[];
    const pinned=r.provenance?.registryURL===source&&r.provenance?.sourceRevision==='835616308111f6851c0387fa9f5eda60c9ffa624';
    return '<section class="panel"><h3>Nguồn gốc &amp; Evidence</h3><dl class="profile-dl">'+field('Loại hồ sơ',esc(types[r.type]||'Thực thể CFP+'))+field('Chương theo chữ số đầu',M.validID(r.id)?'<a href="#chapter/'+r.id[0]+'">Chương '+r.id[0]+'</a>':'Chưa định vị')+field('Nguồn Registry',pinned?'<a href="'+source+'" target="_blank" rel="noopener noreferrer">Bản nguồn 8356163 ↗</a>':'Chưa có provenance Registry được bàn giao')+field('Evidence được bàn giao',evidence.length?evidence.map(e=>linkView(e.link,e.title)).join('<br>'):'Chưa có Evidence xác minh vận hành')+field('DID theo nguồn',esc(r.did||'Chưa được bàn giao'))+field('Trạng thái xác minh',r.identityVerified===true?'Theo nguồn được bàn giao; cần đối chiếu Evidence':'CHƯA XÁC MINH')+'</dl>'+projectsView(r)+'</section>';
  }
  function templateView(type='pair'){
    return '<article class="panel"><h2>Link Mẫu Chung</h2><p class="muted">Khung trình bày áp dụng cho các loại thực thể. Không tạo hồ sơ hoặc cấp ID. Mỗi hồ sơ thật giữ ID/Parent/Evidence của Registry.</p><label for="template-type">Xem cấu trúc cho </label><select id="template-type">'+Object.entries(types).filter(([k])=>!['super_pair','super_software'].includes(k)).map(([k,v])=>'<option value="'+k+'"'+(type===k?' selected':'')+'>'+esc(v)+'</option>').join('')+'</select><dl class="profile-dl">'+['Tên hồ sơ','Canonical ID số','Parent','Nhà phát triển','Quốc gia / tổ chức','HSTDN','Nguồn gốc / DID','Evidence','Trạng thái xác minh'].map(l=>field(l,'Chờ bản ghi có nguồn')).join('')+'</dl>'+(type==='pair'?'<section class="project-section"><h3>Làm Dự Án tại ChatGPT</h3><dl class="profile-dl">'+['Tên dự án','Phạm vi công việc','Trạng thái','Liên kết thực tế'].map(l=>field(l,'Chưa được bàn giao')).join('')+'</dl><p class="muted">Sử dụng Canonical ID và Link Mẫu của Siêu Bộ Đôi. Liên kết dự án chỉ xuất hiện sau kiểm chứng; không tự tạo dự án hoặc URL.</p></section>':'')+'</article>';
  }
  function openaiView(records){
    const developer=records.find(r=>r.id==='69118'&&r.name==='OpenAI'&&r.type==='developer');
    const chatgpt=records.find(r=>r.id==='691181'&&r.name==='ChatGPT'&&r.parent_id==='69118');
    return '<div class="callout"><strong>HSTDN OpenAI mẫu · Chờ Registry HSTDN</strong><br>Đây là góc nhìn của Link Mẫu hiện hữu, chưa phải hồ sơ HSTDN đã được cấp ID. Không suy ID doanh nghiệp từ ID nhà phát triển. Quan hệ hợp tác CFP+–OpenAI: chưa có Evidence xác nhận.</div><div class="master-grid"><article class="panel"><span class="eyebrow">NHÀ PHÁT TRIỂN</span><h2>OpenAI</h2><p>'+ (developer?'<a class="text-link" href="#id/'+developer.id+'">'+developer.id+' · Mở bản ghi nhà phát triển</a>':'Chưa có nguồn nhà phát triển')+'</p><p class="muted">Nguồn Registry bảo toàn ID 69118. Xung đột nhánh Hoa Kỳ còn chờ Human Governance.</p></article><article class="panel"><span class="eyebrow">SẢN PHẨM / AI THEO NGUỒN</span><h2>ChatGPT</h2><p>'+(chatgpt?'<a class="text-link" href="#id/'+chatgpt.id+'">'+chatgpt.id+' · Parent '+chatgpt.parent_id+'</a>':'Chưa có bản ghi nguồn phù hợp')+'</p><p class="muted">Bản ghi sản phẩm/AI được trình bày riêng với nhà phát triển và HSTDN.</p></article></div><article class="panel"><h2>SI/AI liên quan theo Parent nguồn</h2><div class="record-grid">'+(developer?children(records,developer.id).map(M.card).join(''):'')+'</div><dl class="profile-dl">'+field('HSTDN Canonical ID','Chờ Codex 1 / Registry được xác minh')+field('SI, Siêu Bộ Đôi, Robot liên quan','Chưa có bản ghi xác nhận trong snapshot')+field('Quan hệ hợp tác đã xác thực','Chưa có Evidence được bàn giao')+field('Nguồn','<a href="'+source+'" target="_blank" rel="noopener noreferrer">Registry gốc ↗</a>')+'</dl></article>';
  }
  const vaults=Object.freeze([
    {key:'quantum',name:'Kho Lượng Tử',phase:'RESEARCH',status:'Nghiên cứu',error:'Chưa có Evidence hạ tầng lượng tử vận hành',lastSync:null},
    {key:'cloud',name:'Kho Đám Mây',phase:'PENDING',status:'Chưa xác minh kết nối',error:'Thiếu receipt kết nối và đồng bộ',lastSync:null},
    {key:'github',name:'Kho GitHub',phase:'SNAPSHOT',status:'Đọc được snapshot',error:'Chưa có đồng bộ runtime; snapshot không chứng minh đồng bộ 6 Kho',lastSync:null,evidenceURL:source},
    {key:'notion',name:'Kho Notion',phase:'PENDING',status:'Chưa xác minh kết nối',error:'Chưa có readback hoặc receipt trong đợt bàn giao này',lastSync:null},
    {key:'google',name:'Kho Google',phase:'PENDING',status:'Chưa xác minh kết nối',error:'Chưa có bằng chứng truy cập hoặc đồng bộ',lastSync:null},
    {key:'website',name:'Kho Website CFP+',phase:'REVIEW',status:'Giao diện đang review',error:'Chưa deploy; chưa có URL HTTPS hoạt động',lastSync:null}
  ]);
  function vaultsView(){return '<div class="callout">Trạng thái theo Evidence được bàn giao. Không có phép đo trực tiếp hoặc kết nối runtime trong giao diện này. Thời điểm đồng bộ chưa có sẽ để trống.</div><div class="vault-grid">'+vaults.map(v=>'<article class="panel"><div class="section-top"><h2>'+esc(v.name)+'</h2><span class="tag amber">'+esc(v.phase)+'</span></div><p>'+esc(v.status)+'</p><dl class="profile-dl">'+field('Đồng bộ gần nhất',v.lastSync||'Chưa có receipt')+field('Lỗi / dữ liệu còn thiếu',esc(v.error))+field('Evidence',v.evidenceURL?'<a href="'+esc(v.evidenceURL)+'" target="_blank" rel="noopener noreferrer">Snapshot nguồn ↗</a>':'Chưa có Evidence kết nối')+'</dl></article>').join('')+'</div>';}
  root.HUB69P0=Object.freeze({types,groups,chapters,route,validate,verifiedLink,linkView,children,mapView,chapterView,projectsView,profileExtra,templateView,openaiView,vaults,vaultsView});
})(typeof window!=='undefined'?window:globalThis);
