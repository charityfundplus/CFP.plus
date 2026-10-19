(function(root){
  'use strict';
  const M=root.HUB69Model,esc=M.esc;
  const source=Object.freeze({url:'https://app.notion.com/p/3fecaac9a5578132a41fec206bfb0552',lastEdited:'2026-10-19T20:08:51.750Z',date:'2026-10-19',kind:'Bàn giao GrokSI qua Notion; ghi chú nghiên cứu, chưa phải dữ liệu API hoặc nguồn gốc độc lập'});
  const assignment='https://github.com/charityfundplus/CFP.plus/pull/157#issuecomment-6276298491';
  const contexts=Object.freeze({vn:'Việt Nam',us:'Hoa Kỳ',global:'Quốc gia / thị trường khác'});
  const subjects=Object.freeze([
    Object.freeze({key:'starlink',name:'Starlink',scope:'Pháp nhân được báo cáo, thương hiệu và dịch vụ kết nối cần đối chiếu riêng'}),
    Object.freeze({key:'spacex',name:'SpaceX',scope:'Pháp nhân, cổ phần và quyền biểu quyết cần nguồn gốc theo từng trường'}),
    Object.freeze({key:'tesla',name:'Tesla / Optimus',scope:'Phân biệt chủ thể Tesla và sản phẩm Optimus; chưa xác nhận hàng đang bán'}),
    Object.freeze({key:'xai',name:'xAI / Grok',scope:'Tên pháp lý, tên thương mại và sản phẩm/API phải được đối chiếu riêng'}),
    Object.freeze({key:'x',name:'X',scope:'Chưa suy quan hệ sở hữu, Parent hoặc pháp nhân từ tên thương hiệu'}),
    Object.freeze({key:'neuralink',name:'Neuralink',scope:'Chờ nguồn gốc về chủ thể và nghiên cứu lâm sàng; chưa đưa kết luận y tế'}),
    Object.freeze({key:'boring',name:'The Boring Company / Loop',scope:'Tách doanh nghiệp, hệ thống Loop và tiến độ từng dự án'})
  ]);
  const binding=Object.freeze({id:null,parent:null,did:null,canonical:null,countryID:null});
  const knownSubject=key=>subjects.find(s=>s.key===key);
  function route(hash){
    const match=/^#hstdn\/(vn|us|global)(?:\/([a-z]+))?$/.exec(hash);
    if(!match||match[2]&&!knownSubject(match[2]))return null;
    return {view:'hstdn',country:match[1],...(match[2]?{subject:match[2]}:{})};
  }
  function filterRoute(state,key,value){
    if(state.view!=='hstdn')return null;
    if(key==='subject'&&knownSubject(value))return '#hstdn/'+(Object.hasOwn(contexts,state.country)?state.country:'vn')+'/'+value;
    if(key==='country'&&Object.hasOwn(contexts,value)&&knownSubject(state.subject))return '#hstdn/'+value+'/'+state.subject;
    return null;
  }
  // Local review presentation only, never an API envelope or Registry record.
  // No verified state can be granted from source labels, URLs or client booleans.
  const statusOf=field=>field.blocker||!field.value?'BLOCKED':'NOT VERIFIED';
  function item(key,label,value,excerpt,blocker=null,eventDate=null){
    return {key,label,value,sourceURL:source.url,sourceDate:source.date,sourceKind:source.kind,excerpt,blocker,eventDate,originalURL:null,reviewReceipt:null};
  }
  function fieldsFor(subject,country){
    if(!knownSubject(subject)||!Object.hasOwn(contexts,country))return [];
    const rows=[
      item('entity_type','Pháp nhân / thương hiệu / segment / sản phẩm',null,'Phân biệt công ty, công ty con, thương hiệu, sản phẩm và segment; không gán quan hệ sở hữu theo suy diễn.','Chờ mapping phân loại Codex 1 và nguồn pháp lý; nhãn điều hướng không phải loại thực thể được duyệt.'),
      item('legal_name','Tên pháp lý',subject==='starlink'&&country==='vn'?'CÔNG TY TNHH STARLINK SERVICES VIỆT NAM — tên do GrokSI báo cáo':null,subject==='starlink'&&country==='vn'?'GrokSI cung cấp tên CÔNG TY TNHH STARLINK SERVICES VIỆT NAM':'Dữ liệu cần kiểm chứng riêng', 'Chưa có hồ sơ đăng ký gốc được bàn giao cho trường này.'),
      item('trade_name','Tên tham chiếu / thương hiệu',knownSubject(subject).name,'Tesla, SpaceX, Starlink, xAI/Grok, X, Neuralink, The Boring Company.'),
      item('corporate_relationship','Sở hữu doanh nghiệp / quan hệ pháp lý',null,'không gán quan hệ sở hữu theo suy diễn.','Cần nguồn gốc; không chuyển quan hệ doanh nghiệp thành Parent Registry.'),
      item('official_website','Website chính thức của chủ thể pháp lý',null,'Mỗi kết luận phải có URL nguồn gốc, ngày, trích đoạn và trạng thái theo trường dữ liệu','Chưa có URL gốc gắn đúng chủ thể pháp lý trong gói review này.')
    ];
    if(subject==='starlink'){
      rows.push(item('license','Giấy phép theo thị trường',country==='vn'?'57/GP-CVT — số do GrokSI báo cáo':null,'Giấy phép được báo cáo: 57/GP-CVT ngày 03/03/2026.','Cần cơ quan cấp, bản gốc và phạm vi hiệu lực; chưa có kết luận VERIFIED.',country==='vn'?'2026-03-03 — ngày do nguồn báo cáo':null));
      rows.push(item('pilot','Pilot / khả năng cung ứng',country==='vn'?'Bàn giao đề cập pilot; chưa xác minh số lượng hoặc khả năng cung ứng':null,'Pilot được báo cáo: 4 gateway, tối đa 600.000 terminal đến 2030.'));
    }
    if(subject==='spacex')rows.push(item('ownership','Cổ phần / beneficial ownership / quyền biểu quyết','Bàn giao có số liệu; chưa đối chiếu filing gốc','Cần accession number, filing URL, mẫu số và lớp cổ phần.','Thiếu accession, URL filing, lớp cổ phần, mẫu số và ngày hiệu lực độc lập.'));
    if(subject==='tesla')rows.push(item('optimus','Optimus / sản xuất và khả năng mua','Chỉ có mô tả kế hoạch trong nguồn bàn giao','bán ngoài dự kiến 2027 chưa phải hàng hóa đang bán.','Cần nguồn Tesla IR và điều kiện thị trường; không niêm yết hàng sẵn bán.'));
    if(subject==='xai'){
      rows.push(item('legal_aliases','Tên pháp nhân / alias được báo cáo','SpaceXAI LLC / SpaceXSI — tên được nguồn báo cáo, chưa xác minh','Không thay tên pháp nhân trong Registry trước bằng chứng.','Chờ hồ sơ pháp lý gốc; không đổi tên hoặc Parent hiện hữu.'));
      rows.push(item('api_reference','Địa chỉ API được đề xuất','http://api.x.ai/v1 — văn bản từ nguồn; chưa dùng để kết nối','Endpoint đề xuất api.x.ai/v1; giá API theo model/ngày phải đọc tài liệu chính thức tại thời điểm tích hợp.','URL nguồn dùng HTTP; chỉ hiển thị văn bản, không gọi API hoặc tự nâng thành endpoint tin cậy.'));
    }
    if(subject==='x')rows.push(item('x_relationship','Quan hệ X / xAI',null,'Cấu trúc pháp lý xAI/X/Starlink.','Cần nguồn pháp lý riêng, không gộp các hồ sơ theo suy diễn.'));
    if(subject==='neuralink')rows.push(item('clinical','Nghiên cứu lâm sàng / điều kiện tiếp cận',null,'trạng thái thử nghiệm Neuralink','Chưa có nguồn thử nghiệm, cơ quan quản lý, ngày và phạm vi theo thị trường.'));
    if(subject==='boring')rows.push(item('loop','Loop / trạng thái từng dự án','Bàn giao đề cập Vegas, Nashville và Dubai; chưa kiểm chứng từng dự án','Số station, tiến độ, chi phí cần nguồn theo từng dự án.','Cần nguồn gốc gắn dự án, ngày và địa điểm; không coi kế hoạch là kết quả.'));
    rows.push(
      item('country_access','Điều kiện tiếp cận tại '+contexts[country],null,'Ứng dụng cần nghiên cứu','Chưa có quyền, giấy phép, điều khoản và Evidence cho thị trường được chọn.'),
      item('products','Sản phẩm / dịch vụ tại thị trường',null,'products[], vn_access, us_access','Chờ danh mục có nguồn, quyền sử dụng dữ liệu và điều kiện cung ứng.'),
      {...item('local_delivery','Hàng tại quốc gia / giao tại chỗ',null,'hàng tại quốc gia/giao tại chỗ','Chưa có Evidence tồn kho, vùng phục vụ hoặc giao hàng.'),sourceURL:'https://github.com/charityfundplus/CFP.plus/issues/156#issuecomment-6271840896',sourceKind:'Chỉ đạo Website/App tại Issue #156; chưa có bản ghi cung ứng'},
      item('price','Giá và điều khoản theo ngày',null,'Mỗi kết luận phải có URL nguồn gốc, ngày, trích đoạn và trạng thái theo trường dữ liệu','Cần báo giá/điều khoản chính thức đúng model, quốc gia, ngày và phạm vi.'),
      item('cfp_relationship','Hợp tác với CFP+',null,'Không mặc định có hợp tác thương mại với Elon Musk hay bất kỳ đơn vị nào.','Chưa có Evidence quan hệ hợp tác được phê duyệt.')
    );
    return rows;
  }
  function link(url,label){const safe=M.safeURL(url);return safe?'<a href="'+esc(safe)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' ↗</a>':'<span class="pending">Chưa có nguồn gốc</span>';}
  function fieldView(field){
    const status=statusOf(field);
    return '<article class="evidence-field" data-field="'+esc(field.key)+'" data-evidence-status="'+status+'"><div class="section-top"><h3>'+esc(field.label)+'</h3><span class="tag amber">'+status+'</span></div><p class="field-value">'+esc(field.value||'Chưa được bàn giao')+'</p><dl class="field-evidence"><div><dt>Nguồn bàn giao</dt><dd>'+link(field.sourceURL,field.sourceKind||'Nguồn bàn giao')+'</dd></div><div><dt>Ngày của nguồn</dt><dd>'+esc(field.sourceDate||'Chưa có ngày')+'</dd></div>'+(field.eventDate?'<div><dt>Ngày sự kiện được nguồn báo cáo</dt><dd>'+esc(field.eventDate)+'</dd></div>':'')+'<div><dt>Trích đoạn nguồn</dt><dd><q>'+esc(field.excerpt||'Chưa có trích đoạn')+'</q></dd></div><div><dt>Nguồn gốc / receipt độc lập</dt><dd>'+link(field.originalURL,'Nguồn gốc')+' · Chưa có receipt reviewer độc lập</dd></div><div><dt>Điều kiện kiểm chứng tiếp</dt><dd>'+esc(field.blocker||'Cần nguồn gốc và review độc lập đúng trường; tuyên bố của nguồn chưa phải xác minh.')+'</dd></div></dl></article>';
  }
  function view(state){
    if(state.brand||state.country==='unknown')return '';
    if(!Object.hasOwn(contexts,state.country))return '<article class="panel"><span class="eyebrow">VIỆT NAM LÀM MẪU</span><h2>HSTDN có Evidence theo từng trường</h2><p>Cùng một khung cho Việt Nam, Hoa Kỳ và quốc gia khác; theo dõi riêng chủ thể, thị trường ứng dụng và trạng thái kiểm chứng.</p><div class="profile-actions"><a class="btn primary" href="#hstdn/vn/starlink">Mở mô hình Việt Nam</a><a class="btn" href="#hstdn/us/starlink">Đối chiếu Hoa Kỳ</a><a class="btn" href="#hstdn/global/starlink">Khung nhân rộng</a></div></article>';
    const country=state.country,key=state.subject||'starlink',subject=knownSubject(key);
    if(!subject)return '<div class="empty">Chưa có mục trong gói review.</div>';
    const fields=fieldsFor(key,country),blocked=fields.filter(f=>statusOf(f)==='BLOCKED').length;
    return '<section class="panel evidence-review" aria-labelledby="review-model-title"><span class="eyebrow">HSTDN · MÔ HÌNH VIỆT NAM VÀ NHÂN RỘNG</span><h2 id="review-model-title">'+esc(contexts[country])+' · '+esc(subject.name)+'</h2><p>'+esc(subject.scope)+'</p><div class="catalog-banner"><strong>Nguồn bàn giao đang review</strong><p>VERIFIED trong nội dung GrokSI là tuyên bố của nguồn. Chưa có trường nào được Codex 2 hoặc reviewer độc lập xác nhận VERIFIED. Quốc gia đang chọn là bối cảnh ứng dụng, không xác lập quốc gia của pháp nhân.</p></div><div class="catalog-tabs" role="navigation" aria-label="Mô hình theo quốc gia">'+Object.entries(contexts).map(([ctx,label])=>'<a class="btn '+(ctx===country?'primary':'')+'" href="#hstdn/'+ctx+'/'+key+'"'+(ctx===country?' aria-current="page"':'')+'>'+esc(label)+'</a>').join('')+'</div><div class="catalog-filter"><label for="review-subject">Chủ thể / sản phẩm cần đối chiếu</label><select id="review-subject" data-catalog-filter="subject">'+subjects.map(s=>'<option value="'+s.key+'"'+(key===s.key?' selected':'')+'>'+esc(s.name)+'</option>').join('')+'</select></div><p class="catalog-count" role="status">'+fields.length+' trường · VERIFIED: 0 · NOT VERIFIED: '+(fields.length-blocked)+' · BLOCKED: '+blocked+'</p><details class="field-legend"><summary>Ý nghĩa trạng thái và ranh giới dữ liệu</summary><p><strong>VERIFIED:</strong> cần nguồn gốc và receipt kiểm chứng độc lập đúng trường/ngày; chưa có trong gói hiện tại.</p><p><strong>NOT VERIFIED:</strong> có thông tin bàn giao, chưa có xác minh độc lập. <strong>BLOCKED:</strong> thiếu nguồn/giấy phép/mapping hoặc bằng chứng cần thiết.</p><p>Canonical ID / Parent / DID / country ID: chưa có binding được duyệt. Tên pháp lý, thương hiệu, segment và sản phẩm là các trường riêng; không dựng quan hệ Parent từ chúng.</p></details><div class="field-grid">'+fields.map(fieldView).join('')+'</div><div class="callout"><strong>Nối dữ liệu Core: BLOCKED</strong><p>UI dùng cùng cấu trúc trình bày cho Website và App web. Schema/receipt theo trường chờ Codex 1 xác nhận trước khi nối API hiện hữu.</p></div><p class="catalog-caption">Snapshot nguồn Notion: '+esc(source.lastEdited)+'. Đây là bản trình bày review; không có trạng thái xác minh toàn hồ sơ.</p><div class="profile-actions">'+link(source.url,'Mở hồ sơ Notion gốc')+link(assignment,'Chỉ đạo GitHub')+'<a class="btn" href="#commerce">Danh mục sàn hiện hữu</a><a class="btn" href="#technology">Quantum / Space / Future Technologies</a></div></section>';
  }
  root.HUB69HSTDNReview=Object.freeze({source,assignment,contexts,subjects,binding,route,filterRoute,statusOf,fieldsFor,fieldView,view});
})(typeof window!=='undefined'?window:globalThis);
