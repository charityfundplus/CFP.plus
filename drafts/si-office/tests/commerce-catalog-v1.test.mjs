import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {DatabaseSync} from 'node:sqlite';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
import {requestHandlerFetch} from './harness.mjs';
import {hash} from '../core/common.mjs';
import {registry} from '../model.mjs';
const pairKey='hub69-content-demo',base='http://localhost:4174',password='Synthetic-catalog-password';
function fixture(){
 const dir=mkdtempSync(join(tmpdir(),'cfp-catalog-v1-')),db=join(dir,'state.db'),service=new P2Sandbox(db),tokens={};
 for(const [id,role,workspace,pairs] of [['editor','editor','alpha',[pairKey]],['viewer','viewer','alpha',[pairKey]],['foreign','viewer','beta',[pairKey]],['narrow','viewer','alpha',['training-demo']]]){
  service.provision({id,password,role,workspace,pairs});tokens[id]=service.login(id,password);
 }
 const fetch=requestHandlerFetch(createP2HTTP({service}));
 const request=(query='',id='viewer',headers={})=>fetch(base+'/api/v1/commerce/catalog?pairKey='+pairKey+query,{headers:{...(id?{Cookie:'cfp_p2='+tokens[id]}:{}),...headers}});
 return {dir,db,service,tokens,request,close(){service.close();rmSync(dir,{recursive:true,force:true});}};
}
async function seed(x){
 const developer=registry.entities.find(r=>r.type==='developer'&&!registry.blockedCountries.includes(r.ai_country_id));
 const profile=await x.service.execute(x.tokens.editor,'officeCreate',{pairKey,kind:'profile',input:{name:'Synthetic supplier',country:developer.ai_country_id,developer:developer.id,source:'https://example.invalid/PRIVATE-SOURCE',identityEvidence:'https://example.invalid/PRIVATE-EVIDENCE',synthetic:true}});
 for(const [kind,name] of [['product','Solar planner'],['service','Solar advisory']])await x.service.execute(x.tokens.editor,'officeCreate',{pairKey,kind,input:{name,source:'https://example.invalid/PRIVATE-PRODUCT',officeRef:profile.key,scope:'Synthetic only',maturity:'prototype',synthetic:true}});
}
test('v1 GET reuses existing Office catalog with search/filter/pagination and null identity',async()=>{
 const x=fixture();try{
  assert.equal((await (await x.request()).json()).total,0);
  const emptyDB=new DatabaseSync(x.db,{readOnly:true});assert.equal(emptyDB.prepare('SELECT count(*) AS n FROM states').get().n,0);emptyDB.close();
  await seed(x);
  const stateDB=new DatabaseSync(x.db,{readOnly:true}),before=stateDB.prepare('SELECT value FROM states WHERE workspace=?').get('alpha').value;
  const response=await x.request(),page=await response.json();assert.equal(response.status,200);assert.equal(page.total,3);assert.equal(page.items.length,3);
  assert.equal(response.headers.get('cache-control'),'no-store');assert.match(page.catalogRevision,/^[a-f0-9]{64}$/);
  for(const row of page.items){for(const k of ['id','parent','did','canonical'])assert.equal(row[k],null);assert.equal(row.status,'SANDBOX_ONLY');assert.equal(row.verification,'NOT VERIFIED');}
  assert.equal(page.sandbox,true);assert.equal(page.synthetic,true);assert.equal(page.readOnly,true);assert.equal(page.registryWrites,0);assert.equal(page.activationAllowed,false);
  const product=await (await x.request('&query=SOLAR&kind=product')).json();assert.equal(product.total,1);assert.equal(product.items[0].name,'Solar planner');
  const first=await (await x.request('&limit=1')).json(),next=await (await x.request('&limit=1&offset=1')).json();assert.equal(first.total,3);assert.notEqual(first.items[0].key,next.items[0].key);assert.equal(first.catalogRevision,next.catalogRevision);
  assert.equal((await (await x.request('&query=missing')).json()).total,0);
  assert.equal(stateDB.prepare('SELECT value FROM states WHERE workspace=?').get('alpha').value,before);stateDB.close();
 }finally{x.close();}
});
test('v1 GET denies unauthenticated/wrong pair/host and malformed query fields',async()=>{
 const x=fixture();try{
  assert.equal((await x.request('',null)).status,401);assert.equal((await x.request('','narrow')).status,403);
  assert.equal((await x.request('','viewer',{Host:'hostile.invalid'})).status,403);
  for(const q of ['&pairKey=duplicate','&query=a&query=b','&unknown=true','&__proto__=x','&limit=101','&limit=0','&limit=1.2','&offset=-1','&offset=10001','&kind=approved','&query='+'a'.repeat(161)])assert.equal((await x.request(q)).status,400,q);
 }finally{x.close();}
});
test('v1 projection excludes private declarations/tasks and isolates tenant with exact durable response audit',async()=>{
 const x=fixture();try{
  await seed(x);await x.service.execute(x.tokens.editor,'createTask',{pairKey,input:{kind:'website-draft',title:'PRIVATE TASK',text:'PRIVATE CUSTOMER',resource:'website-demo'}},{idempotencyKey:'private'});
  const page=await (await x.request()).json();assert(!JSON.stringify(page).includes('PRIVATE'));assert(!JSON.stringify(page).includes('subject'));assert(!JSON.stringify(page).includes('officeRef'));
  const db=new DatabaseSync(x.db,{readOnly:true});const event=JSON.parse(db.prepare('SELECT value FROM events ORDER BY seq DESC LIMIT 1').get().value);db.close();
  assert.equal(event.subject,'viewer');assert.equal(event.workspace,'alpha');assert.equal(event.action,'commerce:catalog');assert.equal(event.result,'sha256:'+hash(page));
  assert.equal((await (await x.request('','foreign')).json()).total,0);
 }finally{x.close();}
});
test('v1 read fails closed on audit corruption without returning catalog and survives restart',async()=>{
 const x=fixture();try{
  await seed(x);const before=await (await x.request()).json();x.service.close();x.service=new P2Sandbox(x.db);
  assert.deepEqual(x.service.readCommerce(x.tokens.viewer,pairKey),before);
  const db=new DatabaseSync(x.db);db.prepare('UPDATE events SET sha=? WHERE seq=1').run('tampered');db.close();
  assert.throws(()=>x.service.readCommerce(x.tokens.viewer,pairKey),/AUDIT_INTEGRITY_FAILURE/);
 }finally{x.close();}
});
