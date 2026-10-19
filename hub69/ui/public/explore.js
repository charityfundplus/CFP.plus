(function(root){
  'use strict';
  const M=root.HUB69Model,esc=M.esc;
  const sources=Object.freeze({
    assignment:'https://github.com/charityfundplus/CFP.plus/issues/156#issuecomment-6271840896',
    inbox:'https://app.notion.com/p/3fecaac9a5578117a3a6c3d079f70aff?pvs=204',
    trade:'https://app.notion.com/p/3decaac9a55781be8616d39de9978bce',
    tmtc:'https://cfp.plus/8682'
  });
  const countries=Object.freeze({all:'Tất cả quốc gia',vn:'Việt Nam',us:'Hoa Kỳ',global:'Quốc gia / thị trường khác',unknown:'Chưa có phạm vi quốc gia'});
  const topics=Object.freeze({all:'Tất cả công nghệ',quantum:'Quantum',space:'Space',future:'Future Technologies'});
  const frozen=rows=>Object.freeze(rows.map(r=>Object.freeze(r)));
  // UI-only slugs are not Registry IDs. Sample businesses are visibly synthetic.
  const brands=frozen([
    {key:'sample-vn',country:'vn',name:'Thương hiệu minh họa Việt Nam',sample:true,id:null,parent:null,did:null,canonical:null,description:'Mẫu bố cục giới thiệu thương hiệu, sản phẩm và khả năng giao hàng tại Việt Nam.',product:'Nhóm sản phẩm / dịch vụ minh họa',officialURL:null},
    {key:'sample-us',country:'us',name:'Thương hiệu minh họa Hoa Kỳ',sample:true,id:null,parent:null,did:null,canonical:null,description:'Mẫu bố cục giới thiệu thương hiệu, sản phẩm và khả năng giao hàng tại Hoa Kỳ.',product:'Nhóm sản phẩm / dịch vụ minh họa',officialURL:null}
  ]);
  const markets=frozen([
    {key:'amazon',country:'unknown',name:'Amazon',sample:false,id:null,parent:null,did:null,canonical:null,description:'Sàn được nêu trong định hướng 8682; hồ sơ này chỉ dẫn đến trang gốc để tham khảo.',product:'Danh mục sàn tham chiếu; chưa có danh mục hàng được bàn giao',officialURL:'https://www.amazon.com/'}
  ]);
  const technologies=frozen([
    {key:'ibm-quantum',topic:'quantum',name:'IBM Quantum',kind:'Nguồn công nghệ',url:'https://www.ibm.com/quantum',description:'Đọc nguồn về nghiên cứu và tính toán lượng tử.'},
    {key:'google-quantum',topic:'quantum',name:'Google Quantum AI',kind:'Nguồn nghiên cứu',url:'https://quantumai.google/',description:'Đọc nguồn nghiên cứu phần cứng và thuật toán lượng tử.'},
    {key:'nasa',topic:'space',name:'NASA',kind:'Tổ chức / nguồn nghiên cứu',url:'https://www.nasa.gov/',description:'Nguồn tham khảo cho học tập và nghiên cứu không gian.'},
    {key:'esa',topic:'space',name:'ESA',kind:'Tổ chức / nguồn nghiên cứu',url:'https://www.esa.int/',description:'Nguồn tham khảo về không gian và quan sát Trái Đất.'},
    {key:'spacex',topic:'space',name:'SpaceX',kind:'Nguồn doanh nghiệp',url:'https://www.spacex.com/',description:'Đọc nguồn về công nghệ phóng và hạ tầng không gian.'},
    {key:'starlink',topic:'space',name:'Starlink',kind:'Nguồn sản phẩm / dịch vụ',url:'https://www.starlink.com/',description:'Đọc nguồn về dịch vụ kết nối vệ tinh.'},
    {key:'future-models',topic:'future',name:'AI · Mô phỏng · Vật liệu',kind:'Hướng nghiên cứu đề xuất',url:null,description:'Khung tiếp nhận câu hỏi, nguồn gốc, thử nghiệm và review độc lập trước khi giới thiệu ứng dụng.'},
    {key:'future-life',topic:'future',name:'Công nghệ phục vụ Sự Sống',kind:'Hướng nghiên cứu đề xuất',url:null,description:'Khung trình bày ứng dụng trong giáo dục, môi trường và cộng đồng; chờ hồ sơ có Evidence.'}
  ]);
  function route(hash){
    const review=root.HUB69HSTDNReview?.route(hash);
    if(review)return review;
    if(hash==='#hstdn')return {view:'hstdn',country:'all'};
    if(hash==='#commerce')return {view:'commerce',country:'all'};
    if(hash==='#technology')return {view:'technology',topic:'all'};
    const country=/^#(hstdn|commerce)\/(vn|us|unknown)$/.exec(hash);
    if(country)return {view:country[1],country:country[2]};
    const topic=/^#technology\/(quantum|space|future)$/.exec(hash);
    if(topic)return {view:'technology',topic:topic[1]};
    const brand=/^#brand\/(sample-vn|sample-us|amazon)$/.exec(hash);
    if(brand)return {view:'hstdn',brand:brand[1]};
    return null;
  }
  function filterRoute(state,key,value){
    const review=root.HUB69HSTDNReview?.filterRoute(state,key,value);
    if(review)return review;
    if(value==='global'&&state.view!=='hstdn')return null;
    if(key==='country'&&['hstdn','commerce'].includes(state.view)&&Object.hasOwn(countries,value))return '#'+state.view+(value==='all'?'':'/'+value);
    if(key==='topic'&&state.view==='technology'&&Object.hasOwn(topics,value))return '#technology'+(value==='all'?'':'/'+value);
    return null;
  }
  const selectRows=(rows,key,value)=>value==='all'?rows:rows.filter(r=>r[key]===value);
  const out=(url,label)=>M.safeURL(url)?'<a class="btn" href="'+esc(M.safeURL(url))+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' ↗</a>':'<span class="pending">Chưa có URL được bàn giao</span>';
  const field=(label,value)=>'<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>';
  const crumbs=()=>'<nav class="catalog-crumbs" aria-label="Đường đi trong HUB 69"><a href="#home">HUB 69</a><span aria-hidden="true">/</span><a href="#group/789">Nhóm 789</a><span aria-hidden="true">/</span><a href="#chapter/7">Chương 7</a><span aria-hidden="true">/</span><a href="#hstdn">HSTDN</a></nav>';
  function countryFilter(view,country){
    return '<div class="catalog-filter"><label for="catalog-country">Phạm vi quốc gia</label><select id="catalog-country" data-catalog-filter="country">'+Object.entries(countries).filter(([key])=>view==='hstdn'||key!=='global').map(([key,label])=>'<option value="'+key+'"'+(country===key?' selected':'')+'>'+esc(label)+'</option>').join('')+'</select><span class="catalog-caption">Bộ lọc trình bày; chưa gắn Canonical ID quốc gia.</span></div>';
  }
  const tradeGateway=()=>'<article class="panel trade-gateway"><div><span class="eyebrow">8682 · TMTC</span><h2>Tiếp tục tại cổng thương mại</h2><p>Địa chỉ do CFP+ chỉ định. Nội dung tuyến công khai và khả năng giao dịch chưa được nghiệm thu cho bản này.</p></div><div class="profile-actions">'+out(sources.tmtc,'Mở cfp.plus/8682')+out(sources.trade,'Đọc nguồn định hướng')+'</div></article>';
  function brandCard(b){return '<article class="panel catalog-card"><div class="section-top"><span class="catalog-mark" aria-hidden="true">'+(b.sample?'MẪU':'TMTC')+'</span><span class="tag amber">'+(b.sample?'MINH HỌA':'THAM KHẢO')+'</span></div><h2>'+esc(b.name)+'</h2><p>'+esc(b.description)+'</p><dl class="catalog-meta">'+field('Quốc gia trong bố cục',countries[b.country])+field('Hàng tại quốc gia / giao tại chỗ','Chưa có Evidence cung ứng')+'</dl><a class="btn primary" href="#brand/'+esc(b.key)+'">'+(b.sample?'Xem bố cục hồ sơ':'Xem hồ sơ tham chiếu')+' →</a></article>';}
  function brandView(key){
    const b=[...brands,...markets].find(x=>x.key===key);
    if(!b)return '<p class="empty">Không có hồ sơ trong bản review.</p>';
    return crumbs()+'<a class="profile-back" href="'+(b.sample?'#hstdn/'+b.country:'#commerce')+'">← Về danh mục</a><article class="panel"><div class="section-top"><span class="eyebrow">HỒ SƠ THƯƠNG HIỆU</span><span class="tag amber">'+(b.sample?'MẪU MINH HỌA · KHÔNG PHẢI DOANH NGHIỆP THẬT':'THAM CHIẾU · CHƯA XÁC MINH HỢP TÁC')+'</span></div><h2 class="catalog-title">'+esc(b.name)+'</h2><p>'+esc(b.description)+'</p><dl class="profile-dl">'+field('Tên pháp lý / chủ thể','Chưa được bàn giao')+field('Quốc gia trong bố cục',countries[b.country])+field('Canonical ID / Parent / DID','Chưa có binding được phê duyệt')+field('Sản phẩm / dịch vụ',b.product)+field('Hàng hiện có tại quốc gia','Chưa có Evidence tồn kho')+field('Giao tại chỗ / vùng phục vụ','Chưa có Evidence giao hàng')+field('Chất lượng / chứng nhận / xuất xứ','Chưa có hồ sơ kiểm chứng')+field('Quan hệ với CFP+','Chưa có Evidence xác nhận')+field('Quyền dữ liệu / media','Chưa có giấy phép được bàn giao')+field('Nguồn định hướng','Issue #156 / Notion 8682; dữ liệu minh họa được ghi riêng')+'</dl><div class="profile-actions">'+(b.officialURL?out(b.officialURL,'Mở trang sàn gốc'):'<span class="pending">Website thương hiệu: chờ URL có nguồn</span>')+'<a class="btn" href="#commerce">Danh mục sàn</a><a class="btn" href="#technology">Công nghệ liên quan</a></div></article>'+tradeGateway();
  }
  function hstdnView(state){
    if(state.brand)return brandView(state.brand);
    const country=state.country||'all',rows=selectRows(brands,'country',country);
    return crumbs()+'<div class="catalog-banner"><strong>Review bố cục HSTDN</strong><p>Hai thương hiệu dưới đây là mẫu minh họa. Chưa có hồ sơ HSTDN thật, danh tính hay khả năng cung ứng được xác nhận.</p></div>'+countryFilter('hstdn',country)+'<p class="catalog-count" role="status">'+rows.length+' hồ sơ minh họa · 0 HSTDN được xác minh bởi prototype</p><div class="catalog-grid">'+(rows.length?rows.map(brandCard).join(''):'<p class="empty">Chưa có hồ sơ trong phạm vi này. Chọn quốc gia khác hoặc đọc khung hồ sơ chung.</p>')+'</div><div class="profile-actions"><a class="btn" href="#commerce">Danh mục sàn giao thương</a><a class="btn" href="#template">Link Mẫu Chung hiện hữu</a><a class="btn" href="#openai">Tham chiếu OpenAI hiện hữu</a></div>'+tradeGateway();
  }
  function commerceView(state){
    const country=state.country||'all',rows=selectRows(markets,'country',country);
    return crumbs()+'<div class="catalog-banner"><strong>Danh mục sàn tham chiếu</strong><p>Các sàn có thể được bổ sung từ nguồn được duyệt. Thông tin tồn kho, giao tại quốc gia, thanh toán và affiliate chưa được bàn giao.</p></div>'+countryFilter('commerce',country)+'<p class="catalog-count" role="status">'+rows.length+' sàn tham chiếu · 0 adapter được kích hoạt</p><div class="catalog-grid">'+(rows.length?rows.map(b=>brandCard(b)).join(''):'<div class="empty"><strong>Chưa có sàn được xác minh cho '+esc(countries[country])+'.</strong><p>Không suy phạm vi giao hàng từ tên sàn. Có thể xem hồ sơ thương hiệu minh họa tại quốc gia này.</p><a class="btn" href="#hstdn/'+esc(country)+'">Xem bố cục HSTDN quốc gia</a></div>')+'</div>'+tradeGateway();
  }
  function technologyView(state){
    const topic=state.topic||'all',rows=selectRows(technologies,'topic',topic);
    return '<nav class="catalog-crumbs" aria-label="Đường đi công nghệ"><a href="#home">HUB 69</a><span aria-hidden="true">/</span><a href="#group/246">Nhóm 246</a><span aria-hidden="true">/</span><a href="#chapter/6">Chương 6</a><span aria-hidden="true">/</span><a href="#technology">Công nghệ</a></nav><div class="catalog-banner"><strong>Danh mục nghiên cứu từ Evidence Inbox</strong><p>Phân biệt tổ chức, nguồn công nghệ và sản phẩm/dịch vụ. Chưa có bằng chứng tích hợp, tài khoản truy cập, hợp tác hoặc lưu trữ dữ liệu CFP+.</p></div><div class="catalog-tabs" role="navigation" aria-label="Phân khu công nghệ">'+Object.entries(topics).map(([key,label])=>'<a class="btn '+(topic===key?'primary':'')+'" href="#technology'+(key==='all'?'':'/'+key)+'"'+(topic===key?' aria-current="page"':'')+'>'+esc(label)+'</a>').join('')+'</div><p class="catalog-count" role="status">'+rows.length+' nguồn / hướng nghiên cứu</p><div class="catalog-grid">'+rows.map(t=>'<article class="panel catalog-card"><div class="section-top"><span class="catalog-mark" aria-hidden="true">'+esc(t.topic==='quantum'?'Q':t.topic==='space'?'S':'F')+'</span><span class="tag">'+esc(topics[t.topic])+'</span></div><h2>'+esc(t.name)+'</h2><p>'+esc(t.description)+'</p><dl class="catalog-meta">'+field('Loại tham chiếu',t.kind)+field('Integration Evidence / Country / HSTDN','Chưa được bàn giao')+'</dl><div class="profile-actions">'+out(t.url||sources.inbox,t.url?'Đọc nguồn được dẫn':'Đọc đề bài nghiên cứu')+'</div></article>').join('')+'</div><article class="panel"><h2>Từ nguồn đến hồ sơ có Evidence</h2><p>Chủ thể → Sản phẩm / Dịch vụ → Công nghệ → Evidence tích hợp → Quốc gia → HSTDN.</p><p class="catalog-caption">Các URL được kế thừa từ Evidence Inbox. Khả năng truy cập và nội dung hiện tại của từng trang cần kiểm chứng riêng.</p><div class="profile-actions">'+out(sources.inbox,'Evidence Inbox hiện hữu')+'<a class="btn" href="#hstdn">Xem HSTDN</a><a class="btn" href="#training">Học SI/AI</a></div></article>';
  }
  function view(state){
    if(state.view==='hstdn'){
      const current=hstdnView(state),review=root.HUB69HSTDNReview?.view(state)||'';
      // Keep one country selector and one review presenter inside the existing view.
      if(!review)return current;
      const marker='<p class="catalog-count"';
      const pos=current.indexOf(marker);
      return pos>=0?current.slice(0,pos)+review+current.slice(pos):current+review;
    }
    return state.view==='commerce'?commerceView(state):state.view==='technology'?technologyView(state):'';
  }
  root.HUB69Explore=Object.freeze({sources,countries,topics,brands,markets,technologies,route,filterRoute,selectRows,out,brandCard,brandView,view});
})(typeof window!=='undefined'?window:globalThis);
