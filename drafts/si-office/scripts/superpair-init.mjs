// CFP+ • Siêu Bộ Đôi initializer: sample first, then batch, from the pinned Registry.
// Usage: node scripts/superpair-init.mjs --sample <ID> [--out DIR]
//        node scripts/superpair-init.mjs --batch [--ids ID,ID,...] [--out DIR]
//        node scripts/superpair-init.mjs --list
//        node scripts/superpair-init.mjs --help
// Writes evidence JSON only to --out (default: a new OS temp dir). Never edits
// configs/pairs.json, never issues IDs, never calls live SI adapters.
import {mkdtempSync,mkdirSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {CoreEngine} from '../core/core-engine.mjs';
import {batchBuild,buildPairConfig,classifyRecord,chapterOf,ACTIVATION} from '../core/superpair-factory.mjs';
import {registry} from '../model.mjs';

export const HELP=`CFP+ • Siêu Bộ Đôi init (sandbox; no ID issued, no live SI)
  --sample <ID>          practice one registry record (start here, e.g. 69103)
  --batch [--ids a,b]    practice every eligible record (or only the listed IDs)
  --list                 print eligibility for every record in the pinned snapshot
  --out <DIR>            evidence directory (default: new OS temp dir)`;

export function listEligibility(){
 return registry.entities.map(e=>{const c=classifyRecord(e.id);return {id:e.id,type:e.type,name:e.name,...chapterOf(e.id),eligibility:c.eligibility,reason:c.reason};});
}

// One-page ID profile (AI_INDEX standard): ID • Identity • Type • Country • Parent •
// Permanent Link • Main content • Official Source/Evidence • Review Status •
// Work Order/Return • Parent/child/HUB 69 links, then the type module.
export function profileOf(pair,practiceResult){
 const r=pair.registryRef;
 return {id:r.id,identity:{registryName:r.name,pairIdentity:pair.config.identity.name,verification:pair.config.identity.verification,identityBound:false},
  type:r.type,country:pair.config.assignment.country,parent:r.parentId,chapter:r.chapter,group:r.group,
  permanentLink:{...r.links},mainContent:{office12:r.office.modules,training:r.training,forum:r.forum,missions:pair.config.missions},
  officialSourceEvidence:{status:'MISSING EVIDENCE',sources:pair.config.sources,note:'Template links are references, not evidence'},
  reviewStatus:r.recordStatus,workOrderReturn:practiceResult?{pass:practiceResult.pass,runs:practiceResult.runs.map(x=>`${x.kind}/${x.scenario}: ${x.actual}${x.review?' → '+x.review:''}`)}:null,
  hub69:r.hub69,activation:r.activation,snapshot:r.snapshot};
}

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
 if(a.has('--help'))return {help:HELP};
 if(a.has('--list'))return {list:listEligibility()};
 const out=resolve(a.get('--out')||mkdtempSync(join(tmpdir(),'cfp-superpair-')));mkdirSync(out,{recursive:true});
 let mode,built,held;
 if(a.has('--sample')){
  mode='sample';const id=String(a.get('--sample'));const c=classifyRecord(id);
  if(c.eligibility!=='SANDBOX_PRACTICE'){built=[];held=[{id,eligibility:c.eligibility,reason:c.reason}];}
  else{built=[buildPairConfig(id)];held=[];}
 }else if(a.has('--batch')){mode='batch';const ids=typeof a.get('--ids')==='string'?a.get('--ids').split(',').map(s=>s.trim()).filter(Boolean):undefined;({built,held}=batchBuild(ids));}
 else throw Error('USAGE: --sample <ID> | --batch [--out DIR]');
 const practiced=built.length?await practice(built):{results:[],auditValid:null,auditEvents:0,pairStatus:[]};
 const evidence={tool:'cfp-superpair-init',mode,time:new Date().toISOString(),node:process.version,platform:process.platform,
  snapshot:built[0]?.registryRef.snapshot??null,built:built.length,held,practice:practiced,
  pass:built.length>0&&practiced.auditValid===true&&practiced.results.every(r=>r.pass),
  governance:{activation:ACTIVATION,idsIssued:0,identityBound:false,liveAdapters:false,configsPairsJsonModified:false}};
 const body=JSON.stringify(evidence,null,2);
 const file=join(out,`superpair-${mode}-evidence.json`);writeFileSync(file,body);
 const profiles=join(out,'profiles');mkdirSync(profiles,{recursive:true});
 for(const p of built){const res=practiced.results.find(x=>x.pair===p.config.key);writeFileSync(join(profiles,`${p.registryRef.id}.profile.json`),JSON.stringify(profileOf(p,res),null,2));}
 writeFileSync(file+'.sha256',createHash('sha256').update(body).digest('hex')+'  '+`superpair-${mode}-evidence.json\n`);
 return {file,evidence};
}

if(process.argv[1]?.endsWith('superpair-init.mjs')){
 const res=await run(process.argv.slice(2));
 if(res.help){console.log(res.help);process.exit(0);}
 if(res.list){console.table(res.list.map(({id,name,chapter,group,eligibility})=>({id,name,chapter,group,eligibility})));process.exit(0);}
 const {file,evidence}=res;
 console.log(JSON.stringify({file,mode:evidence.mode,built:evidence.built,held:evidence.held.length,pass:evidence.pass,auditValid:evidence.practice.auditValid},null,2));
 process.exitCode=evidence.pass?0:1;
}
