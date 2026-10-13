import {clone,hash,freeze} from './common.mjs';
const records=freeze({
 'website-demo':{name:'HUB 69 content fixture',sourceUrl:'https://cfp.plus/69',text:'Synthetic draft workspace: sole HUB 69; groups V / 000 / 135 / 246 / 789; chapters 0–9. Legacy group label 0 vs 000 requires Human Governance; do not change IDs.',synthetic:true,verifiedSource:false},
 'training-demo':{name:'Training fixture',sourceUrl:'https://github.com/charityfundplus/CFP.plus/issues/126',text:'Observe → supervised practice → authorized operation only after separate human approval. Exercise scores do not grant authority.',synthetic:true,verifiedSource:false},
 'hst-us-demo':{name:'Synthetic US HSTDN fixture',sourceUrl:'https://github.com/charityfundplus/CFP.plus/issues/127',text:'Synthetic Research Company; US research-reference only. No partner, legal-parent or quantum capability claim verified.',synthetic:true,verifiedSource:false}
});
export class KnowledgeEvidence {
 #events=[];
 read(resource){const r=records[resource];if(!r)throw Error('SOURCE_NOT_FOUND');return {...clone(r),resource,sha256:hash(r)};}
 append(actor,action,result,details={}){const e={sequence:this.#events.length+1,time:new Date().toISOString(),actor:{id:actor.id,role:actor.role},action,result,details:clone(details),previousHash:this.#events.at(-1)?.sha256||'GENESIS'};e.sha256=hash(e);this.#events.push(freeze(e));return clone(e);}
 restore(events){this.#events=clone(events);if(!this.verify())throw Error("AUDIT_INTEGRITY_FAILURE");}
 events(){return clone(this.#events);}
 verify(){let previous='GENESIS';for(const {sha256,...e} of this.#events){if(e.previousHash!==previous||hash(e)!==sha256)return false;previous=sha256;}return true;}
 inventory(){return Object.keys(records).map(k=>this.read(k));}
}
