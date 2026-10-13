import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';import {join} from 'node:path';
import {randomBytes} from 'node:crypto';import assert from 'node:assert/strict';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import program from '../configs/training-basic-v1.json' with {type:'json'};
import templates from '../configs/pairs.json' with {type:'json'};
// New scope: universal intake -> six advanced practice drafts, concurrently
// across isolated services. This is not an advanced competency assessment.
export async function rehearseIntakePractice({teams=4}={}){
 if(!Number.isInteger(teams)||teams<2||teams>6)throw Error('TEAM_COUNT_INVALID');
 const root=mkdtempSync(join(tmpdir(),'cfp-intake-practice-')),services=[];
 try{
 const rows=Array.from({length:teams},(_,i)=>{
  const workspace='practice-'+i,database=join(root,workspace+'.db'),service=new P2Sandbox(database),password=randomBytes(24).toString('hex');services.push(service);
  for(const [id,role] of [['learner','editor'],['reviewer','reviewer']])service.provision({id,password,role,workspace,pairs:['*']});
  return {workspace,database,service,learner:service.login('learner',password),reviewer:service.login('reviewer',password),entityType:['new-ai','existing-ai','developer','enterprise'][i%4],tasks:[],applications:[],enrollments:[]};
 });
 for(const row of rows){
  for(const template of templates){
   if(template.key!=='hub69-content-demo')await row.service.execute(row.learner,'instantiate',{templateKey:template.key});
   const application=await row.service.execute(row.learner,'officeCreate',{pairKey:template.key,kind:'application',input:{name:'Synthetic '+row.workspace+' '+template.key,entityType:row.entityType,contact:'https://example.org/synthetic',relationships:[],commitment:true,synthetic:true}});
   row.applications.push(application);
   for(const [i,track] of program.advanced.entries())if(templates[i%templates.length].key===template.key){
    const enrollment=await row.service.execute(row.learner,'officeCreate',{pairKey:template.key,kind:'enrollment',input:{name:'Synthetic advanced practice '+track.key,officeRef:application.key,source:'https://github.com/charityfundplus/CFP.plus/issues/130',scope:'Draft exercise only; verified assessor and real assessment pending',track:track.key,commitment:true,synthetic:true}});row.enrollments.push(enrollment);
    const task=await row.service.execute(row.learner,'createTask',{pairKey:template.key,input:{kind:'training-drill',title:'Advanced practice draft: '+track.key,text:'Synthetic reflection for '+track.key+'. Evidence and permission prerequisites remain pending. No competency or execution approval.',scenario:'normal',resource:template.permissions.resources[0]}},{idempotencyKey:'advanced-'+track.key});row.tasks.push(task);
   }
  }
 }
 // Run one newly mapped advanced exercise per independent DB at a barrier.
 const pending=rows.map(row=>row.service.execute(row.learner,'runTask',{taskKey:row.tasks[0].key}));
 for(const row of rows)assert.throws(()=>row.service.context(row.learner),/BUSY/);
 await Promise.all(pending);
 await Promise.all(rows.map(async row=>{
  for(const [i,task] of row.tasks.entries()){
   if(i)await row.service.execute(row.learner,'runTask',{taskKey:task.key});
   await row.service.execute(row.learner,'feedback',{taskKey:task.key,feedback:'Synthetic reflection: '+row.workspace+' '+task.key});
   await assert.rejects(row.service.execute(row.learner,'reviewTask',{taskKey:task.key,verdict:'acknowledge-draft'}));
   await row.service.execute(row.reviewer,'reviewTask',{taskKey:task.key,verdict:'acknowledge-draft'});
  }
 }));
 const result=[];
 for(const [i,row] of rows.entries()){
  const snapshot=await row.service.execute(row.learner,'snapshot');assert.equal(snapshot.tasks.length,6);assert(snapshot.tasks.every(t=>t.status==='REVIEWED DRAFT'));assert.equal(snapshot.learning.autoPromotion,false);
  assert(row.applications.every(a=>a.status==='EVIDENCE_PENDING'&&['id','parent','did','canonical'].every(k=>a[k]===null)));
  assert(row.enrollments.every(e=>e.assessment==='NOT ASSESSED'&&e.certification===false&&e.execution==='NOT AUTHORIZED'));
  assert.throws(()=>row.service.context(rows[(i+1)%teams].learner),/AUTH_DENIED/);
  const checkpoint=row.service.verify();row.service.close();const reopened=new P2Sandbox(row.database);services.push(reopened);assert.deepEqual(reopened.verify(),checkpoint);
  for(const template of templates){const office=await reopened.execute(row.learner,'officeSnapshot',{pairKey:template.key});assert.equal(office.registrations.length,1);assert.equal(office.records.filter(r=>r.kind==='enrollment').length,2);}
  result.push({workspace:row.workspace,entityType:row.entityType,applications:3,enrollments:6,reviewedAdvancedDrafts:6,pairs:3,restartVerified:true,foreignTokenDenied:true,audit:checkpoint});
 }
 return {mode:'SYNTHETIC ADVANCED PRACTICE / NOT ASSESSED',teams,concurrentServices:teams,sharedDatabase:false,results:result,realMemberACK:false,productionApproved:false};
 }finally{for(const service of services)service.close();rmSync(root,{recursive:true,force:true});}
}
if(process.argv[1]?.endsWith('/intake-team-practice.mjs'))console.log(JSON.stringify(await rehearseIntakePractice(),null,2));
