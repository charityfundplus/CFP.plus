// Only an existing explicitly approved Preview can be suspended. No create,
// resume, deploy or DNS APIs exist in this controller. API key stays off-service.
export async function suspendPreview({serviceId,ownerId,name,apiKey,approved=false,closeAdmission,fetcher=fetch}){
 if(!approved||!/^srv-[a-z0-9]+$/.test(serviceId||'')||!ownerId||!name||!apiKey||typeof closeAdmission!=='function')throw Error('APPROVED_PREVIEW_TARGET_REQUIRED');
 const url='https://api.render.com/v1/services/'+serviceId,headers={Authorization:'Bearer '+apiKey,Accept:'application/json'};
 const get=async()=>{const r=await fetcher(url,{headers,signal:AbortSignal.timeout(10000)});if(r.status!==200)throw Error('RENDER_READ_FAILED:'+r.status);const s=await r.json();if(s.id!==serviceId||s.ownerId!==ownerId||s.name!==name||s.type!=='web_service')throw Error('TARGET_MISMATCH');return s;};
 const before=await get();await closeAdmission();
 if(before.suspended!=='suspended'){const r=await fetcher(url+'/suspend',{method:'POST',headers,signal:AbortSignal.timeout(10000)});if(r.status!==202)throw Error('RENDER_SUSPEND_FAILED:'+r.status);}
 const after=await get();if(after.suspended!=='suspended')throw Error('SUSPEND_NOT_CONFIRMED');
 return {serviceId,suspended:true,readbackVerified:true,alreadySuspended:before.suspended==='suspended'};
}
