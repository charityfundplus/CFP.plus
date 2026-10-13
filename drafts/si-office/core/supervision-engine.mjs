import {requireKeys,text} from './common.mjs';
export function inspectInput(task,config){if(task.text.length>3000||!config.permissions.resources.includes(task.resource))throw Error('INPUT_SCOPE_DENIED');return {stage:'input',result:'PASS',scope:'synthetic; bounded task'};}
export function inspectProposal(proposal,config){
 requireKeys(proposal,['adapter','protocol','externalRequests','tools','output']);if(proposal.adapter!==config.si.provider||proposal.protocol!==1||proposal.externalRequests!==0||!Array.isArray(proposal.tools)||proposal.tools.length>3)throw Error('PROPOSAL_INVALID');
 const o=proposal.output;requireKeys(o,['title','text','source','synthetic','id','parent','did','canonical','sourceVerified','capabilityVerified','legalRelationshipVerified','mode']);
 if(!text(o.title,200)||!text(o.text,3000)||o.synthetic!==true||o.mode!=='DRAFT ONLY'||[o.id,o.parent,o.did,o.canonical].some(x=>x!==null)||[o.sourceVerified,o.capabilityVerified,o.legalRelationshipVerified].some(x=>x!==false))throw Error('OUTPUT_CLAIM_OR_IDENTITY_DENIED');
 requireKeys(o.source,['resource','sha256']);return {stage:'proposal',result:'PASS'};
}
