// One NEW synthetic dossier whose real generated taskKey/output are retained.
// Run only with a pinned source revision; no host/network/provider operation.
import {mkdtempSync,rmSync} from 'node:fs';import {tmpdir} from 'node:os';import {join} from 'node:path';import {randomBytes} from 'node:crypto';
import {P2Sandbox} from '../sandbox/p2-service.mjs';import {hash} from '../core/common.mjs';import {evidenceKinds} from '../core/training-assessment.mjs';
const sourceRevision=process.env.CFP_DEMO_SOURCE_REVISION;if(! /^[a-f0-9]{40}$/.test(sourceRevision||''))throw Error('PINNED_DEMO_SOURCE_REQUIRED');
const dir=mkdtempSync(join(tmpdir(),'cfp-dossier-retained-')),service=new P2Sandbox(join(dir,'state.db'));
try{
 const password=randomBytes(24).toString('hex'),workspace='new-retained-dossier',pairKey='hub69-content-demo';
 service.provision({id:'synthetic-learner',role:'editor',workspace,pairs:[pairKey],password});service.provision({id:'synthetic-rubric-reviewer',role:'reviewer',workspace,pairs:[pairKey],password});
 const learner=service.login('synthetic-learner',password),reviewer=service.login('synthetic-rubric-reviewer',password);
 for(const lesson of ['identity-lineage','ethics-governance','tool-use','security','evidence'])await service.execute(learner,'learn',{pairKey,lesson});
 const created=await service.execute(learner,'createTask',{pairKey,input:{kind:'training-drill',title:'New retained source-claim dossier demonstration',text:'Synthetic plumbing exercise. No actual source, capability, legal or competency verification.',scenario:'normal',resource:'website-demo'}},{idempotencyKey:'retained-dossier-demo-v1'});
 await service.execute(learner,'runTask',{taskKey:created.key});await service.execute(learner,'feedback',{taskKey:created.key,feedback:'Keep exact generated output/taskKey before cleanup; synthetic artifact review only.'});const task=await service.execute(reviewer,'reviewTask',{taskKey:created.key,verdict:'acknowledge-draft'});
 const artifacts=evidenceKinds.sources.map(kind=>{const content=JSON.stringify({kind,source:'https://example.org/synthetic',claim:'Synthetic demonstration only',sourceVerification:'NOT VERIFIED',capabilityVerification:'NOT VERIFIED',legalRelationshipVerification:'NOT VERIFIED'});return {kind,content,sha256:hash(content),taskKey:task.key,outputHash:hash(task.output)};});
 const packet=await service.execute(learner,'prepareAssessment',{taskKey:task.key,input:{track:'sources',sourceRevision,artifacts,synthetic:true}});
 const assessment=await service.execute(reviewer,'reviewAssessment',{assessmentKey:packet.key,input:{verdict:'needs-evidence',feedback:'Hash/task binding demonstrated; genuine primary evidence, complete basic prerequisites and verified assessor remain missing.',artifactSetDigest:packet.artifactSetDigest,synthetic:true}});
 const snapshot=await service.execute(learner,'snapshot');const payload={sourceRevision,mode:'ONE NEW SYNTHETIC DOSSIER / NOT COMPETENCY CERTIFICATION',historicalCohortReexecuted:false,workspace,pairKey,task,assessment,observations:snapshot.learning.observations,feedback:snapshot.learning.feedback,audit:service.verify(),realMemberACK:false,competencyPass:0,activationAllowed:false,fixtureStateRemovedAfterExport:true};
 console.log(JSON.stringify({sha256:hash(payload),digestOf:'UTF-8 JSON.stringify(payload)',payload},null,2));
}finally{service.close();rmSync(dir,{recursive:true,force:true});}
