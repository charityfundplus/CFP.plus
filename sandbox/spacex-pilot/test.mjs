import {createHash} from 'node:crypto';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {Importer} from './adapter.mjs';
import {server,handler} from './server.mjs';
const registry = JSON.parse(await readFile(new URL('./registry.json',import.meta.url)));
const sourceSha = '835616308111f6851c0387fa9f5eda60c9ffa624';
const sample = registry['691121']; // Existing Claude review candidate; test consent only, NOT governance approval.
const options = {sourceSha};
test('approval defaults to deny; registry statuses are preserved',()=>{
 const importer = new Importer(registry);
 assert.throws(()=>importer.import([sample],options),/NOT_APPROVED/);
 assert.equal(importer.rows.length,0);
 assert.equal(importer.events[0].outcome,'BLOCKED');
});
test('approved test fixture imports once; retry is idempotent; copies cannot mutate state',()=>{
 const importer = new Importer(registry,[sample.id]);
 assert.equal(importer.import([sample],options).changed,1);
 assert.equal(importer.import([sample],options).changed,0);
 const copy = importer.rows; copy[0].record.name='mutated';
 assert.equal(importer.rows[0].record.name,sample.name);
 assert.equal(importer.rows[0].record.status,sample.status);
});
test('reverse direction blocked and original source bytes unchanged',async()=>{
 const before=await readFile(new URL('./registry.json',import.meta.url));
 const importer=new Importer(registry,[sample.id]);
 assert.throws(()=>importer.import([sample],{...options,direction:'SPACEX_TO_CFP'}),/WRITEBACK_BLOCKED/);
 assert.equal(importer.rows.length,0);
 assert.deepEqual(await readFile(new URL('./registry.json',import.meta.url)),before);
});
test('unknown fields, parent changes, unapproved IDs, missing provenance fail atomically',()=>{
 for (const record of [{...sample,secret:'DO_NOT_LOG'}, {...sample,parent_id:'69118'}, {...sample,id:'00000'}]) {
  const importer=new Importer(registry,[sample.id]);
  assert.throws(()=>importer.import([sample,record],options));
  assert.equal(importer.rows.length,0);
  assert.ok(!JSON.stringify(importer.events).includes('DO_NOT_LOG'));
 }
 assert.throws(()=>new Importer(registry,[sample.id]).import([sample]),/SOURCE_SHA_REQUIRED/);
});
test('mismatch, duplicate batch and kill switch denied',()=>{
 assert.throws(()=>new Importer(registry,[sample.id]).import([{...sample,name:'fake'}],options),/REGISTRY_MISMATCH/);
 assert.throws(()=>new Importer(registry,[sample.id]).import([sample,sample],options),/DUPLICATE_ID/);
 const importer=new Importer(registry,[sample.id]);importer.stop();
 assert.throws(()=>importer.import([sample],options),/KILL_SWITCH/);
});
test('HTTP preview serves allowlisted assets and rejects every write method',{skip:process.env.PILOT_SOCKET_TEST !== '1' ? 'NOT RUN: set PILOT_SOCKET_TEST=1 in a sandbox allowing loopback sockets' : false},async()=>{
 const app=server();await new Promise(resolve=>app.listen(0,'127.0.0.1',resolve));
 const origin=`http://127.0.0.1:${app.address().port}`;
 try {
  assert.equal((await fetch(origin)).status,200);
  assert.equal((await fetch(origin+'/registry.json')).status,200);
  for(const method of ['POST','PUT','PATCH','DELETE']) assert.equal((await fetch(origin+'/registry.json',{method})).status,405);
  assert.equal((await fetch(origin+'/adapter.mjs')).status,404);
  assert.equal((await fetch(origin+'/%2e%2e/server.mjs')).status,404);
 } finally {await new Promise(resolve=>app.close(resolve));}
});

test('missing ID, wrong parent and wrong source version rejected individually',()=>{
 const importer=new Importer(registry,[sample.id]);
 const missing={...sample};delete missing.id;
 assert.throws(()=>importer.import([missing],options),/NOT_APPROVED/);
 assert.throws(()=>importer.import([{...sample,parent_id:'69118'}],options),/REGISTRY_MISMATCH/);
 assert.throws(()=>importer.import([sample],{sourceSha:'a'.repeat(40)}),/SOURCE_VERSION_MISMATCH/);
 assert.equal(importer.rows.length,0);
});
test('read-only request handler rejects writes and traversal without opening a socket',async()=>{
 async function request(method,url){
  const result={headers:{},setHeader(k,v){this.headers[k]=v},writeHead(status,headers){this.status=status;Object.assign(this.headers,headers)},end(body){this.body=body}};
  await handler({method,url},result);return result;
 }
 for(const method of ['POST','PUT','PATCH','DELETE']) assert.equal((await request(method,'/registry.json')).status,405);
 assert.equal((await request('GET','/')).status,200);
 assert.equal((await request('HEAD','/')).body,undefined);
 assert.equal((await request('GET','/registry.json')).status,200);
 for(const url of ['/adapter.mjs','/../registry.json','/%2e%2e/server.mjs','/?path=/etc/passwd']) assert.equal((await request('GET',url)).status,404);
});

test('fixture is an exact versioned source copy, not an authoritative runtime registry',async()=>{
 const bytes=await readFile(new URL('./registry.json',import.meta.url));
 const gitBlob=createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');
 assert.equal(gitBlob,'1f18068d66379ce90bb079dc56c77b4c4d66dcdf');
});
