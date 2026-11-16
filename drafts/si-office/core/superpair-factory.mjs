// CFP+ • Siêu Bộ Đôi batch factory from the pinned Registry snapshot.
// Read-only: never issues, changes or binds a Canonical ID. Each pair keeps a
// SYNTHETIC identity (enforced by inspectIdentity); the registry record is only
// referenced in a sidecar so Human Governance can decide activation later.
import {registry,modules as OFFICE_MODULES} from '../model.mjs';
import {inspectRegistryRecord} from './identity-registry.mjs';
import {validateConfig} from './core-engine.mjs';
import {clone} from './common.mjs';

export const ACTIVATION='HOLD ACTIVATION • PRODUCTION NO GO';

// registry/HUB69_5_GROUPS_10_CHAPTERS_3_STORES_V1.md: chapter n covers IDs n0–n9;
// numeric groups 000 / 135 / 246 / 789. V and D are internal namespaces, not groups.
const GROUP_BY_CHAPTER=['000','135','246','135','246','135','246','789','789','789'];
export function chapterOf(id){if(typeof id!=='string'||!/^\d+$/.test(id))throw Error('NUMERIC_ID_STRING_REQUIRED');const chapter=Number(id[0]);return {chapter,group:GROUP_BY_CHAPTER[chapter]};}

// Link Mẫu: canonical + 3 stores (HUB69 3-store standard) + workspace (ID Link Template Rollout V1).
// References only — having a link never means verified, authorized or ACTIVE.
export function linkTemplate(id,parentId){
 chapterOf(id);
 const suffix=parentId&&id.startsWith(parentId)?id.slice(parentId.length):null;
 return {
  canonical:`https://cfp.plus/${id}`,github:`https://gh.cfp.plus/${id}`,google:`https://gg.cfp.plus/${id}`,notion:`https://nt.cfp.plus/${id}`,workspace:`https://cg.cfp.plus/${id}`,
  parent:parentId?`https://cfp.plus/${parentId}`:null,hub69:'https://cfp.plus/69',
  // Child digit 1–9 under its parent; leading 0 digits are the namespace-extension branch.
  childDigitConforms:suffix!==null&&/^0*[1-9]$/.test(suffix),
  verified:false
 };
}

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
  // Chapter/group derived from the ID by the documented 10-chapter rule (not inferred identity).
  assignment:{...chapterOf(r.id),field:`Registry practice • ${r.type} • ${r.name}`.slice(0,500),country:r.country||'Unassigned',hstdn:'Research reference only'},
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
  ...chapterOf(r.id),links:linkTemplate(r.id,r.parent_id??r.ai_country_id),
  office:{modules:clone(OFFICE_MODULES),count:OFFICE_MODULES.length},
  training:'configs/training-basic-v1.json',
  forum:{foundation:'P2 HTTP loopback intake (tests/forum-foundation-loopback, forum-independent-qa)',service:'services/forum (Python/PostgreSQL) • origin/claude/forum-schema-location-guard • not bundled',status:'SANDBOX FOUNDATION ONLY'},
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
