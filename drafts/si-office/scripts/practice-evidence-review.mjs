import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

const sha=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');
const PIN='b75b780eb64430355f0b51a4b58b9e5269e0db43';
const hex64=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const hasText=value=>typeof value==='string'&&value.trim().length>0;

// Review packet only: never updates Core state, grants, assessment or old evidence.
export function reviewPracticeEvidence(receipt,program,{sourceRevision,allowedPairs}){
 if(!/^[a-f0-9]{40}$/.test(sourceRevision||'')||!Array.isArray(allowedPairs)||!allowedPairs.length)throw Error('PINNED_DEVELOPMENT_SCOPE_REQUIRED');
 if(receipt?.mode!=='SYNTHETIC ADVANCED PRACTICE / NOT ASSESSED'||!Array.isArray(receipt.results)||!Array.isArray(program.advanced))throw Error('RECEIPT_REQUIRED');
 const seenWorkspaces=new Set(),seenTasks=new Set(),rows=[];
 for(const team of receipt.results){
  if(!hasText(team.workspace)||seenWorkspaces.has(team.workspace))throw Error('WORKSPACE_DUPLICATE_OR_INVALID');
  seenWorkspaces.add(team.workspace);
  if(team.taskEvidence!==undefined&&!Array.isArray(team.taskEvidence))throw Error('TASK_EVIDENCE_INVALID');
  const supplied=team.taskEvidence||[];
  if(supplied.some(item=>!program.advanced.some(track=>track.key===item.track)))throw Error('UNKNOWN_TRACK');
  for(const track of program.advanced){
   const matches=supplied.filter(item=>item.track===track.key);
   if(matches.length>1)throw Error('DUPLICATE_TRACK_BINDING');
   const retained=matches[0],task=retained?.task,findings=[];
   const binding=!!task&&hasText(retained.taskKey)&&retained.taskKey===task.key&&allowedPairs.includes(task.pairKey);
   if(!binding)findings.push('MISSING_OR_INVALID_TASK_PAIR_BINDING');
   if(task?.key){const identity=team.workspace+':'+task.key;if(seenTasks.has(identity))throw Error('DUPLICATE_TASK_BINDING');seenTasks.add(identity);}
   const checks=Array.isArray(task?.checks)&&task.checks.length>0&&task.checks.every(check=>check.pass===true);
   if(!checks)findings.push('MISSING_OR_FAILED_EXECUTION_CHECKS');
   const independentReview=hasText(task?.owner)&&task?.status==='REVIEWED DRAFT'&&hasText(task?.review?.actor)&&task.review.actor!==task.owner&&task.review.verdict==='acknowledge-draft';
   if(!independentReview)findings.push('MISSING_SEPARATE_DRAFT_REVIEW');
   const output=task?.output,outputDigest=output?sha(output):null;
   const synthetic=!!output&&output.synthetic===true&&['id','parent','did','canonical'].every(field=>Object.hasOwn(output,field)&&output[field]===null)&&output.capabilityVerified===false&&output.legalRelationshipVerified===false;
   if(!synthetic)findings.push('OUTPUT_MISSING_OR_OUTSIDE_SYNTHETIC_SCOPE');
   const deliverables=retained?.deliverables||[];
   const actualArtifacts=Array.isArray(deliverables)&&deliverables.length>0&&deliverables.every(artifact=>
    hasText(artifact.kind)&&hasText(artifact.expected)&&hasText(artifact.observed)&&artifact.taskKey===task?.key
    &&artifact.track===track.key&&artifact.sourceRevision===sourceRevision&&artifact.outputSha256===outputDigest&&hex64(artifact.artifactSha256));
   if(!actualArtifacts)findings.push('TRACK_DELIVERABLES_NOT_RETAINED_OR_NOT_BOUND');
   // A generic training artifact/reflection and request-supplied booleans are not authority.
   const reflectionOnly=!actualArtifacts||output?.artifact?.type==='TRAINING EXERCISE DRAFT';
   if(reflectionOnly)findings.push('GENERIC_REFLECTION_IS_NOT_ADVANCED_COMPETENCY_EVIDENCE');
   findings.push('PREREQUISITE_EVIDENCE_REQUIRES_ASSIGNED_ASSESSOR','ASSESSOR_AUTHORITY_PENDING_OFFICIAL_ASSIGNMENT');
   const observed={workspace:team.workspace,track:track.key,taskKey:binding?task.key:null,pairKey:binding?task.pairKey:null,
    expectedEvidence:track.expectedEvidence,outputSha256:outputDigest,retainedTaskEvidence:!!retained,
    executionChecksPass:checks,separateDraftReview:independentReview,syntheticScope:synthetic,
    deliverablesBound:actualArtifacts,findings};
   rows.push({...observed,evidenceSha256:sha(observed),assessment:'NOT ASSESSED',competencyPass:false,privilegeChange:false});
  }
 }
 return {schemaVersion:1,mode:'REVIEW PACKET ONLY',sourceRevision,approvedPreviewRevision:PIN,
  runtimeChanged:false,activation:'HOLD',rows,taskSlots:rows.length,competencyPass:0,
  receiptSha256:sha(receipt),assessorAssignment:'PENDING',operatorAssignment:'PENDING',custodianAssignment:'PENDING'};
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
 const [receiptPath,programPath,sourceRevision]=process.argv.slice(2);
 const receipt=JSON.parse(readFileSync(receiptPath)),program=JSON.parse(readFileSync(programPath));
 const templates=JSON.parse(readFileSync(new URL('../configs/pairs.json',import.meta.url)));
 console.log(JSON.stringify(reviewPracticeEvidence(receipt,program,{sourceRevision,allowedPairs:templates.map(pair=>pair.key)}),null,2));
}
