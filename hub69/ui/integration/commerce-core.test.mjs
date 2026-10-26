// Real loopback catalog HTTP -> existing UI controller/DOM stubs.
// Registry reads are bound to an exact existing Git revision; no Registry write occurs.
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {harness} from '../tests/harness.mjs';
const source=process.env.CFP_COMMERCE_CORE_SOURCE;
if(!source)throw Error('CFP_COMMERCE_CORE_SOURCE must identify reviewed Core sandbox source');
const office=resolve(source,'drafts/si-office');
const {P2Sandbox}=await import(pathToFileURL(join(office,'sandbox/p2-service.mjs')));
const {createP2HTTP}=await import(pathToFileURL(join(office,'sandbox/p2-http.mjs')));
const {createRegistryClient}=await import(pathToFileURL(join(office,'public/registry-client.js')));
const revision=execFileSync('git',['-C',source,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const {registry}=await import(pathToFileURL(join(office,'model.mjs')));
const settle=async h=>{for(let n=0;n<100;n++){if(!h.elements.get('core-status').innerHTML.includes('Đang đọc Core'))return;await new Promise(r=>setTimeout(r,10));}throw Error('UI_LOAD_TIMEOUT');};
test('same Core session serves catalog to Website/App/TMTC; search, reload and logout revoke visible rows',async()=>{
  const dir=mkdtempSync(join(tmpdir(),'cfp-ui-catalog-')),service=new P2Sandbox(join(dir,'state.db'),{registrySource:{root:resolve(source),revision}});
  const pairKey='hub69-content-demo',password='Synthetic-UI-Integration';
  service.provision({id:'editor',password,role:'editor',workspace:'alpha',pairs:[pairKey]});
  const token=service.login('editor',password),developer=registry.entities.find(r=>r.type==='developer'&&!registry.blockedCountries.includes(r.ai_country_id));
  const profile=await service.execute(token,'officeCreate',{pairKey,kind:'profile',input:{name:'Synthetic test supplier',country:developer.ai_country_id,developer:developer.id,source:'https://example.invalid/private',identityEvidence:'https://example.invalid/private',synthetic:true}});
  await service.execute(token,'officeCreate',{pairKey,kind:'product',input:{name:'Core learning kit',source:'https://example.invalid/private',officeRef:profile.key,maturity:'prototype',synthetic:true}});
  const server=createP2HTTP({service});let cookie='';
  try{
    await new Promise((done,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',done);});const origin='http://127.0.0.1:'+server.address().port;
    const transport=(path,options={})=>fetch(origin+path,{...options,headers:{Origin:origin,Cookie:cookie,...options.headers}});
    const registryClient=createRegistryClient({fetchImpl:transport});
    const h=harness({hash:'#catalog',coreClient:{...registryClient,catalog:async options=>{
      const params=new URLSearchParams({pairKey,query:options?.query||'',kind:options?.kind||'all',limit:'30',offset:String(options?.offset||0)});
      const r=await transport('/api/v1/commerce/catalog?'+params);if(!r.ok)throw Object.assign(Error('catalog denied'),{status:r.status});return r.json();
    },logout:async()=>{const r=await transport('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});assert.equal(r.status,200);}}});
    await settle(h);assert.match(h.elements.get('commerce-content').innerHTML,/Danh mục Core chưa sẵn sàng/);assert.doesNotMatch(h.elements.get('commerce-content').innerHTML,/Bộ hạt giống/);
    const login=await transport('/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:'editor',password})});assert.equal(login.status,200);cookie=login.headers.get('set-cookie').split(';')[0];
    await h.events.click(h.click('[data-core-retry]'));await settle(h);assert.match(h.elements.get('commerce-content').innerHTML,/Core learning kit/);assert.match(h.elements.get('commerce-content').innerHTML,/2 kết quả/);assert.match(h.elements.get('source-caption').textContent,new RegExp(revision));
    h.go('#id/691181');await settle(h);assert.match(h.elements.get('profile').innerHTML,/ChatGPT/);assert.match(h.elements.get('profile').innerHTML,/href="#id\/69118"/);
    h.go('#catalog');await settle(h);
    h.events.input({target:{id:'commerce-search',value:'learning'}});await h.events.click(h.click('[data-catalog-read]'));await settle(h);assert.match(h.elements.get('commerce-content').innerHTML,/1 kết quả/);
    h.go('#app');await settle(h);assert.match(h.elements.get('app-content').innerHTML,/href="#catalog"/);
    h.go('#commerce');await settle(h);assert.match(h.elements.get('commerce-content').innerHTML,/Core learning kit/);
    await h.events.click(h.click('[data-core-logout]'));assert.doesNotMatch(h.elements.get('commerce-content').innerHTML,/Core learning kit/);assert.match(h.elements.get('commerce-content').innerHTML,/Danh mục Core chưa sẵn sàng/);
    assert.equal((await transport('/api/v1/commerce/catalog?pairKey='+pairKey)).status,401);
  }finally{await new Promise(done=>server.close(done));service.close();rmSync(dir,{recursive:true,force:true});}
});
