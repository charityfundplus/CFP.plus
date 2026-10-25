import {test} from 'node:test';import assert from 'node:assert/strict';
import config from '../configs/provider-preparation.json' with {type:'json'};
import {providerPreflight} from '../scripts/provider-preflight.mjs';
test('NEW provider preflight leaves unknown checkout/fees null and never authorizes activation',()=>{for(const profile of config.profiles){const missing=providerPreflight(profile);assert.equal(missing.projectedGrossCents,null);assert(missing.missing.length>=7);assert.equal(missing.activationAllowed,false);assert.equal(missing.providerCalls,0);
 const fixture={quoteReference:'synthetic-fixture-not-checkout',taxLocation:'synthetic',quotedBaseCents:profile.listBaseCents,taxCents:122,paymentFxFeesCents:0,pendingOrMeteredCents:0,backupDestinationVerified:true,outerCloseVerified:true,globalEgressVerified:true,residualCostVerified:true,hostRehearsalAuthority:true};assert.equal(providerPreflight(profile,fixture).readyForHumanReview,true);assert.equal(providerPreflight(profile,fixture).activationAllowed,false);
 fixture.pendingOrMeteredCents=400;assert(providerPreflight(profile,fixture).missing.includes('gross monthly total <=1500 cents'));
 fixture.paymentFxFeesCents=null;assert.equal(providerPreflight(profile,fixture).projectedGrossCents,null);
 }});
