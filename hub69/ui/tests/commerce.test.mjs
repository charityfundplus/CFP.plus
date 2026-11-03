import test from 'node:test';
import assert from 'node:assert/strict';
import {harness} from './harness.mjs';
const h=harness(),K=h.ctx.HUB69Commerce;
const envelope=()=>({items:[{key:'draft-product',name:'Học liệu thử',kind:'product',status:'SANDBOX_ONLY',maturity:'draft',synthetic:true,verification:'NOT VERIFIED',id:null,parent:null,did:null,canonical:null}],total:1,limit:30,offset:0,catalogRevision:'c'.repeat(64),sandbox:true,synthetic:true,readOnly:true,activationAllowed:false,registryWrites:0});
test('search folds Vietnamese accents, combines category and yields useful empty state without Registry writes',()=>{
  const before=JSON.stringify(h.ctx.HUB69_DATA);
  h.go('#catalog');assert.match(h.elements.get('commerce-content').innerHTML,/4 kết quả/);
  h.events.input({target:{id:'commerce-search',value:'DAO TAO'}});assert.match(h.elements.get('commerce-results').innerHTML,/Đào tạo/);assert.doesNotMatch(h.elements.get('commerce-results').innerHTML,/Bộ hạt/);
  h.events.change({target:{dataset:{catalogFilter:'commerce-kind'},value:'product'}});assert.equal(h.ctx.location.hash,'#catalog/product');h.windowEvents.hashchange();assert.match(h.elements.get('commerce-content').innerHTML,/Không có kết quả/);
  assert.equal(JSON.stringify(h.ctx.HUB69_DATA),before);for(const r of K.samples)for(const key of ['id','parent','did','canonical'])assert.equal(r[key],null);
});
test('catalog detail and generated navigation stay inside the HUB and never offer checkout or a fabricated canonical',()=>{
  const sample=K.samples[0];h.go('#catalog/item/'+sample.key);const html=h.elements.get('commerce-content').innerHTML;
  assert.match(html,/Chưa gắn định danh/);assert.match(html,/href="#home"/);assert.match(html,/href="#catalog\/product"/);assert.doesNotMatch(html,/href="https:\/\/cfp.plus\/sample|data-checkout|data-order/);
  for(const bad of ['#catalog/item/<script>','#catalog/product/extra','#catalog/__proto__','#catalog/item/'+('a'.repeat(121))])assert.equal(h.ctx.HUB69P0.route(bad).invalid,true);
});
test('Core catalogue validation strips private fields and rejects identity claims, active flags, duplicates and malformed pagination',()=>{
  const good=envelope();good.items[0].customerEmail='private@example.invalid';assert.equal(K.validate(good).items[0].customerEmail,undefined);
  for(const mutate of [d=>d.activationAllowed=true,d=>d.synthetic=false,d=>d.registryWrites=1,d=>d.items[0].canonical='https://cfp.plus/1',d=>d.items[0].synthetic=false,d=>d.items[0].status='ACTIVE',d=>d.items[0].id='001',d=>d.items.push(d.items[0]),d=>d.offset=-1,d=>d.limit=0,d=>d.catalogRevision='invalid']){
    const d=envelope();mutate(d);assert.throws(()=>K.validate(d),/CATALOG_/);
  }
  const d=envelope();d.items[0].name='<img src=x onerror=alert(1)>';
  const html=K.view({view:'commerce',kind:'all'},{coreMode:true,coreState:{phase:'ready',data:{catalog:{phase:'ready',data:K.validate(d)}}}});
  assert.ok(!html.includes('<img'));assert.match(html,/&lt;img/);
});
test('same Core session clears commerce on reload/logout/failure, never substituting browser samples',async()=>{
  const provenance={revision:'a'.repeat(40),files:[]};let fail=false;
  const client={snapshot:async()=>({records:[],provenance,sourceCommit:provenance.revision}),openai:async()=>({provenance}),catalog:async()=>{if(fail)throw Object.assign(Error('forbidden'),{status:403});return envelope();},logout:async()=>{}};
  const c=h.ctx.HUB69CoreBinding.createController({client:async()=>client,onChange(){}});
  await c.load();assert.equal(c.getState().data.catalog.phase,'ready');
  fail=true;const pending=c.load();assert.equal(c.getState().data,null);await pending;
  assert.equal(c.getState().data.catalog.data,null);
  const html=K.view({view:'commerce'},{coreMode:true,coreState:c.getState()});assert.match(html,/Danh mục Core chưa sẵn sàng/);assert.doesNotMatch(html,/Bộ hạt giống/);
  await c.logout();assert.equal(c.getState().data,null);
});
test('opening a result on a later Core page retains its query category and offset',async()=>{
  const provenance={revision:'a'.repeat(40),files:[]},requests=[];
  const client={snapshot:async()=>({records:[],sourceCommit:provenance.revision,provenance}),openai:async()=>({provenance}),catalog:async options=>{
    requests.push(options);const d=envelope();d.offset=options.offset;d.total=61;d.items[0].key='page-'+options.offset;return d;
  },logout:async()=>{}};
  const local=harness({hash:'#catalog/product',coreClient:client});
  const tick=()=>new Promise(r=>setImmediate(r));await tick();
  await local.events.click({target:{closest:s=>s==='[data-catalog-page]'?{dataset:{catalogPage:'next'}}:null}});await tick();
  assert.equal(requests.at(-1).offset,30);
  local.go('#catalog/item/page-30');await tick();
  assert.equal(requests.at(-1).offset,30);assert.equal(requests.at(-1).kind,'product');
  assert.match(local.elements.get('commerce-content').innerHTML,/Chưa gắn định danh/);
});
