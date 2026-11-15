import {test} from 'node:test';
import assert from 'node:assert/strict';
import {reviewPracticeEvidence} from '../scripts/practice-evidence-review.mjs';
const sourceRevision='690b711316fd1dc41d7bee328609d471f1ddafb9';
const program={advanced:[{key:'sources',expectedEvidence:'primary source conflicts'},{key:'access',expectedEvidence:'server denial'}]};
const scope={sourceRevision,allowedPairs:['training-demo']};
function task(key){return {key,pairKey:'training-demo',owner:'synthetic-learner',status:'REVIEWED DRAFT',review:{actor:'synthetic-reviewer',verdict:'acknowledge-draft'},checks:[{pass:true}],output:{synthetic:true,id:null,parent:null,did:null,canonical:null,capabilityVerified:false,legalRelationshipVerified:false,artifact:{type:'TRAINING EXERCISE DRAFT'}}};}
function receipt(){return {mode:'SYNTHETIC ADVANCED PRACTICE / NOT ASSESSED',results:[{workspace:'team-a',taskEvidence:[{taskKey:'task-a',track:'sources',task:task('task-a')},{taskKey:'task-b',track:'access',task:task('task-b')}]}]};}
test('real task binding is preserved but reflections/self-declared authority cannot grant competency',()=>{
 const input=receipt();input.results[0].taskEvidence[0].assessorVerified=true;const before=JSON.stringify(input);
 const result=reviewPracticeEvidence(input,program,scope);
 assert.equal(result.rows.length,2);assert.equal(result.rows[0].taskKey,'task-a');
 assert.equal(result.rows[0].executionChecksPass,true);assert.equal(result.rows[0].separateDraftReview,true);
 assert(result.rows[0].findings.includes('GENERIC_REFLECTION_IS_NOT_ADVANCED_COMPETENCY_EVIDENCE'));
 assert(result.rows.every(row=>row.assessment==='NOT ASSESSED'&&!row.competencyPass&&!row.privilegeChange));
 assert.equal(result.approvedPreviewRevision,'b75b780eb64430355f0b51a4b58b9e5269e0db43');
 assert.equal(JSON.stringify(input),before);
});
test('missing history is not filled and wrong pair/self-review/failed checks are findings',()=>{
 const history={mode:'SYNTHETIC ADVANCED PRACTICE / NOT ASSESSED',results:[{workspace:'old-team'}]};
 assert(reviewPracticeEvidence(history,program,scope).rows.every(row=>row.taskKey===null));
 const input=receipt();const retained=input.results[0].taskEvidence[0];
 retained.task.pairKey='foreign';retained.task.review.actor=retained.task.owner;retained.task.checks[0].pass=false;
 const row=reviewPracticeEvidence(input,program,scope).rows[0];
 assert.equal(row.taskKey,null);assert.equal(row.executionChecksPass,false);assert.equal(row.separateDraftReview,false);
});
test('duplicate tasks/tracks/workspaces and unknown track fail closed',()=>{
 const a=receipt();a.results[0].taskEvidence.push(structuredClone(a.results[0].taskEvidence[0]));
 assert.throws(()=>reviewPracticeEvidence(a,program,scope),/DUPLICATE_TRACK/);
 const b=receipt();b.results.push(structuredClone(b.results[0]));assert.throws(()=>reviewPracticeEvidence(b,program,scope),/WORKSPACE_DUPLICATE/);
 const c=receipt();c.results[0].taskEvidence[1].taskKey='task-a';c.results[0].taskEvidence[1].task=task('task-a');
 assert.throws(()=>reviewPracticeEvidence(c,program,scope),/DUPLICATE_TASK/);
 const d=receipt();d.results[0].taskEvidence[0].track='unknown';assert.throws(()=>reviewPracticeEvidence(d,program,scope),/UNKNOWN_TRACK/);
});
