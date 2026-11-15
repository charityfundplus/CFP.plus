import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runIntegratedTraining} from './integrated-training.mjs';
const snapshot=JSON.parse(readFileSync(new URL('./source-snapshot.json',import.meta.url)));
const program=JSON.parse(readFileSync(new URL('../../configs/training-basic-v1.json',import.meta.url)));
test('new sources draft integrates existing curriculum and reviewer with artifact digests',()=>{
 const before=JSON.stringify(snapshot),r=runIntegratedTraining(snapshot,program);
 assert.equal(JSON.stringify(snapshot),before);
 assert.equal(r.curriculum.basic.length,5);assert.equal(r.curriculum.officeExercises.length,12);
 assert.equal(r.curriculum.advanced.length,6);
 const row=r.review.rows.find(x=>x.track==='sources');
 assert.equal(row.taskKey,r.taskKey);assert(row.deliverablesBound);assert(row.separateDraftReview);
 assert.equal(row.outputSha256,r.feedback.outputSha256);assert.equal(row.competencyPass,false);
 assert.equal(row.assessment,'NOT ASSESSED');assert.equal(r.activationAllowed,false);
 assert.equal(r.review.rows.filter(x=>x.taskKey!==null).length,1);
 assert(r.review.rows.filter(x=>x.track!=='sources').every(x=>x.taskKey===null));
 assert(r.receipt.results[0].taskEvidence[0].task.output.artifact.claims[0].observed.includes('Meta AI'));
 assert.equal(r.componentProposal.state,'PROPOSED READY FOR LOCAL SYNTHETIC USE ONLY');
});
test('a pair without source mission or unknown binding cannot run this exercise',()=>{
 assert.throws(()=>runIntegratedTraining(snapshot,program,{pairKey:'training-demo'}),/SYNTHETIC_SOURCE_SCOPE/);
 assert.throws(()=>runIntegratedTraining(snapshot,program,{pairKey:'691183'}),/SYNTHETIC_SOURCE_SCOPE/);
});
test('changed source bytes fail before practice receipt is produced',()=>{
 const s=structuredClone(snapshot);s.files.find(f=>f.path==='registry/6911513.md').content+='changed';
 assert.throws(()=>runIntegratedTraining(s,program),/SOURCE_INTEGRITY/);
});
