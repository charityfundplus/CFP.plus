// Trusted local coordinator, NOT an anonymous HTTP or agent-assignment endpoint.
// Tokens stay in caller memory. One queue per DB identity within this coordinator;
// independent DBs may run concurrently. No general multi-process SQLite claim.
import {requireKeys,text,clone} from '../core/common.mjs';
const permitted=new Set(['createTask','runTask','learn','feedback','prepareAssessment','reviewAssessment','officeCreate','officeSnapshot']);
export class PairCoordinator {
 #bindings;#busy=false;
 constructor(bindings,{maxConcurrentDatabases=2}={}){
  if(!Array.isArray(bindings)||!bindings.length||bindings.length>12||!Number.isInteger(maxConcurrentDatabases)||maxConcurrentDatabases<1||maxConcurrentDatabases>4)throw Error('COORDINATOR_CONFIG_INVALID');
  this.maxConcurrentDatabases=maxConcurrentDatabases;this.#bindings=new Map();
  for(const binding of bindings){requireKeys(binding,['name','service','token','pairKey']);if(!text(binding.name,80)||!text(binding.pairKey,80)||this.#bindings.has(binding.name)||typeof binding.service?.coordinationKey!=='string')throw Error('COORDINATOR_BINDING_INVALID');this.#bindings.set(binding.name,binding);}
 }
 async dispatch(jobs){
  if(this.#busy)throw Error('COORDINATOR_BUSY');
  if(!Array.isArray(jobs)||!jobs.length||jobs.length>24)throw Error('COORDINATOR_BATCH_INVALID');
  const groups=new Map();
  for(const [index,job] of jobs.entries()){
   requireKeys(job,['binding','command','args','options']);const binding=this.#bindings.get(job.binding);
   if(!binding||!permitted.has(job.command))throw Error('COORDINATOR_COMMAND_DENIED');
   if(job.args?.pairKey&&job.args.pairKey!==binding.pairKey)throw Error('COORDINATOR_PAIR_DENIED');
   const group=groups.get(binding.service.coordinationKey)||[];group.push({index,job,binding});groups.set(binding.service.coordinationKey,group);
  }
  this.#busy=true;const pending=[...groups.values()],results=Array(jobs.length);let active=0,peak=0;
  const worker=async()=>{while(pending.length){const group=pending.shift();active++;peak=Math.max(peak,active);try{for(const {index,job,binding} of group){
   try{
    const auth=binding.service.context(binding.token);if(!auth.pairs.includes('*')&&!auth.pairs.includes(binding.pairKey))throw Error('COORDINATOR_PAIR_DENIED');
    if(job.args?.taskKey||job.args?.assessmentKey){const state=await binding.service.execute(binding.token,'snapshot');const row=job.args.taskKey?state.tasks.find(t=>t.key===job.args.taskKey):state.learning.assessments.find(t=>t.key===job.args.assessmentKey);if(!row||row.pairKey!==binding.pairKey)throw Error('COORDINATOR_TASK_SCOPE_DENIED');}
    const value=await binding.service.execute(binding.token,job.command,job.args||{},job.options||{});
    results[index]={binding:job.binding,pairKey:binding.pairKey,command:job.command,status:'COMPLETED SYNTHETIC',value:clone(value)};
   }catch(e){results[index]={binding:job.binding,pairKey:binding.pairKey,command:job.command,status:'DENIED / FAILED',error:e.message};}
  }}finally{active--;}}};
  try{await Promise.all(Array.from({length:Math.min(this.maxConcurrentDatabases,pending.length)},worker));return {mode:'BOUNDED LOCAL COORDINATION / SYNTHETIC ONLY',peakConcurrentDatabases:peak,results,memberAssignmentVerified:false,productionApproved:false};}finally{this.#busy=false;}
 }
}
