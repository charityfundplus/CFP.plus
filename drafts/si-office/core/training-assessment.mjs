import {clone,hash,key,requireKeys,text} from './common.mjs';
import program from '../configs/training-basic-v1.json' with {type:'json'};

export const evidenceKinds=Object.freeze({
 durability:['checkpoint-before','restart-observation'],
 access:['scope-denial','grants-boundary'],
 recovery:['backup-manifest','restore-generation'],
 sources:['claim-register','conflict-resolution'],
 interoperability:['version-matrix','mock-call-ledger'],
 website:['ui-link-receipt','target-readback']
});

export function prepareAssessment(actor,task,input,learning){
 requireKeys(input,['track','sourceRevision','artifacts','synthetic']);
 const track=program.advanced.find(t=>t.key===input.track);
 if(!track||input.synthetic!==true||! /^[a-f0-9]{40}$/.test(input.sourceRevision||''))throw Error('ASSESSMENT_INPUT_INVALID');
 if(task.kind!=='training-drill'||task.owner!==actor.id||task.status!=='REVIEWED DRAFT'||task.review?.actor===actor.id||task.review?.verdict!=='acknowledge-draft'||!task.output)throw Error('ASSESSMENT_TASK_EVIDENCE_REQUIRED');
 const lessons=new Set(learning.observations.filter(o=>o.subject===actor.id&&o.pairKey===task.pairKey).map(o=>o.lesson));
 if(program.basic.lessons.some(l=>!lessons.has(l.key)))throw Error('ASSESSMENT_BASIC_PREREQUISITES_REQUIRED');
 if(!learning.feedback.some(f=>f.subject===actor.id&&f.taskKey===task.key&&f.outputHash===task.proposalHash))throw Error('ASSESSMENT_FEEDBACK_REQUIRED');
 if(task.checks.length!==18||task.checks.some(c=>c.pass!==true&&c.result!=='PASS'))throw Error('ASSESSMENT_CHECKS_REQUIRED');
 const expected=evidenceKinds[track.key];
 if(!Array.isArray(input.artifacts)||input.artifacts.length!==expected.length)throw Error('ASSESSMENT_ARTIFACTS_REQUIRED');
 const kinds=new Set();
 for(const artifact of input.artifacts){
  requireKeys(artifact,['kind','content','sha256','taskKey','outputHash']);
  if(!expected.includes(artifact.kind)||kinds.has(artifact.kind)||!text(artifact.content,4000)||artifact.sha256!==hash(artifact.content)||artifact.taskKey!==task.key||artifact.outputHash!==hash(task.output))throw Error('ASSESSMENT_ARTIFACT_INVALID');
  kinds.add(artifact.kind);
 }
 return {key:key(),subject:actor.id,pairKey:task.pairKey,taskKey:task.key,track:track.key,sourceRevision:input.sourceRevision,
  expectedEvidence:track.expectedEvidence,artifacts:clone(input.artifacts),artifactSetDigest:hash(input.artifacts),sourceRevisionVerification:'USER DECLARED / RUNTIME RECEIPT MATCH REQUIRED',
  status:'SYNTHETIC EVIDENCE PACKET / REVIEW PENDING',review:null,createdAt:new Date().toISOString(),
  provenance:'USER-SUPPLIED ARTIFACTS; HASH/BINDING CHECKED, CLAIMS NOT VERIFIED',
  prerequisites:'FIVE BASIC ACKNOWLEDGEMENTS AND REVIEWED TASK CHECKED; FULL BASIC COMPETENCE / PREREQUISITE AUTHORITY NOT VERIFIED',
  competencyAssessment:'NOT ASSESSED',assessorAuthority:'PENDING EXTERNAL VERIFICATION',certification:false,privilegeChange:false};
}

export function reviewAssessment(actor,row,input){
 requireKeys(input,['verdict','feedback','artifactSetDigest','synthetic']);
 if(actor.role!=='reviewer'||actor.id===row.subject)throw Error('INDEPENDENT_ASSESSMENT_REVIEW_REQUIRED');
 if(row.review)throw Error('ASSESSMENT_ALREADY_REVIEWED');
 if(input.synthetic!==true||!['meets-synthetic-rubric','needs-evidence'].includes(input.verdict)||!text(input.feedback,1500)||input.artifactSetDigest!==row.artifactSetDigest)throw Error('ASSESSMENT_REVIEW_INVALID');
 // A server-authorized synthetic reviewer is NOT a verified competency assessor.
 return {...clone(row),status:'SYNTHETIC RUBRIC REVIEWED / NOT CERTIFIED',
  review:{subject:actor.id,verdict:input.verdict,feedback:input.feedback,artifactSetDigest:row.artifactSetDigest,time:new Date().toISOString(),realAssessorVerified:false}};
}
