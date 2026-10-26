// Real TCP integration. Requires sandbox loopback-network permission.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
import {registry} from '../model.mjs';
test('real loopback TCP login, private versioned catalog read, filtering, isolation and logout',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'cfp-commerce-tcp-')),service=new P2Sandbox(join(dir,'state.db')),server=createP2HTTP({service});
 const password='Synthetic-loopback-password',pairKey='hub69-content-demo';
 for(const [id,workspace] of [['editor','alpha'],['foreign','beta']])service.provision({id,password,role:'editor',workspace,pairs:[pairKey]});
 try{
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const base='http://127.0.0.1:'+server.address().port,route='/api/v1/commerce/catalog?pairKey='+pairKey;
  const post=(path,cookie,body)=>fetch(base+path,{method:'POST',headers:{Origin:base,'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{})},body:JSON.stringify(body)});
  assert.equal((await fetch(base+route)).status,401);
  const login=await post('/api/session','',{id:'editor',password});assert.equal(login.status,200);
  const setCookie=login.headers.get('set-cookie');assert.match(setCookie,/HttpOnly/);assert.match(setCookie,/SameSite=Strict/);const cookie=setCookie.split(';')[0];
  const developer=registry.entities.find(r=>r.type==='developer'&&!registry.blockedCountries.includes(r.ai_country_id));
  const p=await (await post('/api/core/office-create',cookie,{pairKey,kind:'profile',input:{name:'Synthetic TCP supplier',country:developer.ai_country_id,developer:developer.id,source:'https://example.invalid/private',identityEvidence:'https://example.invalid/private',synthetic:true}})).json();assert.ok(p.key);
  const product=await post('/api/core/office-create',cookie,{pairKey,kind:'product',input:{name:'TCP Solar planner',source:'https://example.invalid/private',officeRef:p.key,maturity:'prototype',synthetic:true}});assert.equal(product.status,200);
  const response=await fetch(base+route+'&query=solar&kind=product',{headers:{Cookie:cookie}}),page=await response.json();
  assert.equal(response.status,200);assert.equal(response.headers.get('cache-control'),'no-store');assert.equal(page.total,1);assert.equal(page.items[0].name,'TCP Solar planner');assert.equal(page.items[0].canonical,null);assert.equal(page.activationAllowed,false);assert(!JSON.stringify(page).includes('example.invalid'));
  const otherLogin=await post('/api/session','',{id:'foreign',password}),other=otherLogin.headers.get('set-cookie').split(';')[0];
  assert.equal((await (await fetch(base+route,{headers:{Cookie:other}})).json()).total,0);
  assert.equal((await fetch(base+route+'&limit=101',{headers:{Cookie:cookie}})).status,400);
  assert.equal((await post('/api/logout',cookie,{})).status,200);assert.equal((await fetch(base+route,{headers:{Cookie:cookie}})).status,401);
 }finally{await new Promise(resolve=>server.close(resolve));service.close();rmSync(dir,{recursive:true,force:true});}
});
