import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
const source=await readFile(new URL('public/sw.js',root),'utf8');
function worker({offline=false}={}) {
  const events={},stored=new Map(),network=[];
  const cache={put:async(k,v)=>stored.set(k,v),match:async k=>stored.get(k)};
  const context={URL,Response,self:{location:{href:'https://preview.test/hub69/sw.js'},addEventListener:(n,f)=>events[n]=f},caches:{open:async()=>cache},fetch:async(request)=>{network.push(request);if(offline&&typeof request!=='string')throw Error('offline');return new Response('fallback');}};
  vm.runInNewContext(source,context);return {events,stored,network};
}
test('offline install caches only a data-free fallback; API/auth/mutations are untouched',async()=>{
  const w=worker();let pending;w.events.install({waitUntil:p=>pending=p});await pending;
  assert.deepEqual([...w.stored.keys()],['https://preview.test/hub69/offline.html']);
  for(const [url,mode,method] of [['https://preview.test/api/entities','navigate','GET'],['https://preview.test/hub69/auth','navigate','GET'],['https://else.test/hub69/','navigate','GET'],['https://preview.test/hub69/','navigate','POST'],['https://preview.test/hub69/registry.js','cors','GET']]){
    w.events.fetch({request:{url,mode,method},respondWith(){assert.fail('private or non-shell request intercepted');}});
  }
});
test('shell navigation is network-first and falls back only on network failure',async()=>{
  for(const offline of [false,true]){
    const w=worker({offline});let p;w.events.install({waitUntil:v=>p=v});await p;
    w.events.fetch({request:{url:'https://preview.test/hub69/index.html',mode:'navigate',method:'GET'},respondWith:v=>p=v});
    assert.equal(await (await p).text(),'fallback');assert.equal(w.network.length,2);assert.equal(w.stored.size,1);
  }
});
test('manifest, generated PNG dimensions and both bundles agree',async()=>{
  const manifest=JSON.parse(await readFile(new URL('dist/manifest.webmanifest',root)));
  assert.equal(manifest.scope,'./');assert.equal(manifest.start_url,'./index.html#home');assert.equal(manifest.display,'standalone');
  for(const size of [192,512])for(const dir of ['dist','core-dist']){
    const b=await readFile(new URL(`${dir}/icon-${size}.png`,root));assert.equal(b.readUInt32BE(16),size);assert.equal(b.readUInt32BE(20),size);
  }
  const standalone=await readFile(new URL('HUB69-review.html',root),'utf8');assert.doesNotMatch(standalone,/<script[^>]+src=|rel="manifest"/);
});
test('registration is inert in file review and unsupported/insecure contexts',async()=>{
  const js=await readFile(new URL('public/pwa.js',root),'utf8');
  for(const [secure,protocol,worker] of [[true,'file:',true],[false,'http:',true],[true,'https:',false]]){
    vm.runInNewContext(js,{window:{isSecureContext:secure,addEventListener(){assert.fail('registered');}},navigator:worker?{serviceWorker:{}}:{},location:{protocol}});
  }
});
