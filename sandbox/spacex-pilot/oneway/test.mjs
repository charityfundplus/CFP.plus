// Self-contained tests: every test writes only to its own mkdtemp directory.
// Committed files under evidence/ are read-only historical receipts and are checked to be unchanged at the end.
import {test} from 'node:test';import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync,readdirSync,existsSync,symlinkSync,statSync} from 'node:fs';
import {tmpdir} from 'node:os';import {join,resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createServer} from 'node:http';
import {Adapter,sign,canonical,hash,loadPinned,guardDirection} from './core.mjs';
import {build} from './demo.mjs';
import {makeHandler} from './server.mjs';
const here=import.meta.dirname;
const now=new Date('2026-10-29T01:00:00Z');
const base={record_id:'SIM-20261029-001',source:'CFP+_SANDBOX',status:'sandbox_practice',timestamp_utc:'2026-10-29T01:00:00Z',version:'0.1'};
const tmp=()=>mkdtempSync(join(tmpdir(),'cfp-oneway-'));
function fresh(){const dir=tmp();return {dir,a:new Adapter(join(dir,'test.sqlite'),()=>now,{enabled:true})};}
const evidenceDir=resolve(here,'evidence');
const digestTree=dir=>Object.fromEntries(readdirSync(dir,{recursive:true}).filter(f=>statSync(join(dir,f)).isFile()).sort().map(f=>[f,hash(readFileSync(join(dir,f)))]));
const evidenceBefore=digestTree(evidenceDir);

test('E1 missing/extra/wrong-type fields rejected without records',()=>{const {a}=fresh();for(const p of [{...sign(base),status:undefined},{...sign(base),extra:'x'},{...sign(base),version:1}])assert.equal(a.ingest(p).result,'INVALID_PAYLOAD');assert.equal(a.snapshot().records.length,0);a.close();});
test('E2 incorrect hash rejected',()=>{const {a}=fresh();assert.equal(a.ingest({...sign(base),content_hash:'0'.repeat(64)}).result,'HASH_MISMATCH');assert.equal(a.snapshot().records.length,0);a.close();});
test('E3a reverse refused before any records transaction; only refusal audited',()=>{
 assert.throws(()=>guardDirection('SANDBOX_TO_CFP'),/WRITEBACK_BLOCKED/);
 const {a}=fresh();const calls=[];const exec=a.db.exec.bind(a.db);a.db.exec=sql=>{calls.push(sql);return exec(sql);};
 assert.equal(a.ingest(sign(base),'SANDBOX_TO_CFP').result,'WRITEBACK_BLOCKED');
 assert.deepEqual(calls,[],'no BEGIN/COMMIT issued for reverse request');
 const s=a.snapshot();assert.equal(s.records.length,0);assert.deepEqual(s.audit.map(x=>[x.result,x.record_id,x.hash]),[['WRITEBACK_BLOCKED',null,null]]);a.close();});
test('E3b direct source write denied by Node permission model (fresh probe, temp source)',t=>{
 const dir=tmp();const src=join(dir,'source.json');writeFileSync(src,JSON.stringify(sign(base),null,2));const before=hash(readFileSync(src));
 const r=spawnSync(process.execPath,['--permission',`--allow-fs-read=${join(here,'permission-probe.mjs')}`,`--allow-fs-read=${src}`,join(here,'permission-probe.mjs'),src],{encoding:'utf8'});
 if(r.error?.code==='EPERM'){t.skip('BLOCKED: subprocess spawn EPERM in this executor');return;}
 assert.equal(r.status,0,r.stderr);const receipt=JSON.parse(r.stdout);
 assert.equal(receipt.code,'ERR_ACCESS_DENIED');assert.equal(receipt.permission,'FileSystemWrite');
 assert.equal(hash(readFileSync(src)),before);assert.equal(hash(receipt.source),before);console.log('PRE_POST_SOURCE_SHA256',before);});
test('E4 UTC format, impossible date and >300s skew rejected; exact boundary allowed',()=>{const {a}=fresh();for(const t of ['2026-02-30T01:00:00Z','2026-10-29T01:05:01Z','2026-10-29T01:00:00+00:00'])assert.equal(a.ingest(sign({...base,timestamp_utc:t})).result,'INVALID_TIMESTAMP');assert.equal(a.ingest(sign({...base,timestamp_utc:'2026-10-29T01:05:00Z'})).result,'IMPORTED');a.close();});
test('E5 same ID+hash idempotent; different hash conflict with no overwrite',()=>{const {a}=fresh();assert.equal(a.ingest(sign(base)).result,'IMPORTED');assert.equal(a.ingest(sign(base)).result,'IDEMPOTENT');assert.equal(a.ingest(sign({...base,status:'review_pending'})).result,'CONFLICT');assert.deepEqual(a.snapshot().records,[sign(base)]);a.close();});
test('fixed canonical bytes and independent SHA256 known answer',()=>{assert.equal(hash('abc'),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');assert.equal(canonical(base),'{"record_id":"SIM-20261029-001","source":"CFP+_SANDBOX","status":"sandbox_practice","timestamp_utc":"2026-10-29T01:00:00Z","version":"0.1"}');const {a}=fresh();assert.equal(a.ingest({...sign(base),source:' CFP+_SANDBOX '}).result,'IMPORTED');a.close();});
test('failure rolls transaction back; retry survives reopen; rollback retains audit',()=>{const {a,dir}=fresh();assert.equal(a.ingest(sign(base),'CFP_TO_SANDBOX',true).result,'INJECTED_FAILURE');assert.equal(a.snapshot().records.length,0);assert.equal(a.ingest(sign(base)).result,'IMPORTED');a.close();const b=new Adapter(join(dir,'test.sqlite'),()=>now,{enabled:true});assert.equal(b.snapshot().records.length,1);b.rollback(base.record_id);assert.equal(b.snapshot().records.length,0);assert.deepEqual(b.snapshot().audit.map(x=>x.result),['INJECTED_FAILURE','IMPORTED','ROLLED_BACK']);assert.throws(()=>b.db.exec('DELETE FROM audit'),/APPEND_ONLY/);assert.throws(()=>b.db.exec("UPDATE audit SET result='fake'"),/APPEND_ONLY/);b.close();});
// Ported from PR #183
test('#183 kill switch OFF by default, refused before destination is created',()=>{const dir=tmp();const db=join(dir,'absent.sqlite');for(const o of [undefined,{},{enabled:'true'},{enabled:1}])assert.throws(()=>new Adapter(db,()=>now,o),/KILL_SWITCH_OFF/);assert.equal(existsSync(db),false);assert.throws(()=>build(join(dir,'out')),/KILL_SWITCH_OFF/);assert.equal(existsSync(join(dir,'out','sandbox.sqlite')),false);});
test('#183 symlinked destination database rejected',()=>{const dir=tmp();writeFileSync(join(dir,'real.sqlite'),'');symlinkSync(join(dir,'real.sqlite'),join(dir,'link.sqlite'));assert.throws(()=>new Adapter(join(dir,'link.sqlite'),()=>now,{enabled:true}),/SYMLINK_DESTINATION_REJECTED/);});
test('#183 source snapshot pin: tampered or unpinned source rejected before import',()=>{const dir=tmp();const src=join(dir,'source.json');writeFileSync(src,JSON.stringify(sign(base)));const pin=hash(readFileSync(src));assert.deepEqual(loadPinned(src,pin).input,sign(base));assert.throws(()=>loadPinned(src),/SOURCE_PIN_REQUIRED/);assert.throws(()=>loadPinned(src,'0'.repeat(64)),/SOURCE_SNAPSHOT_UNVERIFIED/);writeFileSync(src,JSON.stringify({...sign(base),status:'review_pending'}));assert.throws(()=>loadPinned(src,pin),/SOURCE_SNAPSHOT_UNVERIFIED/);});
test('UI export (built in temp dir) exactly matches persisted database',()=>{const dir=tmp();const {snapshot}=build(dir,()=>now,{enabled:true});const saved=JSON.parse(readFileSync(join(dir,'audit.json')));const html=readFileSync(join(dir,'preview.html'),'utf8');const embedded=JSON.parse(html.match(/id="data">(.*?)<\/script>/s)[1]);assert.deepEqual(embedded,saved);const b=new Adapter(join(dir,'sandbox.sqlite'),()=>now,{enabled:true});assert.deepEqual(JSON.parse(JSON.stringify(b.snapshot())),saved);b.close();assert.deepEqual(saved.audit.map(x=>x.result),['IMPORTED','IDEMPOTENT','WRITEBACK_BLOCKED']);assert.deepEqual(JSON.parse(JSON.stringify(snapshot)),saved);});
test('read-only preview handler denies writes and serves matching audit',()=>{const dir=tmp();build(dir,()=>now,{enabled:true});const handle=makeHandler(dir);for(const method of ['POST','PUT','PATCH','DELETE']){const res={writeHead(code){this.code=code;},end(body){this.body=body;}};handle({method,url:'/audit.json'},res);assert.equal(res.code,405);assert.equal(res.body,'WRITEBACK_BLOCKED');}for(const url of ['/../core.mjs','/evidence/audit.json','/sandbox.sqlite']){const res={writeHead(code){this.code=code;},end(){}};handle({method:'GET',url},res);assert.equal(res.code,404);}const res={writeHead(code){this.code=code;},end(body){this.body=body;}};handle({method:'GET',url:'/audit.json'},res);assert.equal(res.code,200);assert.deepEqual(JSON.parse(res.body),JSON.parse(readFileSync(join(dir,'audit.json'))));});
test('HTTP end-to-end on 127.0.0.1 (ephemeral port): GET ok, writes 405, unknown 404',async t=>{
 const dir=tmp();build(dir,()=>now,{enabled:true});const server=createServer(makeHandler(dir));
 try{await new Promise((ok,fail)=>{server.once('error',fail);server.listen(0,'127.0.0.1',ok);});}
 catch(e){if(['EPERM','EACCES'].includes(e.code)){t.skip(`BLOCKED: listen ${e.code}`);return;}throw e;}
 try{const url=`http://127.0.0.1:${server.address().port}`;
  const page=await fetch(url+'/');assert.equal(page.status,200);assert.match(page.headers.get('content-type'),/text\/html/);assert.equal(page.headers.get('x-content-type-options'),'nosniff');const body=await page.text();assert.match(body,/PRODUCTION NO-GO/);assert.match(body,/Không thể hiện hợp tác/);
  const audit=await fetch(url+'/audit.json');assert.equal(audit.status,200);assert.deepEqual(await audit.json(),JSON.parse(readFileSync(join(dir,'audit.json'))));
  for(const method of ['POST','PUT','PATCH','DELETE']){const r=await fetch(url+'/audit.json',{method,body:method==='DELETE'?undefined:'{}'});assert.equal(r.status,405);assert.equal(r.headers.get('allow'),'GET, HEAD');assert.equal(await r.text(),'WRITEBACK_BLOCKED');}
  assert.equal((await fetch(url+'/sandbox.sqlite')).status,404);
  assert.deepEqual(JSON.parse(readFileSync(join(dir,'audit.json'))).audit.length,3,'HTTP writes did not change audit');
 }finally{await new Promise(ok=>server.close(ok));}});
test('committed evidence/ was not modified by this test run',()=>{assert.deepEqual(digestTree(evidenceDir),evidenceBefore);});
