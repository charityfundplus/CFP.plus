import {createHash,randomUUID} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {inspect} from './team-readiness.mjs';
import {reviewPracticeEvidence} from '../../scripts/practice-evidence-review.mjs';
const hash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

// New local sources exercise. No old cohort replay and no real member/assessor impersonation.
export function runIntegratedTraining(snapshot,program,{workspace='local-synthetic-roster-sources',pairKey='hub69-content-demo'}={}){
 const templates=JSON.parse(snapshot.files.find(f=>f.path==='drafts/si-office/configs/pairs.json').content);
 const pair=templates.find(p=>p.key===pairKey);
 if(!pair || pair.identity.id!==null || !pair.missions.includes('registry-audit'))throw Error('SYNTHETIC_SOURCE_SCOPE_REQUIRED');
 const inventory=inspect(snapshot);
 const source=inventory.records.find(r=>r.id==='6911513');
 const parent=inventory.records.find(r=>r.id===source?.parent);
 if(!source || !parent || !source.findings.includes('PARENT_LABEL_REVIEW'))throw Error('SOURCE_CONFLICT_NOT_OBSERVED');
 const taskKey=randomUUID();
 const profile=snapshot.files.find(f=>f.path==='registry/6911513.md').content;
 const parentLabel=profile.split('\n').find(line=>line.replaceAll('**','').startsWith('Parent Entity:'))?.replaceAll('**','').trim();
 if(!parentLabel)throw Error('PARENT_LABEL_SOURCE_REQUIRED');
 const claimRegister={kind:'claim-register',mode:'SYNTHETIC LOCAL SOURCES PRACTICE',taskKey,
  sourceRevision:snapshot.revision,readOnly:true,sourceId:source.id,parentId:source.parent,
  sources:[...source.profileLinks,...parent.profileLinks],
  claims:[{expected:'Parent label agrees with parent Registry entity',observed:`${parentLabel}; Registry parent ${parent.id}: ${parent.name}`,verdict:'NEEDS HUMAN REVIEW'}],
  sourceFinding:source.findings,identityVerified:false,capabilityVerified:false,legalRelationshipVerified:false,
  remedy:'Keep both sources intact; request Human Governance reconciliation, no automatic renumbering'};
 const output={synthetic:true,id:null,parent:null,did:null,canonical:null,capabilityVerified:false,legalRelationshipVerified:false,artifact:claimRegister};
 const checks=[
  {name:'source-byte-integrity',pass:true},
  {name:'retained-source-conflict',pass:source.findings.includes('PARENT_LABEL_REVIEW')},
  {name:'unbound-practice-identity',pass:['id','parent','did','canonical'].every(k=>output[k]===null)},
  {name:'no-runtime-promotion',pass:inventory.counts.activePairs===0 && inventory.activationAllowed===false}
 ];
 const task={key:taskKey,pairKey,owner:'synthetic-local-editor',status:'REVIEWED DRAFT',output,checks,
  review:{actor:'synthetic-local-reviewer',verdict:'acknowledge-draft',authority:'MOCK ONLY / NOT AN ASSESSOR'}};
 const deliverable={kind:'claim-register',expected:claimRegister.claims[0].expected,observed:claimRegister.claims[0].observed,
  taskKey,track:'sources',sourceRevision:snapshot.revision,outputSha256:hash(output),artifactSha256:hash(claimRegister)};
 const receipt={mode:'SYNTHETIC ADVANCED PRACTICE / NOT ASSESSED',results:[{workspace,taskEvidence:[{track:'sources',taskKey,task,deliverables:[deliverable]}]}]};
 const review=reviewPracticeEvidence(receipt,program,{sourceRevision:snapshot.revision,allowedPairs:templates.map(p=>p.key)});
 const curriculum={basic:program.basic.lessons.map(l=>({key:l.key,title:l.title,completion:'NOT RECORDED IN THIS EXERCISE'})),
  officeExercises:program.exercises.map(e=>({key:e.localKey,module:e.officeModule,state:'RETAIN EXISTING EVIDENCE / NOT RERUN'})),
  advanced:program.advanced.map(t=>({key:t.key,title:t.title,prerequisites:t.prerequisites,state:t.key==='sources'?'NEW SYNTHETIC DRAFT RETAINED':'NOT EXECUTED IN THIS SCOPE',assessment:'NOT ASSESSED'}))};
 return {mode:'LOCAL SYNTHETIC INTEGRATED PRACTICE',sourceRevision:snapshot.revision,taskKey,receipt,review,curriculum,
  feedback:{taskKey,outputSha256:hash(output),text:{vi:'Giữ nguyên hai nguồn; xin quyết định HG cho mâu thuẫn. Bài thực hành không chứng nhận SI.',en:'Preserve both sources; request HG resolution. Practice does not certify SI.'}},
  execution:{checks:checks.length,checksPass:checks.every(c=>c.pass),realMemberAck:false,assessorVerified:false,providerCalls:0},
  componentProposal:{name:'read-only inventory + sources training sidecar',state:'PROPOSED READY FOR LOCAL SYNTHETIC USE ONLY',requiresHumanReview:true,scope:'No server grants, paid resources, runtime adapters, competency or pair activation'},
  realPairs:{ready:0,active:0,status:'BLOCKED — VERIFIED OPERATOR/ACCESS/BINDING MISSING'},activationAllowed:false,privilegeChange:false};
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){
 const [snapshotPath,programPath,outputPath]=process.argv.slice(2);
 const result=runIntegratedTraining(JSON.parse(readFileSync(snapshotPath)),JSON.parse(readFileSync(programPath)));
 const payload=JSON.stringify(result,null,2)+'\n';writeFileSync(outputPath,payload,{flag:'wx'});
 const readback=readFileSync(outputPath,'utf8');if(readback!==payload)throw Error('LOCAL_RECEIPT_READBACK_FAILED');
 console.log(JSON.stringify({taskKey:result.taskKey,outputPath,payloadSha256:createHash('sha256').update(readback).digest('hex'),checks:result.execution,competency:'NOT ASSESSED',realPairs:result.realPairs}));
}
