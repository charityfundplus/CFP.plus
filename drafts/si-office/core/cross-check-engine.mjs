import {checkTool} from './security-permission.mjs';
import {hash} from './common.mjs';
// Four axes / eight checks, repeated before and after draft staging.
// Deterministic checkers are independent of SI adapter, not eight human/AI reviewers.
export function crossCheck(config,task,proposal,source,round){
 const o=proposal.output;
 const rules=[['technical','bounded-output',()=>typeof o.text==='string'&&o.text.length<=3000],['technical','task-binding',()=>o.title===task.title],['security','tool-allowlist',()=>{checkTool(config,{tool:'source.read',resource:task.resource});if(task.kind!=='registry-audit')checkTool(config,{tool:'draft.write',resource:task.resource});proposal.tools.forEach(t=>checkTool(config,t));return true;}],['security','synthetic-only',()=>o.synthetic===true&&proposal.externalRequests===0],['evidence','source-binding',()=>o.source.resource===task.resource&&o.source.sha256===source.sha256],['evidence','source-integrity',()=>{const {resource,sha256,...r}=source;return hash(r)===sha256;}],['governance','immutable-identity',()=>[o.id,o.parent,o.did,o.canonical].every(x=>x===null)],['governance','no-self-verification',()=>[o.sourceVerified,o.capabilityVerified,o.legalRelationshipVerified].every(x=>x===false)]];
 return rules.map(([axis,name,run])=>{try{return {axis,name,round,pass:run()===true};}catch{return {axis,name,round,pass:false};}});
}
