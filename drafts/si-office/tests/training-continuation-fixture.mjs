import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
import program from '../configs/training-basic-v1.json' with {type:'json'};
const s=new P2Sandbox(process.env.CFP_P2_DB);
for(const [id,role,workspace] of [['learner','editor','alpha'],['reviewer','reviewer','alpha'],['other','editor','alpha'],['outsider','editor','beta']])s.provision({id,password:'Synthetic-preview-fixture',role,workspace,pairs:['hub69-content-demo']});
const a=s.login('learner','Synthetic-preview-fixture'),r=s.login('reviewer','Synthetic-preview-fixture');
for(const l of program.basic.lessons)await s.execute(a,'learn',{pairKey:'hub69-content-demo',lesson:l.key});
for(const e of program.exercises.slice(0,11)){
 const t=await s.execute(a,'createTask',{pairKey:e.pairTemplate,input:e.task},{idempotencyKey:e.localKey});
 await s.execute(a,'runTask',{taskKey:t.key});await s.execute(a,'feedback',{taskKey:t.key,feedback:'Synthetic preview reflection'});await s.execute(r,'reviewTask',{taskKey:t.key,verdict:'acknowledge-draft'});
}
const server=createP2HTTP({service:s});server.listen(4191,'127.0.0.1',()=>console.log('READY'));
process.on('SIGTERM',()=>server.close(()=>{s.close();process.exit(0);}));
