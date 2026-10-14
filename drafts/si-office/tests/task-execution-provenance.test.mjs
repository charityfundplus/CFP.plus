import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,cpSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {trainingWorksheet} from '../scripts/training-export-worksheet.mjs';
import {gitRead,executionProvenance} from '../scripts/build-provenance.mjs';
const source=fileURLToPath(new URL('../',import.meta.url));
test('new execution receipt survives checkpoint, reopening, private backup/restore; source drift fails closed',async()=>{
 const root=mkdtempSync(join(tmpdir(),'cfp-task-source-')),state=mkdtempSync(join(tmpdir(),'cfp-task-state-'));
 let service,restored;
 try{
  cpSync(source,root,{recursive:true,filter:p=>!p.includes('/tests')&&!p.includes('/docs')&&!p.includes('/.git')});
  gitRead(root,'init','-q');gitRead(root,'config','user.name','Synthetic Fixture');gitRead(root,'config','user.email','fixture@example.invalid');gitRead(root,'add','.');gitRead(root,'commit','-qm','Synthetic task provenance fixture');
  const {P2Sandbox}=await import(pathToFileURL(join(root,'sandbox/p2-service.mjs')));
  const database=join(state,'state.sqlite');service=new P2Sandbox(database);
  for(const [id,role] of [['learner','editor'],['reviewer','reviewer']])service.provision({id,role,password:'synthetic-password-123',workspace:'fixture',maintainer:role==='reviewer'});
  let token=service.login('learner','synthetic-password-123');
  const input={kind:'website-draft',title:'Synthetic source-bound task',text:'Synthetic content only',scenario:'normal',resource:'website-demo'};
  const t=await service.execute(token,'createTask',{pairKey:'hub69-content-demo',input},{idempotencyKey:'source-fixture'});
  const run=await service.execute(token,'runTask',{taskKey:t.key});assert.equal(run.executionReceipt.sourceVerified,true);assert.equal(run.executionReceipt.taskKey,t.key);assert.equal(run.executionReceipt.subject,'learner');assert.equal(run.executionReceipt.authorityVerified,false);assert(run.executionReceipt.outputSha256);
  const build=executionProvenance(root),payload={format:'cfp-training-evidence-v1',workspace:'fixture',journey:{subject:'learner',pairKey:run.pairKey,basicDraftReady:true},tasks:[run],observations:[],feedback:[],sourceRevision:build.revision,buildProvenance:build};
  const envelope=()=>{const payloadJSON=JSON.stringify(payload);return {payloadJSON,digestOf:'UTF-8 payloadJSON bytes',sha256:createHash('sha256').update(payloadJSON).digest('hex')};};
  const program={basic:{lessons:[]},exercises:[],advanced:[]},scope={developmentRevision:build.revision,allowedPairs:[run.pairKey],sourceRoot:root};
  assert.equal(trainingWorksheet(envelope(),program,scope).taskReceiptBindingsVerified,true);assert.equal(trainingWorksheet(envelope(),program,scope).taskExecutionRevisionVerified,false);
  const forged=structuredClone(run.executionReceipt);payload.tasks[0].executionReceipt.taskKey='foreign';assert.throws(()=>trainingWorksheet(envelope(),program,scope),/TASK_EXECUTION_SOURCE_RECEIPT_MISMATCH/);payload.tasks[0].executionReceipt=structuredClone(forged);payload.tasks[0].executionReceipt.subject='foreign';assert.throws(()=>trainingWorksheet(envelope(),program,scope),/TASK_EXECUTION_SOURCE_RECEIPT_MISMATCH/);payload.tasks[0].executionReceipt=structuredClone(forged);payload.tasks[0].executionReceipt.workspace='foreign';assert.throws(()=>trainingWorksheet(envelope(),program,scope),/TASK_EXECUTION_SOURCE_RECEIPT_MISMATCH/);payload.tasks[0].executionReceipt=forged;
  const historical=structuredClone(run);delete historical.executionReceipt;payload.tasks=[historical];assert.equal(trainingWorksheet(envelope(),program,scope).taskExecutionRevisionVerified,false);payload.tasks=[run];
  service.close();service=new P2Sandbox(database);token=service.login('learner','synthetic-password-123');
  let snap=await service.execute(token,'snapshot');assert.deepEqual(snap.tasks.find(x=>x.key===t.key).executionReceipt,run.executionReceipt);
  const admin=service.login('reviewer','synthetic-password-123'),backup=join(state,'backup.sqlite');service.backup(admin,backup);restored=P2Sandbox.restore(backup,join(state,'restored.sqlite'));
  const restoredToken=restored.login('learner','synthetic-password-123');snap=await restored.execute(restoredToken,'snapshot');assert.deepEqual(snap.tasks.find(x=>x.key===t.key).executionReceipt,run.executionReceipt);
  const next=await service.execute(token,'createTask',{pairKey:'hub69-content-demo',input},{idempotencyKey:'drift-fixture'});writeFileSync(join(root,'public','core.js'),'// source changed after module load');
  const drift=await service.execute(token,'runTask',{taskKey:next.key});assert.equal(drift.executionReceipt.sourceVerified,false);assert.equal(drift.executionReceipt.activationAllowed,false);
 }finally{service?.close();restored?.close();rmSync(root,{recursive:true,force:true});rmSync(state,{recursive:true,force:true});}
});
