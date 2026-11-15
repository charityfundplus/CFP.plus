// READ-ONLY report generator. No provisioning, checkout, payment, DNS or APIs.
import {readFileSync} from 'node:fs';import {fileURLToPath} from 'node:url';
export function providerPreflight(profile,evidence=null){
 const missing=[];
 const integer=n=>Number.isInteger(n)&&n>=0;
 if(!evidence?.quoteReference||!evidence?.taxLocation)missing.push('account-specific quote and tax location');
 const amounts=['taxCents','paymentFxFeesCents','pendingOrMeteredCents'];
 if(amounts.some(k=>!integer(evidence?.[k])))missing.push('tax, payment/FX fees and pending/metered exposure (unknown is not zero)');
 if(!integer(evidence?.quotedBaseCents)||evidence.quotedBaseCents!==profile.listBaseCents)missing.push('quoted base configuration matches profile');
 const projected=missing.length?null:evidence.quotedBaseCents+amounts.reduce((n,k)=>n+evidence[k],0);
 if(projected!==null&&projected>1500)missing.push('gross monthly total <=1500 cents');
 if(evidence?.backupDestinationVerified!==true)missing.push('private backup destination, ACL, custody and restore');
 if(evidence?.outerCloseVerified!==true)missing.push('HTTPS outer close and external observer');
 if(evidence?.globalEgressVerified!==true)missing.push('global host/Spaces coverage and quota');
 if(evidence?.residualCostVerified!==true)missing.push('residual charges and total-budget control');
 if(evidence?.hostRehearsalAuthority!==true)missing.push('separate host/environment rehearsal authority');
 return {provider:profile.provider,listBaseCents:profile.listBaseCents,projectedGrossCents:projected,missing,
  evidenceProvenance:'CALLER-PROVIDED CHECKLIST; AUTHORITY/QUOTE MUST BE VERIFIED BY HUMAN GOVERNANCE',
  readyForHumanReview:missing.length===0,activationAllowed:false,checkoutPerformed:false,providerCalls:0};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const config=JSON.parse(readFileSync(new URL('../configs/provider-preparation.json',import.meta.url)));
 console.log(JSON.stringify({status:config.status,profiles:config.profiles.map(p=>providerPreflight(p))},null,2));
}
