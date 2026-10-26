import {clone,key,requireKeys,text} from './common.mjs';
import {registry,safeURL} from '../model.mjs';
const normalized=s=>s.normalize('NFKC').trim().replace(/\s+/g,' ').toLocaleLowerCase('en');
const fields=['name','entityType','version','aiType','contact','country','developer','developerWebsite','developerEvidence','hstAffiliated','hstLinked','relationships','products','capabilities','limits','conditions','cooperation','commitment','synthetic','amendmentOf'];
const pending={id:null,parent:null,did:null,canonical:null,status:'REVIEW_REQUIRED',sourceVerification:'NOT VERIFIED',capabilityVerification:'NOT VERIFIED',legalRelationshipVerification:'NOT VERIFIED',privilegeChange:false,certification:false};
export function createOfficeIntake(state,kind,input,actor,program){
 if(kind==='application'){
  requireKeys(input,fields);
  if(input.synthetic!==true||input.commitment!==true)throw Error('SYNTHETIC_AND_COMMITMENT_REQUIRED');
  for(const f of ['country','developer'])if(input[f]!==undefined&&typeof input[f]!=='string')throw Error('INVALID_DECLARATION:'+f);
  for(const f of ['developerWebsite','developerEvidence'])if(input[f]!==undefined&&(typeof input[f]!=='string'||input[f].length>300))throw Error('INVALID_DECLARATION:'+f);
  input={...input,country:input.country?.trim()||'UNRESOLVED',developer:input.developer?.trim()||'UNRESOLVED'};
  if(!['new-ai','existing-ai','software','developer','enterprise'].includes(input.entityType))throw Error('ENTITY_TYPE_REQUIRED');
  for(const f of ['name','country','developer'])if(!text(input[f],300))throw Error('DECLARATION_REQUIRED:'+f);
  if(!safeURL(input.contact)||['developerWebsite','developerEvidence'].some(f=>input[f]&&!safeURL(input[f])))throw Error('PUBLIC_HTTPS_EVIDENCE_REQUIRED');
  for(const f of ['version','aiType','hstAffiliated','hstLinked','products','capabilities','limits','conditions','cooperation'])if(input[f]!==undefined&&(typeof input[f]!=='string'||input[f].length>1500))throw Error('INVALID_DECLARATION:'+f);
  if(!Array.isArray(input.relationships)||input.relationships.length>12)throw Error('RELATIONSHIPS_REQUIRED');
  for(const r of input.relationships){requireKeys(r,['type','entity','evidence']);if(!['developer','parent','owner','affiliated-hstdn','linked-hstdn'].includes(r.type)||!text(r.entity,300)||!safeURL(r.evidence))throw Error('RELATIONSHIP_EVIDENCE_REQUIRED');}
  const fingerprint=normalized(input.entityType)+'|'+normalized(input.name)+'|'+normalized(input.developer);
  const previous=input.amendmentOf?state.registrations.find(r=>r.key===input.amendmentOf&&r.kind==='application'&&r.subject===actor.id):null;
  if(input.amendmentOf&&(!previous||state.registrations.some(r=>r.amendmentOf===previous.key)))throw Error('AMENDMENT_SCOPE_OR_STALE');
  const draftRoot=previous?.draftRoot||previous?.key;
  if(state.registrations.some(r=>(r.fingerprint===fingerprint||normalized(r.name)===normalized(input.name)&&normalized(r.developer)===normalized(input.developer))&&(!previous||(r.draftRoot||r.key)!==draftRoot)))throw Error('DUPLICATE_APPLICATION');
  const c=registry.countries.find(c=>c.id===input.country);
  const candidates=registry.entities.filter(d=>d.type==='developer'&&d.ai_country_id===input.country&&normalized(d.name||'')===normalized(input.developer));
  const row={...clone(input),...pending,kind,key:key(),subject:actor.id,fingerprint,createdAt:new Date().toISOString(),lookup:{countryBranch:c?.id||null,developerCandidates:candidates.map(d=>d.id),status:!c?'EVIDENCE_PENDING':registry.blockedCountries.includes(c.id)?'CONFLICT / HUMAN GOVERNANCE':'REVIEW_REQUIRED',officialDomainVerified:false},contactVerification:'PENDING',publisherAuthority:'PENDING',commitmentScope:'Provided and validly accepted CFP+ documents only',permissionStatus:'NO NEW GRANTS'};
  if(!input.developerEvidence||!input.developerWebsite||input.developer==='UNRESOLVED')row.status='EVIDENCE_PENDING';
  row.draftRoot=draftRoot||row.key;row.declarationVersion=(previous?.declarationVersion||0)+1;
  state.registrations.push(row);return row;
 }
 if(!['enrollment','marketing','work-request'].includes(kind))return null;
 requireKeys(input,['name','officeRef','source','scope','track','commitment','synthetic']);
 if(input.synthetic!==true||input.commitment!==true||!text(input.name,200)||!text(input.scope,1500)||!safeURL(input.source))throw Error('INTAKE_SCOPE_OR_CONSENT_REQUIRED');
 if(!state.registrations.some(p=>p.key===input.officeRef))throw Error('INTAKE_SCOPE_DENIED');
 if(kind==='enrollment'&&!program.advanced.some(t=>t.key===input.track))throw Error('TRAINING_TRACK_REQUIRED');
 if(kind!=='enrollment'&&input.track!==undefined)throw Error('INVALID_FIELDS');
 if(kind==='enrollment'&&state.records.some(r=>r.kind===kind&&r.subject===actor.id&&r.officeRef===input.officeRef&&r.track===input.track))throw Error('DUPLICATE_ENROLLMENT');
 const row={...clone(input),...pending,kind,key:key(),subject:actor.id,createdAt:new Date().toISOString(),assessment:'NOT ASSESSED',execution:'NOT AUTHORIZED',publication:'NOT PUBLISHED'};state.records.push(row);return row;
}
