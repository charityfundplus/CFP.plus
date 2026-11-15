import {searchCatalog,createInquiry,matchInquiry,createOpportunity,updateOpportunity,commercialState} from './commercial-intake.mjs';
import templates from '../configs/pairs.json' with {type:'json'};
import {clone,freeze,hash,requireKeys,text,MODULES,key} from './common.mjs';
import {inspectIdentity} from './identity-registry.mjs';
import {MockSIAdapter} from './si-adapter.mjs';
import {TaskEngine,buildDraftArtifact} from './task-engine.mjs';
import {checkActor,checkTool} from './security-permission.mjs';
import {inspectInput,inspectProposal} from './supervision-engine.mjs';
import {crossCheck} from './cross-check-engine.mjs';
import {LearningTraining} from './learning-training.mjs';
import {MonitoringRecovery} from './monitoring-recovery.mjs';
import {KnowledgeEvidence} from './knowledge-evidence.mjs';
import {VersionUpgrade} from './version-upgrade.mjs';
import {hubInventory} from './hub69-integration.mjs';
import {createState,validateRegistration,validateHSTDN,safeURL,modules,registry} from '../model.mjs';
import {moduleContracts} from '../public/office-contracts.js';
import {createOfficeIntake} from './office-intake.mjs';
const system={id:'core-system-synthetic',role:'system'};
export function validateConfig(config){
 requireKeys(config,['key','name','mode','identity','si','software','assignment','missions','supervision','permissions','owner','sources','testStatus','operatingStatus']);
 if(!text(config.key,80)||!/^[a-z][a-z0-9-]+$/.test(config.key)||!text(config.name)||config.mode!=='sandbox'||config.operatingStatus!=='SYNTHETIC SANDBOX ONLY')throw Error('SANDBOX_CONFIG_REQUIRED');
 inspectIdentity(config.identity);requireKeys(config.si,['provider','protocol']);if(!['mock-local','mock-alternate'].includes(config.si.provider)||config.si.protocol!==1)throw Error('LIVE_ADAPTER_FORBIDDEN');
 requireKeys(config.software,['name','version']);if(config.software.name!=='CFP+ Standard Core'||config.software.version!=='0.1.0-sandbox')throw Error('CONFIG_VERSION_INVALID');
 requireKeys(config.assignment,['group','chapter','field','country','hstdn']);if(!['V','000','135','246','789'].includes(config.assignment.group)||!Number.isInteger(config.assignment.chapter)||config.assignment.chapter<0||config.assignment.chapter>9||!['field','country','hstdn'].every(k=>text(config.assignment[k])))throw Error('ASSIGNMENT_INVALID');
 requireKeys(config.permissions,['tools','resources']);if(!Array.isArray(config.permissions.tools)||!config.permissions.tools.length||config.permissions.tools.length>2||new Set(config.permissions.tools).size!==config.permissions.tools.length||!config.permissions.tools.includes('source.read')||!config.permissions.tools.every(k=>['source.read','draft.write'].includes(k))||!Array.isArray(config.permissions.resources)||!config.permissions.resources.length||config.permissions.resources.length>10||new Set(config.permissions.resources).size!==config.permissions.resources.length||!config.permissions.resources.every(r=>text(r,100)))throw Error('PERMISSIONS_INVALID');
 if(!Array.isArray(config.missions)||!config.missions.length||!config.missions.every(m=>['website-draft','registry-audit','training-drill','hst-us-draft'].includes(m))||!text(config.owner)||!text(config.supervision)||!Array.isArray(config.sources)||config.sources.some(s=>!text(s)||!s.startsWith('https://'))||config.testStatus!=='TEST REQUIRED')throw Error('CONFIG_SCOPE_INVALID');
 return freeze(clone(config));
}
export class CoreEngine {
 #office=new Map();#pairs=new Map();#tasks=new TaskEngine();#knowledge=new KnowledgeEvidence();#learning=new LearningTraining();#monitor=new MonitoringRecovery();#upgrades=new VersionUpgrade();#templates;#adapterFactory;#timeout;#checkpointWriter;
 constructor({configs=templates,adapterFactory=provider=>new MockSIAdapter(provider),timeoutMs=150,checkpoint=null,checkpointWriter=null}={}){
  if(!Array.isArray(configs)||!configs.length)throw Error('CONFIG_REQUIRED');this.#templates=configs.map(validateConfig);if(new Set(this.#templates.map(c=>c.key)).size!==this.#templates.length)throw Error('DUPLICATE_PAIR_CONFIG');
  this.#checkpointWriter=checkpointWriter;this.#adapterFactory=adapterFactory;this.#timeout=timeoutMs;
  if(checkpoint)this.#restore(checkpoint);else this.instantiate(system,this.#templates[0].key,true);
 }
 checkpoint(){return clone({schema:[...this.#office.values()].some(o=>o.commercial?.inquiries?.length||o.commercial?.opportunities?.length)?3:this.#learning.snapshot().assessments.length?2:1,office:[...this.#office.entries()],pairs:[...this.#pairs.values()].map(p=>({...p,busy:false})),tasks:this.#tasks.all(),audit:this.#knowledge.events(),learning:this.#learning.snapshot(),alerts:this.#monitor.alerts(),upgrade:{version:this.#upgrades.version,history:this.#upgrades.history}});}
 #restore(c){
  if(![1,2,3].includes(c.schema)||!Array.isArray(c.pairs)||!Array.isArray(c.tasks))throw Error('CHECKPOINT_INCOMPATIBLE');
  // Schema 2 makes legacy readers refuse assessment-bearing evidence instead of
  // silently discarding it on their next checkpoint. Never migrate the audit.
  const assessments=c.learning?.assessments;
  if(c.schema>=2&&!Array.isArray(assessments)||assessments!==undefined&&!Array.isArray(assessments))throw Error('CHECKPOINT_ASSESSMENT_RETENTION_REQUIRED');
  const assessmentKeys=new Set((assessments||[]).map(row=>row.key));
  if(assessmentKeys.size!==(assessments||[]).length||(c.audit||[]).some(event=>['assessment-evidence','assessment-rubric'].includes(event.action)&&!assessmentKeys.has(event.details?.assessmentKey)))throw Error('CHECKPOINT_ASSESSMENT_RETENTION_REQUIRED');
  // Commercial state needs owner-aware readers; predecessors accepting only 1/2
  // must refuse schema 3 rather than expose private records via old Office routes.
  const officeRows=c.office||[];if(!Array.isArray(officeRows))throw Error('CHECKPOINT_COMMERCE_RETENTION_REQUIRED');
  const retained=new Map(),officeKeys=new Set();for(const [pairKey,state] of officeRows){if(!text(pairKey)||officeKeys.has(pairKey)||!state||typeof state!=='object')throw Error('CHECKPOINT_COMMERCE_RETENTION_REQUIRED');officeKeys.add(pairKey);if(!state.commercial)continue;
   if(!Array.isArray(state.commercial.inquiries)||!Array.isArray(state.commercial.opportunities))throw Error('CHECKPOINT_COMMERCE_RETENTION_REQUIRED');
   for(const row of [...state.commercial.inquiries,...state.commercial.opportunities]){if(!text(row.key)||!text(row.subject)||retained.has(row.key))throw Error('CHECKPOINT_COMMERCE_RETENTION_REQUIRED');retained.set(row.key,{pairKey,row});}
  }
  const latest=new Map();for(const event of c.audit||[])if(['inquiry-create-evidence','opportunity-create-evidence','opportunity-status-evidence'].includes(event.action)){
   const saved=retained.get(event.details?.recordKey);if(!saved||saved.pairKey!==event.details?.pairKey||saved.row.subject!==event.details?.subject)throw Error('CHECKPOINT_COMMERCE_RETENTION_REQUIRED');latest.set(saved.row.key,event);
  }
  for(const {row} of retained.values()){const event=latest.get(row.key),record=clone(row);delete record.auditLink;
   if(!event||row.auditLink?.sequence!==event.sequence||row.auditLink?.sha256!==event.sha256||row.auditLink?.recordHash!==hash(record)||event.details.recordHash!==hash(record))throw Error('CHECKPOINT_COMMERCE_RETENTION_REQUIRED');
  }
  if((retained.size||latest.size)&&c.schema!==3)throw Error('CHECKPOINT_COMMERCE_SCHEMA_REQUIRED');
  this.#office=new Map(clone(c.office||[]));this.#knowledge.restore(c.audit);this.#tasks.restore(c.tasks);this.#learning.restore(c.learning);this.#monitor.restore(c.alerts);
  if(!['0.1.0-sandbox','0.1.1-sandbox'].includes(c.upgrade.version))throw Error('CHECKPOINT_VERSION_INVALID');
  this.#upgrades.version=c.upgrade.version;this.#upgrades.history=clone(c.upgrade.history);
  for(const saved of c.pairs){const config=validateConfig(saved.config);if(!this.#templates.some(t=>t.key===config.key&&hash(t)===hash(config)))throw Error('CHECKPOINT_CONFIG_CONFLICT');this.#pairs.set(config.key,{...clone(saved),config,busy:false,identity:inspectIdentity(config.identity)});}
  for(const t of this.#tasks.all())if(t.status==='RUNNING'){const live=this.#tasks.get(t.key);live.status='INTERRUPTED';live.output=null;live.error='PROCESS_RESTART';const p=this.#pair(t.pairKey);p.status='STOPPED';p.epoch++;p.stopReason='PROCESS_RESTART';this.#knowledge.append(system,'restart-interrupt','REVIEW REQUIRED',{taskKey:t.key});}
 }
 #pair(k){const p=this.#pairs.get(k);if(!p)throw Error('PAIR_NOT_FOUND');return p;}
 #authorize(actor,action){try{checkActor(actor,action);}catch(e){this.#knowledge.append({id:actor?.id||'unknown',role:actor?.role||'unknown'},action,'DENIED');throw e;}}
 #act(actor,action,run){this.#authorize(actor,action);try{const result=run();this.#knowledge.append(actor,action,'PASS');return clone(result);}catch(e){this.#knowledge.append(actor,action,'DENIED',{reason:e.message});throw e;}}
 instantiate(actor,templateKey,bootstrap=false){if(!bootstrap)this.#authorize(actor,'instantiate');else if(actor!==system)throw Error('BOOTSTRAP_FORBIDDEN');const config=this.#templates.find(c=>c.key===templateKey);if(!config)throw Error('CONFIG_NOT_FOUND');if(this.#pairs.has(config.key))throw Error('PAIR_ALREADY_EXISTS');config.permissions.resources.forEach(r=>this.#knowledge.read(r));const p={config,status:'READY',epoch:0,busy:false,stopReason:null,modules:Object.fromEntries(MODULES.map(k=>[k,this.#upgrades.version])),identity:inspectIdentity(config.identity)};this.#pairs.set(config.key,p);this.#knowledge.append(actor,'instantiate','PASS',{pairKey:config.key,configHash:hash(config)});return this.#publicPair(p);}
 #publicPair(p){return clone({key:p.config.key,name:p.config.name,status:p.status,busy:p.busy,stopReason:p.stopReason,config:p.config,identity:p.identity,modules:p.modules});}
 snapshot(actor){this.#authorize(actor,'read');return {mode:'SYNTHETIC SANDBOX • PRODUCTION NO-GO',pairs:[...this.#pairs.values()].map(p=>this.#publicPair(p)),templates:this.#templates.map(c=>({key:c.key,name:c.name,assignment:clone(c.assignment)})),tasks:this.#tasks.all(),learning:this.#learning.snapshot(),alerts:this.#monitor.alerts(),versions:this.#upgrades.snapshot(),knowledge:this.#knowledge.inventory(),audit:this.#knowledge.events(),auditValid:this.#knowledge.verify(),hub69:hubInventory(),groups:['V','000','135','246','789'],chapters:Array.from({length:10},(_,i)=>i)};}
 #officeState(pairKey){this.#pair(pairKey);if(!this.#office.has(pairKey))this.#office.set(pairKey,createState());return this.#office.get(pairKey);}
 officeSnapshot(actor,pairKey){this.#authorize(actor,'read');const state=clone(this.#officeState(pairKey));if(state.commercial)state.commercial=commercialState(state,actor);return {...state,modules,moduleContracts,registry};}
 officeCreate(actor,pairKey,kind,input){return this.#act(actor,'office-create',()=>{const state=this.#officeState(pairKey);let row;
  if(['application','enrollment','marketing','work-request'].includes(kind)){row=createOfficeIntake(state,kind,input,actor,this.#learning.snapshot().program);}
  else if(kind==='profile'){row=validateRegistration(input);if(state.registrations.some(p=>p.name===row.name&&p.developer===row.developer))throw Error('DUPLICATE_PROFILE');row.key=key();state.registrations.push(row);}
  else if(kind==='hstdn'){row=validateHSTDN(input,state);row.key=key();state.hstdn.push(row);}
  else if(['product','service'].includes(kind)){requireKeys(input,['name','source','officeRef','hstdnRef','scope','maturity','synthetic']);if(input.synthetic!==true||!text(input.name,200)||!safeURL(input.source)||!state.registrations.some(p=>p.key===input.officeRef&&p.subject===actor.id)||input.hstdnRef&&!state.hstdn.some(h=>h.key===input.hstdnRef&&h.members.includes(input.officeRef)))throw Error('CATALOG_SCOPE_INVALID');if(kind==='product'&&!['concept','research','prototype'].includes(input.maturity)||kind==='service'&&!text(input.scope,300))throw Error('CATALOG_MATURITY_REQUIRED');row={...clone(input),kind,key:key(),status:'DRAFT',sourceVerification:'NOT VERIFIED',capabilityVerification:'NOT VERIFIED',legalRelationshipVerification:'NOT VERIFIED'};state.records.push(row);}
  else throw Error('OFFICE_KIND_DENIED');row.subject??=actor.id;this.#knowledge.append(actor,'office-record','DRAFT ONLY',{pairKey,kind,recordKey:row.key,recordHash:hash(row)});return row;});}
 catalogSearch(actor,pairKey,input){this.#authorize(actor,'read');return searchCatalog(this.#officeState(pairKey),input);}
 commerceState(actor,pairKey){this.#authorize(actor,'read');return commercialState(this.#officeState(pairKey),actor);}
 inquiryMatch(actor,pairKey,input){this.#authorize(actor,'read');return matchInquiry(this.#officeState(pairKey),actor,input);}
 #commercialWrite(actor,pairKey,input,action,fn){return this.#act(actor,action,()=>{const row=fn(this.#officeState(pairKey),actor,input);delete row.auditLink;const event=this.#knowledge.append(actor,action+'-evidence','SYNTHETIC ONLY',{pairKey,subject:actor.id,recordKey:row.key,recordHash:hash(row)});row.auditLink={sequence:event.sequence,sha256:event.sha256,recordHash:event.details.recordHash};return row;});}
 inquiryCreate(actor,pairKey,input){return this.#commercialWrite(actor,pairKey,input,'inquiry-create',createInquiry);}
 opportunityCreate(actor,pairKey,input){return this.#commercialWrite(actor,pairKey,input,'opportunity-create',createOpportunity);}
 opportunityStatus(actor,pairKey,input){return this.#commercialWrite(actor,pairKey,input,'opportunity-status',updateOpportunity);}
 learn(actor,pairKey,lesson){return this.#act(actor,'learn',()=>{this.#pair(pairKey);return this.#learning.lesson(actor,pairKey,lesson);});}
 feedback(actor,taskKey,feedback){return this.#act(actor,'feedback',()=>this.#learning.feedback(actor,this.#tasks.get(taskKey),feedback));}
 prepareAssessment(actor,taskKey,input){return this.#act(actor,'assessment-submit',()=>{const row=this.#learning.prepareAssessment(actor,this.#tasks.get(taskKey),input);this.#knowledge.append(actor,'assessment-evidence','SYNTHETIC ONLY',{pairKey:row.pairKey,taskKey,assessmentKey:row.key,artifactSetDigest:row.artifactSetDigest});return row;});}
 reviewAssessment(actor,assessmentKey,input){return this.#act(actor,'assessment-review',()=>{const row=this.#learning.reviewAssessment(actor,assessmentKey,input);this.#knowledge.append(actor,'assessment-rubric','NOT CERTIFIED',{pairKey:row.pairKey,taskKey:row.taskKey,assessmentKey,artifactSetDigest:row.artifactSetDigest});return row;});}
 createTask(actor,pairKey,input){return this.#act(actor,'create-task',()=>{const p=this.#pair(pairKey);if(p.status!=='READY')throw Error('PAIR_STOPPED');return this.#tasks.create(p.config,actor,input);});}
 async runTask(actor,taskKey){
  this.#authorize(actor,'run-task');const t=this.#tasks.get(taskKey),p=this.#pair(t.pairKey);
  if(p.status!=='READY'||p.busy||t.status!=='QUEUED'){this.#knowledge.append(actor,'run-task','DENIED',{taskKey,reason:'TASK_OR_PAIR_NOT_READY'});throw Error('TASK_OR_PAIR_NOT_READY');}
  const epoch=p.epoch,controller=new AbortController();p.busy=true;this.#monitor.attach(p.config.key,controller);t.status='RUNNING';t.progress=10;
  this.#knowledge.append(actor,'task-start','PASS',{taskKey});let timer;
  if(this.#checkpointWriter){try{this.#checkpointWriter(this.checkpoint());}catch(e){controller.abort();p.busy=false;this.#monitor.detach(p.config.key);throw e;}}
  try{
   t.checks.push(inspectInput(t,p.config));checkTool(p.config,{tool:'source.read',resource:t.resource});if(t.kind!=='registry-audit')checkTool(p.config,{tool:'draft.write',resource:t.resource});const source=this.#knowledge.read(t.resource);
   const adapter=this.#adapterFactory(p.config.si.provider);
   const proposal=await Promise.race([adapter.propose({task:clone(t),source:clone(source),signal:controller.signal}),new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('ADAPTER_TIMEOUT'));},this.#timeout);})]);
   if(p.epoch!==epoch||p.status!=='READY')throw Error('SAFE_STOP');
   t.checks.push(inspectProposal(proposal,p.config));t.proposalHash=hash(proposal);for(const tool of proposal.tools){checkTool(p.config,tool);this.#knowledge.append(actor,'tool-check','PASS',{taskKey,tool:tool.tool,resource:tool.resource});}
   const before=crossCheck(p.config,t,proposal,source,'before-stage');t.checks.push(...before);if(before.some(c=>!c.pass))throw Error('CROSS_CHECK_FAILED');t.progress=70;
   // Stage only a cloned draft; check again before committing it into task evidence.
   const staged=clone(proposal),after=crossCheck(p.config,t,staged,this.#knowledge.read(t.resource),'after-stage');t.checks.push(...after);if(after.some(c=>!c.pass))throw Error('CROSS_CHECK_FAILED');
   if(p.epoch!==epoch||p.status!=='READY')throw Error('SAFE_STOP');
   t.output={...clone(staged.output),artifact:buildDraftArtifact(t.kind,staged.output)};t.status='AWAITING HUMAN REVIEW';t.progress=100;this.#knowledge.append(actor,'task-output','DRAFT ONLY',{taskKey,outputHash:hash(t.output),checks:before.length+after.length});
  }catch(e){
   if(p.epoch!==epoch||p.status==='STOPPED'){t.status='INTERRUPTED';t.error='SAFE_STOP';}
   else{t.status=/DENIED|CROSS_CHECK|INVALID/.test(e.message)?'BLOCKED':'FAILED';t.error=e.message;this.#monitor.stop(p,this.#tasks,e.message);t.status=/DENIED|CROSS_CHECK|INVALID/.test(e.message)?'BLOCKED':'FAILED';this.#monitor.alert(p.config.key,t.status);}
   t.output=null;this.#knowledge.append(actor,'task-exception',t.status,{taskKey,reason:t.error});
  }finally{clearTimeout(timer);controller.abort();p.busy=false;this.#monitor.detach(p.config.key);if(t.kind==='training-drill')this.#learning.evaluate(t);}
  return clone(t);
 }
 reviewTask(actor,taskKey,verdict){return this.#act(actor,'review',()=>{const t=this.#tasks.get(taskKey);if(t.status!=='AWAITING HUMAN REVIEW'||!['acknowledge-draft','reject-draft'].includes(verdict)||t.owner===actor.id)throw Error('INDEPENDENT_DEMO_REVIEW_REQUIRED');t.status=verdict==='acknowledge-draft'?'REVIEWED DRAFT':'REJECTED DRAFT';t.review={actor:actor.id,verdict,time:new Date().toISOString(),productionApproved:false};return t;});}
 stop(actor,pairKey){return this.#act(actor,'stop',()=>{const p=this.#pair(pairKey);this.#monitor.stop(p,this.#tasks);return this.#publicPair(p);});}
 recover(actor,pairKey){return this.#act(actor,'recover',()=>{const p=this.#pair(pairKey);const message=this.#monitor.recover(p);return {...this.#publicPair(p),message};});}
 retry(actor,taskKey){return this.#act(actor,'retry',()=>{const old=this.#tasks.get(taskKey),p=this.#pair(old.pairKey);if(!['FAILED','INTERRUPTED'].includes(old.status)||p.status!=='READY')throw Error('EXPLICIT_RECOVER_THEN_RETRY_REQUIRED');return this.#tasks.create(p.config,actor,{kind:old.kind,title:old.title,text:old.text,scenario:old.scenario,resource:old.resource},old.key);});}
 upgrade(actor,target){return this.#act(actor,'upgrade',()=>this.#upgrades.apply(target,[...this.#pairs.values()],this.#tasks));}
 rollback(actor){return this.#act(actor,'rollback',()=>this.#upgrades.rollback([...this.#pairs.values()],this.#tasks));}
}
