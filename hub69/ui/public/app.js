(function(){
  'use strict';
  const M=window.HUB69Model,P=window.HUB69P0,T=window.HUB69Training,C=window.HUB69CoreBinding,X=window.HUB69Explore;
  const coreMode=window.HUB69_CONFIG?.mode==='core';
  let records=coreMode?[]:window.HUB69_DATA.records,coreState=null,coreController;
  let studyStorage;try{studyStorage=localStorage;}catch{}
  let study=T.readProgress(studyStorage);
  const $=id=>document.getElementById(id);
  let saved=[];
  try{const s=JSON.parse(localStorage.getItem('hub69.saved.v1')||'[]');if(Array.isArray(s))saved=s.filter(x=>M.validID(x)&&M.lookup(records,x).kind==='found');}catch{}
  let toastTimer;
  function notice(message){clearTimeout(toastTimer);$('notice').textContent=message;$('notice').hidden=false;toastTimer=setTimeout(()=>{$('notice').hidden=true;},4500);}
  function renderSaved(){const s=records.filter(r=>saved.includes(r.id));$('saved-items').innerHTML=s.length?s.map(r=>'<a href="#id/'+M.esc(r.id)+'">'+M.esc(r.name)+' <code>'+M.esc(r.id)+'</code></a>').join(''):'Lưu một mục trong trang ID để mở nhanh tại đây.';}
  function renderList(){
    const found=M.filter(records,$('search').value,$('type').value,saved);
    $('result-count').textContent=found.length+' / '+records.length+' bản ghi nguồn';
    $('records').innerHTML=found.length?found.map(M.card).join(''):'<div class="empty"><strong>Không có kết quả trong snapshot này.</strong><p>Thử tên hoặc ID chính xác. Hub giữ nguyên số 0 và không tự cấp ID mới.</p></div>';
  }
  function render(){
    const state=P.route(location.hash);
    for(const view of ['home','master','id','chapters','vaults','openai','template','training','hstdn','commerce','technology'])$('view-'+view).hidden=view!==state.view;
    document.querySelectorAll('[data-nav]').forEach(a=>{const active=a.dataset.nav===(state.view==='commerce'?'hstdn':state.view);a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    const labels={home:'Tổng quan',master:'Master Hub',id:'Tra cứu ID',chapters:'5 Nhóm · 10 Chương',vaults:'6 Kho',openai:'HSTDN OpenAI mẫu',template:'Link Mẫu Chung',training:'Đào tạo SI/AI',hstdn:'HSTDN theo quốc gia',commerce:'Danh mục sàn · 8682 TMTC',technology:'Quantum · Space · Future Technologies'};
    $('breadcrumb').textContent='HUB 69 / '+labels[state.view]+(state.id?' / '+state.id:'')+(state.chapter?' / Chương '+state.chapter:state.group?' / Nhóm '+state.group:'');
    document.title=(state.id?state.id+' • ':state.view==='home'?'':labels[state.view]+' • ')+'HUB 69 • CFP+';
    $('directory').hidden=!!state.id||!!state.invalid;$('profile').hidden=!state.id&&!state.invalid;
    const blocked=coreMode&&coreState?.phase!=='ready';
    $('core-status').innerHTML=coreMode?C.statusView(coreState):'<span class="tag">Snapshot 26 bản ghi · Chưa kết nối Core API</span>';
    document.querySelectorAll('[data-record-count]').forEach(el=>el.textContent=records.length);
    document.querySelectorAll('[data-source-summary]').forEach(el=>el.textContent=coreMode?(blocked?'Chưa có dữ liệu Core được xác nhận.':records.length+' tham chiếu từ Core; gồm 26 binding developer/AI. Không phải roster 91 Siêu Bộ Đôi.'):'26 binding developer/AI trong snapshot. Không phải roster 91 Siêu Bộ Đôi.');
    $('directory-pin').textContent=coreMode?(blocked?'Core chưa sẵn sàng':'Core · '+coreState.data.sourceCommit.slice(0,7)):'Snapshot · 8356163';
    $('source-caption').textContent=coreMode?(blocked?'Không hiển thị hồ sơ từ lần đọc cũ.':'Nguồn Core tại '+coreState.data.sourceCommit+'. Hash và Git blob nằm trong từng hồ sơ.'):'Registry snapshot tại 8356163. Không tự coi bản ghi là VERIFIED/ACTIVE.';
    if(state.view==='id'&&(state.id||state.invalid)){
      if(blocked){$('profile').innerHTML=C.statusView(coreState);}
      else{
      const result=state.invalid?{kind:'invalid'}:M.lookup(records,state.id);
      if(result.kind==='found'){$('profile').innerHTML=M.profile(result.record,records,saved)+P.profileExtra(result.record,records);document.title=result.record.id+' • '+result.record.name+' • HUB 69';}
      else{$('profile').innerHTML='<a class="profile-back" href="#id">← Về danh mục ID</a><div class="panel"><span class="tag amber">CHƯA ĐỊNH VỊ</span><h2 style="margin-top:15px">'+(result.kind==='invalid'?'Đường dẫn không hợp lệ':result.kind==='ambiguous'?'ID bị trùng trong nguồn':'ID '+M.esc(state.id)+' chưa có trong snapshot')+'</h2><p class="muted">Không tự suy diễn tên, Chương, Parent hoặc trang đích. Điều này không chứng minh ID không tồn tại ở nguồn khác.</p><div class="profile-actions"><a href="#id" class="btn primary">Tra cứu danh mục</a><a href="#master" class="btn">Về Master Hub</a></div></div>';}
      }
    }else if(state.view==='id'||state.view==='home')renderList();
    if(state.view==='chapters')$('chapter-map').innerHTML=blocked?C.statusView(coreState):P.mapView(records,state);
    if(state.view==='vaults')$('vault-monitor').innerHTML=blocked?C.statusView(coreState):P.vaultsView(coreState?.data?.openai);
    if(state.view==='openai')$('openai-profile').innerHTML=blocked?C.statusView(coreState):P.openaiView(records,coreState?.data?.openai);
    if(state.view==='template')$('common-template').innerHTML=P.templateView();
    if(state.view==='training')$('training-content').innerHTML=T.view(study,state.lesson);
    if(['hstdn','commerce','technology'].includes(state.view))$(state.view+'-content').innerHTML=X.view(state);
    renderSaved();
  }
  document.querySelectorAll('[data-lookup]').forEach(form=>form.addEventListener('submit',event=>{event.preventDefault();const input=form.elements.id;const id=input.value.trim();if(!M.validID(id)){notice('ID phải là chuỗi chữ số. Các số 0 được giữ nguyên.');input.focus();return;}const hash=id==='69'?'#home':'#id/'+id;if(location.hash===hash)render();else location.hash=hash;}));
  $('search').addEventListener('input',renderList);$('type').addEventListener('change',renderList);
  document.addEventListener('change',event=>{
    if(event.target.dataset?.catalogFilter){const key=event.target.dataset.catalogFilter,state=P.route(location.hash);const next=X.filterRoute(state,key,event.target.value);if(next)location.hash=next;return;}
    if(event.target.id==='template-type'){$('common-template').innerHTML=P.templateView(event.target.value);$('template-type').focus();}
    const key=event.target.dataset?.study;
    if(key&&T.validKey(key)){study=event.target.checked?[...new Set([...study,key])]:study.filter(k=>k!==key);const stored=T.saveProgress(studyStorage,study);render();$('study-'+key)?.focus();notice(stored?'Đã lưu ghi nhận đọc trên trình duyệt; chưa phải đánh giá năng lực.':'Chỉ ghi nhận đọc trong phiên này; trình duyệt chặn lưu lâu dài.');}
  });
  document.addEventListener('click',async event=>{
    if(event.target.closest('a.skip')){event.preventDefault();$('content').focus();return;}
    if(event.target.closest('[data-core-retry]')&&coreController){await coreController.load(P.route(location.hash).id);return;}
    if(event.target.closest('[data-core-logout]')&&coreController){await coreController.logout();return;}
    const save=event.target.closest('[data-save]');
    if(save){const id=save.dataset.save;if(M.lookup(records,id).kind!=='found')return;saved=saved.includes(id)?saved.filter(x=>x!==id):[...saved,id];let persisted=true;try{localStorage.setItem('hub69.saved.v1',JSON.stringify(saved));}catch{persisted=false;}render();notice(persisted?(saved.includes(id)?'Đã lưu mục trên trình duyệt này.':'Đã bỏ lưu mục.'):'Đã cập nhật tạm trong phiên này; trình duyệt không cho lưu lâu dài.');}
    const copy=event.target.closest('[data-copy]');
    if(copy){const link=new URL(location.href);link.hash='id/'+copy.dataset.copy;try{await navigator.clipboard.writeText(link.href);notice('Đã sao chép liên kết mục.');}catch{notice('Chưa sao chép được. Bạn có thể sao chép địa chỉ trên thanh trình duyệt.');}}
  });
  window.addEventListener('hashchange',()=>{if(coreController)coreController.load(P.route(location.hash).id);else render();window.scrollTo({top:0,behavior:'auto'});$('content').focus({preventScroll:true});});
  document.querySelectorAll('[data-record-count]').forEach(el=>el.textContent=records.length);
  const issues=P.validate(records);
  if(issues.length)$('registry-diagnostics').innerHTML='<div class="callout">'+issues.length+' vấn đề cấu trúc nguồn: '+issues.map(i=>M.esc(i.code+' '+i.id)).join(' · ')+'. Chờ review; không tự sửa dữ liệu.</div>';
  render();
  if(coreMode){coreController=C.createController({client:C.sameOriginClient,onChange:s=>{
    coreState=s;records=s.data?.records||[];
    if(s.phase!=='ready')for(const id of ['profile','openai-profile','chapter-map','vault-monitor','records','saved-items'])$(id).innerHTML='';
    render();
  }});coreController.load(P.route(location.hash).id);window.addEventListener('focus',()=>coreController.load(P.route(location.hash).id));}
})();
