import {clone,hash,key,text} from './common.mjs';
export const MATCHER_VERSION='DETERMINISTIC SYNTHETIC NAME-TOKEN MATCH v1; NO LIVE AI';
const normalized=value=>value.normalize('NFKC').trim().replace(/\s+/g,' ').toLocaleLowerCase('en');
function validate(input,fields){
 if(!input||typeof input!=='object'||Array.isArray(input)||input.synthetic!==true||Object.keys(input).some(k=>!['synthetic',...fields].includes(k)))throw Error('SYNTHETIC_COMMERCE_FIELDS_REQUIRED');
}
function query(value){if(!text(value,300))throw Error('COMMERCE_QUERY_INVALID');return value.trim();}
function withoutAudit(row){const value=clone(row);delete value.auditLink;return value;}
export function catalog(state){
 return [...state.registrations.map(r=>({...clone(r),kind:'profile'})),...state.hstdn.map(r=>({...clone(r),kind:'hstdn'})),...state.records.filter(r=>['product','service'].includes(r.kind)).map(clone)].map(r=>({...r,verification:'NOT VERIFIED',synthetic:true}));
}
export function searchCatalog(state,input){
 validate(input,['query','kind']);const q=normalized(query(input.query));
 if(!['all','profile','hstdn','product','service'].includes(input.kind))throw Error('CATALOG_KIND_INVALID');
 const results=catalog(state).filter(r=>(input.kind==='all'||r.kind===input.kind)&&normalized(r.name).includes(q));
 return {results,total:results.length,synthetic:true};
}
export function createInquiry(state,actor,input){
 validate(input,['intent','query','officeRef']);
 if(!['buy','sell','partner','invest'].includes(input.intent)||!state.registrations.some(r=>r.key===input.officeRef&&r.subject===actor.id))throw Error('INQUIRY_REFERENCE_INVALID');
 const q=query(input.query),rows=state.commercial?.inquiries||[];
 if(rows.some(r=>r.subject===actor.id&&r.intent===input.intent&&normalized(r.query)===normalized(q)&&r.officeRef===input.officeRef))throw Error('INQUIRY_DUPLICATE');
 const row={key:key(),subject:actor.id,intent:input.intent,query:q,officeRef:input.officeRef,status:'DRAFT',synthetic:true,externalCalls:0,payment:false,affiliationVerified:false};
 state.commercial??={inquiries:[],opportunities:[]};state.commercial.inquiries.push(row);return row;
}
function inquiry(state,actor,id){const row=state.commercial?.inquiries.find(r=>r.key===id&&r.subject===actor.id);if(!row)throw Error('INQUIRY_NOT_FOUND');return row;}
export function matchInquiry(state,actor,input){
 validate(input,['inquiryKey']);const row=inquiry(state,actor,input.inquiryKey),terms=[...new Set(normalized(row.query).split(' '))];
 const types=['buy','sell'].includes(row.intent)?['product','service']:['profile','hstdn'];
 const pool=catalog(state).filter(r=>types.includes(r.kind)&&r.key!==row.officeRef).sort((a,b)=>a.key.localeCompare(b.key));
 const matches=pool.map(r=>{
  const name=normalized(r.name),matched=terms.filter(t=>name.includes(t)),score=Math.round(100*matched.length/terms.length);
  return {key:r.key,kind:r.kind,name:r.name,score,reasons:[`Intent ${row.intent} permits ${r.kind}`,`Name matched ${matched.length}/${terms.length} query terms: ${matched.join(', ')||'none'}`],synthetic:true,verification:'NOT VERIFIED',provenance:{matcherVersion:MATCHER_VERSION,inquirySha256:hash(withoutAudit(row)),querySha256:hash({intent:row.intent,query:normalized(row.query)}),catalogSha256:hash(pool),catalogRecords:pool.map(r=>({key:r.key,sha256:hash(r)})),targetSha256:hash(r),targetSnapshot:clone(r),terms,matchedTerms:matched}};
 }).filter(r=>r.score>0).sort((a,b)=>b.score-a.score||a.key.localeCompare(b.key));
 return {inquiryKey:row.key,matches,total:matches.length,model:MATCHER_VERSION,synthetic:true};
}
export function createOpportunity(state,actor,input){
 validate(input,['inquiryKey','targetKey']);const match=matchInquiry(state,actor,{inquiryKey:input.inquiryKey,synthetic:true}).matches.find(r=>r.key===input.targetKey);
 if(!match)throw Error('OPPORTUNITY_MATCH_REQUIRED');
 if(state.commercial.opportunities.some(r=>r.subject===actor.id&&r.inquiryKey===input.inquiryKey&&r.targetKey===input.targetKey))throw Error('OPPORTUNITY_DUPLICATE');
 const row={key:key(),subject:actor.id,inquiryKey:input.inquiryKey,targetKey:match.key,targetKind:match.kind,score:match.score,reasons:clone(match.reasons),matchProvenance:clone(match.provenance),status:'DRAFT',synthetic:true,externalCalls:0,payment:false,affiliationVerified:false};
 state.commercial.opportunities.push(row);return row;
}
export function updateOpportunity(state,actor,input){
 validate(input,['opportunityKey','status']);const row=state.commercial?.opportunities.find(r=>r.key===input.opportunityKey&&r.subject===actor.id);
 if(!row)throw Error('OPPORTUNITY_NOT_FOUND');
 if(!['UNDER REVIEW','CLOSED'].includes(input.status)||row.status==='CLOSED'||row.status===input.status)throw Error('OPPORTUNITY_TRANSITION_INVALID');
 row.status=input.status;return row;
}
export function commercialState(state,actor){return clone({inquiries:(state.commercial?.inquiries||[]).filter(r=>r.subject===actor.id),opportunities:(state.commercial?.opportunities||[]).filter(r=>r.subject===actor.id),synthetic:true,model:MATCHER_VERSION});}
