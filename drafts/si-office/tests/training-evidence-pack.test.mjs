import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {trainingEvidencePack} from '../scripts/training-evidence-pack.mjs';

const program={basic:{lessons:[{key:'evidence'}]},exercises:['pair-a','pair-b'].map((pairTemplate,i)=>({
  localKey:'exercise-'+i,pairTemplate,officeModule:i,task:{kind:'training-drill',title:'Fixture '+i,text:'Synthetic',scenario:'normal',resource:pairTemplate}})),advanced:[{key:'sources'}]};
const scope={subject:'synthetic-learner',developmentRevision:'4e6e11a1e7d8d4edcf361ac2f79b183d678cb20a',allowedPairs:['pair-a','pair-b']};
function payload(i){const e=program.exercises[i];return {format:'cfp-training-evidence-v1',sourceRevision:'SEE BUILD MANIFEST',
 journey:{subject:scope.subject,pairKey:e.pairTemplate,exercises:[{exercise:e.localKey,taskKey:'task-'+i}],basicDraftReady:false},
 tasks:[{...e.task,key:'task-'+i,pairKey:e.pairTemplate,owner:scope.subject,status:'REVIEWED DRAFT',
  checks:Array.from({length:18},()=>({result:'PASS'})),output:{synthetic:true},proposalHash:'synthetic-proposal-'+i,
  review:{actor:'synthetic-separate-reviewer',verdict:'acknowledge-draft'}}],
 observations:[{subject:scope.subject,pairKey:e.pairTemplate,lesson:'evidence'}],
 feedback:[{subject:scope.subject,pairKey:e.pairTemplate,taskKey:'task-'+i,outputHash:'synthetic-proposal-'+i}],office:{}};}
function envelope(p){const payloadJSON=JSON.stringify(p);return {payloadJSON,sha256:createHash('sha256').update(payloadJSON).digest('hex'),digestOf:'UTF-8 payloadJSON bytes'};}
test('merges selected-pair exports for one subject without changing evidence or granting authority',()=>{
 const input=[envelope(payload(0)),envelope(payload(1))],before=JSON.stringify(input);
 const pack=trainingEvidencePack(input,program,scope);assert.equal(pack.basicDraftEvidenceReady,true);
 assert.deepEqual(pack.exercises.map(e=>e.taskKey),['task-0','task-1']);assert.equal(pack.sourceRevisionVerified,false);
 assert.equal(pack.advanced[0].competencyPass,false);assert.equal(pack.activationAllowed,false);assert.equal(pack.coreStateChanged,false);
 assert.equal(JSON.stringify(input),before);
});
test('missing second-pair export preserves unknown task and incomplete readiness',()=>{
 const pack=trainingEvidencePack([envelope(payload(0))],program,scope);
 assert.deepEqual(pack.missingPairs,['pair-b']);assert.equal(pack.exercises[1].taskKey,null);
 assert.equal(pack.basicDraftEvidenceReady,false);assert.equal(pack.lessons[1].acknowledged,false);
 const absent=payload(0);delete absent.tasks[0].output;
 const incomplete=trainingEvidencePack([envelope(absent),envelope(payload(1))],program,scope);
 assert.equal(incomplete.exercises[0].outputSha256,null);assert.equal(incomplete.basicDraftEvidenceReady,false);
});
test('foreign subject, tampered envelope, duplicate pair and reused exercise mappings are rejected',()=>{
 const e=envelope(payload(0));assert.throws(()=>trainingEvidencePack([e,e],program,scope),/DUPLICATE/);
 assert.throws(()=>trainingEvidencePack([e],program,{...scope,subject:'foreign'}),/SUBJECT/);
 assert.throws(()=>trainingEvidencePack([{...e,payloadJSON:e.payloadJSON+' '}],program,scope),/HASH/);
 const p=payload(0);p.journey.exercises.push({...p.journey.exercises[0]});
 assert.throws(()=>trainingEvidencePack([envelope(p)],program,scope),/DUPLICATE/);
 const foreign=payload(0);foreign.journey.exercises[0].exercise='exercise-1';
 assert.throws(()=>trainingEvidencePack([envelope(foreign)],program,scope),/EXERCISE_PAIR/);
});
