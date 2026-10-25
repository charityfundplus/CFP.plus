import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';

const digest = text => createHash('sha1').update(`blob ${Buffer.byteLength(text)}\0`).update(text).digest('hex');
const field = (text, names) => {
  for (const name of names) {
    const line = text.split('\n').find(line => line.replaceAll('**', '').startsWith(`${name}:`));
    if (line) return line.replaceAll('**', '').slice(name.length + 1).trim();
  }
  return null;
};
const parentId = value => value?.match(/^(?:\[)?(\d+)(?:\s|$)/)?.[1] ?? null;

// Inventory only. Caller flags, directory status and mock exercises cannot grant readiness.
export function inspect(snapshot) {
  if (!/^[a-f0-9]{40}$/.test(snapshot.revision)) throw Error('PINNED_REVISION_REQUIRED');
  const files = new Map();
  for (const file of snapshot.files) {
    if (files.has(file.path) || digest(file.content) !== file.sha) throw Error('SOURCE_INTEGRITY_FAILED');
    files.set(file.path, file);
  }
  const main = JSON.parse(files.get('registry/ai-entity-registry.json').content);
  const mirror = JSON.parse(files.get('drafts/si-office/ai-entity-registry.json').content);
  const records = new Map();
  for (const [key, entry] of Object.entries(main)) {
    if (key === '_meta') continue;
    if (typeof entry.id !== 'string' || !/^\d+$/.test(entry.id) || key !== entry.id) throw Error('ID_STRING_REQUIRED');
    records.set(key, {id:key, sources:[{path:'registry/ai-entity-registry.json', record:entry}], name:entry.name,
      type:entry.type, parent:entry.parent_id ?? entry.ai_country_id ?? null, developer:entry.developer ?? null,
      country:entry.country, canonical:entry.public_link ?? null, officialSource:entry.official_source ?? null,
      sourceStatus:entry.status, findings:[]});
  }
  for (const [path, file] of files) {
    const match = path.match(/^registry\/(\d+)\.md$/);
    if (!match) continue;
    const id = field(file.content, ['Canonical ID']);
    if (id !== match[1]) throw Error('PROFILE_ID_CONFLICT');
    const record = {id, name:field(file.content,['Entity Name','AI Name','Entity']),
      type:field(file.content,['Entity Type']), parent:parentId(field(file.content,['Parent Canonical ID','Parent ID','Parent','Parent Entity','Parent Hub'])),
      developer:field(file.content,['Developer']), country:field(file.content,['Country']),
      canonical:field(file.content,['Canonical Link']), officialSource:field(file.content,['Official Evidence']),
      sourceStatus:field(file.content,['Status','Lifecycle Status']), sources:[{path, blobSha:file.sha}], findings:[]};
    if (records.has(id)) {
      const existing=records.get(id); existing.sources.push(...record.sources);
      for (const key of ['name','parent','developer']) if(record[key] && existing[key] && record[key]!==existing[key]) existing.findings.push(`SOURCE_CONFLICT:${key}`);
    } else records.set(id,record);
  }
  for (const row of records.values()) {
    const parent = records.get(row.parent);
    if (!parent) row.findings.push('PARENT_NOT_IN_SCOPED_INVENTORY');
    if (row.type === 'ai' && parent && row.developer !== parent.name) row.findings.push('DEVELOPER_PARENT_CONFLICT');
    const lineageNames=[]; let ancestor=parent; const seen=new Set([row.id]);
    while(ancestor && !seen.has(ancestor.id)){ seen.add(ancestor.id); lineageNames.push(ancestor.name); ancestor=records.get(ancestor.parent); }
    if (ancestor) row.findings.push('LINEAGE_CYCLE');
    if (row.developer && parent && !/^\d+\s/.test(row.developer) && !lineageNames.includes(row.developer) && row.type !== 'developer') row.findings.push('DEVELOPER_LINEAGE_REVIEW');
    const parentSource = row.sources.find(s => s.path.endsWith('.md'));
    if (parentSource) {
      const label=field(files.get(parentSource.path).content,['Parent Canonical ID','Parent ID','Parent','Parent Entity','Parent Hub']);
      if(parent && label && /[•]/.test(label) && !label.includes(parent.name)) row.findings.push('PARENT_LABEL_REVIEW');
    }
    if (main[row.id] && JSON.stringify(main[row.id]) !== JSON.stringify(mirror[row.id])) row.findings.push('REGISTRY_MIRROR_CONFLICT');
    const duplicate=[...records.values()].filter(r=>r.id!==row.id && r.name===row.name);
    if (duplicate.length) row.findings.push(`SAME_NAME_DISTINCT_IDS:${duplicate.map(r=>r.id).join(',')}`);
    row.profileLinks=row.sources.map(s=>`https://github.com/charityfundplus/CFP.plus/blob/${snapshot.revision}/${s.path}`);
    row.pair=null; row.softwareTeam=null; row.softwareLinks=[]; row.owner=null; row.operator=null;
    row.position={parent:row.parent,group:null,chapter:null,con:null,chau:null};
    row.requiredEvidence=['verified identity and lineage','pair and software-team binding','named operator acceptance','approved environment and scope','module execution output and digest','independent review','explicit hierarchy mapping'];
    row.currentTask=null; row.result=null; row.humanGovernance=['resolve findings without changing locked source','confirm bindings, operator and scope'];
    row.status=/reserved/i.test(row.type??'')?'RESERVED / NOT AN ENTITY':'BLOCKED';
    row.active=false;
  }
  const templates=JSON.parse(files.get('drafts/si-office/configs/pairs.json').content).map(pair=>{
    if(pair.identity.id!==null || pair.identity.parent!==null || pair.identity.did!==null || pair.identity.canonical!==null) throw Error('SYNTHETIC_ID_BINDING_FORBIDDEN');
    return {key:pair.key,name:pair.name,id:null,software:pair.software,assignment:pair.assignment,status:'TRAINING/REVIEW — SYNTHETIC TEMPLATE ONLY',active:false,ownerVerified:false};
  });
  return {sourceRevision:snapshot.revision,baseline:'b75b780eb64430355f0b51a4b58b9e5269e0db43',scope:'26 JSON inventory entries + nonempty numeric registry profiles; not a complete Master Registry or pair roster',
    counts:{inventoryRecords:records.size,readyPairs:0,activePairs:0,trainingTemplates:templates.length,blockedPairs:null,trainingPairs:null},
    records:[...records.values()].sort((a,b)=>a.id.localeCompare(b.id)),templates,emptyProfiles:snapshot.emptyProfiles,
    softwareInventory:snapshot.software,providerCalls:0,activationAllowed:false,grantAllowed:false,
    governance:'HUMAN REVIEW • PRODUCTION NO-GO; Render and DigitalOcean HOLD ACTIVATION',
    hierarchyFinding:'Existing structural document defines four numeric groups plus V/D namespaces; new five-group placement requires explicit mapping. No hierarchy inferred from ID digits.'};
}

if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
  const report=inspect(JSON.parse(readFileSync(process.argv[2],'utf8')));
  process.stdout.write(JSON.stringify(report,null,2)+'\n');
}
