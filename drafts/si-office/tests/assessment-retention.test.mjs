import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {randomBytes,createHash} from 'node:crypto';
import {CoreEngine} from '../core/core-engine.mjs';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {hash} from '../core/common.mjs';
import {evidenceKinds} from '../core/training-assessment.mjs';
const learner={id:'retention-learner',role:'editor'}, reviewer={id:'retention-reviewer',role:'reviewer'},pairKey='hub69-content-demo';
async function packet(call){
 for(const lesson of ['identity-lineage','ethics-governance','tool-use','security','evidence'])await call(learner,'learn',[pairKey,lesson]);
 const t=await call(learner,'createTask',[pairKey,{kind:'training-drill',title:'Retention regression',text:'Synthetic only',scenario:'normal',resource:'website-demo'}]);
 await call(learner,'runTask',[t.key]);await call(learner,'feedback',[t.key,'Synthetic retention fixture']);
 const reviewed=await call(reviewer,'reviewTask',[t.key,'acknowledge-draft']);
 const artifacts=evidenceKinds.recovery.map(kind=>{const content=JSON.stringify({kind,synthetic:true});return {kind,content,sha256:hash(content),taskKey:t.key,outputHash:hash(reviewed.output)};});
 return call(learner,'prepareAssessment',[t.key,{track:'recovery',sourceRevision:'11bb42464afebcd2962ca0ab94df0822853445c3',synthetic:true,artifacts}]);
}
test('assessment-bearing checkpoint refuses legacy schema reader and detects evidence loss without audit edits',async()=>{
 const e=new CoreEngine();await packet((a,method,args)=>e[method](a,...args));const c=e.checkpoint();assert.equal(c.schema,2);
 // Execute the pinned predecessor implementation with current unchanged imports.
 const original=readFileSync(new URL('./fixtures/core-engine-11bb.txt',import.meta.url),'utf8');
 assert.equal(createHash('sha1').update('blob '+Buffer.byteLength(original)+'\0').update(original).digest('hex'),'fa73ae63d2b1b353efccbccebe8f3eabdda30dcb');
 const fixture=fileURLToPath(new URL('../core/legacy-retention-fixture-'+randomBytes(8).toString('hex')+'.mjs',import.meta.url));
 try{writeFileSync(fixture,original);const {CoreEngine:LegacyEngine}=await import(pathToFileURL(fixture).href);assert.throws(()=>new LegacyEngine({checkpoint:c}),/CHECKPOINT_INCOMPATIBLE/);}finally{rmSync(fixture,{force:true});}
 const restored=new CoreEngine({checkpoint:c});assert.deepEqual(restored.checkpoint().learning.assessments,c.learning.assessments);assert.deepEqual(restored.checkpoint().audit,c.audit);
 for(const schema of [1,2])for(const replacement of [undefined,[]]){const damaged=structuredClone(c);damaged.schema=schema;damaged.learning.assessments=replacement;assert.throws(()=>new CoreEngine({checkpoint:damaged}),/ASSESSMENT_RETENTION_REQUIRED/);}
 const legacy=new CoreEngine().checkpoint();delete legacy.learning.assessments;assert.deepEqual(new CoreEngine({checkpoint:legacy}).checkpoint().learning.assessments,[]);
});
test('upgrade and sandbox rollback retain assessment checkpoints, review, and prior audit prefix',async()=>{
 const e=new CoreEngine();const row=await packet((a,m,args)=>e[m](a,...args));e.reviewAssessment(reviewer,row.key,{verdict:'needs-evidence',feedback:'Synthetic only',artifactSetDigest:row.artifactSetDigest,synthetic:true});
 const before=e.checkpoint();e.upgrade(reviewer,'0.1.1-sandbox');e.rollback(reviewer);const after=new CoreEngine({checkpoint:e.checkpoint()}).checkpoint();assert.equal(after.schema,2);assert.deepEqual(after.learning.assessments,before.learning.assessments);assert.deepEqual(after.audit.slice(0,before.audit.length),before.audit);assert.equal(after.upgrade.version,'0.1.0-sandbox');
});
test('SQLite backup restore retains schema2 packets and revokes old sessions',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'cfp-retention-'));let service,restored;
 try{service=new P2Sandbox(join(dir,'state.db'));const password=randomBytes(24).toString('hex'),tokens={};for(const actor of [learner,reviewer]){service.provision({id:actor.id,role:actor.role,workspace:'retention-fixture',password,maintainer:actor===reviewer});tokens[actor.id]=service.login(actor.id,password);}
 const mapping={learn:args=>({pairKey:args[0],lesson:args[1]}),createTask:args=>({pairKey:args[0],input:args[1]}),runTask:args=>({taskKey:args[0]}),feedback:args=>({taskKey:args[0],feedback:args[1]}),reviewTask:args=>({taskKey:args[0],verdict:args[1]}),prepareAssessment:args=>({taskKey:args[0],input:args[1]})};
 const row=await packet((a,m,args)=>service.execute(tokens[a.id],m,mapping[m](args),m==='createTask'?{idempotencyKey:'retention-new-task'}:{}));const before=await service.execute(tokens[learner.id],'snapshot');service.backup(tokens[reviewer.id],join(dir,'backup.db'));restored=P2Sandbox.restore(join(dir,'backup.db'),join(dir,'restored.db'));
 await assert.rejects(restored.execute(tokens[learner.id],'snapshot'),/AUTH_DENIED/);const fresh=restored.login(learner.id,password),after=await restored.execute(fresh,'snapshot');assert.deepEqual(after.learning.assessments,before.learning.assessments);assert.equal(after.learning.assessments[0].key,row.key);assert.deepEqual(after.audit,before.audit);assert.equal(after.learning.autoPromotion,false);
 }finally{restored?.close();service?.close();rmSync(dir,{recursive:true,force:true});}
});
