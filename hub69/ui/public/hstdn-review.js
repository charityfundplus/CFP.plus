(function(root){
  'use strict';
  const M=root.HUB69Model,esc=M.esc;
  const source=Object.freeze({url:'https://app.notion.com/p/3fecaac9a5578132a41fec206bfb0552',lastEdited:'2026-10-19T20:08:51.750Z',date:'2026-10-19',kind:'Bàn giao GrokSI qua Notion; ghi chú nghiên cứu, chưa phải dữ liệu API hoặc nguồn gốc độc lập'});
  const assignment='https://github.com/charityfundplus/CFP.plus/pull/157#issuecomment-6276298491';
  const contexts=Object.freeze({vn:'Việt Nam',us:'Hoa Kỳ',global:'Quốc gia / thị trường khác'});
  const subjects=Object.freeze([
    Object.freeze({key:'starlink',name:'Starlink',scope:'Pháp nhân được báo cáo, thương hiệu và dịch vụ kết nối cần đối chiếu riêng'}),
    Object.freeze({key:'spacex',name:'SpaceX',scope:'Pháp nhân, cổ phần và quyền biểu quyết cần nguồn gốc theo từng trường'}),
    Object.freeze({key:'tesla',name:'Tesla / Optimus / Megapack',scope:'Tách chủ thể, sản phẩm và điều kiện từng dự án; chưa xác nhận hàng tại thị trường'}),
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
  const reviewRun=Object.freeze({readAt:'2026-10-19T22:50:49.993Z',reviewer:'Codex · đọc và đối chiếu nguồn',independentReceipt:null});
  const urls=Object.freeze({
    starlinkNotice:'https://cattien2.lamdong.gov.vn/chi-tiet-tin-tuc/?param=tuan-thu-quy-dinh-phap-luat-khi-su-dung-thiet-bi-dau-cuoi-thu-phat-song-ve-tinh-phi-dia-tinh-tai-viet-nam',
    starlinkPlans:'https://starlink.com/vn/service-plans',
    grokTerms:'https://x.ai/legal/terms-of-service',
    subscriptionTerms:'https://x.ai/legal/bundled-subscription-terms',
    plans:'https://x.ai/pricing',
    legacyPlans:'https://docs.x.ai/x-subscription/pricing',
    quickstart:'https://docs.x.ai/developers/quickstart',
    apiPricing:'https://docs.x.ai/developers/pricing',
    megapack:'https://www.tesla.com/megapack',
    registry:'https://github.com/charityfundplus/CFP.plus/blob/383ffcf5fa3a229d442393a86fa189e52bc09289/registry/ai-entity-registry.json'
  });
  function comparison(result,url,date,excerpt,observation,action,scope){
    return {result,url,date,excerpt,observation,action,scope,readAt:reviewRun.readAt,reviewer:reviewRun.reviewer};
  }
  function comparisonFor(subject,country,key){
    if(subject==='starlink'&&country==='vn'){
      if(key==='legal_name')return comparison('Khớp',urls.starlinkNotice,'2026-06-23','Công ty TNHH Starlink Services Việt Nam','Tên trong bàn giao khớp tên được thông báo chính quyền nêu. Chưa đọc giấy đăng ký doanh nghiệp.','Giữ tên dưới dạng claim đang review; GrokSI bổ sung bản đăng ký gốc.','Thông báo chính quyền; không phải bản gốc giấy đăng ký hoặc giấy phép');
      if(key==='license')return comparison('Sai lệch',urls.starlinkNotice,'2026-06-23','Ngày 13/02/2026','Thông báo nêu Cục Viễn thông cấp 57/GP-CVT ngày 13/02/2026; bàn giao ghi 03/03/2026.','Giữ cả hai ngày và chặn riêng trường giấy phép; cần bản gốc từ cơ quan cấp để kết luận.','Sai lệch ngày; chưa xác nhận toàn bộ nội dung hoặc hiệu lực giấy phép');
      if(key==='price')return comparison('Chưa xác minh',urls.starlinkPlans,null,null,'Trang kế hoạch dịch vụ Việt Nam không trả nội dung giá có thể đọc trong lượt này.','Chỉ chặn giá/điều kiện theo địa chỉ; tiếp tục các trường có nguồn khác.','Không suy giá hoặc khả năng đăng ký từ URL/HTTP thành công');
    }
    if(subject==='xai'){
      if(key==='legal_name')return comparison('Khớp',urls.grokTerms,'2026-10-12','SpaceXAI LLC','Điều khoản Consumer tự nêu bên cung cấp là SpaceXAI LLC, công ty tại Nevada.','Lưu là nội dung tự công bố của nguồn; cần đăng ký pháp nhân và reviewer độc lập trước binding.','Bên trong điều khoản dịch vụ; không xác minh Parent pháp lý');
      if(key==='trade_name')return comparison('Khớp',urls.grokTerms,'2026-10-12','SpaceXSI','Điều khoản dùng SpaceXSI làm tên gọi của SpaceXAI LLC. Grok là sản phẩm/dịch vụ được liệt kê riêng.','Tách tên pháp lý, tên gọi thương mại và sản phẩm; không đổi tên xAI trong Registry.','Tên gọi theo điều khoản; chưa phải chứng nhận đăng ký thương hiệu');
      if(key==='cfp_parent')return comparison('Khớp',urls.registry,null,'"parent_id": "69119"','Mã nguồn ghim có Grok 691191, parent_id 69119 và tên Developer xAI.','Chỉ ghi nhận quan hệ CFP+ hiện hữu; không dùng làm Parent pháp lý hoặc cấp binding HSTDN mới.','Quan sát Registry tại SHA ghim; không là chứng cứ sở hữu doanh nghiệp');
      if(key==='api_reference')return comparison('Sai lệch',urls.quickstart,'2026-10-10','https://api.x.ai/v1','Tài liệu dùng HTTPS; bàn giao ghi địa chỉ HTTP.','Đề xuất HTTPS trong ghi chú candidate; chưa gọi API hoặc kích hoạt adapter.','Tài liệu kỹ thuật; không chứng minh quyền truy cập hay khả năng vận hành');
      if(key==='subscription_seller')return comparison('Chưa xác minh',urls.subscriptionTerms,'2026-10-07','X Subscription Corp','Điều khoản bundle nêu X Subscription Corp là bên bán và merchant of record; bên cung cấp từng dịch vụ được tách riêng.','Bổ sung claim còn thiếu trong bàn giao; không đồng nhất bên bán bundle với pháp nhân Grok hoặc Parent.','Bổ sung từ nguồn; chưa có claim tương ứng trong gói gốc để đối chiếu');
      if(key==='subscription_plans')return comparison('Chưa xác minh',urls.plans,null,'API usage is billed separately','Bảng niêm yết USD/tháng: Free 0; Plus 8; Premium 30; Super 100; Ultra 200. Chưa gồm thuế/phí; quyền API trong gói trả phí có usage tính riêng.','Giữ ngày đọc, đơn vị, chu kỳ và loại gói; không coi đây là giá checkout tại Việt Nam/Hoa Kỳ hoặc giá API.','Bảng giá công khai đọc ngày 19/10/2026; trang không nêu ngày công bố');
      if(key==='legacy_plans')return comparison('Chưa xác minh',urls.legacyPlans,'2026-10-11','Existing Cursor, SuperGrok, and X Premium plans continue','Nguồn nói các gói hiện hữu tiếp tục; chuyển sang gói gộp là tùy chọn.','Giữ riêng SuperGrok hiện hữu và bảng The X Subscription; cần Evidence đúng gói/tài khoản nếu báo giá.','Bổ sung từ tài liệu; không suy rằng mọi tài khoản đã được chuyển gói');
      if(key==='api_pricing')return comparison('Chưa xác minh',urls.apiPricing,'2026-10-10','Prices per 1M tokens','Ví dụ grok-4.3, USD/1M token: ngữ cảnh ngắn input 1.25, cached 0.20, output 2.50; từ 200k input token áp dụng 2.50/0.40/5.00 cho mọi token trong request. Endpoint vùng US có phụ phí 10%; công cụ tính riêng.','Chỉ dùng ví dụ gắn model/ngữ cảnh/endpoint/ngày đọc; không gộp vào giá thuê bao hoặc báo giá toàn thị trường.','Giá tham khảo từ tài liệu, chưa gọi API hoặc xác nhận billing/account');
    }
    if(subject==='tesla'&&key==='megapack_availability')return comparison('Chưa xác minh',urls.megapack,null,'contracted an Availability Guarantee','Chú thích giới hạn phép đo ở các dự án đã ký Availability Guarantee và vận hành hơn 30 ngày; trung bình 12 tháng trước được trọng số GWh.','Giữ đầy đủ điều kiện; không suy bảo đảm chung, giá hoặc khả năng giao tại Việt Nam. GrokSI bổ sung claim/điều khoản gốc.','Chỉ đọc được chú thích; thiếu claim Megapack trong bàn giao và hợp đồng cụ thể');
    return null;
  }
  function fieldsFor(subject,country){
    if(!knownSubject(subject)||!Object.hasOwn(contexts,country))return [];
    const rows=[
      item('entity_type','Pháp nhân / thương hiệu / segment / sản phẩm',null,'Phân biệt công ty, công ty con, thương hiệu, sản phẩm và segment; không gán quan hệ sở hữu theo suy diễn.','Chờ mapping phân loại Codex 1 và nguồn pháp lý; nhãn điều hướng không phải loại thực thể được duyệt.'),
      item('legal_name','Tên pháp lý',subject==='starlink'&&country==='vn'?'CÔNG TY TNHH STARLINK SERVICES VIỆT NAM — tên do GrokSI báo cáo':subject==='xai'?'SpaceXAI LLC — tên do GrokSI báo cáo':null,subject==='starlink'&&country==='vn'?'GrokSI cung cấp tên CÔNG TY TNHH STARLINK SERVICES VIỆT NAM':subject==='xai'?'GrokSI báo cáo tên SpaceXAI LLC':'Dữ liệu cần kiểm chứng riêng', 'Chưa có hồ sơ đăng ký gốc được bàn giao cho trường này.'),
      item('trade_name','Tên tham chiếu / thương hiệu',subject==='xai'?'SpaceXSI — tên gọi do GrokSI báo cáo':subject==='tesla'?'Tesla':subject==='boring'?'The Boring Company':knownSubject(subject).name,subject==='xai'?'tên thương mại SpaceXSI chưa hoàn tất xác minh pháp lý':'Tesla, SpaceX, Starlink, xAI/Grok, X, Neuralink, The Boring Company.'),
      item('corporate_relationship','Sở hữu doanh nghiệp / quan hệ pháp lý',null,'không gán quan hệ sở hữu theo suy diễn.','Cần nguồn gốc; không chuyển quan hệ doanh nghiệp thành Parent Registry.'),
      item('legal_parent','Parent pháp lý',null,'không gán quan hệ sở hữu theo suy diễn.','Thiếu chứng cứ quan hệ pháp lý; không lấy Parent CFP+ để điền trường này.'),
      item('cfp_parent','Parent CFP+ hiện hữu',null,'Không thay tên pháp nhân trong Registry trước bằng chứng.','Chỉ đọc binding có thẩm quyền; chưa gắn ghi chú nghiên cứu vào hồ sơ Registry.'),
      item('official_website','Website chính thức của chủ thể pháp lý',null,'Mỗi kết luận phải có URL nguồn gốc, ngày, trích đoạn và trạng thái theo trường dữ liệu','Chưa có URL gốc gắn đúng chủ thể pháp lý trong gói review này.')
    ];
    if(subject==='starlink'){
      rows.push(item('license','Giấy phép theo thị trường',country==='vn'?'57/GP-CVT — số do GrokSI báo cáo':null,'Giấy phép được báo cáo: 57/GP-CVT ngày 03/03/2026.','Cần cơ quan cấp, bản gốc và phạm vi hiệu lực; chưa có kết luận VERIFIED.',country==='vn'?'2026-03-03 — ngày do nguồn báo cáo':null));
      rows.push(item('pilot','Pilot / khả năng cung ứng',country==='vn'?'Bàn giao đề cập pilot; chưa xác minh số lượng hoặc khả năng cung ứng':null,'Pilot được báo cáo: 4 gateway, tối đa 600.000 terminal đến 2030.'));
    }
    if(subject==='spacex')rows.push(item('ownership','Cổ phần / beneficial ownership / quyền biểu quyết','Bàn giao có số liệu; chưa đối chiếu filing gốc','Cần accession number, filing URL, mẫu số và lớp cổ phần.','Thiếu accession, URL filing, lớp cổ phần, mẫu số và ngày hiệu lực độc lập.'));
    if(subject==='tesla')rows.push(
      item('optimus','Optimus / sản xuất và khả năng mua','Chỉ có mô tả kế hoạch trong nguồn bàn giao','bán ngoài dự kiến 2027 chưa phải hàng hóa đang bán.','Cần nguồn Tesla IR và điều kiện thị trường; không niêm yết hàng sẵn bán.'),
      item('megapack_availability','Megapack / điều kiện chỉ số availability',null,null,'Cần GrokSI bổ sung đoạn claim và điều khoản gốc; vẫn tiếp tục đối chiếu nguồn đọc được.'),
      item('megapack_terms','Megapack / giá, bảo hành, giao hàng và lắp đặt',null,null,'Chưa có báo giá/hợp đồng theo cấu hình, địa điểm, phạm vi công việc và ngày; không suy từ trang sản phẩm.')
    );
    if(subject==='xai'){
      rows.push(item('api_reference','Địa chỉ API được đề xuất','http://api.x.ai/v1 — văn bản từ nguồn; chưa dùng để kết nối','Endpoint đề xuất api.x.ai/v1; giá API theo model/ngày phải đọc tài liệu chính thức tại thời điểm tích hợp.','URL nguồn dùng HTTP; chỉ hiển thị văn bản, không gọi API hoặc tự nâng thành endpoint tin cậy.'));
      for(const [key,label] of [['subscription_seller','Grok / bên bán gói thuê bao'],['subscription_plans','Grok / bảng gói thuê bao tham khảo'],['legacy_plans','Grok / gói SuperGrok hiện hữu'],['api_pricing','Grok / giá API theo model và ngữ cảnh']])rows.push(item(key,label,null,null,'Cần claim bàn giao, review độc lập và điều kiện đúng thị trường; ghi chú nguồn đã đọc không cấp quyền sử dụng.'));
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
    return rows.map(field=>({...field,comparison:comparisonFor(subject,country,field.key)}));
  }
  function link(url,label){const safe=M.safeURL(url);return safe?'<a href="'+esc(safe)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' ↗</a>':'<span class="pending">Chưa có nguồn gốc</span>';}
  function comparisonView(field){
    const c=field.comparison;
    if(!c)return '<p class="pending">Đối chiếu: Chưa xác minh · thiếu nguồn gốc cho trường này.</p>';
    const result=['Khớp','Sai lệch','Chưa xác minh'].includes(c.result)?c.result:'Chưa xác minh';
    return '<details><summary>Đối chiếu: '+result+'</summary><dl class="field-evidence"><div><dt>Nguồn đã đọc</dt><dd>'+link(c.url,'Nguồn đối chiếu')+'</dd></div><div><dt>Ngày công bố / cập nhật nguồn</dt><dd>'+esc(c.date||'Nguồn không nêu ngày')+'</dd></div><div><dt>Ngày đọc</dt><dd>'+esc(c.readAt)+'</dd></div><div><dt>Đoạn Evidence đã đọc</dt><dd>'+esc(c.excerpt||'Không trích xuất được nội dung hỗ trợ trường')+'</dd></div><div><dt>Nhận xét</dt><dd>'+esc(c.observation)+'</dd></div><div><dt>Cách xử lý</dt><dd>'+esc(c.action)+'</dd></div><div><dt>Phạm vi nguồn</dt><dd>'+esc(c.scope)+'</dd></div><div><dt>Reviewer</dt><dd>'+esc(c.reviewer)+' · Chờ receipt Claude độc lập</dd></div></dl></details>';
  }
  function fieldView(field){
    const status=statusOf(field);
    return '<article class="evidence-field" data-field="'+esc(field.key)+'" data-evidence-status="'+status+'"><div class="section-top"><h3>'+esc(field.label)+'</h3><span class="tag amber">'+status+'</span></div><p class="field-value">'+esc(field.value||'Chưa được bàn giao')+'</p><dl class="field-evidence"><div><dt>Nguồn bàn giao</dt><dd>'+link(field.sourceURL,field.sourceKind||'Nguồn bàn giao')+'</dd></div><div><dt>Ngày của nguồn</dt><dd>'+esc(field.sourceDate||'Chưa có ngày')+'</dd></div>'+(field.eventDate?'<div><dt>Ngày sự kiện được nguồn báo cáo</dt><dd>'+esc(field.eventDate)+'</dd></div>':'')+'<div><dt>Trích đoạn nguồn</dt><dd><q>'+esc(field.excerpt||'Chưa có trích đoạn')+'</q></dd></div><div><dt>Nguồn gốc / receipt độc lập</dt><dd>'+link(field.originalURL,'Nguồn gốc')+' · Chưa có receipt reviewer độc lập</dd></div><div><dt>Điều kiện kiểm chứng tiếp</dt><dd>'+esc(field.blocker||'Cần nguồn gốc và review độc lập đúng trường; tuyên bố của nguồn chưa phải xác minh.')+'</dd></div></dl>'+comparisonView(field)+'</article>';
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
