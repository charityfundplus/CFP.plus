import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {once} from 'node:events';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';

// Synthetic foundation evidence only: does not implement or certify a forum.
test('real TCP intake survives restart; versions, isolation, origin and revoked session hold',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'cfp-forum-foundation-'));
 const db=join(dir,'state.db'),password='Synthetic-foundation-password';
 let service,server;
 const open=async()=>{service=new P2Sandbox(db);server=createP2HTTP({service});server.listen(0,'127.0.0.1');await once(server,'listening');return 'http://127.0.0.1:'+server.address().port;};
 const close=async()=>{if(server?.listening){server.closeAllConnections();await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));}server=null;service?.close();};
 try{
  let origin=await open();
  for(const [id,role,workspace] of [['editor','editor','alpha'],['viewer','viewer','alpha'],['foreign','editor','beta']])service.provision({id,password,role,workspace,pairs:['hub69-content-demo']});
  const post=(path,body,cookie='',requestOrigin=origin)=>fetch(origin+path,{method:'POST',headers:{Origin:requestOrigin,'Content-Type':'application/json',Cookie:cookie},body:JSON.stringify(body)});
  const login=async id=>{const r=await post('/api/session',{id,password});assert.equal(r.status,200);assert.match(r.headers.get('set-cookie'),/HttpOnly; SameSite=Strict/);return r.headers.get('set-cookie').split(';')[0];};
  const editor=await login('editor'),viewer=await login('viewer'),foreign=await login('foreign');
  const input={name:'Synthetic Foundation AI',entityType:'new-ai',contact:'https://example.org/contact',relationships:[],synthetic:true,commitment:true};
  const args=(kind,input)=>({pairKey:'hub69-content-demo',kind,input});
  const create=body=>post('/api/core/office-create',body,editor);
  assert.equal((await post('/api/core/office-create',args('application',input),viewer)).status,403);
  assert.equal((await post('/api/core/office-create',args('application',input),editor,'https://invalid.example')).status,403);
  const r=await create(args('application',input));assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store');const original=await r.json();
  for(const f of ['id','parent','did','canonical'])assert.equal(original[f],null);
  assert.equal(original.status,'EVIDENCE_PENDING');
  const version=await create(args('application',{...input,amendmentOf:original.key,capabilities:'Updated synthetic declaration'}));assert.equal(version.status,200);assert.equal((await version.json()).declarationVersion,2);
  assert.equal((await create(args('application',input))).status,400);
  const request={name:'Synthetic work',officeRef:original.key,source:'https://example.org/evidence',scope:'Bounded sandbox work',synthetic:true,commitment:true};
  const foreignResult=await post('/api/core/office-create',args('work-request',request),foreign);
  assert.equal(foreignResult.status,403);assert.equal((await foreignResult.json()).error,'INTAKE_SCOPE_DENIED');
  const missingOffice=await create(args('work-request',{...request,officeRef:'unknown-synthetic-office'}));
  assert.equal(missingOffice.status,403);assert.equal((await missingOffice.json()).error,'INTAKE_SCOPE_DENIED');
  for(const invalid of [{...request,commitment:false},{...request,source:'http://invalid.example'}]){
   const result=await create(args('work-request',invalid));assert.equal(result.status,400);
   assert.equal((await result.json()).error,'INTAKE_SCOPE_OR_CONSENT_REQUIRED');
  }
  const work=await create(args('work-request',request));assert.equal(work.status,200);assert.equal((await work.json()).execution,'NOT AUTHORIZED');
  const snapshot=async cookie=>{const r=await post('/api/core/office',{pairKey:'hub69-content-demo'},cookie);assert.equal(r.status,200);return r.json();};
  const before=await snapshot(editor);const checkpoint=service.verify();assert(checkpoint.sequence>0);
  await close();origin=await open();assert.deepEqual(service.verify(),checkpoint);
  assert.deepEqual(await snapshot(editor),before);
  assert.equal((await snapshot(foreign)).registrations.length,0);
  assert.equal((await post('/api/logout',{},editor)).status,200);
  assert.equal((await post('/api/core/office',{pairKey:'hub69-content-demo'},editor)).status,401);
 }finally{await close();rmSync(dir,{recursive:true,force:true});}
});
