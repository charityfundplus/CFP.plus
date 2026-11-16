// CFP+ • Siêu Bộ Đôi batch factory from the pinned Registry snapshot.
// Read-only: never issues, changes or binds a Canonical ID. Each pair keeps a
// SYNTHETIC identity (enforced by inspectIdentity); the registry record is only
// referenced in a sidecar so Human Governance can decide activation later.
import {registry,modules as OFFICE_MODULES} from '../model.mjs';
import {inspectRegistryRecord} from './identity-registry.mjs';
import {validateConfig} from './core-engine.mjs';
import {clone} from './common.mjs';

export const ACTIVATION='HOLD ACTIVATION • PRODUCTION NO GO';

export function classifyRecord(id){
 const inspection=inspectRegistryRecord(id);
 if(!inspection.recordFound)return {id,eligibility:'NOT_IN_SNAPSHOT',reason:'ID absent from pinned registry snapshot; no profile is created',inspection};
 if(!inspection.lineageConsistent||inspection.status!=='MISSING EVIDENCE')return {id,eligibility:'HELD',reason:inspection.status,inspection};
 return {id,eligibility:'SANDBOX_PRACTICE',reason:'Lineage consistent; evidence still missing, so practice only',inspection};
}

export function buildPairConfig(id){
 const c=classifyRecord(id);
 if(c.eligibility!=='SANDBOX_PRACTICE')throw Error(c.eligibility==='HELD'?'HELD_HUMAN_GOVERNANCE':'NOT_IN_REGISTRY_SNAPSHOT');
 const r=c.inspection.record;
 const config=validateConfig({
  key:`reg-${r.id}-practice`,
  name:`${r.id} • ${r.name} • Siêu Bộ Đôi • Sandbox Practice`,
  mode:'sandbox',
  identity:{name:`Siêu Trí Tuệ (SI🤖AI🤖) • Practice for registry ${r.id}`,developer:'Synthetic Developer • not a legal entity',country:'Synthetic / Unassigned',id:null,parent:null,did:null,canonical:null,verification:'SYNTHETIC ONLY',source:'local-synthetic-fixture'},
  si:{provider:'mock-local',protocol:1},
  software:{name:'CFP+ Standard Core',version:'0.1.0-sandbox'},
  // Group/chapter mirror the existing hub69-content-demo template; real assignment is a governance decision.
  assignment:{group:'V',chapter:0,field:`Registry practice • ${r.type} • ${r.name}`.slice(0,500),country:r.country||'Unassigned',hstdn:'Research reference only'},
  missions:['registry-audit','training-drill'],
  supervision:'4 axes / 8 deterministic checks / 2 rounds; human demo reviewer',
  permissions:{tools:['source.read','draft.write'],resources:['training-demo']},
  owner:'Human Governance • sandbox operator; unverified identity',
  sources:['https://cfp.plus/69',`https://cfp.plus/${r.id}`],
  testStatus:'TEST REQUIRED',
  operatingStatus:'SYNTHETIC SANDBOX ONLY'
 });
 const registryRef={
  id:r.id,type:r.type,name:r.name,parentId:r.parent_id??r.ai_country_id,aiCountryId:r.ai_country_id,
  snapshot:registry.sourceCommit,recordStatus:c.inspection.status,lineageConsistent:c.inspection.lineageConsistent,
  hub69:'https://cfp.plus/69',permanentLinkReference:`https://cfp.plus/${r.id}`,permanentLinkVerified:false,
  office:{modules:clone(OFFICE_MODULES),count:OFFICE_MODULES.length},
  training:'configs/training-basic-v1.json',
  forum:'NOT INTEGRATED • forum package lives on a separate branch',
  identityBound:false,activation:ACTIVATION
 };
 return {config,registryRef};
}

export function batchBuild(ids=registry.entities.map(e=>e.id)){
 const seen=new Set(),built=[],held=[];
 for(const id of ids){
  if(seen.has(id))continue;seen.add(id);
  const c=classifyRecord(id);
  if(c.eligibility==='SANDBOX_PRACTICE')built.push(buildPairConfig(id));
  else held.push({id,eligibility:c.eligibility,reason:c.reason});
 }
 return {snapshot:registry.sourceCommit,built,held,activation:ACTIVATION};
}
