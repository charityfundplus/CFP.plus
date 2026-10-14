import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,rmSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash,randomBytes} from 'node:crypto';
import {CoreEngine} from '../core/core-engine.mjs';
import {registry} from '../model.mjs';
import {hash} from '../core/common.mjs';
const actor={id:'commercial-retention-owner',role:'editor'},other={id:'other-owner',role:'editor'},pairKey='hub69-content-demo';
function seed(engine){const d=registry.entities.find(r=>r.type==='developer'&&!registry.blockedCountries.includes(r.ai_country_id));return engine.officeCreate(actor,pairKey,'profile',{name:'Synthetic retained enterprise',country:d.ai_country_id,developer:d.id,source:'https://example.org/synthetic',identityEvidence:'https://example.org/synthetic',synthetic:true});}
test('commercial checkpoint refuses actual predecessor, detects retained audit-record loss and preserves old audit',async()=>{
 const e=new CoreEngine(),p=seed(e);assert.equal(p.subject,actor.id);
 const i=e.inquiryCreate(actor,pairKey,{intent:'partner',officeRef:p.key,query:'synthetic',synthetic:true});
 const checkpoint=e.checkpoint();assert.equal(checkpoint.schema,3);
 const original=readFileSync(new URL('./fixtures/core-engine-b381.txt',import.meta.url));
 assert.equal(createHash('sha256').update(original).digest('hex'),'98a2b2d040d532cb97e24ff2dd37972879870a9ef4258e9ac9f93837b42f0997');
 const path=fileURLToPath(new URL('../core/legacy-commerce-fixture-'+randomBytes(8).toString('hex')+'.mjs',import.meta.url));
 try{writeFileSync(path,original);const {CoreEngine:Legacy}=await import(pathToFileURL(path).href);assert.throws(()=>new Legacy({checkpoint}),/CHECKPOINT_INCOMPATIBLE/);}finally{rmSync(path,{force:true});}
 const restored=new CoreEngine({checkpoint});assert.deepEqual(restored.commerceState(actor,pairKey).inquiries,[i]);assert.deepEqual(restored.checkpoint().audit,checkpoint.audit);
 for(const damage of [c=>delete c.office[0][1].commercial,c=>c.office[0][1].commercial.inquiries=[],c=>c.office[0][1].commercial.inquiries[0].subject='foreign',c=>c.office[0][1].commercial.inquiries[0].auditLink.sha256='f'.repeat(64),c=>c.schema=2,c=>c.office.push(structuredClone(c.office[0]))]){
  const damaged=structuredClone(checkpoint);damage(damaged);assert.throws(()=>new CoreEngine({checkpoint:damaged}),/CHECKPOINT_COMMERCE/);
 }
 assert.equal(new CoreEngine({checkpoint:new CoreEngine().checkpoint()}).checkpoint().schema,1);
});
test('owned enterprise references and matching inputs are source bound, without retrospective owner assignment',()=>{
 const e=new CoreEngine(),p=seed(e);
 assert.throws(()=>e.inquiryCreate(other,pairKey,{intent:'buy',query:'solar',officeRef:p.key,synthetic:true}),/REFERENCE_INVALID/);
 assert.throws(()=>e.officeCreate(other,pairKey,'product',{name:'Synthetic wrong-owner product',source:'https://example.org/synthetic',officeRef:p.key,scope:'Synthetic',maturity:'prototype',synthetic:true}),/CATALOG_SCOPE/);
 const product=e.officeCreate(actor,pairKey,'product',{name:'Synthetic solar tool',source:'https://example.org/synthetic',officeRef:p.key,scope:'Synthetic',maturity:'prototype',synthetic:true});
 const i=e.inquiryCreate(actor,pairKey,{intent:'buy',query:'solar',officeRef:p.key,synthetic:true});
 const m=e.inquiryMatch(actor,pairKey,{inquiryKey:i.key,synthetic:true}).matches[0];assert.equal(m.score,100);assert.equal(m.provenance.targetSnapshot.key,product.key);assert.equal(m.provenance.targetSha256,hash(m.provenance.targetSnapshot));assert.equal(m.provenance.querySha256,hash({intent:'buy',query:'solar'}));
 const opportunity=e.opportunityCreate(actor,pairKey,{inquiryKey:i.key,targetKey:product.key,synthetic:true});assert.deepEqual(opportunity.matchProvenance,m.provenance);
 const legacy=new CoreEngine(),old=seed(legacy),c=legacy.checkpoint();delete c.office[0][1].registrations[0].subject;
 const preserved=new CoreEngine({checkpoint:c});assert.equal(preserved.officeSnapshot(actor,pairKey).registrations[0].subject,undefined);assert.throws(()=>preserved.inquiryCreate(actor,pairKey,{intent:'buy',query:'solar',officeRef:old.key,synthetic:true}),/REFERENCE_INVALID/);
});
test('software declaration remains unbound and unverified in the existing Office intake',()=>{
 const e=new CoreEngine();const row=e.officeCreate(actor,pairKey,'application',{name:'Synthetic software',entityType:'software',contact:'https://example.org/synthetic',relationships:[],commitment:true,synthetic:true});
 assert.equal(row.subject,actor.id);for(const k of ['id','parent','did','canonical'])assert.equal(row[k],null);assert.equal(row.capabilityVerification,'NOT VERIFIED');assert.equal(row.privilegeChange,false);
});
