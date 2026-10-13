import {pathToFileURL} from 'node:url';import {join,resolve} from 'node:path';
import {mkdtempSync,rmSync,readFileSync,writeFileSync,existsSync} from 'node:fs';import {tmpdir} from 'node:os';import {randomBytes} from 'node:crypto';import assert from 'node:assert/strict';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {SandboxReleaseControl,packRelease,verifyRelease} from '../sandbox/release-control.mjs';
export async function rehearseCompatibility(baselineRoot){
 const {P2Sandbox:Baseline}=await import(pathToFileURL(join(resolve(baselineRoot),'sandbox/p2-service.mjs'))),dir=mkdtempSync(join(tmpdir(),'cfp-compat-'));let old,current,rolled;
 try{
 const password=randomBytes(24).toString('hex');old=new Baseline(join(dir,'baseline.db'));old.provision({id:'synthetic-owner',password,role:'editor',workspace:'synthetic-space',maintainer:true});let token=old.login('synthetic-owner',password);await old.execute(token,'snapshot');const checkpoint=old.verify();const snapshot=join(dir,'baseline-copy.db');old.backup(token,snapshot);
 current=P2Sandbox.restore(snapshot,join(dir,'current.db'));assert.equal(current.verify().sequence,checkpoint.sequence+1);assert.throws(()=>current.context(token),/AUTH_DENIED/);token=current.login('synthetic-owner',password);
 const p=await current.execute(token,'officeCreate',{pairKey:'hub69-content-demo',kind:'application',input:{name:'Synthetic compatibility declaration',entityType:'existing-ai',contact:'https://example.org',relationships:[],synthetic:true,commitment:true}});assert.equal(p.id,null);assert.equal(p.status,'EVIDENCE_PENDING');
 const source=new URL('..',import.meta.url).pathname,a=join(dir,'release-a'),b=join(dir,'release-b'),da=packRelease(source,a);
 assert(verifyRelease(a,da).files.some(f=>f.path==='scripts/guarded-preview.mjs'));
 const candidate=join(dir,'candidate-source');packRelease(source,candidate);const launcher=join(candidate,'scripts/guarded-preview.mjs');writeFileSync(launcher,readFileSync(launcher,'utf8')+'\n// Synthetic changed-launcher rollback fixture\n');const db=packRelease(candidate,b);assert.notEqual(da,db);
 const c=new SandboxReleaseControl(join(dir,'control'));await c.activate({service:current,token,release:a,digest:da});await c.activate({service:current,token,release:b,digest:db});const prior=current.verify();const rollback=await c.rollback({service:current,token});assert.equal(c.current().digest,da);assert(existsSync(rollback.retainedCurrentDatabase));assert.deepEqual(current.verify(),prior);
 rolled=new P2Sandbox(rollback.restoredDatabase);const fresh=rolled.login('synthetic-owner',password);assert.equal((await rolled.execute(fresh,'officeSnapshot',{pairKey:'hub69-content-demo'})).registrations[0].key,p.key);
 return {baselineRevision:'b75b780eb64430355f0b51a4b58b9e5269e0db43',scope:'baseline SQLite -> latest restore/intake; changed launcher packaging/pointer rollback, not provider deploy',schemaCompatibility:true,newGenerationAndSessionRevocation:true,intakePreserved:true,launcherIncludedInRelease:true,differentLauncherRollback:true,originalDBRetained:true,providerRollbackExecuted:false};
 }finally{rolled?.close();current?.close();old?.close();rmSync(dir,{recursive:true,force:true});}
}
if(process.argv[1]?.endsWith('/rehearse-preview-compat.mjs'))console.log(JSON.stringify(await rehearseCompatibility(process.argv[2]),null,2));
