import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {harness} from './harness.mjs';
const root=new URL('../',import.meta.url);

test('HSTDN review deep links cover seven subjects and three contexts without accepting Registry IDs',()=>{
  const h=harness(),R=h.ctx.HUB69HSTDNReview,P=h.ctx.HUB69P0;
  assert.equal(R.subjects.length,7);
  for(const country of Object.keys(R.contexts))for(const s of R.subjects){const state=P.route('#hstdn/'+country+'/'+s.key);assert.equal(state.country,country);assert.equal(state.subject,s.key);}
  for(const path of ['#hstdn/vn/69118','#hstdn/vn/__proto__','#hstdn/us/spacex/extra','#hstdn/vn/%73tarlink','#hstdn/global/<script>','#hstdn/984/starlink','#commerce/global'])assert.equal(P.route(path).invalid,true,path);
});

test('one presenter renders field source, date, excerpt, status and next verification for all contexts',()=>{
  const h=harness(),R=h.ctx.HUB69HSTDNReview;
  for(const country of Object.keys(R.contexts))for(const s of R.subjects){
    const fields=R.fieldsFor(s.key,country),html=R.view({country,subject:s.key});
    assert.ok(fields.length>=10);assert.equal(new Set(fields.map(f=>f.key)).size,fields.length);
    for(const f of fields){assert.ok(f.sourceURL);assert.equal(f.sourceDate,'2026-10-19');assert.ok(f.excerpt);assert.ok(['BLOCKED','NOT VERIFIED'].includes(R.statusOf(f)));assert.ok(html.includes('data-field="'+f.key+'"'));}
    for(const label of ['Nguồn bàn giao','Ngày của nguồn','Trích đoạn nguồn','Nguồn gốc / receipt độc lập','Điều kiện kiểm chứng tiếp'])assert.ok(html.includes(label),label);
    assert.match(html,/VERIFIED: 0/);assert.doesNotMatch(html,/data-evidence-status="VERIFIED"/);
  }
});

test('Vietnam reported legal name and license do not migrate to US or global contexts',()=>{
  const R=harness().ctx.HUB69HSTDNReview;
  const vn=R.fieldsFor('starlink','vn'),license=vn.find(f=>f.key==='license');
  assert.match(vn.find(f=>f.key==='legal_name').value,/STARLINK SERVICES VIỆT NAM/);assert.equal(R.statusOf(license),'BLOCKED');
  assert.equal(license.sourceDate,'2026-10-19');assert.match(license.eventDate,/2026-03-03/);
  for(const country of ['us','global']){const rows=R.fieldsFor('starlink',country);assert.equal(rows.find(f=>f.key==='legal_name').value,null);assert.equal(rows.find(f=>f.key==='license').value,null);assert.doesNotMatch(R.view({country}),/CÔNG TY TNHH STARLINK SERVICES VIỆT NAM/);}
});

test('source-reported VERIFIED, booleans, URLs and claimed receipts cannot grant verification',()=>{
  const R=harness().ctx.HUB69HSTDNReview;
  for(const sourceStatus of ['VERIFIED','ACTIVE','APPROVED']){
    const f={key:'test',label:'Unit fixture',value:'Reported claim',sourceURL:'https://example.com/',sourceDate:'2026-10-19',excerpt:'Unit fixture',status:sourceStatus,verified:true,independent:true,reviewReceipt:'https://example.com/review'};
    assert.equal(R.statusOf(f),'NOT VERIFIED');assert.match(R.fieldView(f),/data-evidence-status="NOT VERIFIED"/);assert.doesNotMatch(R.fieldView(f),/data-evidence-status="VERIFIED"/);
  }
  assert.equal(R.statusOf({value:null,status:'VERIFIED'}),'BLOCKED');assert.equal(R.statusOf({value:'x',blocker:'missing primary'}),'BLOCKED');
});

test('subject and country controls retain the selected context and return valid routes',()=>{
  const h=harness({hash:'#hstdn/vn/starlink'});
  h.events.change({target:{dataset:{catalogFilter:'subject'},value:'spacex'}});assert.equal(h.ctx.location.hash,'#hstdn/vn/spacex');h.windowEvents.hashchange();
  h.events.change({target:{dataset:{catalogFilter:'country'},value:'us'}});assert.equal(h.ctx.location.hash,'#hstdn/us/spacex');h.windowEvents.hashchange();
  h.events.change({target:{dataset:{catalogFilter:'country'},value:'global'}});assert.equal(h.ctx.location.hash,'#hstdn/global/spacex');h.windowEvents.hashchange();
  assert.match(h.elements.get('hstdn-content').innerHTML,/Cổ phần/);assert.equal(h.elements.get('view-hstdn').hidden,false);
  const X=h.ctx.HUB69Explore;assert.equal(X.filterRoute({view:'commerce'},'country','global'),null);assert.equal(X.filterRoute({view:'hstdn'},'subject','__proto__'),null);
});

test('all new model navigation destinations resolve and contain no placeholder or unsafe external links',()=>{
  const h=harness(),R=h.ctx.HUB69HSTDNReview,P=h.ctx.HUB69P0;
  const states=[{country:'all'},...Object.keys(R.contexts).flatMap(country=>R.subjects.map(s=>({country,subject:s.key})))];
  for(const state of states){const html=R.view(state);for(const [,href] of html.matchAll(/href="([^"]*)"/g)){assert.ok(href&&href!=='#');if(href.startsWith('#'))assert.equal(P.route(href).invalid,undefined,href);else assert.ok(h.ctx.HUB69Model.safeURL(href));}}
});

test('legal entity, brand, product and Registry Parent remain separate with no inferred identity binding',async()=>{
  const h=harness(),R=h.ctx.HUB69HSTDNReview,before=JSON.stringify(h.ctx.HUB69_DATA);
  const schema=JSON.parse(await readFile(new URL('profile.schema.json',root),'utf8'));assert.ok(schema.required.includes('id'));assert.match(schema.properties.id.pattern,/0-9/);
  for(const s of R.subjects){h.go('#hstdn/vn/'+s.key);const keys=R.fieldsFor(s.key,'vn').map(f=>f.key);for(const k of ['entity_type','legal_name','trade_name','corporate_relationship','products'])assert.ok(keys.includes(k));}
  assert.equal(JSON.stringify(h.ctx.HUB69_DATA),before);assert.equal(h.values.size,0);
  for(const v of Object.values(R.binding))assert.equal(v,null);assert.equal(Object.isFrozen(R.binding),true);
});

test('ownership, clinical, Optimus and alias gaps stay blocked at the affected field only',()=>{
  const R=harness().ctx.HUB69HSTDNReview;
  for(const [subject,key] of [['spacex','ownership'],['tesla','optimus'],['xai','legal_aliases'],['x','x_relationship'],['neuralink','clinical'],['boring','loop']]){
    const rows=R.fieldsFor(subject,'vn');assert.equal(R.statusOf(rows.find(f=>f.key===key)),'BLOCKED');assert.equal(R.statusOf(rows.find(f=>f.key==='trade_name')),'NOT VERIFIED');
  }
});

test('API proposal is text only and source fields escape injected markup and unsafe URLs',()=>{
  const R=harness().ctx.HUB69HSTDNReview,html=R.view({country:'vn',subject:'xai'});
  assert.match(html,/http:\/\/api\.x\.ai\/v1/);assert.doesNotMatch(html,/href="http:\/\/api\.x\.ai/);
  const f={key:'<img src=x>',label:'<script>x</script>',value:'<svg onload=x>',sourceURL:'javascript:alert(1)',sourceDate:'<b>x</b>',excerpt:'<img src=x>',originalURL:'https://user:password@example.com/',eventDate:'<img>',blocker:'<script>'};
  const output=R.fieldView(f);assert.doesNotMatch(output,/<script|<img|<svg|href="javascript:|href="https:\/\/user:/);assert.match(output,/&lt;script/);
});

test('review module has the same bytes in offline and Core builds with no new network or storage path',async()=>{
  const js=await readFile(new URL('public/hstdn-review.js',root),'utf8');
  assert.doesNotMatch(js,/\bfetch\s*\(|XMLHttpRequest|WebSocket|localStorage|indexedDB/);
  for(const dir of ['dist','core-dist'])assert.equal(await readFile(new URL(dir+'/hstdn-review.js',root),'utf8'),js);
  assert.ok((await readFile(new URL('HUB69-review.html',root),'utf8')).includes(js.trim()));
  assert.match(await readFile(new URL('core-dist/registry.js',root),'utf8'),/records:\[\]/);
});

test('research notes stay outside Registry profiles and cannot become a fallback after Core authentication failure',async()=>{
  const api={snapshot:async()=>{throw Object.assign(Error('Expired fixture'),{status:401});},openai:async()=>({}),detail:async()=>({}),logout:async()=>{}};
  const h=harness({hash:'#hstdn/vn/starlink',coreClient:api});await new Promise(resolve=>setImmediate(resolve));
  assert.match(h.elements.get('hstdn-content').innerHTML,/ghi chú nghiên cứu, chưa phải dữ liệu API/);
  assert.equal(h.elements.get('records').innerHTML,'');assert.equal(h.elements.get('profile').innerHTML,'');
  h.go('#id/691181');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.elements.get('view-hstdn').hidden,true);assert.match(h.elements.get('profile').innerHTML,/hết hạn/);
  assert.doesNotMatch(h.elements.get('profile').innerHTML,/STARLINK|field-evidence|NOT VERIFIED/);
});

test('field review mobile source wraps evidence and retains touch-sized subject selection',async()=>{
  const css=await readFile(new URL('public/style.css',root),'utf8');
  assert.match(css,/\.field-grid\{display:grid;grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
  assert.match(css,/@media\(max-width:700px\)\{[\s\S]*?\.field-grid\{grid-template-columns:minmax\(0,1fr\)\}/);
  assert.match(css,/#review-subject\{[^}]*min-height:44px[^}]*font-size:16px/);
  assert.match(css,/\.field-evidence dd\{[^}]*overflow-wrap:anywhere/);
});
