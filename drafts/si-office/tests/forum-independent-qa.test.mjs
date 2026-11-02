import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,writeFileSync,mkdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {once} from 'node:events';
import {spawn} from 'node:child_process';
import net from 'node:net';
import {DatabaseSync} from 'node:sqlite';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
import {hash} from '../core/common.mjs';
function evidence(name,value){const dir=process.env.CFP_FORUM_QA_EVIDENCE_DIR;if(dir){mkdirSync(dir,{recursive:true});writeFileSync(join(dir,name),value);}}
const password='Synthetic-independent-QA-only';
const pairKey='hub69-content-demo';
async function fixture(){
 const dir=mkdtempSync(join(tmpdir(),'cfp-independent-')),db=join(dir,'state.db');
 let service,server,origin;
 async function open(){service=new P2Sandbox(db);server=createP2HTTP({service});server.listen(0,'127.0.0.1');await once(server,'listening');origin='http://127.0.0.1:'+server.address().port;}
 async function close(){if(server?.listening){server.closeAllConnections();await new Promise((r,j)=>server.close(e=>e?j(e):r()));}service?.close();}
 await open();
 for(const [id,role,workspace,pairs] of [['author','editor','alpha',[pairKey]],['recipient','editor','alpha',[pairKey]],['reviewer','reviewer','alpha',[pairKey]],['viewer','viewer','alpha',[pairKey]],['foreign','editor','beta',[pairKey]],['ungranted','editor','alpha',['training-demo']]])service.provision({id,password,role,workspace,pairs});
 const request=async(path,body,cookie='',headers={})=>{
  const r=await fetch(origin+path,{method:body===undefined?'GET':'POST',headers:{Origin:origin,'Content-Type':'application/json',Cookie:cookie,...headers},...(body===undefined?{}:{body:JSON.stringify(body)})});
  const value=await r.json();return {status:r.status,headers:r.headers,value};
 };
 const login=async id=>{const r=await request('/api/session',{id,password});assert.equal(r.status,200);assert.match(r.headers.get('set-cookie'),/HttpOnly; SameSite=Strict/);return r.headers.get('set-cookie').split(';')[0];};
 const create=(cookie,extra={})=>request('/api/core/tasks',{pairKey,kind:'website-draft',title:'Independent QA task',text:'Synthetic only',resource:'website-demo',idempotencyKey:'qa-task',...extra},cookie);
 return {request,login,create,get service(){return service;},db,close,open,async clean(){await close();rmSync(dir,{recursive:true,force:true});}};
}
test('QA-01 task persists after server/SQLite restart and is read in a fresh independent session',async()=>{
 const x=await fixture();try{
  const author=await x.login('author'),t=await x.create(author);assert.equal(t.status,200);assert.equal(t.value.owner,'author');
  await x.close();await x.open();const recipient=await x.login('recipient');
  const state=await x.request('/api/core/state',undefined,recipient);assert.equal(state.status,200);
  assert.deepEqual(state.value.tasks.find(v=>v.key===t.value.key),t.value);assert.equal(state.value.auditValid,true);
 }finally{await x.clean();}
});
test('QA-02 idempotency replay survives restart; changed payload returns 409',async()=>{
 const x=await fixture();try{const a=await x.login('author'),first=await x.create(a);await x.close();await x.open();
  const again=await x.create(a);assert.equal(again.status,200);assert.deepEqual(again.value,first.value);
  assert.equal((await x.create(a,{title:'Conflicting title'})).status,409);
  assert.equal((await x.request('/api/core/state',undefined,a)).value.tasks.length,1);
 }finally{await x.clean();}
});
test('QA-03 anonymous, viewer, foreign workspace and ungranted pair cannot mutate another task',async()=>{
 const x=await fixture();try{const a=await x.login('author'),t=(await x.create(a)).value;
  assert.equal((await x.request('/api/core/state')).status,401);
  assert.equal((await x.create(await x.login('viewer'))).status,403);
  for(const id of ['foreign','ungranted']){const c=await x.login(id);assert.equal((await x.request('/api/core/run',{taskKey:t.key},c)).status,403);assert.equal((await x.request('/api/core/state',undefined,c)).value.tasks.length,0);}
  assert.equal((await x.request('/api/core/state',undefined,a)).value.tasks[0].status,'QUEUED');
 }finally{await x.clean();}
});
test('QA-04 generated synthetic output hash and task-specific audit survive restart, independent review is required',async()=>{
 const x=await fixture();try{const a=await x.login('author'),t=(await x.create(a)).value;
  const run=await x.request('/api/core/run',{taskKey:t.key},a);assert.equal(run.status,200);assert.equal(run.value.status,'AWAITING HUMAN REVIEW');
  assert.equal(run.value.executionReceipt.outputSha256,hash(run.value.output));assert.equal(run.value.executionReceipt.activationAllowed,false);
  const state=(await x.request('/api/core/state',undefined,a)).value;
  const event=state.audit.find(e=>e.action==='task-output'&&e.details.taskKey===t.key);assert.equal(event.details.outputHash,hash(run.value.output));assert.equal(state.auditValid,true);
  assert.equal((await x.request('/api/core/review',{taskKey:t.key,verdict:'acknowledge-draft'},a)).status,403);
  const r=await x.login('reviewer');assert.equal((await x.request('/api/core/review',{taskKey:t.key,verdict:'acknowledge-draft'},r)).status,200);
  const checkpoint=x.service.verify();await x.close();await x.open();assert.deepEqual(x.service.verify(),checkpoint);
  const reread=(await x.request('/api/core/state',undefined,await x.login('recipient'))).value.tasks.find(v=>v.key===t.key);
  assert.equal(reread.key,t.key);assert.equal(reread.executionReceipt.outputSha256,hash(reread.output));assert.equal(reread.review.productionApproved,false);
 }finally{await x.clean();}
});
test('QA-05 session logout is isolated to the revoked session',async()=>{
 const x=await fixture();try{const a=await x.login('author'),b=await x.login('author');assert.notEqual(a,b);assert.equal((await x.request('/api/logout',{},a)).status,200);assert.equal((await x.request('/api/core/state',undefined,a)).status,401);assert.equal((await x.request('/api/core/state',undefined,b)).status,200);}finally{await x.clean();}
});
test('QA-06 hostile origin, role/owner injection, oversized body and SQL-like credentials fail closed',async()=>{
 const x=await fixture();try{const a=await x.login('author');
  assert.equal((await x.request('/api/session',{id:'author',password,role:'reviewer'})).status,400);
  assert.equal((await x.request('/api/session',{id:"' OR 1=1 --",password})).status,401);
  assert.equal((await x.request('/api/core/tasks',{pairKey},a,{Origin:'https://evil.example'})).status,403);
  assert.equal((await x.create(a,{owner:'reviewer'})).status,400);
  assert.equal((await x.create(a,{text:'x'.repeat(9000)})).status,413);
  assert.equal((await x.request('/api/core/state',undefined,a)).value.tasks.length,0);
 }finally{await x.clean();}
});
test('QA-07 persisted output modification without matching audit is detected',async()=>{
 const x=await fixture();try{const a=await x.login('author');await x.create(a);await x.close();
  const db=new DatabaseSync(x.db);const row=db.prepare('SELECT value FROM states WHERE workspace=?').get('alpha');const state=JSON.parse(row.value);state.tasks[0].title='Tampered';db.prepare('UPDATE states SET value=? WHERE workspace=?').run(JSON.stringify(state),'alpha');db.close();
  assert.throws(()=>new P2Sandbox(x.db),/STATE_INTEGRITY_FAILURE/);
 }finally{await x.clean();}
});
test('QA-09 malformed unauthenticated request target must not terminate HTTP server',async()=>{
 const child=spawn(process.execPath,[new URL('./forum-http-crash-fixture.mjs',import.meta.url).pathname],{stdio:['ignore','pipe','pipe']});
 let stderr='';child.stderr.on('data',b=>stderr+=b);
 try{
  const [line]=await once(child.stdout,'data');const port=Number(String(line).trim());assert(port>0);
  const exited=once(child,'exit');
  let rawResponse='';
  await new Promise((resolve,reject)=>{const s=net.connect(port,'127.0.0.1',()=>s.write('GET http://[ HTTP/1.1\r\nHost: 127.0.0.1:'+port+'\r\nConnection: close\r\n\r\n'));s.on('data',b=>rawResponse+=b);s.on('error',reject);s.on('close',resolve);s.setTimeout(3000,()=>s.destroy());});
  await Promise.race([exited,new Promise(resolve=>setTimeout(resolve,200))]);
  if(child.exitCode===null&&child.signalCode===null){const response=await fetch('http://127.0.0.1:'+port+'/');assert.equal(response.status,200);assert.match(rawResponse,/^HTTP\/1\.1 400 /);}
  else{await exited;evidence('malformed-target-crash.log',stderr);assert.fail('Unauthenticated malformed request terminated server; exit='+child.exitCode+'; see malformed-target-crash.log');}
 }finally{evidence('malformed-target-crash.log',stderr);if(child.exitCode===null&&child.signalCode===null){const done=once(child,'exit');child.kill();await done;}}
});
