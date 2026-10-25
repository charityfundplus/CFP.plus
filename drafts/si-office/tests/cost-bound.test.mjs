import {test} from 'node:test';
import assert from 'node:assert/strict';
import {costBound} from '../scripts/cost-bound.mjs';

const ref = 'https://example.invalid/synthetic-evidence';
const fixture = () => ({currency:'USD',basis:'grossUSD',period:'synthetic-month',scope:'single synthetic preview',
  nonOverlapping:true,allocationEvidenceRef:ref,targetCents:1500,
  components:['F','U','D','R','S'].map((group,index)=>({group,cents:index===0?1220:0,evidenceRef:ref}))});

test('unknown closure/residual and omitted groups cannot become zero',()=>{
  const p=fixture();p.components[2].cents=null;p.components[3].cents=null;
  const r=costBound(p);assert.equal(r.boundCents,null);assert.equal(r.withinTargetArithmetic,null);
  assert.deepEqual(r.unknown,['D','R']);assert.equal(r.knownSubtotalCents,1220);
  p.components.pop();assert(costBound(p).unknown.includes('S'));
});
test('one gross USD scope and nonoverlapping allocation are required',()=>{
  for(const change of [{currency:'VND'},{basis:'netUSD'},{nonOverlapping:false},{period:''},{scope:''},{allocationEvidenceRef:null}])
    assert.throws(()=>costBound({...fixture(),...change}),/SCOPE/);
  const p=fixture();p.components.push({...p.components[0]});assert.throws(()=>costBound(p),/DUPLICATE/);
});
test('exact target is arithmetic only, never authority or hard cap',()=>{
  const p=fixture();p.components[0].cents=1500;const before=JSON.stringify(p);const r=costBound(p);
  assert.equal(r.boundCents,1500);assert.equal(r.headroomCents,0);assert.equal(r.withinTargetArithmetic,true);
  assert.equal(r.hardCapVerified,false);assert.equal(r.evidenceAuthenticated,false);assert.equal(r.activationAllowed,false);
  assert.equal(r.providerCalls,0);assert.equal(r.checkoutPerformed,false);assert.equal(JSON.stringify(p),before);
});
test('retained resources can push residual exposure above target',()=>{
  const p=fixture();p.components[3].cents=525;const r=costBound(p);
  assert.equal(r.boundCents,1745);assert.equal(r.withinTargetArithmetic,false);assert.equal(r.headroomCents,-245);
});
test('negative fractional unsafe and unreferenced amounts fail closed',()=>{
  for(const value of [-1,0.1,NaN,Infinity,Number.MAX_SAFE_INTEGER+1,'0',undefined]) {
    const p=fixture();p.components[0].cents=value;assert.throws(()=>costBound(p),/AMOUNT/);
  }
  for(const value of ['',null,'http://example.invalid','https://user:secret@example.invalid']) {
    const p=fixture();p.components[0].evidenceRef=value;assert.throws(()=>costBound(p),/REFERENCE/);
  }
  const p=fixture();p.components[0].cents=Number.MAX_SAFE_INTEGER;p.components[1].cents=1;
  assert.throws(()=>costBound(p),/UNSAFE/);
});
