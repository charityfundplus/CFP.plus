import {registry} from '../model.mjs';
import {requireKeys,text,clone} from './common.mjs';
export function inspectIdentity(identity){
 requireKeys(identity,['name','developer','country','id','parent','did','canonical','verification','source']);
 if(!text(identity.name)||!text(identity.developer)||!text(identity.country)||identity.verification!=='SYNTHETIC ONLY')throw Error('IDENTITY_EVIDENCE_REQUIRED');
 if(['id','parent','did','canonical'].some(k=>identity[k]!==null))throw Error('CANONICAL_ALLOCATION_FORBIDDEN');
 if(identity.source!=='local-synthetic-fixture')throw Error('IDENTITY_SOURCE_NOT_AUTHORIZED');
 return {...clone(identity),identityVerified:false,capabilityVerified:false,legalRelationshipVerified:false,scope:'Synthetic sandbox identity only'};
}

export function inspectRegistryRecord(id){
 if(typeof id!=='string'||!/^\d+$/.test(id))throw Error('NUMERIC_ID_STRING_REQUIRED');
 const record=registry.entities.find(e=>e.id===id);if(!record)return {id,status:'MISSING EVIDENCE',recordFound:false,identityVerified:false};
 const country=registry.countries.find(c=>c.id===record.ai_country_id),parent=record.type==='ai'?registry.entities.find(e=>e.id===record.parent_id&&e.type==='developer'):country;
 const consistent=!!country&&!!parent&&country.country_id===record.country_id&&(record.type!=='ai'||parent.ai_country_id===record.ai_country_id);
 return {record:clone(record),snapshot:registry.sourceCommit,recordFound:true,lineageConsistent:consistent,status:!consistent||registry.blockedCountries.includes(record.ai_country_id)?'CONFLICT / HUMAN GOVERNANCE':'MISSING EVIDENCE',identityVerified:false,sourceVerified:false,capabilityVerified:false,legalRelationshipVerified:false,reason:'Read-only inventory is not verified identity or allocation authority'};
}
