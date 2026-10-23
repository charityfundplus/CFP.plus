(function(root){
  'use strict';
  const M=root.HUB69Model,esc=M.esc;
  const source='https://github.com/charityfundplus/CFP.plus/issues/156';
  const countries=Object.freeze({all:'Tất cả quốc gia',vn:'Việt Nam',us:'Hoa Kỳ'});
  const roles=Object.freeze({all:'Tất cả vai trò',supplier:'Nhà cung cấp',buyer:'Đối tác mua',seller:'Đối tác bán'});
  // Presentation fixtures only: these keys are UI slugs, never Registry records or identity bindings.
  const samples=Object.freeze(['vn','us'].flatMap(country=>['supplier','buyer','seller'].map(role=>Object.freeze({
    key:country+'-'+role,country,role,name:roles[role]+' minh họa · '+countries[country],
    id:null,parent:null,did:null,canonical:null,verified:false
  }))));
  function route(hash){
    if(hash==='#app')return {view:'app'};
    if(hash==='#partners')return {view:'partners',country:'all',role:'all'};
    const partner=/^#partners\/(all|vn|us)\/(all|supplier|buyer|seller)$/.exec(hash);
    if(partner)return {view:'partners',country:partner[1],role:partner[2]};
    const reference=/^#reference\/(8682|8882)$/.exec(hash);
    if(reference)return {view:'reference',reference:reference[1]};
    return null;
  }
  function filterRoute(state,key,value){
    if(state.view!=='partners')return null;
    if(key==='partner-country'&&Object.hasOwn(countries,value))return '#partners/'+value+'/'+(state.role||'all');
    if(key==='partner-role'&&Object.hasOwn(roles,value))return '#partners/'+(state.country||'all')+'/'+value;
    return null;
  }
  const back=()=>'<nav class="catalog-crumbs" aria-label="Đường đi trong HUB 69"><a href="#home">HUB 69</a><span aria-hidden="true">/</span><a href="#chapters">5 Nhóm · 10 Chương</a></nav>';
  const sourceLink=(url,label)=>'<a class="btn" href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' ↗</a>';
  const action=(href,label)=>'<a class="btn" href="'+href+'">'+esc(label)+' →</a>';
  const gateway=()=>'<div class="profile-actions">'+action('#reference/8682','8682 · TMTC')+action('#reference/8882','8882 · TTTC')+'</div>';
  function referenceView(id){
    const label=id==='8682'?'TMTC':'TTTC';
    return back()+'<article class="panel"><span class="tag amber">PENDING REVIEW · Binding chưa xác minh</span><h2>'+id+' · '+label+'</h2><p>Tham chiếu theo giao việc CFP+. Chưa có nguồn Registry có thẩm quyền xác nhận Entity, Parent, DID và trang đích cho bản giao diện này.</p><dl class="profile-dl"><div><dt>Địa chỉ được đề cập</dt><dd><code>https://cfp.plus/'+id+'</code></dd></div><div><dt>Quyền vận hành</dt><dd>HOLD ACTIVATION · Không có giao dịch hoặc chuyển tiếp tự động.</dd></div><div><dt>Điều kiện mở liên kết</dt><dd>Custodian bàn giao hàng Registry, revision, quyền và kết quả đối chiếu nội dung tuyến.</dd></div></dl><div class="profile-actions">'+sourceLink(source,'Đọc giao việc gốc')+action('#partners','Danh mục đối tác')+action('#commerce','Danh mục sàn')+'</div></article>';
  }
  function select(id,key,label,options,value){
    return '<div class="catalog-filter"><label for="'+id+'">'+label+'</label><select id="'+id+'" data-catalog-filter="'+key+'">'+Object.entries(options).map(([k,v])=>'<option value="'+k+'"'+(k===value?' selected':'')+'>'+esc(v)+'</option>').join('')+'</select></div>';
  }
  function partnersView(state){
    const country=state.country||'all',role=state.role||'all';
    const rows=samples.filter(r=>(country==='all'||r.country===country)&&(role==='all'||r.role===role));
    return back()+'<div class="catalog-banner"><strong>Nhà cung cấp &amp; đối tác mua bán</strong><p>6 mẫu bố cục cho Việt Nam và Hoa Kỳ. Chờ hồ sơ doanh nghiệp, nguồn sản phẩm và Evidence hợp tác.</p></div><div class="directory-filters">'+select('partner-country','partner-country','Quốc gia',countries,country)+select('partner-role','partner-role','Vai trò',roles,role)+'</div><p role="status" class="catalog-count">'+rows.length+' mẫu minh họa · 0 đối tác được xác minh</p><div class="catalog-grid">'+rows.map(r=>'<article class="panel catalog-card"><span class="tag amber">MINH HỌA</span><h2>'+esc(r.name)+'</h2><p>Giới thiệu năng lực, danh mục hàng và nhu cầu hợp tác tại '+esc(countries[r.country])+'.</p><dl class="catalog-meta"><div><dt>Sản phẩm / Nhu cầu</dt><dd>Chờ danh mục có nguồn</dd></div><div><dt>Hàng tại quốc gia / Giao tại chỗ</dt><dd>Chưa có Evidence tồn kho và giao hàng</dd></div><div><dt>ID / Parent / DID / Canonical</dt><dd>Chưa gắn định danh</dd></div></dl>'+action('#hstdn/'+r.country,'HSTDN '+countries[r.country])+'</article>').join('')+'</div><article class="panel"><h2>Tiếp tục theo nhu cầu</h2><p>Mở hồ sơ HSTDN, đối chiếu nguồn rồi chuyển yêu cầu sang đầu mối được phê duyệt.</p>'+gateway()+'</article>';
  }
  const summaries=Object.freeze([
    ['Nền tảng chung','Nguyên tắc, nguồn, định danh và cách tham gia CFP+.'],
    ['Sự Sống','Tổ chức nội dung và sáng kiến phục vụ Sự Sống theo nguồn được review.'],
    ['Con Người','Tra cứu hồ sơ và năng lực; quyền riêng tư theo Human Governance.'],
    ['Bộ Tam và Ba Quỹ','Đọc định hướng, nguồn và Evidence của các quỹ; chờ hồ sơ được bàn giao.'],
    ['Tôn Giáo và Tín Ngưỡng','Tổ chức nguồn theo phạm vi, giữ rõ bối cảnh và nguồn gốc.'],
    ['Chi Hội · Cộng đồng','Khung hồ sơ Chi Hội: giới thiệu, địa bàn, người phụ trách, chương trình, nhu cầu và Evidence.'],
    ['SI 🤖 AI 🤖 Robot 🤖 Siêu Phần Mềm & Công Nghệ','Tra cứu nhà phát triển, SI/AI/Robot, đào tạo và các nguồn công nghệ.'],
    ['HSTDN · Doanh nghiệp','Đi từ quốc gia đến hồ sơ, sản phẩm, nhà cung cấp và nhu cầu hợp tác.'],
    ['Tổ Chức và Quỹ','Hồ sơ tổ chức, phạm vi hoạt động và nguồn xác nhận.'],
    ['Quốc gia · Vùng lãnh thổ','Duyệt bối cảnh Việt Nam và Hoa Kỳ; bối cảnh trình bày chưa cấp binding quốc gia.']
  ]);
  function chapterOverview(id){
    const n=Number(id);if(!Number.isInteger(n)||n<0||n>9)return '';
    const [title,description]=summaries[n];
    const actions=n===5?sourceLink('https://app.notion.com/p/3fecaac9a557815ca9f6fbf60844d50b?pvs=204','Nguồn Chi Hội · cần quyền Notion')+action('#template','Khung hồ sơ chung'):
      n===6?action('#id','Danh mục SI/AI theo nguồn')+action('#technology','Nguồn công nghệ')+action('#training','Đào tạo'):
      n===7||n===9?action('#hstdn/vn','HSTDN Việt Nam')+action('#hstdn/us','HSTDN Hoa Kỳ')+action('#partners','Nhà cung cấp & đối tác'):action('#template','Khung hồ sơ chung');
    return '<div class="chapter-overview"><h3>'+esc(title)+'</h3><p>'+esc(description)+'</p><div class="profile-actions">'+actions+'</div>'+(n===5?'<dl class="profile-dl"><div><dt>Chi Hội thực tế</dt><dd>Chưa có danh mục đã xác minh trong nguồn hiện tại.</dd></div><div><dt>Nhu cầu cộng đồng</dt><dd>Chờ mục tiêu, địa bàn, người phụ trách và Evidence.</dd></div></dl>':'')+'</div>';
  }
  function appView({coreMode=false,coreState=null}={}){
    const status=coreMode?(coreState?.phase==='ready'?'Đã đọc Core trong phiên hiện hữu':'Core chưa sẵn sàng'):'Review offline · Core chưa kết nối';
    return back()+'<div class="catalog-banner"><strong>App shell · Bản review trên trình duyệt</strong><p>Cùng màn hình, Design System và lớp đọc Core với Website. Có gói PWA để review trên HTTPS riêng tư hoặc localhost. Chưa có App native. Chưa nghiệm thu cài đặt trên thiết bị thật.</p></div><div class="app-shell-preview"><article class="panel"><span class="eyebrow">CFP+ · HUB 69</span><h2>Điều bạn cần, từ một hub.</h2><p>Chọn công việc để đi tới màn hình dùng chung.</p><div class="app-shortcuts">'+action('#id','Tra cứu ID')+action('#chapter/5','Chi Hội')+action('#technology','SI · AI · Công nghệ')+action('#hstdn','HSTDN')+action('#partners','Nhà cung cấp')+action('#chapter/9','Quốc gia')+'</div></article><article class="panel"><h2>Phiên &amp; kết nối</h2><p role="status">'+esc(status)+'</p>'+(coreMode?action('/p2','Đăng nhập tại Văn phòng Core'):'<button class="btn" disabled>Đăng nhập · Chờ môi trường Core được duyệt</button>')+'<p class="muted">Đăng nhập do Core hiện hữu xử lý. Bản review này không thu mật khẩu.</p><h3>Điều kiện dùng App</h3><p>HTTPS riêng tư, cùng origin với Core, tài khoản thử và Evidence trên thiết bị thật. Trên iPhone: Safari → Chia sẻ → Thêm vào Màn hình chính. Trên Android hoặc máy tính: dùng mục Cài đặt của trình duyệt nếu có. Khi mất kết nối, chỉ hiện hướng dẫn kết nối lại; không đăng nhập ngoại tuyến.</p></article></div>';
  }
  function view(state,context){return state.view==='partners'?partnersView(state):state.view==='reference'?referenceView(state.reference):state.view==='app'?appView(context):'';}
  root.HUB69Workspace=Object.freeze({samples,countries,roles,route,filterRoute,chapterOverview,referenceView,partnersView,appView,view});
})(typeof window!=='undefined'?window:globalThis);
