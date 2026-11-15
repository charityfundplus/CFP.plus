import {CoreEngine} from '../core/core-engine.mjs';
import program from '../configs/training-basic-v1.json' with {type:'json'};
const core=new CoreEngine(),editor={id:'synthetic-trainee',role:'editor'},reviewer={id:'synthetic-reviewer',role:'reviewer'};const results=[];
for(const lesson of program.basic.lessons)core.learn(editor,'hub69-content-demo',lesson.key);
for(const exercise of program.exercises){const t=core.createTask(editor,exercise.pairTemplate,exercise.task);const run=await core.runTask(editor,t.key);core.feedback(editor,t.key,'Synthetic evidence reflection: '+exercise.expectedOutput);core.reviewTask(reviewer,t.key,'acknowledge-draft');results.push({exercise:exercise.localKey,officeModule:exercise.officeModule,taskKey:t.key,status:run.status,checks:run.checks.length,privilegeChange:false});}
console.log(JSON.stringify({program:program.version,mode:'SUPERVISED SYNTHETIC DRAFT EXERCISES; NOT 12 COMPLETE PRODUCTION MODULES',results,auditValid:core.snapshot(reviewer).auditValid,noAutomaticPromotion:true},null,2));
