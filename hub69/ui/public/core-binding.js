(function(root){
  'use strict';
  const fingerprint=p=>JSON.stringify([p?.revision,p?.files]);
  function createController({client,onChange}){
    let epoch=0,loggingOut=false,state={phase:'idle',data:null,status:null};
    const publish=value=>{state=value;onChange(state);};
    const clear=phase=>publish({phase,data:null,status:null});
    async function load(id){
      if(loggingOut)return;
      const run=++epoch;clear('loading');
      try{
        const api=await client();
        const [snapshot,openai,detail]=await Promise.all([api.snapshot(),api.openai(),id?api.detail(id):null]);
        if(run!==epoch)return;
        const pin=fingerprint(snapshot.provenance);
        if(!snapshot.provenance||pin!==fingerprint(openai.provenance)||(detail&&pin!==fingerprint(detail.provenance)))throw Error('CORE_SOURCE_CHANGED_DURING_READ');
        if(detail&&detail.record?.id!==id)throw Error('CORE_DETAIL_ID_MISMATCH');
        publish({phase:'ready',status:200,data:{...snapshot,openai}});
      }catch(error){
        if(run!==epoch)return;
        publish({phase:'error',data:null,status:Number.isInteger(error.status)?error.status:null});
      }
    }
    function invalidate(){++epoch;clear('signed-out');}
    async function logout(){
      loggingOut=true;invalidate();
      try{const api=await client();await api.logout();}catch{publish({phase:'logout-error',data:null,status:null});}
      finally{loggingOut=false;}
    }
    return Object.freeze({load,logout,invalidate,getState:()=>state});
  }
  async function sameOriginClient(){
    // Reuse Codex 1's existing client and authenticated service. No API URL input,
    // registry copy, token storage, cross-origin call or snapshot fallback.
    const {createRegistryClient}=await import('/registry-client.js');
    return {...createRegistryClient(),async logout(){
      const response=await fetch('/api/logout',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:'{}'});
      if(!response.ok)throw Error('LOGOUT_NOT_CONFIRMED');
    }};
  }
  function statusView(state){
    if(state?.phase==='ready')return '<span class="tag">Core API · Đã đọc qua phiên hiện hữu</span><button class="btn" data-core-retry>Đọc lại</button><button class="btn" data-core-logout>Đăng xuất Core</button>';
    const phase=state?.phase;
    const message=phase==='loading'?'Đang đọc Core API…':phase==='logout-error'?'Đã xóa dữ liệu khỏi giao diện. Chưa xác nhận đăng xuất máy chủ; mở Văn phòng để kiểm tra.':phase==='signed-out'?'Đã xóa dữ liệu khỏi giao diện. Cần đăng nhập Core để đọc lại.':state?.status===401?'Phiên Core chưa đăng nhập hoặc đã hết hạn.':state?.status===404?'ID chưa có trong nguồn Core.':state?.status===503?'Nguồn Registry hiện không sẵn sàng.':state?.status===403?'Core từ chối quyền hoặc miền truy cập.':'Chưa đọc được dữ liệu Core hợp lệ.';
    return '<div class="callout"><strong>'+message+'</strong><p>Hồ sơ cũ đã được ẩn. Chỉ tiếp tục khi nguồn và phiên đọc được xác nhận.</p><div class="profile-actions"><a class="btn" href="/p2">Mở Văn phòng / Đăng nhập</a><button class="btn" data-core-retry'+(phase==='loading'?' disabled':'')+'>Thử lại</button></div></div>';
  }
  root.HUB69CoreBinding=Object.freeze({createController,sameOriginClient,statusView});
})(typeof window!=='undefined'?window:globalThis);
