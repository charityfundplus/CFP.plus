import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,writeFileSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
import {requestHandlerFetch} from './harness.mjs';
import {registry} from '../model.mjs';
import {hash} from '../core/common.mjs';
const output=process.argv[2];if(!output)throw Error('CREATE_ONLY_OUTPUT_REQUIRED');
const directory=mkdtempSync(join(tmpdir(),'cfp-commercial-evidence-')),service=new P2Sandbox(join(directory,'state.db'));
const pairKey='hub69-content-demo',origin='http://localhost:4174',password='Synthetic-commercial-evidence-2026',checks=[],trace=[];
const check=(name,value)=>{assert(value,name);checks.push({name,expected:true,observed:true});};
try{
 for(const [id,role,workspace,pairs] of [['commerce-owner','editor','commercial-fixture',[pairKey]],['commerce-peer','editor','commercial-fixture',[pairKey]],['commerce-viewer','viewer','commercial-fixture',[pairKey]],['commerce-foreign','editor','foreign-fixture',[pairKey]],['commerce-narrow','editor','commercial-fixture',['training-demo']]])service.provision({id,role,workspace,pairs,password});
 const fetch=requestHandlerFetch(createP2HTTP({service})),cookies={};
 async function request(route,body,id){const r=await fetch(origin+route,{method:body===undefined?'GET':'POST',headers:{Origin:origin,'Content-Type':'application/json',...(id?{Cookie:cookies[id]}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});const data=await r.json();if(route==='/api/session'&&r.status===200)cookies[body.id]=r.headers.get('set-cookie').split(';')[0];trace.push({route,actor:id||body?.id||'unauthenticated',status:r.status,error:data.error||null});return {status:r.status,data};}
 for(const id of ['commerce-owner','commerce-peer','commerce-viewer','commerce-foreign','commerce-narrow']){const r=await request('/api/session',{id,password});check('login '+id,r.status===200);}
 async function call(command,input,id='commerce-owner',idempotencyKey){const r=await request('/api/core/'+command,{pairKey,...(input?{input}:{}),...(idempotencyKey?{idempotencyKey}:{})},id);assert.equal(r.status,200,JSON.stringify(r.data));return r.data;}
 const initial=(await request('/api/core/state',undefined,'commerce-owner')).data;check('actual runtime source pinned',initial.buildProvenance.verified===true);
 const d=registry.entities.find(r=>r.type==='developer'&&!registry.blockedCountries.includes(r.ai_country_id));
 async function office(kind,input){const r=await request('/api/core/office-create',{pairKey,kind,input:{...input,synthetic:true}},'commerce-owner');assert.equal(r.status,200,JSON.stringify(r.data));return r.data;}
 const profile=await office('profile',{name:'Synthetic solar enterprise',country:d.ai_country_id,developer:d.id,source:'https://example.org/synthetic/enterprise',identityEvidence:'https://example.org/synthetic/enterprise'});
 check('new requester is own unbound synthetic profile',profile.subject==='commerce-owner'&&['id','parent','did','canonical'].every(k=>profile[k]===null));
 const hstdn=await office('hstdn',{name:'Synthetic solar consortium',jurisdiction:'Synthetic only',members:[profile.key],relation_type:'proposed-collaboration',source:'https://example.org/synthetic/consortium'});
 const product=await office('product',{name:'Synthetic solar kit',officeRef:profile.key,hstdnRef:hstdn.key,source:'https://example.org/synthetic/product',scope:'Synthetic catalogue only',maturity:'prototype'});
 const serviceRecord=await office('service',{name:'Synthetic solar training',officeRef:profile.key,hstdnRef:hstdn.key,source:'https://example.org/synthetic/service',scope:'Synthetic catalogue only',maturity:'concept'});
 const search=await call('catalog-search',{query:'solar',kind:'all',synthetic:true});check('enterprise/HSTDN/product/service search',search.total===4);
 check('zero search does not invent records',(await call('catalog-search',{query:'unlisted',kind:'all',synthetic:true})).total===0);
 const input={intent:'buy',query:'solar',officeRef:profile.key,synthetic:true};const inquiry=await call('inquiry-create',input,'commerce-owner','inquiry-new');
 check('request idempotency returns same receipt',(await call('inquiry-create',input,'commerce-owner','inquiry-new')).key===inquiry.key);
 const conflict=await request('/api/core/inquiry-create',{pairKey,input:{...input,query:'changed'},idempotencyKey:'inquiry-new'},'commerce-owner');check('conflicting idempotency denied',conflict.status===409);
 const duplicate=await request('/api/core/inquiry-create',{pairKey,input,idempotencyKey:'inquiry-semantic-duplicate'},'commerce-owner');check('semantic duplicate denied',duplicate.status===400&&/DUPLICATE/.test(duplicate.data.error));
 const matching=await call('inquiry-match',{inquiryKey:inquiry.key,synthetic:true});check('explainable deterministic matches',matching.total===2&&matching.matches.every(m=>m.score===100&&m.reasons.length===2)&&matching.model.includes('NO LIVE AI'));
 const chosen=matching.matches.find(m=>m.key===product.key);check('target and query hashes independently checked',chosen.provenance.targetSha256===hash(chosen.provenance.targetSnapshot)&&chosen.provenance.querySha256===hash({intent:'buy',query:'solar'}));
 const opportunity=await call('opportunity-create',{inquiryKey:inquiry.key,targetKey:product.key,synthetic:true},'commerce-owner','opportunity-new');check('opportunity retains matching provenance',JSON.stringify(opportunity.matchProvenance)===JSON.stringify(chosen.provenance));
 check('opportunity idempotency',(await call('opportunity-create',{inquiryKey:inquiry.key,targetKey:product.key,synthetic:true},'commerce-owner','opportunity-new')).key===opportunity.key);
 await call('opportunity-status',{opportunityKey:opportunity.key,status:'UNDER REVIEW',synthetic:true});const closed=await call('opportunity-status',{opportunityKey:opportunity.key,status:'CLOSED',synthetic:true});
 check('status roundtrip remains synthetic',closed.status==='CLOSED'&&closed.externalCalls===0&&closed.payment===false&&closed.affiliationVerified===false);
 for(const id of ['commerce-peer','commerce-foreign']){
  const own=await call('commerce-state',null,id);check('isolated records '+id,own.inquiries.length===0&&own.opportunities.length===0);
  const denied=await request('/api/core/inquiry-match',{pairKey,input:{inquiryKey:inquiry.key,synthetic:true}},id);check('foreign inquiry denied '+id,denied.status===400);
  const ref=await request('/api/core/inquiry-create',{pairKey,input,idempotencyKey:'foreign-requester'},id);check('foreign requester reference denied '+id,ref.status===400);
 }
 const viewer=await request('/api/core/inquiry-create',{pairKey,input,idempotencyKey:'viewer'},'commerce-viewer');check('viewer write denied',viewer.status===403);
 const narrow=await request('/api/core/catalog-search',{pairKey,input:{query:'solar',kind:'all',synthetic:true}},'commerce-narrow');check('ungranted pair denied',narrow.status===403);
 const unauth=await request('/api/core/commerce-state',{pairKey});check('unauthenticated state denied',unauth.status===401);
 for(const [label,extra] of [['real contact',{contact:'real@example.org'}],['payment',{payment:true}],['non-synthetic',{synthetic:false}],['invalid query',{query:42}]]){const denied=await request('/api/core/inquiry-create',{pairKey,input:{...input,...extra},idempotencyKey:label},'commerce-owner');check(label+' rejected',denied.status===400);}
 const zero=await call('inquiry-create',{...input,query:'unlisted'},'commerce-owner','zero-match');check('zero match',(await call('inquiry-match',{inquiryKey:zero.key,synthetic:true})).total===0);
 const badTarget=await request('/api/core/opportunity-create',{pairKey,input:{inquiryKey:zero.key,targetKey:product.key,synthetic:true},idempotencyKey:'no-match-opportunity'},'commerce-owner');check('unmatched opportunity denied',badTarget.status===400);
 const invalidStatus=await request('/api/core/opportunity-status',{pairKey,input:{opportunityKey:opportunity.key,status:'PAID',synthetic:true}},'commerce-owner');check('payment status denied',invalidStatus.status===400);
 const commercial=await call('commerce-state'),final=(await request('/api/core/state',undefined,'commerce-owner')).data;
 check('source stable through actual flow',final.buildProvenance.verified&&final.buildProvenance.manifestSha256===initial.buildProvenance.manifestSha256);
 for(const row of [...commercial.inquiries,...commercial.opportunities]){const record={...row};delete record.auditLink;const event=final.audit.find(e=>e.sequence===row.auditLink.sequence&&e.sha256===row.auditLink.sha256);check('record audit link '+row.key,event&&event.details.recordKey===row.key&&event.details.recordHash===hash(record)&&row.auditLink.recordHash===hash(record));}
 const peerState=(await request('/api/core/state',undefined,'commerce-peer')).data;check('peer audit excludes private commercial identifiers',peerState.audit.every(e=>!e.action.startsWith('inquiry-')&&!e.action.startsWith('opportunity-')));
 const raw=JSON.stringify({mode:'REAL HTTP HANDLER + SQLITE / NO SOCKET OR BROWSER',executionRevision:final.buildProvenance.revision,buildManifest:final.buildProvenance.manifest,buildManifestSha256:final.buildProvenance.manifestSha256,owner:'Codex local synthetic operator',seed:{profile,hstdn,product,service:serviceRecord},search,inquiry,matching,opportunity:closed,commercial,checks,trace,audit:final.audit,serviceAuditReadback:service.verify(),independentOpenSIAck:false,authorityVerified:false,actualIphoneSafari:false,publicHttps:false,activationAllowed:false,limits:['Unsigned local trace, not external execution/authority attestation.','Catalog targets are shared inside granted workspace; private commercial records are subject-scoped.','Deterministic synthetic matching, no live SI/AI call, no real contact/payment/contract.','Actual browser/mobile/Safari and approved HTTPS deployment remain BLOCKED.']},null,2)+'\n';
 writeFileSync(output,raw,{flag:'wx'});assert.equal(readFileSync(output,'utf8'),raw);console.log(JSON.stringify({checks:checks.length,executionRevision:final.buildProvenance.revision,manifestSha256:final.buildProvenance.manifestSha256,inquiryKey:inquiry.key,opportunityKey:opportunity.key,outputSha256:createHash('sha256').update(raw).digest('hex'),scope:'REAL HTTP HANDLER + SQLITE / NO SOCKET OR BROWSER'}));
}finally{service.close();rmSync(directory,{recursive:true,force:true});}
