import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const digest=text=>createHash('sha256').update(text).digest('hex');
const text=value=>typeof value==='string'&&value.trim().length>0;
const PIN='b75b780eb64430355f0b51a4b58b9e5269e0db43';
const publicEvidence=value=>{try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}};

// Consumes the existing UI envelope; never writes the Core or accepts authority.
export function trainingWorksheet(envelope,program,{developmentRevision,allowedPairs}){
 if(!/^[a-f0-9]{40}$/.test(developmentRevision||'')||!Array.isArray(allowedPairs))throw Error('DEVELOPMENT_PROVENANCE_REQUIRED');
 if(typeof envelope?.payloadJSON!=='string'||envelope.digestOf!=='UTF-8 payloadJSON bytes'||envelope.sha256!==digest(envelope.payloadJSON))throw Error('EXPORT_HASH_MISMATCH');
 const p=JSON.parse(envelope.payloadJSON),j=p.journey;
 if(p.format!=='cfp-training-evidence-v1'||!text(j?.subject)||!allowedPairs.includes(j?.pairKey)||!Array.isArray(p.tasks)||!Array.isArray(p.observations)||!Array.isArray(p.feedback))throw Error('EXPORT_SCOPE_INVALID');
 const findings=['REVISION_REQUIRES_BUILD_MANIFEST_READBACK','ASSESSOR_AUTHORITY_PENDING'];
 const taskKeys=new Set();
 for(const task of p.tasks){
  if(!text(task.key)||taskKeys.has(task.key)||task.pairKey!==j.pairKey||task.owner!==j.subject)throw Error('TASK_SCOPE_OR_DUPLICATE');
  taskKeys.add(task.key);
 }
 if(p.observations.some(row=>row.subject!==j.subject||row.pairKey!==j.pairKey)||p.feedback.some(row=>!taskKeys.has(row.taskKey)||row.pairKey!==j.pairKey))throw Error('OBSERVATION_OR_FEEDBACK_SCOPE');
 const lessons=program.basic.lessons.map(lesson=>({key:lesson.key,title:lesson.title,
  acknowledged:p.observations.some(row=>row.lesson===lesson.key),meaning:{vi:'Ghi nhận đã học; chưa chứng nhận năng lực',en:'Study acknowledgement; not competency certification'}}));
 const mappings=Array.isArray(j.exercises)?j.exercises:[];
 if(mappings.some(row=>!program.exercises.some(e=>[row.exercise,row.localKey,row.exerciseKey,row.key].includes(e.localKey))))findings.push('EXERCISE_MAPPING_REQUIRES_REVIEW');
 const exercises=program.exercises.map(exercise=>{
  const mapping=mappings.find(row=>[row.exercise,row.localKey,row.exerciseKey,row.key].includes(exercise.localKey));
  const task=p.tasks.find(t=>t.key===mapping?.taskKey);
  const taskMatches=!!task&&task.pairKey===exercise.pairTemplate&&['kind','title','text','scenario','resource'].every(field=>task[field]===exercise.task[field]);
  const checks=taskMatches&&Array.isArray(task?.checks)&&task.checks.length===18&&task.checks.every(check=>check.pass===true||check.result==='PASS');
  const feedback=!!task&&p.feedback.some(row=>row.subject===j.subject&&row.taskKey===task.key&&row.outputHash===task.proposalHash);
  const reviewed=!!task&&task.status==='REVIEWED DRAFT'&&text(task.review?.actor)&&task.review.actor!==task.owner&&task.review.verdict==='acknowledge-draft';
  return {localKey:exercise.localKey,module:exercise.officeModule,taskKey:task?.key||null,
   outputSha256:task?.output?digest(JSON.stringify(task.output)):null,checksPass:checks,feedbackBound:feedback,separateDraftReview:reviewed,
   basicDraftEvidenceReady:checks&&feedback&&reviewed,assessment:'NOT ASSESSED'};
 });
 const office=p.office||{},apps=Array.isArray(office.applications)?office.applications:[],refs=new Set(apps.map(a=>a.key));
 const declarations=apps.map(app=>{
  const f=[];
  if(app.subject!==j.subject)f.push('DECLARANT_SCOPE_MISMATCH');
  if(['id','parent','did','canonical'].some(field=>app[field]!==null))f.push('IMMUTABLE_IDENTITY_NOT_UNBOUND');
  if(!text(app.country)||app.country==='UNRESOLVED')f.push('COUNTRY_EVIDENCE_PENDING');
  if(!text(app.developer)||app.developer==='UNRESOLVED')f.push('DEVELOPER_EVIDENCE_PENDING');
  if((app.relationships||[]).some(r=>!publicEvidence(r.evidence)))f.push('RELATIONSHIP_SOURCE_MISSING_OR_INVALID');
  return {localRecordKey:app.key,findings:f,identityStatus:'NOT VERIFIED',capabilityStatus:'NOT VERIFIED',legalRelationshipStatus:'NOT VERIFIED'};
 });
 const hstdn=(office.hstdn||[]).map(row=>({localRecordKey:row.key,findings:[
  ...(!Array.isArray(row.members)||!row.members.length||row.members.some(member=>!refs.has(member))?['HSTDN_MEMBER_EVIDENCE_OUTSIDE_EXPORTED_DECLARATIONS']:[]),
  ...(!publicEvidence(row.source)?['HSTDN_SOURCE_MISSING_OR_INVALID']:[])],legalRelationshipStatus:'NOT VERIFIED'}));
 const ready=lessons.every(l=>l.acknowledged)&&exercises.every(e=>e.basicDraftEvidenceReady);
 if(j.basicDraftReady!==ready)findings.push('DECLARED_JOURNEY_READINESS_DIFFERS_FROM_RETAINED_EVIDENCE');
 return {schemaVersion:1,mode:'READ_ONLY VI/EN WORKSHEET',approvedPreviewRevision:PIN,
  developmentRevision,sourceRevisionClaim:p.sourceRevision||null,sourceRevisionVerified:false,
  inputSha256:envelope.sha256,subject:j.subject,pairKey:j.pairKey,lessons,exercises,
  advanced:program.advanced.map(track=>({key:track.key,title:track.title||null,prerequisites:track.prerequisites,assessment:'NOT ASSESSED',competencyPass:false})),
  declarations,hstdn,findings,basicDraftEvidenceReady:ready,privilegeChange:false,
  activation:'HOLD',operatorAssignment:'PENDING',custodianAssignment:'PENDING'};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const [inputPath,revision]=process.argv.slice(2);
 const program=JSON.parse(readFileSync(new URL('../configs/training-basic-v1.json',import.meta.url)));
 const pairs=JSON.parse(readFileSync(new URL('../configs/pairs.json',import.meta.url)));
 console.log(JSON.stringify(trainingWorksheet(JSON.parse(readFileSync(inputPath)),program,{developmentRevision:revision,allowedPairs:pairs.map(p=>p.key)}),null,2));
}
