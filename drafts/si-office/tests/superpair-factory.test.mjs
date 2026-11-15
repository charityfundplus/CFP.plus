import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {registry} from '../model.mjs';
import {classifyRecord,buildPairConfig,batchBuild,chapterOf,linkTemplate} from '../core/superpair-factory.mjs';
import {validateConfig} from '../core/core-engine.mjs';
import {run} from '../scripts/superpair-init.mjs';
import {diagnose} from '../scripts/env-doctor.mjs';

test('factory never binds or issues a Canonical ID',()=>{
 for(const {config,registryRef} of batchBuild().built){
  for(const k of ['id','parent','did','canonical'])assert.equal(config.identity[k],null);
  assert.equal(config.identity.verification,'SYNTHETIC ONLY');
  assert.equal(registryRef.identityBound,false);
  assert.equal(registryRef.permanentLinkVerified,false);
  assert.ok(registry.entities.some(e=>e.id===registryRef.id),'only existing registry IDs are referenced');
  assert.deepEqual(validateConfig(config),config);
 }
});

test('blocked country and conflicts are held for Human Governance',()=>{
 assert.equal(classifyRecord('691181').eligibility,'HELD');
 assert.throws(()=>buildPairConfig('691181'),/HELD_HUMAN_GOVERNANCE/);
 const {built,held}=batchBuild();
 assert.equal(built.length+held.length,new Set(registry.entities.map(e=>e.id)).size);
 assert.ok(held.every(h=>h.eligibility==='HELD'));
 assert.ok(built.every(b=>!registry.blockedCountries.includes(b.registryRef.aiCountryId)));
});

test('unknown or malformed IDs never create a profile',()=>{
 assert.equal(classifyRecord('691186').eligibility,'NOT_IN_SNAPSHOT');
 assert.throws(()=>buildPairConfig('9999999'),/NOT_IN_REGISTRY_SNAPSHOT/);
 assert.throws(()=>classifyRecord('69/../1'),/NUMERIC_ID_STRING_REQUIRED/);
});

test('batch is deduplicated and keys are unique',()=>{
 const ids=registry.entities.map(e=>e.id);
 const {built}=batchBuild([...ids,...ids]);
 assert.equal(new Set(built.map(b=>b.config.key)).size,built.length);
});

test('sample then batch practice: normal → human review, overreach → blocked, audit chain valid',async()=>{
 const out=mkdtempSync(join(tmpdir(),'cfp-sp-test-'));
 try{
  const sample=await run(['--sample','69103','--out',out]);
  assert.equal(sample.evidence.pass,true);
  assert.equal(sample.evidence.built,1);
  const batch=await run(['--batch','--out',out]);
  assert.equal(batch.evidence.pass,true);
  assert.equal(batch.evidence.practice.auditValid,true);
  assert.equal(batch.evidence.governance.idsIssued,0);
  for(const r of batch.evidence.practice.results)for(const x of r.runs)assert.equal(x.actual,x.expected);
  const body=readFileSync(batch.file,'utf8');
  assert.equal(readFileSync(batch.file+'.sha256','utf8').split(' ')[0],createHash('sha256').update(body).digest('hex'));
  const held=await run(['--sample','691181','--out',out]);
  assert.equal(held.evidence.pass,false);
  assert.equal(held.evidence.built,0);
 }finally{rmSync(out,{recursive:true,force:true});}
});

test('chapter/group follow the documented 10-chapter rule; V/D are never groups',()=>{
 assert.deepEqual(chapterOf('69103'),{chapter:6,group:'246'});
 assert.deepEqual(chapterOf('0'),{chapter:0,group:'000'});
 assert.deepEqual(chapterOf('312'),{chapter:3,group:'135'});
 assert.deepEqual(chapterOf('91'),{chapter:9,group:'789'});
 assert.throws(()=>chapterOf('V1'),/NUMERIC_ID_STRING_REQUIRED/);
 for(const {config} of batchBuild().built)assert.ok(['000','135','246','789'].includes(config.assignment.group));
});

test('Link Mẫu: numeric-only paths, 3 stores + workspace, never verified',()=>{
 const l=linkTemplate('69103','6910');
 assert.equal(l.canonical,'https://cfp.plus/69103');
 assert.equal(l.github,'https://gh.cfp.plus/69103');assert.equal(l.google,'https://gg.cfp.plus/69103');assert.equal(l.notion,'https://nt.cfp.plus/69103');
 assert.equal(l.workspace,'https://cg.cfp.plus/69103');assert.equal(l.parent,'https://cfp.plus/6910');
 assert.equal(l.verified,false);assert.equal(l.childDigitConforms,true);
 assert.equal(linkTemplate('691001','6910').childDigitConforms,true,'0-prefixed namespace extension');
 assert.equal(linkTemplate('69100','6910').childDigitConforms,false,'0 is never a final child digit');
 assert.equal(linkTemplate('69103','6984').childDigitConforms,false,'wrong parent');
 for(const v of Object.values(l))if(typeof v==='string')assert.match(v,/^https:\/\/[a-z.]+\/\d+$/);
});

test('CLI: --list covers the snapshot, --ids limits the batch, profiles follow the one-page ID standard',async()=>{
 const {list}=await run(['--list']);
 assert.equal(list.length,registry.entities.length);
 const out=mkdtempSync(join(tmpdir(),'cfp-sp-cli-'));
 try{
  const b=await run(['--batch','--ids','69103,69101,691181','--out',out]);
  assert.equal(b.evidence.built,2);assert.deepEqual(b.evidence.held.map(h=>h.id),['691181']);
  const prof=JSON.parse(readFileSync(join(out,'profiles','69103.profile.json'),'utf8'));
  for(const k of ['id','identity','type','country','parent','permanentLink','mainContent','officialSourceEvidence','reviewStatus','workOrderReturn','hub69'])assert.ok(k in prof,k);
  assert.equal(prof.mainContent.office12.length,12);
  assert.equal(prof.identity.identityBound,false);
  assert.equal(prof.workOrderReturn.pass,true);
 }finally{rmSync(out,{recursive:true,force:true});}
 assert.match((await run(['--help'])).help,/no ID issued/);
});

test('environment doctor is read-only and reports required checks',async()=>{
 const r=await diagnose({port:0});
 assert.ok(Array.isArray(r.required)&&r.required.some(c=>c.name==='node>=22'&&c.ok));
 assert.equal(typeof r.ready,'boolean');
 assert.match(r.scope,/No credentials/);
});
