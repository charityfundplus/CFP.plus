// Real loopback HTTP integration against the unchanged, pinned Codex 1 service.
// This is a short-lived test fixture, not a preview server or deployment.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,rmSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {harness} from '../tests/harness.mjs';
const pins=JSON.parse(readFileSync(new URL('./source-pins.json',import.meta.url)));
if(!process.env.CFP_CODEX1_SOURCE)throw Error('CFP_CODEX1_SOURCE must identify the pinned read-only Codex 1 checkout');
const root=resolve(process.env.CFP_CODEX1_SOURCE),office=join(root,'drafts/si-office');
assert.equal(execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),pins.codex1Revision);
for(const f of pins.files)assert.equal(createHash('sha256').update(readFileSync(join(root,f.path))).digest('hex'),f.sha256);
const {P2Sandbox}=await import(pathToFileURL(join(office,'sandbox/p2-service.mjs')));
const {createP2HTTP}=await import(pathToFileURL(join(office,'sandbox/p2-http.mjs')));
const {createRegistryClient}=await import(pathToFileURL(join(office,'public/registry-client.js')));
const settle=async h=>{for(let i=0;i<200;i++){if(!h.elements.get('core-status').innerHTML.includes('Đang đọc Core'))return;await new Promise(r=>setTimeout(r,5));}throw Error('Core UI did not settle');};
async function fixture(run,{sourceUnavailable=false}={}){
  const dir=mkdtempSync(join(tmpdir(),'cfp-codex2-integration-'));
  const service=new P2Sandbox(join(dir,'state.db'),{registrySource:{root,revision:sourceUnavailable?'0'.repeat(40):pins.codex1Revision}});
  const password='Synthetic-Codex2-loopback';service.provision({id:'viewer',password,role:'viewer',workspace:'alpha'});
  const server=createP2HTTP({service});let cookie='';
  try{
    await new Promise(done=>server.listen(0,'127.0.0.1',done));const origin='http://127.0.0.1:'+server.address().port;
    const transport=(path,options={})=>fetch(origin+path,{...options,headers:{Origin:origin,Cookie:cookie,...options.headers}});
    const client={...createRegistryClient({fetchImpl:transport}),async logout(){const r=await transport('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});assert.equal(r.status,200);}};
    const login=async()=>{const r=await transport('/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:'viewer',password})});assert.equal(r.status,200);cookie=r.headers.get('set-cookie').split(';')[0];};
    await run({client,transport,login});
  }finally{await new Promise(done=>server.close(done));service.close();rmSync(dir,{recursive:true,force:true});}
}
test('real Core -> UI: anonymous 401, login/retry, 224 references and dynamic record provenance',async()=>fixture(async({client,login})=>{
  const h=harness({hash:'#id/691181',coreClient:client});await settle(h);
  assert.ok(h.elements.get('core-status').innerHTML.includes('chưa đăng nhập'));assert.ok(!h.elements.get('profile').innerHTML.includes('69118 · OpenAI'));
  await login();await h.events.click(h.click('[data-core-retry]'));await settle(h);
  assert.ok(h.elements.get('profile').innerHTML.includes('href="#id/69118"'));
  assert.ok(h.elements.get('profile').innerHTML.includes(pins.codex1Revision.slice(0,7)));
  assert.ok(h.elements.get('profile').innerHTML.includes('SHA-256'));assert.ok(h.elements.get('source-caption').textContent.includes(pins.codex1Revision));
  h.go('#id');await settle(h);assert.equal(h.elements.get('records').innerHTML.match(/class="record-card"/g).length,224);
}));
test('real Core -> UI: 0 and 000 stay distinct and 404 clears all earlier profile data',async()=>fixture(async({client,login})=>{
  await login();const h=harness({hash:'#id/691181',coreClient:client});await settle(h);
  h.go('#id/000');await settle(h);assert.ok(h.elements.get('profile').innerHTML.includes('ID chưa có'));assert.ok(!h.elements.get('profile').innerHTML.includes('ChatGPT'));
  assert.equal(h.elements.get('records').innerHTML,'');assert.equal(h.ctx.location.hash,'#id/000');
}));
test('real Core -> UI: OpenAI and six vaults use Core readback, never a fabricated HSTDN or live sync',async()=>fixture(async({client,login})=>{
  await login();const h=harness({hash:'#openai',coreClient:client});await settle(h);
  const html=h.elements.get('openai-profile').innerHTML;
  for(const id of ['911','6911','69118','691181'])assert.ok(html.includes('href="#id/'+id+'"'));
  assert.ok(html.includes('Projects in ChatGPT'));assert.ok(html.includes('Chưa cấp / Chưa cấp / Chưa cấp / Chưa cấp'));
  h.go('#vaults');await settle(h);assert.equal((h.elements.get('vault-monitor').innerHTML.match(/Kết nối được xác nhận: Chưa có/g)||[]).length,6);
}));
test('real Core -> UI: logout revokes the session and hides profiles and saved record labels',async()=>fixture(async({client,login})=>{
  await login();const h=harness({hash:'#id/691181',coreClient:client});await settle(h);
  await h.events.click(h.click('[data-save]'));assert.ok(h.elements.get('saved-items').innerHTML.includes('ChatGPT'));
  await h.events.click(h.click('[data-core-logout]'));assert.ok(!h.elements.get('profile').innerHTML.includes('ChatGPT'));assert.ok(!h.elements.get('saved-items').innerHTML.includes('ChatGPT'));
  await assert.rejects(client.snapshot(),e=>e.status===401);
}));
test('UI clears rows after an injected 503 following a real Core read; no bundled snapshot fallback',async()=>fixture(async({client,login})=>{
  await login();const h=harness({hash:'#id/691181',coreClient:client});await settle(h);
  client.snapshot=async()=>{throw Object.assign(Error('REGISTRY_SOURCE_UNAVAILABLE'),{status:503});};
  await h.events.click(h.click('[data-core-retry]'));assert.ok(h.elements.get('core-status').innerHTML.includes('không sẵn sàng'));assert.ok(!h.elements.get('profile').innerHTML.includes('ChatGPT'));assert.equal(h.elements.get('records').innerHTML,'');
}));
test('real Core source revision mismatch returns 503 and the UI remains empty',async()=>fixture(async({client,login})=>{
  await login();const h=harness({hash:'#id/691181',coreClient:client});await settle(h);
  assert.ok(h.elements.get('core-status').innerHTML.includes('không sẵn sàng'));assert.equal(h.elements.get('records').innerHTML,'');
  assert.ok(!h.elements.get('profile').innerHTML.includes('ChatGPT'));
},{sourceUnavailable:true}));
