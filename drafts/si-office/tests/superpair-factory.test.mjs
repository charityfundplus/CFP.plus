import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {registry} from '../model.mjs';
import {classifyRecord,buildPairConfig,batchBuild} from '../core/superpair-factory.mjs';
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

test('environment doctor is read-only and reports required checks',async()=>{
 const r=await diagnose({port:0});
 assert.ok(Array.isArray(r.required)&&r.required.some(c=>c.name==='node>=22'&&c.ok));
 assert.equal(typeof r.ready,'boolean');
 assert.match(r.scope,/No credentials/);
});
