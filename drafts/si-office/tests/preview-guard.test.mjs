import {test} from 'node:test';import assert from 'node:assert/strict';
import http from 'node:http';import {mkdtempSync,rmSync,readFileSync} from 'node:fs';import {tmpdir} from 'node:os';import {join} from 'node:path';
import {guardPreview} from '../scripts/preview-guard.mjs';import {createGuardedPreview} from '../scripts/guarded-preview.mjs';
const policy=()=>({expiresAt:Date.now()+60000,usageObservedAt:Date.now(),usageMaxAgeMs:60000,projectedUSD:7.25,byteLimit:100000,responseByteLimit:65536,requestLimit:10,windowMs:60000,syntheticOnly:true,adaptersDisabled:true,backupOK:true});
const listen=s=>new Promise(resolve=>s.listen(0,'127.0.0.1',()=>resolve(s.address().port)));
const stop=s=>new Promise(resolve=>s.close(resolve));
test('Actual HTTP: integrated curriculum launcher, request throttling, persisted expiry across restart',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'cfp-guard-http-'));let p;try{
  const cfg={database:join(dir,'state.db'),origin:'https://preview.example',revision:'f3be4842d973e2e882102ed16376a57954d87d63',policy:{...policy(),requestLimit:1}};
  p=createGuardedPreview(cfg);let port=await listen(p.server);
  const get=()=>fetch('http://127.0.0.1:'+port+'/api/curriculum',{headers:{Host:'preview.example'}});
  const r=await get();assert.equal(r.status,200);const body=await r.json();assert.equal(body.advanced.length,6);assert.equal(r.headers.get('x-cfp-preview-revision'),cfg.revision);assert(p.guard.read().bytes>0);
  assert.equal((await get()).status,429);p.guard.close('EXPIRED');await stop(p.server);p.service.close();p=createGuardedPreview(cfg);port=await listen(p.server);assert.equal((await get()).status,503);assert.equal(p.guard.read().closed,'EXPIRED');
 }finally{if(p){await stop(p.server);p.service.close();}rmSync(dir,{recursive:true,force:true});}
});
test('Actual HTTP: streamed body cannot exceed limit; closure persists; malformed policy denied',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'cfp-guard-bytes-'));let s;try{
  const stateFile=join(dir,'guard.json'),cfg={stateFile,policy:{...policy(),responseByteLimit:5}};
  const g=guardPreview((req,res)=>{res.write('123');res.end('456');},cfg);s=http.createServer(g.handler);const port=await listen(s);
  await assert.rejects(fetch('http://127.0.0.1:'+port));assert.equal(g.read().bytes,0);assert.equal(JSON.parse(readFileSync(stateFile)).closed,'RESPONSE_BYTES');
  const reopened=guardPreview(()=>assert.fail('dispatch'),cfg);assert.equal(reopened.check(),'RESPONSE_BYTES');
  assert.throws(()=>guardPreview(()=>{}, {...cfg,policy:{...policy(),usageMaxAgeMs:NaN}}),/POLICY_REQUIRED/);
 }finally{if(s)await stop(s);rmSync(dir,{recursive:true,force:true});}
});
