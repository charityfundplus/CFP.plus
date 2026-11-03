(function(root){
  'use strict';
  const M=root.HUB69Model,esc=M.esc;
  const kinds=Object.freeze({all:'Tất cả',profile:'Hồ sơ',hstdn:'Doanh nghiệp',product:'Sản phẩm',service:'Dịch vụ'});
  // Presentation-only fixtures. Keys are UI slugs; never numeric identity/Registry records.
  const samples=Object.freeze([
    {key:'sample-seed',name:'Bộ hạt giống minh họa',kind:'product',description:'Mẫu bố cục sản phẩm cho cộng đồng.'},
    {key:'sample-learning',name:'Bộ học liệu minh họa',kind:'product',description:'Mẫu bố cục học liệu; không có hàng để mua.'},
    {key:'sample-training',name:'Đào tạo kỹ năng số minh họa',kind:'service',description:'Mẫu dịch vụ học tập; chưa có đơn vị cung cấp.'},
    {key:'sample-logistics',name:'Dịch vụ giao nhận minh họa',kind:'service',description:'Mẫu dịch vụ; chưa có vùng phục vụ được xác minh.'}
  ].map(r=>Object.freeze({...r,id:null,parent:null,did:null,canonical:null,synthetic:true,verification:'NOT VERIFIED',status:'draft',maturity:'sandbox'})));
  function route(hash){
    if(hash==='#catalog')return {view:'commerce',country:'all',catalog:true,kind:'all'};
    const m=/^#catalog\/(all|profile|hstdn|product|service)$/.exec(hash);
    if(m)return {view:'commerce',country:'all',catalog:true,kind:m[1]};
    const item=/^#catalog\/item\/([A-Za-z0-9_-]{1,120})$/.exec(hash);
    return item?{view:'commerce',country:'all',catalog:true,kind:'all',item:item[1]}:null;
  }
  function validate(data){
    if(!data||data.sandbox!==true||data.synthetic!==true||data.readOnly!==true||data.activationAllowed!==false||data.registryWrites!==0||!Array.isArray(data.items)||data.items.length>100||!Number.isSafeInteger(data.total)||data.total<data.items.length||!Number.isSafeInteger(data.limit)||data.limit<1||data.limit>100||data.items.length>data.limit||!Number.isSafeInteger(data.offset)||data.offset<0||data.offset>10000||!(/^[a-f0-9]{64}$/).test(data.catalogRevision||''))throw Error('CATALOG_CONTRACT_REJECTED');
    const keys=new Set();
    const items=data.items.map(r=>{
      if(!r||typeof r.key!=='string'||!(/^[A-Za-z0-9_-]{1,120}$/).test(r.key)||keys.has(r.key)||!Object.hasOwn(kinds,r.kind)||r.kind==='all'||typeof r.name!=='string'||r.name.length>300||!r.name.trim()||r.synthetic!==true||r.verification!=='NOT VERIFIED'||r.status!=='SANDBOX_ONLY'||['id','parent','did','canonical'].some(k=>r[k]!==null))throw Error('CATALOG_ROW_REJECTED');
      keys.add(r.key);
      return Object.freeze({key:r.key,name:r.name,kind:r.kind,status:typeof r.status==='string'?r.status.slice(0,80):'pending',maturity:typeof r.maturity==='string'?r.maturity.slice(0,80):'sandbox',id:null,parent:null,did:null,canonical:null,synthetic:true,verification:'NOT VERIFIED'});
    });
    return Object.freeze({items:Object.freeze(items),total:data.total,limit:data.limit,offset:data.offset,catalogRevision:data.catalogRevision});
  }
  function select(rows,query='',kind='all'){
    if(!Object.hasOwn(kinds,kind))return [];
    const q=M.fold(query).slice(0,120);
    return rows.filter(r=>(kind==='all'||r.kind===kind)&&(!q||M.fold(r.name+' '+(r.description||'')+' '+kinds[r.kind]).includes(q)));
  }
  const back=()=>'<nav class="catalog-crumbs" aria-label="Điều hướng danh mục TMTC"><a href="#home">HUB 69</a><span aria-hidden="true">/</span><a href="#commerce">TMTC 8682</a><span aria-hidden="true">/</span><a href="#catalog">Sản phẩm &amp; dịch vụ</a></nav>';
  function results(rows,state,query){
    const found=select(rows,query,state.kind||'all');
    return '<p role="status" aria-live="polite">'+found.length+' kết quả trong '+rows.length+' mục thử đang hiển thị · 0 mục được xác minh để giao dịch</p><div class="catalog-grid">'+(found.length?found.map(r=>'<article class="panel catalog-card"><span class="tag amber">DỮ LIỆU THỬ · '+esc(kinds[r.kind])+'</span><h3>'+esc(r.name)+'</h3><p>'+esc(r.description||'Bản nháp trong Văn phòng Core sandbox.')+'</p><a class="btn" href="#catalog/item/'+esc(r.key)+'">Xem chi tiết →</a></article>').join(''):'<p class="empty">Không có kết quả. Thử tên khác hoặc chọn tất cả danh mục.</p>')+'</div>';
  }
  function view(state,{coreMode=false,coreState=null,query=''}={}){
    const catalog=coreState?.data?.catalog;
    const rows=coreMode?(coreState?.phase==='ready'&&catalog?.phase==='ready'?catalog.data.items:[]):samples;
    const banner='<div class="catalog-banner"><strong>TMTC 8682 · Sản phẩm &amp; dịch vụ sandbox</strong><p>'+(coreMode?'Đọc qua phiên Backend chung. Dữ liệu thử chỉ thuộc phạm vi được cấp quyền.':'Bố cục minh họa trên trình duyệt; chưa kết nối Backend.')+' Không có hàng bán, đặt đơn, thanh toán hoặc cấp định danh.</p></div>';
    if(coreMode&&(coreState?.phase!=='ready'||catalog?.phase!=='ready'))return back()+banner+'<div class="callout" role="status"><strong>Danh mục Core chưa sẵn sàng</strong><p>Không hiển thị dữ liệu cũ hoặc thay bằng mẫu. Cần phiên đăng nhập, quyền đọc cặp sandbox và endpoint danh mục.</p><button class="btn" data-core-retry>Đọc lại Core</button></div>';
    if(state.item){
      const r=rows.find(r=>r.key===state.item);
      if(!r)return back()+banner+'<p class="empty" role="status">Mục không có trong trang dữ liệu hiện tại hoặc chưa được cấp quyền.</p>';
      return back()+banner+'<article class="panel"><span class="tag amber">DỮ LIỆU THỬ · CHƯA XÁC MINH</span><h2>'+esc(r.name)+'</h2><dl class="profile-dl"><div><dt>Danh mục</dt><dd>'+esc(kinds[r.kind])+'</dd></div><div><dt>Trạng thái nháp</dt><dd>'+esc(r.status)+'</dd></div><div><dt>ID / Parent / DID / Canonical</dt><dd>Chưa gắn định danh</dd></div><div><dt>Đơn vị cung cấp / xuất xứ / giao hàng</dt><dd>Chưa có Evidence xác nhận</dd></div></dl><p>'+esc(r.description||'Bản ghi thử từ Backend chung; không phải niêm yết thương mại.')+'</p><a class="btn" href="#catalog/'+r.kind+'">← Về danh mục</a></article>';
    }
    const kind=state.kind||'all';
    return back()+banner+'<div class="directory-filters"><div class="catalog-filter"><label for="commerce-search">Tìm sản phẩm, dịch vụ</label><input id="commerce-search" type="search" maxlength="120" autocomplete="off" value="'+esc(query)+'" aria-controls="commerce-results" placeholder="Ví dụ: học liệu, đào tạo">'+(coreMode?'<button class="btn" data-catalog-read>Tìm trong Core</button>':'')+'</div><div class="catalog-filter"><label for="commerce-kind">Danh mục</label><select id="commerce-kind" data-catalog-filter="commerce-kind">'+Object.entries(kinds).map(([k,v])=>'<option value="'+k+'"'+(kind===k?' selected':'')+'>'+esc(v)+'</option>').join('')+'</select></div></div>'+(coreMode?'<p class="muted">'+rows.length+' / '+catalog.data.total+' mục thuộc trang API hiện tại. Tìm khi gõ trong trang; dùng Tìm trong Core để tìm toàn danh mục được cấp quyền.</p><div class="profile-actions"><button class="btn" data-catalog-page="previous"'+(catalog.data.offset===0?' disabled':'')+'>Trang trước</button><button class="btn" data-catalog-page="next"'+(catalog.data.offset+catalog.data.limit>=catalog.data.total?' disabled':'')+'>Trang sau</button></div>':'')+'<div id="commerce-results">'+results(rows,state,query)+'</div>';
  }
  root.HUB69Commerce=Object.freeze({kinds,samples,route,validate,select,results,view});
})(typeof window!=='undefined'?window:globalThis);
