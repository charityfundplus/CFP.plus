import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const context=vm.createContext({URL});
for(const f of ['model.js','p0.js'])vm.runInContext(await readFile(new URL('../public/'+f,import.meta.url),'utf8'),context);
vm.runInContext((await readFile(new URL('../public/registry.js',import.meta.url),'utf8')).replace('window.HUB69_DATA','globalThis.data'),context);
const M=context.HUB69Model,P=context.HUB69P0,records=context.data.records;
const plain=x=>JSON.parse(JSON.stringify(x));
test('five groups cover ten chapters without replacing numeric ID 0 or 000',()=>{
  assert.deepEqual(plain(P.groups.map(g=>g.id)),['V','000','135','246','789']);
  const ids=P.groups.flatMap(g=>g.chapters).sort();assert.deepEqual(plain(ids),[...'0123456789']);
  assert.equal(P.chapters.find(c=>c.id==='0').group,'000');
  assert.equal(M.lookup(records,'000').kind,'missing');assert.equal(P.route('#group/000').group,'000');
  assert.equal(P.route('#id/000').id,'000');assert.equal(P.route('#id/0').id,'0');
});
test('all group/chapter deep links resolve and malformed structural routes fail closed',()=>{
  for(const g of P.groups)assert.equal(P.route('#group/'+g.id).view,'chapters');
  for(const c of P.chapters)assert.equal(P.route('#chapter/'+c.id).chapter,c.id);
  for(const path of ['#group/0','#group/v','#chapter/00','#chapter/10','#chapter/<script>','#group/000/1'])assert.equal(P.route(path).invalid,true);
});
test('real source supports Chapter 6 → OpenAI → ChatGPT without mutating Parent',()=>{
  const before=JSON.stringify(records),html=P.chapterView(P.chapters[6],records);
  assert.ok(html.indexOf('Chương 6')<html.indexOf('href="#id/69118"'));
  assert.ok(html.indexOf('href="#id/69118"')<html.indexOf('href="#id/691181"'));
  assert.ok(html.includes('Parent nguồn: 69118'));assert.ok(html.includes('Parent chưa có trong nguồn'));
  assert.equal(JSON.stringify(records),before);
});
test('all ten chapters render while empty chapters create no child identities',()=>{
  const html=P.mapView(records);
  for(let i=0;i<10;i++)assert.ok(html.includes('id="chapter-'+i+'"'));
  const empty=P.chapterView(P.chapters[9],records);
  assert.ok(empty.includes('Chưa có bản ghi con'));assert.ok(!empty.includes('href="#id/'));
});
test('V is coordination, 000 is a navigation group and neither rewrites lineage',()=>{
  const v=P.mapView(records,{group:'V'}),zero=P.mapView(records,{group:'000'});
  assert.ok(v.includes('Điều phối tổng thể'));assert.ok(v.includes('href="#master"'));
  assert.ok(!v.includes('class="id-tree"'));assert.ok(zero.includes('id="chapter-0"'));
  assert.ok(!zero.includes('id="chapter-6"'));
});
test('source validation detects duplicates, missing parents, cycles, chapter conflicts and cross-chapter links',()=>{
  const fixture=[{id:'06',chapter:'0'},{id:'06'},{id:'61',parent_id:'62'},{id:'62',parent_id:'61'},{id:'63',parent_id:'99'},{id:'11',parent_id:'06',chapter:'2'}];
  const codes=P.validate(fixture).map(i=>i.code);
  for(const c of ['DUPLICATE_ID','PARENT_MISSING','PARENT_CYCLE','CHAPTER_CONFLICT','CROSS_CHAPTER_PARENT'])assert.ok(codes.includes(c));
  assert.equal(M.lookup(fixture,'06').kind,'ambiguous');
});
test('cyclic tree terminates with a visible warning rather than recursive rendering',()=>{
  const r=[{id:'61',parent_id:'62',name:'Synthetic A'},{id:'62',parent_id:'61',name:'Synthetic B'}];
  const html=P.chapterView(P.chapters[6],r);assert.ok(html.includes('vòng lặp'));assert.ok(html.length<5000);
});
test('parent unavailable in snapshot is shown verbatim without synthesizing an entity',()=>{
  const r={id:'001',parent_id:'000',name:'Synthetic unit fixture',type:'si'};
  const html=M.profile(r,[r],[]);assert.ok(html.includes('<code>000</code>'));assert.ok(!html.includes('href="#id/000"'));
});
test('all requested entity classes have a shared profile schema and safe type labels',()=>{
  for(const type of ['pair','software','si','ai','robot','developer','hstdn','country','organization','entity']){
    const r={id:'001',type,name:'Synthetic unit fixture'};
    const html=M.profile(r,[r],[])+P.profileExtra(r,[r]);
    assert.ok(html.includes(P.types[type]));
    for(const key of ['Parent','Nhà phát triển','Nguồn gốc','Evidence','Trạng thái xác minh'])assert.ok(html.includes(key));
  }
});
test('pair project section keeps the existing ID and emits no guessed project URL',()=>{
  const html=P.projectsView({id:'0007',type:'pair'});
  for(const text of ['Làm Dự Án tại ChatGPT','ID 0007','Tên dự án','Phạm vi','Trạng thái'])assert.ok(html.includes(text));
  assert.ok(!html.includes('href='));assert.equal(P.projectsView({id:'0007',type:'ai'}),'');
});
const receipt={url:'https://chatgpt.com/',verified:true,visibility:'public',checkedAt:'2026-10-16T14:00:00Z',evidenceURL:'https://github.com/charityfundplus/CFP.plus/issues/130'};
test('project external links require public verification receipt and a valid timestamp',()=>{
  assert.equal(P.verifiedLink(receipt),'https://chatgpt.com/');
  for(const change of [{verified:false},{visibility:'private'},{checkedAt:null},{checkedAt:'2026-99-99T12:00:00Z'},{evidenceURL:null},{url:'javascript:alert(1)'},{url:'https://user:password@chatgpt.com/'}])assert.equal(P.verifiedLink({...receipt,...change}),null);
});
test('private project metadata is not rendered; public unverified links remain inactive',()=>{
  const html=P.projectsView({id:'0007',type:'pair',chatgptProjects:[{visibility:'private',name:'PRIVATE_SENTINEL'},{visibility:'public',name:'Public unit fixture',scope:'Test scope',status:'PENDING',link:{...receipt,verified:false}}]});
  assert.ok(!html.includes('PRIVATE_SENTINEL'));assert.ok(html.includes('Public unit fixture'));assert.ok(!html.includes('href="https://chatgpt.com'));
});
test('project names and scope markup are escaped even with a verified link',()=>{
  const html=P.projectsView({id:'0007',type:'pair',chatgptProjects:[{visibility:'public',name:'<img src=x>',scope:'<script>x</script>',status:'<b>x</b>',link:receipt}]});
  assert.ok(!html.includes('<img'));assert.ok(!html.includes('<script>'));assert.ok(html.includes('href="https://chatgpt.com/"'));
});
test('generic template switches project section by entity class without creating a record',()=>{
  assert.ok(P.templateView('pair').includes('Làm Dự Án tại ChatGPT'));
  for(const type of ['developer','hstdn','country','robot'])assert.ok(!P.templateView(type).includes('Làm Dự Án tại ChatGPT'));
  assert.ok(!P.templateView('pair').includes('href="https://chatgpt.com/'));
});
test('OpenAI view separates developer and product; no HSTDN ID or partnership is invented',()=>{
  const html=P.openaiView(records);
  for(const t of ['NHÀ PHÁT TRIỂN','SẢN PHẨM / AI','69118','691181','Parent 69118','Chờ Codex 1','chưa có Evidence xác nhận'])assert.ok(html.includes(t));
  assert.ok(!html.includes('HSTDN ID 69118'));assert.ok(!html.includes('href="https://openai.com'));
});
test('OpenAI view fails closed when expected source identity or parent is missing',()=>{
  const html=P.openaiView([{id:'69118',name:'Different identity',type:'developer'},{id:'691181',name:'ChatGPT',parent_id:'unverified'}]);
  assert.ok(!html.includes('href="#id/69118"'));assert.ok(!html.includes('href="#id/691181"'));
});
test('six vaults disclose unknown last sync and quantum research separately from source snapshot',()=>{
  assert.equal(P.vaults.length,6);assert.ok(P.vaults.every(v=>v.lastSync===null));
  assert.equal(P.vaults.find(v=>v.key==='quantum').phase,'RESEARCH');
  assert.equal(P.vaults.find(v=>v.key==='github').phase,'SNAPSHOT');
  const html=P.vaultsView();assert.ok(html.includes('Chưa deploy'));assert.ok(html.includes('Không có phép đo trực tiếp'));
  assert.ok(!html.includes('SYNC VERIFIED'));assert.ok(!html.includes('CONNECTED'));
});
test('unverified canonical and official URLs are readable but never active external links',()=>{
  for(const r of records){const html=M.profile(r,records,[]);assert.ok(!html.includes('href="https://'));}
});
test('every generated navigation href points to an implemented route or an evidence source',async()=>{
  const html=await readFile(new URL('../public/index.html',import.meta.url),'utf8');
  const output=html+P.mapView(records)+P.vaultsView()+P.openaiView(records)+P.templateView()+records.map(r=>M.profile(r,records,[])+P.profileExtra(r,records)).join('');
  const hashes=[...output.matchAll(/href="(#[^"]+)"/g)].map(m=>m[1]);
  for(const hash of hashes){if(hash==='#content')continue;assert.ok(!P.route(hash).invalid,hash);}
  assert.ok(hashes.length>150);
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);
});
