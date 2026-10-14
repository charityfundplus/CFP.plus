// Temporary synthetic fixture for the NEW export field, never a hosted preview.
import {join} from 'node:path';import {writeFileSync} from 'node:fs';import {randomBytes} from 'node:crypto';
import {P2Sandbox} from '../sandbox/p2-service.mjs';import {createP2HTTP} from '../sandbox/p2-http.mjs';
import {hash} from '../core/common.mjs';import {evidenceKinds} from '../core/training-assessment.mjs';
if(process.env.CFP_NEW_SCOPE_LOCAL_QA!=='true'||!process.env.CFP_ASSESSMENT_QA_DIR)throw Error('LOCAL_QA_ONLY');
const dir=process.env.CFP_ASSESSMENT_QA_DIR,service=new P2Sandbox(join(dir,'state.db'));
const accounts=['learner','other','reviewer','viewer'].map(id=>({id,role:id==='reviewer'?'reviewer':id==='viewer'?'viewer':'editor',workspace:'export-qa',pairs:['*'],password:randomBytes(24).toString('hex')}));
for(const account of accounts)service.provision(account);writeFileSync(join(dir,'accounts.json'),JSON.stringify(accounts),{mode:0o600,flag:'wx'});
const reviewer=service.login('reviewer',accounts.find(a=>a.id==='reviewer').password);
for(const id of ['learner','other']){
 const token=service.login(id,accounts.find(a=>a.id===id).password),pairKey='hub69-content-demo';
 for(const lesson of ['identity-lineage','ethics-governance','tool-use','security','evidence'])await service.execute(token,'learn',{pairKey,lesson});
 const queued=await service.execute(token,'createTask',{pairKey,input:{kind:'training-drill',title:'New export fixture '+id,text:'Synthetic test only',scenario:'normal',resource:'website-demo'}},{idempotencyKey:'export-'+id});
 await service.execute(token,'runTask',{taskKey:queued.key});await service.execute(token,'feedback',{taskKey:queued.key,feedback:'Test output not real competence'});const task=await service.execute(reviewer,'reviewTask',{taskKey:queued.key,verdict:'acknowledge-draft'});
 const artifacts=evidenceKinds.sources.map(kind=>{const content='Synthetic export fixture '+kind;return {kind,content,sha256:hash(content),taskKey:task.key,outputHash:hash(task.output)};});
 await service.execute(token,'prepareAssessment',{taskKey:task.key,input:{track:'sources',sourceRevision:'690b711316fd1dc41d7bee328609d471f1ddafb9',artifacts,synthetic:true}});
}
const server=createP2HTTP({service});server.listen(0,'127.0.0.1',()=>writeFileSync(join(dir,'ready.json'),JSON.stringify({url:'http://127.0.0.1:'+server.address().port+'/p2',scope:'Local new-export QA only, no pinned-build claim'}),{mode:0o600,flag:'wx'}));
process.once('SIGTERM',()=>server.close(()=>{service.close();process.exit(0);}));
