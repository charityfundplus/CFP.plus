import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {inspect} from './team-readiness.mjs';
const source=JSON.parse(readFileSync(new URL('./source-snapshot.json',import.meta.url),'utf8'));
const copy=()=>structuredClone(source);
function replace(s,path,content){const f=s.files.find(f=>f.path===path);f.content=content;f.sha=createHash('sha1').update(`blob ${Buffer.byteLength(content)}\0`).update(content).digest('hex');}

test('actual inventory detects source conflicts without mutating original IDs or statuses',()=>{
 const before=JSON.stringify(source),report=inspect(source);
 assert.equal(JSON.stringify(source),before);
 assert(report.records.find(r=>r.id==='6911513').findings.includes('PARENT_LABEL_REVIEW'));
 assert(report.records.find(r=>r.id==='698461').findings.includes('DEVELOPER_LINEAGE_REVIEW'));
 assert(report.records.find(r=>r.id==='69845').findings.some(f=>f.startsWith('SAME_NAME_DISTINCT_IDS')));
 assert(report.records.some(r=>r.id==='691001'));
 assert.equal(report.records.find(r=>r.id==='69849').status,'RESERVED / NOT AN ENTITY');
});
test('source bytes and revision must be intact',()=>{
 const s=copy();s.files[0].content+=' ';
 assert.throws(()=>inspect(s),/SOURCE_INTEGRITY/);
 s.revision='b75b780';assert.throws(()=>inspect(s),/PINNED_REVISION/);
});
test('directory ACTIVE and caller claims cannot promote operational status',()=>{
 const s=copy();s.ready=true;s.active=true;s.approved=true;
 const r=inspect(s);assert.equal(r.counts.readyPairs,0);assert.equal(r.counts.activePairs,0);
 assert.equal(r.activationAllowed,false);assert.equal(r.grantAllowed,false);assert.equal(r.providerCalls,0);
 assert(r.records.every(row=>row.active===false));assert.equal(r.counts.blockedPairs,null);
 assert.equal(r.counts.trainingTemplates,3);assert(r.templates.every(row=>row.id===null));
});
test('synthetic identity cannot be silently bound to real Registry IDs',()=>{
 const s=copy(),path='drafts/si-office/configs/pairs.json';
 const pairs=JSON.parse(s.files.find(f=>f.path===path).content);pairs[0].identity.id='691183';
 replace(s,path,JSON.stringify(pairs));assert.throws(()=>inspect(s),/SYNTHETIC_ID_BINDING/);
});
test('numeric conversion of IDs fails rather than dropping zeros',()=>{
 const s=copy(),path='registry/ai-entity-registry.json';
 const registry=JSON.parse(s.files.find(f=>f.path===path).content);registry['691001'].id=691001;
 replace(s,path,JSON.stringify(registry));assert.throws(()=>inspect(s),/ID_STRING_REQUIRED/);
});
