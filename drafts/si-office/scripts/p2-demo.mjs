import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {randomBytes} from 'node:crypto';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
const dir=mkdtempSync(join(tmpdir(),'cfp-p2-demo-')),password=randomBytes(24).toString('hex');let s=new P2Sandbox(join(dir,'state.db')),restored;
try{
 for(const [id,role,maintainer] of [['editor','editor',false],['reviewer','reviewer',true]])s.provision({id,password,role,workspace:'synthetic',maintainer});
 const e=s.login('editor',password),r=s.login('reviewer',password);
 const task=await s.execute(e,'createTask',{pairKey:'hub69-content-demo',input:{kind:'website-draft',title:'P2 synthetic demo',text:'Draft only',resource:'website-demo',scenario:'normal'}},{idempotencyKey:'demo'});
 await s.execute(e,'runTask',{taskKey:task.key});await s.execute(r,'reviewTask',{taskKey:task.key,verdict:'acknowledge-draft'});
 const checkpoint=s.verify(),backup=join(dir,'backup.db');s.backup(r,backup);restored=P2Sandbox.restore(backup,join(dir,'restore.db'));
 const rr=restored.login('reviewer',password),state=await restored.execute(rr,'snapshot');
 console.log(JSON.stringify({mode:'P2 SYNTHETIC ONLY / PRODUCTION NO-GO',reviewedTask:state.tasks[0].status,restoredTasks:state.tasks.length,checkpoint,restoreCheckpoint:restored.verify(),adapters:restored.adapters(rr),identity:state.pairs[0].config.identity},null,2));
}finally{restored?.close();s.close();rmSync(dir,{recursive:true,force:true});}
