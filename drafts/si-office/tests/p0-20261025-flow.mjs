import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {randomBytes,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {executionProvenance} from '../scripts/build-provenance.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
export async function runP0Flow(destination){
 mkdirSync(destination,{recursive:false});
 const temp=mkdtempSync(join(tmpdir(),'cfp-p0-')),services=[],checks=[];
 const checked=(name,expected,observed)=>{assert.deepEqual(observed,expected,name);checks.push({name,expected,observed,result:'PASS'});};
 try{
  const source=executionProvenance(fileURLToPath(new URL('../',import.meta.url)));
  checked('runtime bytes match Git source',true,source.verified);
  const rows=['hub69-content-demo','training-demo'].map((pairKey,i)=>{
   const workspace='p0-team-'+i,database=join(temp,workspace+'.sqlite'),service=new P2Sandbox(database),password=randomBytes(24).toString('hex');services.push(service);
   for(const [id,role] of [['learner','editor'],['reviewer','reviewer']])service.provision({id,password,role,workspace,pairs:[pairKey]});
   return {workspace,database,service,password,pairKey,learner:service.login('learner',password),reviewer:service.login('reviewer',password)};
  });
  for(const [i,row] of rows.entries()){
   if(i)await row.service.execute(row.learner,'instantiate',{templateKey:row.pairKey});
   row.registration=await row.service.execute(row.learner,'officeCreate',{pairKey:row.pairKey,kind:'application',input:{name:'Synthetic P0 '+row.workspace,entityType:'new-ai',contact:'https://example.org/synthetic',relationships:[],commitment:true,synthetic:true}});
   for(const f of ['id','parent','did','canonical'])checked(row.workspace+' unbound '+f,null,row.registration[f]);
   for(const lesson of ['identity-lineage','ethics-governance','tool-use','security','evidence'])await row.service.execute(row.learner,'learn',{pairKey:row.pairKey,lesson});
   row.task=await row.service.execute(row.learner,'createTask',{pairKey:row.pairKey,input:{kind:'training-drill',title:'P0 '+row.workspace,text:'Synthetic isolated exercise '+row.workspace,scenario:'normal',resource:i?'training-demo':'website-demo'}},{idempotencyKey:'p0-round'});
  }
  const pending=rows.map(row=>row.service.execute(row.learner,'runTask',{taskKey:row.task.key}));
  for(const row of rows){assert.throws(()=>row.service.context(row.learner),/BUSY/);checks.push({name:row.workspace+' in flight at concurrency barrier',expected:'BUSY',observed:'BUSY',result:'PASS'});}
  const runs=await Promise.all(pending);
  for(const [i,row] of rows.entries()){
   checked(row.workspace+' execution receipt',true,runs[i].executionReceipt.sourceVerified);
   checked(row.workspace+' execution revision',source.revision,runs[i].executionReceipt.revision);
   checked(row.workspace+' output digest',sha(JSON.stringify(runs[i].output)),runs[i].executionReceipt.outputSha256);
   await row.service.execute(row.learner,'feedback',{taskKey:row.task.key,feedback:'Synthetic feedback for '+row.workspace});
   await assert.rejects(row.service.execute(row.learner,'reviewTask',{taskKey:row.task.key,verdict:'acknowledge-draft'}));
   checks.push({name:row.workspace+' learner cannot review own draft',expected:'DENIED',observed:'DENIED',result:'PASS'});
   await row.service.execute(row.reviewer,'reviewTask',{taskKey:row.task.key,verdict:'acknowledge-draft'});
   const foreign=rows[1-i];
   assert.throws(()=>row.service.context(foreign.learner),/AUTH_DENIED/);
   await assert.rejects(row.service.execute(row.learner,'runTask',{taskKey:foreign.task.key}),/PAIR_SCOPE_DENIED/);
   await assert.rejects(row.service.execute(row.learner,'officeSnapshot',{pairKey:foreign.pairKey}),/PAIR_SCOPE_DENIED/);
   checks.push({name:row.workspace+' foreign token/task/pair denied',expected:3,observed:3,result:'PASS'});
   const state=await row.service.execute(row.learner,'snapshot'),office=await row.service.execute(row.learner,'officeSnapshot',{pairKey:row.pairKey});
   checked(row.workspace+' only own task',[row.task.key],state.tasks.map(t=>t.key));
   checked(row.workspace+' five study records',5,state.learning.observations.length);
   checked(row.workspace+' feedback bound',state.tasks[0].proposalHash,state.learning.feedback[0].outputHash);
   checked(row.workspace+' reviewed draft','REVIEWED DRAFT',state.tasks[0].status);
   checked(row.workspace+' no auto promotion',false,state.learning.autoPromotion);
   const checkpoint=row.service.verify();row.service.close();
   const reopened=new P2Sandbox(row.database);services.push(reopened);
   checked(row.workspace+' durable audit after reopen',checkpoint,reopened.verify());
   const readback=await reopened.execute(row.learner,'snapshot');
   checked(row.workspace+' durable task readback',state.tasks,readback.tasks);
   checked(row.workspace+' durable learning readback',state.learning,readback.learning);
   checked(row.workspace+' durable registration readback',office,await reopened.execute(row.learner,'officeSnapshot',{pairKey:row.pairKey}));
   const payload={format:'cfp-p0-synthetic-round-v1',workspace:row.workspace,pairKey:row.pairKey,registration:row.registration,tasks:readback.tasks,learning:readback.learning,auditCheckpoint:checkpoint,source,assessment:'NOT ASSESSED',activationAllowed:false};
   const bytes=JSON.stringify(payload,null,2)+'\n',path=join(destination,row.workspace+'.json');writeFileSync(path,bytes,{flag:'wx'});
   checked(row.workspace+' saved Evidence byte readback',sha(bytes),sha(readFileSync(path)));
  }
  // Shared SQLite database: workspace and pair grants must both hold.
  const shared=new P2Sandbox(join(temp,'shared.sqlite'));services.push(shared);const password=randomBytes(24).toString('hex');
  for(const workspace of ['alpha','beta'])shared.provision({id:workspace,password,role:'editor',workspace,pairs:['hub69-content-demo']});
  const alpha=shared.login('alpha',password),beta=shared.login('beta',password);
  const task=await shared.execute(alpha,'createTask',{pairKey:'hub69-content-demo',input:{kind:'website-draft',title:'Alpha private draft',text:'Synthetic alpha only',resource:'website-demo'}},{idempotencyKey:'shared'});
  checked('shared DB beta cannot list alpha task',[],(await shared.execute(beta,'snapshot')).tasks);
  await assert.rejects(shared.execute(beta,'runTask',{taskKey:task.key}),/PAIR_SCOPE_DENIED/);
  shared.provision({id:'limited',password,role:'editor',workspace:'alpha',pairs:['training-demo']});
  const limited=shared.login('limited',password);
  checked('same workspace different pair cannot list task',[],(await shared.execute(limited,'snapshot')).tasks);
  await assert.rejects(shared.execute(limited,'runTask',{taskKey:task.key}),/PAIR_SCOPE_DENIED/);
  checks.push({name:'shared DB cross-workspace and same-workspace cross-pair writes denied',expected:2,observed:2,result:'PASS'});
  const receipt={schemaVersion:1,mode:'LOCAL SYNTHETIC / TWO CONCURRENT DATABASES',startedFrom:'06f386b1ba52358779cec6bc26c2d88f6a33664a',runtimeRevision:source.revision,manifestSha256:source.manifestSha256,checkedAt:new Date().toISOString(),concurrentServices:2,sharedDatabaseIsolationAlsoTested:true,checks,competencyPass:false,independentReview:'PENDING',productionApproved:false};
  writeFileSync(join(destination,'RUNTIME_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});return receipt;
 }finally{for(const s of services)s.close();rmSync(temp,{recursive:true,force:true});}
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const receipt=await runP0Flow(process.argv[2]);console.log(JSON.stringify({runtimeRevision:receipt.runtimeRevision,checks:receipt.checks.length,fail:0,concurrentServices:2}));}
