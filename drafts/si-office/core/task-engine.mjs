import {requireKeys,text,key,clone} from './common.mjs';
export const TASK_KINDS=['website-draft','registry-audit','training-drill','hst-us-draft'];
export const SCENARIOS=['normal','overreach','bad-evidence','false-claim','adapter-error','timeout'];
export class TaskEngine {
 #tasks=[];
 create(config,actor,input,retryOf=null){
  requireKeys(input,['kind','title','text','scenario','resource']);
  if(!TASK_KINDS.includes(input.kind)||!config.missions.includes(input.kind)||!text(input.title,200)||input.text!==undefined&&!text(input.text,3000)||!SCENARIOS.includes(input.scenario||'normal'))throw Error('TASK_SCOPE_INVALID');
  const resource=input.resource||config.permissions.resources[0];if(!config.permissions.resources.includes(resource))throw Error('TASK_RESOURCE_DENIED');const t={key:key(),pairKey:config.key,kind:input.kind,title:input.title,text:input.text||'',scenario:input.scenario||'normal',resource,owner:actor.id,status:'QUEUED',progress:0,attempt:retryOf?2:1,retryOf,output:null,error:null,checks:[],review:null};this.#tasks.push(t);return t;
 }
 get(id){const t=this.#tasks.find(x=>x.key===id);if(!t)throw Error('TASK_NOT_FOUND');return t;}
 restore(tasks){this.#tasks=clone(tasks);}
 all(){return clone(this.#tasks);}
 pending(pairKey){return this.#tasks.some(t=>t.pairKey===pairKey&&['RUNNING','QUEUED','AWAITING HUMAN REVIEW'].includes(t.status));}
 interrupt(pairKey){for(const t of this.#tasks)if(t.pairKey===pairKey&&['QUEUED','RUNNING'].includes(t.status)){t.status='INTERRUPTED';t.error='SAFE_STOP';}}
}
// Trusted draft renderers; all identities remain unassigned, labels are display-only.
export function buildDraftArtifact(kind,output){
 if(kind==='website-draft'){
  const chapterNames=['Nền Tảng','Sự Sống','Con Người','Ba Quỹ','Tôn Giáo','Cộng Đồng','Siêu Trí Tuệ (SI🤖AI🤖) Robot 🤖 Siêu Phần Mềm & Công Nghệ','Doanh Nghiệp / HSTDN','Tổ Chức','Quốc Gia'];
  return {type:'WEBSITE CONTENT DRAFT',hub:'https://cfp.plus/69',groups:[{label:'V',chapters:[]},{label:'000',chapters:[0]},{label:'135',chapters:[1,3,5]},{label:'246',chapters:[2,4,6]},{label:'789',chapters:[7,8,9]}],chapters:chapterNames.map((title,chapter)=>({chapterSymbol:chapter,title,draftText:output.text,sections:[{localKey:'section-'+chapter,title:'Giới thiệu / Introduction',children:[{localKey:'detail-'+chapter,title:'Evidence & Work',status:'DRAFT'}]}],status:'DRAFT',canonical:null})),legacyLabelConflict:'0 vs 000: HUMAN GOVERNANCE; display-only draft; existing ID untouched',published:false};
 }
 if(kind==='hst-us-draft')return {type:'SYNTHETIC HSTDN PROFILE',legalName:'Synthetic Research Company • not a real legal entity',jurisdiction:'United States research scope only',industry:'Research / Education',officialWebsite:null,publicSourceURL:'https://github.com/charityfundplus/CFP.plus/issues/127',sourceCheckedAt:null,fixtureReadAt:new Date().toISOString(),products:[{name:'Synthetic Research Toolkit',maturity:'RESEARCH',capabilityStatus:'NOT VERIFIED'}],services:[{name:'Synthetic evidence review',scope:'Sandbox demonstration only'}],markets:['Research reference only'],publicContacts:[],legalRelations:[],id:null,parent:null,did:null,canonical:null,sourceStatus:'NOT VERIFIED',legalRelationshipStatus:'NOT VERIFIED',capabilityStatus:'NOT VERIFIED',description:output.text,published:false};
 if(kind==='registry-audit')return {type:'REGISTRY AUDIT DRAFT',finding:'US mapping conflict from baseline documentation',status:'CONFLICT / HUMAN GOVERNANCE',changesApplied:false,renumber:false};
 return {type:'TRAINING EXERCISE DRAFT',level:'SUPERVISED PRACTICE',promotionAllowed:false};
}
