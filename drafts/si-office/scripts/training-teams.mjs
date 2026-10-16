import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import program from '../configs/training-basic-v1.json' with {type:'json'};

// Independent services/databases run concurrently. Each service retains its
// existing single-writer contract; this does not share one DB across processes.
export async function rehearseTeams({teams=3}={}){
 if(!Number.isInteger(teams)||teams<2||teams>6)throw Error('TEAM_COUNT_INVALID');
 const root=mkdtempSync(join(tmpdir(),'cfp-training-teams-')),services=[];
 try{
  const rows=Array.from({length:teams},(_,i)=>{
   const workspace='team-'+i,service=new P2Sandbox(join(root,workspace+'.db'));
   services.push(service);
   for(const [id,role] of [['learner','editor'],['reviewer','reviewer']])service.provision({id,password:'Synthetic-team-rehearsal',role,workspace,pairs:['*']});
   return {workspace,service,learner:service.login('learner','Synthetic-team-rehearsal'),reviewer:service.login('reviewer','Synthetic-team-rehearsal')};
  });
  // Reach a barrier while runTask awaits an adapter, proving real overlap.
  const tasks=await Promise.all(rows.map(r=>r.service.execute(r.learner,'createTask',{pairKey:'hub69-content-demo',input:program.exercises[0].task},{idempotencyKey:'overlap'})));
  const inFlight=rows.map((r,i)=>r.service.execute(r.learner,'runTask',{taskKey:tasks[i].key}));
  for(const r of rows)assert.throws(()=>r.service.context(r.learner),/BUSY/);
  const runs=await Promise.all(inFlight);assert(runs.every(t=>t.status==='AWAITING HUMAN REVIEW'));
  await Promise.all(rows.map(async(r,i)=>{
   await r.service.execute(r.learner,'feedback',{taskKey:tasks[i].key,feedback:'Synthetic team '+i+' reflection'});
   await r.service.execute(r.reviewer,'reviewTask',{taskKey:tasks[i].key,verdict:'acknowledge-draft'});
   for(const templateKey of ['training-demo','us-hstdn-demo']){
    await r.service.execute(r.learner,'instantiate',{templateKey});
    const resource=templateKey==='training-demo'?'training-demo':'hst-us-demo';
    const t=await r.service.execute(r.learner,'createTask',{pairKey:templateKey,input:{kind:'training-drill',title:'Synthetic team '+i+' • '+templateKey,text:'Bounded synthetic practice',resource,scenario:'normal'}},{idempotencyKey:templateKey});
    assert.equal((await r.service.execute(r.learner,'runTask',{taskKey:t.key})).status,'AWAITING HUMAN REVIEW');
    await r.service.execute(r.reviewer,'reviewTask',{taskKey:t.key,verdict:'acknowledge-draft'});
   }
  }));
  const results=[];
  for(const [i,r] of rows.entries()){
   const s=await r.service.execute(r.learner,'snapshot');assert.equal(s.pairs.length,3);assert.equal(s.tasks.length,3);assert(s.tasks.every(t=>t.status==='REVIEWED DRAFT'));assert.equal(s.learning.autoPromotion,false);
   assert(s.learning.feedback.every(f=>f.text==='Synthetic team '+i+' reflection'));
   assert(s.pairs.every(p=>Object.values(p.config.identity).length&&p.config.identity.id===null&&p.config.identity.parent===null&&p.config.identity.did===null&&p.config.identity.canonical===null));
   // A token from another team's service cannot authenticate here.
   assert.throws(()=>r.service.context(rows[(i+1)%teams].learner),/AUTH_DENIED/);
   const before=r.service.verify();r.service.close();const reopened=new P2Sandbox(join(root,r.workspace+'.db'));services.push(reopened);
   assert.deepEqual(reopened.verify(),before);assert.equal((await reopened.execute(r.learner,'snapshot')).tasks.length,3);
   results.push({workspace:r.workspace,pairs:3,reviewedTasks:3,foreignTokenDenied:true,restartVerified:true,audit:before});
  }
  return {mode:'SYNTHETIC REHEARSAL / NO REAL MEMBER ACK',teams,concurrentServices:teams,sharedDatabase:false,pairsPerTeam:3,results,productionApproved:false};
 }finally{for(const s of services)s.close();rmSync(root,{recursive:true,force:true});}
}
if(process.argv[1]?.endsWith('/training-teams.mjs'))console.log(JSON.stringify(await rehearseTeams(),null,2));
