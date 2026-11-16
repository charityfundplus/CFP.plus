// CFP+ • Siêu Bộ Đôi initializer: sample first, then batch, from the pinned Registry.
// Usage: node scripts/superpair-init.mjs --sample <ID> [--out DIR]
//        node scripts/superpair-init.mjs --batch [--out DIR]
// Writes evidence JSON only to --out (default: a new OS temp dir). Never edits
// configs/pairs.json, never issues IDs, never calls live SI adapters.
import {mkdtempSync,mkdirSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {CoreEngine} from '../core/core-engine.mjs';
import {batchBuild,buildPairConfig,classifyRecord,ACTIVATION} from '../core/superpair-factory.mjs';

const SCENARIOS=[['registry-audit','normal','AWAITING HUMAN REVIEW'],['registry-audit','overreach','BLOCKED'],['training-drill','normal','AWAITING HUMAN REVIEW'],['training-drill','overreach','BLOCKED']];

export async function practice(pairs){
 const core=new CoreEngine({configs:pairs.map(p=>p.config)});
 const operator={id:'sandbox-operator',role:'editor'},reviewer={id:'independent-reviewer',role:'reviewer'};
 const results=[];
 for(const [i,p] of pairs.entries()){
  if(i>0)core.instantiate(operator,p.config.key);
  const runs=[];
  for(const [kind,scenario,expected] of SCENARIOS){
   const t=core.createTask(operator,p.config.key,{kind,title:`${p.registryRef.id} • ${kind}`,text:'Synthetic practice; no real data.',scenario});
   const r=await core.runTask(operator,t.key);
   let review=null;if(r.status==='AWAITING HUMAN REVIEW')review=core.reviewTask(reviewer,t.key,'acknowledge-draft').status;
   if(core.snapshot(operator).pairs.find(x=>x.key===p.config.key).status!=='READY')core.recover(reviewer,p.config.key);
   runs.push({kind,scenario,expected,actual:r.status,review,pass:r.status===expected});
  }
  results.push({pair:p.config.key,registryRef:p.registryRef,runs,pass:runs.every(x=>x.pass)});
 }
 const snap=core.snapshot(operator);
 return {results,auditValid:snap.auditValid,auditEvents:snap.audit.length,pairStatus:snap.pairs.map(x=>({key:x.key,status:x.status}))};
}

export async function run(argv){
 const a=new Map();for(let i=0;i<argv.length;i++){if(argv[i].startsWith('--'))a.set(argv[i],argv[i+1]&&!argv[i+1].startsWith('--')?argv[++i]:true);}
 const out=resolve(a.get('--out')||mkdtempSync(join(tmpdir(),'cfp-superpair-')));mkdirSync(out,{recursive:true});
 let mode,built,held;
 if(a.has('--sample')){
  mode='sample';const id=String(a.get('--sample'));const c=classifyRecord(id);
  if(c.eligibility!=='SANDBOX_PRACTICE'){built=[];held=[{id,eligibility:c.eligibility,reason:c.reason}];}
  else{built=[buildPairConfig(id)];held=[];}
 }else if(a.has('--batch')){mode='batch';({built,held}=batchBuild());}
 else throw Error('USAGE: --sample <ID> | --batch [--out DIR]');
 const practiced=built.length?await practice(built):{results:[],auditValid:null,auditEvents:0,pairStatus:[]};
 const evidence={tool:'cfp-superpair-init',mode,time:new Date().toISOString(),node:process.version,platform:process.platform,
  snapshot:built[0]?.registryRef.snapshot??null,built:built.length,held,practice:practiced,
  pass:built.length>0&&practiced.auditValid===true&&practiced.results.every(r=>r.pass),
  governance:{activation:ACTIVATION,idsIssued:0,identityBound:false,liveAdapters:false,configsPairsJsonModified:false}};
 const body=JSON.stringify(evidence,null,2);
 const file=join(out,`superpair-${mode}-evidence.json`);writeFileSync(file,body);
 writeFileSync(file+'.sha256',createHash('sha256').update(body).digest('hex')+'  '+`superpair-${mode}-evidence.json\n`);
 return {file,evidence};
}

if(process.argv[1]?.endsWith('superpair-init.mjs')){
 const {file,evidence}=await run(process.argv.slice(2));
 console.log(JSON.stringify({file,mode:evidence.mode,built:evidence.built,held:evidence.held.length,pass:evidence.pass,auditValid:evidence.practice.auditValid},null,2));
 process.exitCode=evidence.pass?0:1;
}
