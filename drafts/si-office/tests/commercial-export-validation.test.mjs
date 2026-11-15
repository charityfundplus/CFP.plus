import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash,webcrypto} from 'node:crypto';
import vm from 'node:vm';
const source=readFileSync(new URL('../public/p2-office.js',import.meta.url),'utf8');
const callback=source.slice(source.indexOf("$('#p2-export-evidence').onclick="));
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
async function run({tamper=false,changeScope=false,changeBuild=false}={}){
 const row={key:'synthetic-opportunity',subject:'learner',status:'DRAFT',reasons:['synthetic match'],score:50};
 const recordHash=hash(row);row.auditLink={sequence:1,sha256:'audit-event',recordHash};
 const initial={auth:{id:'learner',workspace:'alpha'},tasks:[],learning:{feedback:[],observations:[]},audit:[],auditValid:true,buildProvenance:{verified:false}};
 const final={...initial,audit:[{sequence:1,sha256:'audit-event',details:{pairKey:'pair',recordKey:row.key,recordHash}}]};
 if(changeBuild)final.buildProvenance={verified:true,revision:'changed'};
 const button={},status={};let downloaded=null,fetchCount=0,currentPair='pair';
 const context={state:initial,$:s=>s==='#p2-export-evidence'?button:status,pair:()=>currentPair,crypto:webcrypto,TextEncoder,setTimeout:()=>{},scopedAssessmentEvidence:()=>[],journeyEvidence:()=>({subject:'learner',pairKey:'pair'}),fetch:async()=>({ok:true,json:async()=>++fetchCount===1?initial:final}),api:async command=>{if(command==='office')return{registrations:[],hstdn:[],records:[]};if(changeScope)currentPair='foreign';if(tamper)row.score=99;return{inquiries:[],opportunities:[row]};},Blob:class{constructor(parts){this.parts=parts;}},URL:{createObjectURL:blob=>{downloaded=JSON.parse(blob.parts[0]);return'blob:synthetic';},revokeObjectURL:()=>{}},el:()=>({click(){}})};
 vm.runInNewContext(callback,context);await button.onclick();return{status:status.textContent,downloaded};
}
test('Commerce export includes final audit readback and unchanged training digest envelope',async()=>{const r=await run();assert(r.downloaded);const p=JSON.parse(r.downloaded.payloadJSON);assert.equal(p.commerce.opportunities.length,1);assert.equal(p.audit.length,1);assert.equal(p.commerce.approval,'NOT AUTHORIZED');assert.equal(createHash('sha256').update(r.downloaded.payloadJSON).digest('hex'),r.downloaded.sha256);});
test('Commerce export refuses tampered record bytes',async()=>{const r=await run({tamper:true});assert.equal(r.downloaded,null);assert.equal(r.status,'COMMERCE_AUDIT_READBACK_FAILED');});
test('Commerce export refuses changed selected pair',async()=>{const r=await run({changeScope:true});assert.equal(r.downloaded,null);assert.equal(r.status,'EXPORT_SCOPE_CHANGED');});
test('Commerce export refuses changed build claim',async()=>{const r=await run({changeBuild:true});assert.equal(r.downloaded,null);assert.equal(r.status,'EXPORT_BUILD_CHANGED');});
