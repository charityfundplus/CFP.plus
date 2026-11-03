(function () {
  'use strict';
  if(window.HUB69_CONFIG?.mode!=='app')return;
  const $=id=>document.getElementById(id);
  const el=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
  let ready=false,write=false,taskWrite=false,busy=false,epoch=0;
  function controls(){for(const b of document.querySelectorAll('#view-intake form button'))b.disabled=busy||!ready||!write;document.querySelector('#intake-task button').disabled=busy||!ready||!taskWrite||!$('intake-profile-key').options.length;}
  function clear(message){ready=false;write=false;taskWrite=false;$('intake-profiles').replaceChildren();$('intake-profile-key').replaceChildren();$('intake-status').textContent=message;controls();}
  async function api(path,body){
    if(window.Capacitor?.isNativePlatform?.()&&!(location.protocol==='https:'&&location.origin===window.HUB69_CONFIG?.approvedStagingOrigin))throw Error('Chưa cấu hình HTTPS sandbox được phê duyệt.');
    let r;try{r=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});}catch{clear('Mất kết nối · chưa xác minh dữ liệu.');throw Error('Mất kết nối backend.');}
    const data=await r.json();if(!r.ok){if(r.status===401||r.status>=500)clear('Phiên hoặc dữ liệu chưa được xác minh.');throw Error(data.error||'Không truy cập được dữ liệu.');}return data;
  }
  function requestKey(form,payload){const s=JSON.stringify(payload);if(form.dataset.payload!==s){form.dataset.payload=s;form.dataset.key=crypto.randomUUID();}return form.dataset.key;}
  async function read(){
    if(location.hash!=='#intake')return;const run=++epoch;
    try{
      const [profiles,state,grants]=await Promise.all([api('manual/profiles'),api('state'),api('social/spaces')]);if(run!==epoch)return;
      ready=true;write=['editor','admin'].includes(state.user.role);taskWrite=write&&grants.spaces.some(s=>s.key==='si-ai-forum'&&s.write);
      $('intake-status').textContent='Chương 0 ưu tiên · '+state.user.id+' · '+(write?'Có quyền nhập thủ công':'Chỉ đọc');
      const current=$('intake-profile-key').value;
      $('intake-profile-key').replaceChildren(...profiles.profiles.map(p=>{const o=el('option',p.name+' · Chương '+p.chapter);o.value=p.profile_key||p.key;return o;}));if(profiles.profiles.some(p=>(p.profile_key||p.key)===current))$('intake-profile-key').value=current;
      $('intake-profiles').replaceChildren(...profiles.profiles.map(p=>{const card=el('article','');card.className='panel';card.append(el('h2',p.name),el('p',p.kind+' · '+(p.role_label||'Chưa có nhãn vai trò')+' · Chương '+p.chapter),el('p',p.description),el('small','NHẬP THỦ CÔNG • CHƯA XÁC MINH • chưa cấp Canonical/Parent/DID'),el('p','Mã vận hành: '+(p.profile_key||p.key)));return card;}));controls();
    }catch(error){if(run===epoch)clear('Đăng nhập tại Vận hành rồi đọc lại. '+error.message);}
  }
  async function action(fn){if(busy)return;busy=true;controls();try{await fn();}catch(error){$('intake-message').textContent=error.message;}finally{busy=false;controls();}}
  window.addEventListener('DOMContentLoaded',()=>{
    $('intake-refresh').onclick=()=>action(read);
    $('intake-create').onsubmit=event=>{event.preventDefault();const form=event.currentTarget;const payload={kind:form.elements.kind.value,name:form.elements.name.value,role_label:form.elements.kind.value==='cmp-role'?form.elements.role_label.value:'',description:form.elements.description.value,chapter:Number(form.elements.chapter.value)};action(async()=>{await api('manual/profiles',{...payload,idempotency_key:requestKey(form,payload)});$('intake-message').textContent='Đã lưu hồ sơ nhập thủ công; chưa cấp định danh hoặc quyền vận hành.';await read();});};
    $('intake-task').onsubmit=event=>{event.preventDefault();const form=event.currentTarget,payload=Object.fromEntries(new FormData(form));action(async()=>{const task=await api('manual/tasks',{...payload,idempotency_key:requestKey(form,payload)});$('intake-message').textContent='Đã giao nhiệm vụ '+task.key+' gắn hồ sơ. Người nhận phải đăng nhập và tiếp nhận; chưa có ACK thay người khác.';});};
    read();
  });
  window.addEventListener('hashchange',read);window.addEventListener('online',read);window.addEventListener('offline',()=>{++epoch;clear('Mất kết nối · không dùng dữ liệu cũ.');});
  window.addEventListener('message',event=>{const frame=$('operations-frame');if(event.origin===location.origin&&event.source===frame?.contentWindow&&event.data?.type==='cfp-session-changed')read();});
})();
