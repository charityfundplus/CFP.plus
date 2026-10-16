import {readFileSync,writeFileSync,renameSync,existsSync,statSync} from 'node:fs';
import {dirname} from 'node:path';import {randomUUID} from 'node:crypto';
export function guardPreview(handler,{stateFile,policy,clock=()=>Date.now()}){
 if(statSync(dirname(stateFile)).mode&0o077)throw Error('PRIVATE_GUARD_DIRECTORY_REQUIRED');
 const p=policy;
 for(const k of ['expiresAt','usageObservedAt','usageMaxAgeMs','projectedUSD','byteLimit','responseByteLimit','requestLimit','windowMs'])if(!Number.isFinite(p[k]))throw Error('POLICY_REQUIRED:'+k);
 if(p.usageMaxAgeMs<=0||p.byteLimit<=0||p.responseByteLimit<=0||p.responseByteLimit>1048576||!Number.isSafeInteger(p.requestLimit)||p.requestLimit<=0||p.windowMs<=0)throw Error('POLICY_RANGE');
 if(p.syntheticOnly!==true||p.adaptersDisabled!==true||p.backupOK!==true)throw Error('PREVIEW_SAFETY_REQUIRED');
 let state=existsSync(stateFile)?JSON.parse(readFileSync(stateFile)):{bytes:0,windowStart:clock(),requests:0,closed:null};
 if(!Number.isFinite(state.bytes)||state.bytes<0||!Number.isFinite(state.windowStart)||!Number.isSafeInteger(state.requests)||state.requests<0)throw Error('GUARD_STATE_INVALID');
 function save(){const temp=stateFile+'.'+randomUUID();writeFileSync(temp,JSON.stringify(state),{flag:'wx',mode:0o600});renameSync(temp,stateFile);}
 function close(reason){if(!state.closed){state.closed=reason;save();}return state.closed;}
 function reason(){const now=clock();if(state.closed)return state.closed;
  if(now>=p.expiresAt)return close('EXPIRED');
  if(now-p.usageObservedAt>p.usageMaxAgeMs||now<p.usageObservedAt)return close('STALE_USAGE');
  if(p.projectedUSD>=12)return close('BUDGET');if(state.bytes>=p.byteLimit)return close('BYTES');return null;
 }
 const guarded=(req,res)=>{
  if(reason()){res.writeHead(503,{'Content-Length':'0','Cache-Control':'no-store'});res.end();return;}
  const now=clock();if(now-state.windowStart>=p.windowMs){state.windowStart=now;state.requests=0;}state.requests++;save();
  if(state.requests>p.requestLimit){res.writeHead(429,{'Content-Length':'0','Cache-Control':'no-store'});res.end();return;}
  const write=res.write.bind(res),end=res.end.bind(res);let chunks=[],size=0,failed=false;
  const collect=(chunk,encoding)=>{if(chunk==null)return true;const b=Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk,typeof encoding==='string'?encoding:undefined);size+=b.length;
   if(size>p.responseByteLimit||state.bytes+size>p.byteLimit){failed=true;close('RESPONSE_BYTES');chunks=[];res.destroy();return false;}chunks.push(b);return true;};
  res.write=(chunk,encoding,callback)=>{const ok=collect(chunk,encoding);const cb=typeof encoding==='function'?encoding:callback;if(cb)queueMicrotask(cb);return ok;};
  res.end=(chunk,encoding,callback)=>{if(failed)return res;if(!collect(chunk,encoding))return res;
   if(state.bytes+size>p.byteLimit)close('BYTES');
   if(reason()){chunks=[];res.destroy();return res;}state.bytes+=size;save();
   for(const b of chunks)write(b);chunks=[];return end(typeof encoding==='function'?encoding:callback);};
  try{Promise.resolve(handler(req,res)).catch(()=>{close('HANDLER_FAILURE');res.destroy();});}catch{close('HANDLER_FAILURE');res.destroy();}
 };
 return {handler:guarded,read:()=>({...state}),check:reason,close};
}
