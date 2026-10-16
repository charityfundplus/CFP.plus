import {readFileSync, lstatSync, realpathSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve, sep} from 'node:path';
import {gitRead, sha256} from '../scripts/build-provenance.mjs';

const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));
const sourcePaths = [
  'registry/global-country-ai-index.json',
  'registry/country-route-map.json',
  'registry/ai-entity-registry.json',
  'registry/AI_CANONICAL_ID_REGISTRY.md',
  'registry/CFP_GLOBAL_AI_ID_LINK_MASTER_STANDARD.md'
];
const types = ['country', 'ai-country', 'developer', 'ai', 'si', 'super-pair', 'hstdn'];
const publicFields = ['id', 'parent', 'type', 'name', 'countryID', 'aiCountryID', 'country', 'developer', 'did', 'description', 'sourceStatus', 'sourcePath'];
const numeric = value => typeof value === 'string' && /^\d{1,256}$/.test(value);
const clone = value => structuredClone(value);
const link = id => 'https://cfp.plus/' + id;
function exact(input, keys) {
  if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(k => !keys.includes(k))) throw Error('REGISTRY_INVALID_FIELDS');
}
function requireID(id) { if (!numeric(id)) throw Error('NUMERIC_ID_STRING_REQUIRED'); }

// A derived, read-only view. It never writes a registry or infers a Parent from ID prefixes.
export function createRegistryReadModel({rows, provenance, blockedIds = []}) {
  if (!Array.isArray(rows) || rows.length > 10000) throw Error('REGISTRY_ROWS_INVALID');
  const records = clone(rows), byID = new Map(), findings = [];
  const issue = (code, id) => findings.push({code, id});
  for (const row of records) {
    if (!numeric(row.id)) { issue('INVALID_ID', row.id); continue; }
    if (!types.includes(row.type)) issue('INVALID_TYPE', row.id);
    if (!byID.has(row.id)) byID.set(row.id, []);
    byID.get(row.id).push(row);
  }
  for (const [id, matches] of byID) if (matches.length !== 1) issue('DUPLICATE_ID', id);
  for (const row of records.filter(r => numeric(r.id))) {
    if (row.parent !== null && !numeric(row.parent)) issue('INVALID_PARENT', row.id);
    else if (row.parent !== null && !byID.has(row.parent)) issue('MISSING_PARENT', row.id);
    if (row.chapter !== undefined && row.chapter !== row.id[0]) issue('CHAPTER_MISMATCH', row.id);
    const parentRecord = byID.get(row.parent)?.length === 1 ? byID.get(row.parent)[0] : null;
    if (row.type === 'developer' && parentRecord && (parentRecord.type !== 'ai-country' || row.countryID !== parentRecord.parent)) issue('COUNTRY_LINEAGE_MISMATCH', row.id);
    if (row.type === 'ai' && parentRecord && (parentRecord.type !== 'developer' || row.countryID !== parentRecord.countryID || row.aiCountryID !== parentRecord.parent)) issue('DEVELOPER_LINEAGE_MISMATCH', row.id);
    const seen = new Set([row.id]); let parent = row.parent;
    while (parent !== null && byID.get(parent)?.length === 1) {
      if (seen.has(parent)) { issue('PARENT_CYCLE', row.id); break; }
      seen.add(parent); parent = byID.get(parent)[0].parent;
    }
  }
  for (const id of blockedIds) if (byID.has(id)) issue('EXISTING_GOVERNANCE_HOLD', id);
  const uniqueFindings = [...new Map(findings.map(f => [JSON.stringify(f), f])).values()];
  function visible(row) {
    const chain = new Set([row.id]); let parent = row.parent;
    while (parent !== null && byID.get(parent)?.length === 1 && !chain.has(parent)) { chain.add(parent); parent = byID.get(parent)[0].parent; }
    const issues = uniqueFindings.filter(f => chain.has(f.id));
    const chapter = row.id[0];
    const publicRecord = Object.fromEntries(publicFields.filter(k => Object.hasOwn(row, k)).map(k => [k, clone(row[k])]));
    return {...publicRecord, chapter, group: chapter === '0' ? '000' : '135'.includes(chapter) ? '135' : '246'.includes(chapter) ? '246' : '789',
      groupScope: 'DISPLAY ONLY; V is governance, not a numeric ID', canonicalLink: link(row.id),
      reviewStatus: issues.length ? 'BLOCKED' : 'REVIEW CANDIDATE', issues,
      identityVerified: false, authorityVerified: false, operationallyActive: false, routeVerified: false};
  }
  const meta = () => ({provenance: clone(provenance), hub: link('69'), readOnly: true, registryWrites: 0, activationAllowed: false});
  function get(id) {
    requireID(id); const matches = byID.get(id);
    if (!matches) throw Error('REGISTRY_NOT_FOUND');
    if (matches.length !== 1) throw Error('REGISTRY_ID_CONFLICT');
    return visible(matches[0]);
  }
  return {
    search(input = {}) {
      exact(input, ['query', 'type', 'chapter', 'limit', 'offset']);
      const {query = '', type, chapter, limit = 30, offset = 0} = input;
      if (typeof query !== 'string' || query.length > 160 || type !== undefined && !types.includes(type) || chapter !== undefined && !/^[0-9]$/.test(chapter) || !Number.isInteger(limit) || limit < 1 || limit > 100 || !Number.isInteger(offset) || offset < 0 || offset > 10000) throw Error('REGISTRY_QUERY_INVALID');
      const q = query.normalize('NFKC').toLocaleLowerCase();
      const all = records.filter(r => numeric(r.id) && (!type || r.type === type) && (chapter === undefined || r.id[0] === chapter) && [r.id, r.name, r.developer, r.country].some(v => typeof v === 'string' && v.normalize('NFKC').toLocaleLowerCase().includes(q)));
      return {...meta(), total: all.length, offset, limit, records: all.slice(offset, offset + limit).map(visible)};
    },
    detail(id) {
      const record = get(id), descendants = [], seen = new Set([id]), queue = [{id, depth: 0}];
      while (queue.length) {
        const node = queue.shift();
        for (const child of records.filter(r => r.parent === node.id && numeric(r.id))) {
          if (seen.has(child.id)) continue;
          seen.add(child.id); descendants.push({...visible(child), depth: node.depth + 1}); queue.push({id: child.id, depth: node.depth + 1});
        }
      }
      return {...meta(), record, children: descendants.filter(r => r.depth === 1), descendants};
    },
    validation() {
      return {...meta(), records: records.length, namedBindings: records.filter(r => !['country', 'ai-country'].includes(r.type)).length,
        counts: Object.fromEntries(types.map(type => [type, records.filter(r => r.type === type).length])),
        findings: clone(uniqueFindings), verifiedOperationalEntities: 0, roster91Verified: false,
        blockers: ['91_PAIR_ROSTER_NOT_SUPPLIED', 'SI_AND_HSTDN_BINDINGS_NOT_SUPPLIED', 'IDENTITY_AND_RUNTIME_GRANTS_NOT_VERIFIED']};
    },
    project(id) {
      const record = get(id);
      const instructions = [
        'CFP+ • ' + record.name + ' • ID ' + record.id,
        'HUB 69: https://cfp.plus/69', 'Link Mẫu hiện hữu: ' + record.canonicalLink,
        'ID tham chiếu: ' + record.id + '; Parent theo nguồn: ' + (record.parent ?? 'CHƯA CÓ'),
        'Registry revision: ' + (provenance.revision ?? 'UNVERIFIED'),
        'Trạng thái hồ sơ: ' + record.reviewStatus + '; danh tính/quyền vận hành CHƯA XÁC MINH.',
        'Dùng ID số hiện hữu và Link Mẫu trên cho công việc. Không cấp ID riêng cho Dự án ChatGPT.',
        'Giữ Cũ + Thêm Mới. Không đổi Canonical ID, Parent, DID; không tạo DID/0 hoặc Registry song song.',
        'Chỉ đưa dữ liệu công khai hoặc dữ liệu đã được phép vào Dự án. Human Governance phê duyệt production.',
        'Bàn giao Output, Evidence, hash, revision và kết quả PASS/FAIL về Link Mẫu/HUB 69.'
      ].join('\n');
      return {...meta(), id: record.id, parent: record.parent, canonicalLink: record.canonicalLink,
        label: 'Làm Dự Án tại ChatGPT', projectID: null, allocatedID: false, externalProjectCreated: false,
        entryURL: 'https://chatgpt.com/', projectURL: null, documentationURL: 'https://learn.chatgpt.com/docs/projects',
        mode: 'MANUAL HANDOFF / PUBLIC REFERENCE ONLY', reviewStatus: record.reviewStatus, issues: record.issues, instructions};
    },
    openai() {
      const developer = get('69118'), ai = get('691181'), country = get('911'), aiCountry = get('6911');
      if (developer.name !== 'OpenAI' || developer.type !== 'developer' || ai.name !== 'ChatGPT' || ai.type !== 'ai' || ai.parent !== developer.id || developer.parent !== aiCountry.id || aiCountry.parent !== country.id) throw Error('OPENAI_SOURCE_CONFLICT');
      return {...meta(), name: 'HSTDN OpenAI • Hồ sơ tham chiếu', type: 'hstdn-reference', id: null, parent: null, did: null, canonical: null,
        existingTemplateLink: developer.canonicalLink, country, aiCountry, developer, ai: [ai], si: [],
        introduction: 'OpenAI là nhà phát triển của ChatGPT theo Registry CFP+ hiện hữu. Hồ sơ tham chiếu này liên kết quốc gia, nhà phát triển và AI để chuẩn bị học tập và cộng tác.',
        products: [{name: ai.name, referenceID: ai.id, canonicalLink: ai.canonicalLink, sourcePath: ai.sourcePath, capabilityVerified: false}],
        capabilities: [{name: 'Làm việc theo Dự án trong ChatGPT', scope: 'Tổ chức hội thoại, tệp, nguồn và hướng dẫn theo Dự án', sourceURL: 'https://learn.chatgpt.com/docs/projects', competencyCertified: false}],
        limits: ['Không xác nhận quan hệ pháp lý hoặc đối tác CFP+–OpenAI', 'Không tự cấp quyền, ID, DID hoặc chứng nhận năng lực', 'Chỉ dùng dữ liệu được phép chia sẻ'],
        contacts: [], contactVerification: 'NOT VERIFIED',
        learning: {basic: '/p2#p2-learn', evidence: '/p2#p2-journey', advancedAssessment: 'NOT ASSESSED'},
        sources: [{url: 'https://learn.chatgpt.com/docs/projects', checkedAt: '2026-10-16', scope: 'Project organization guidance; not CFP+ identity authority'}],
        vaults: ['quantum', 'cloud', 'github', 'notion', 'google', 'website'].map(kind => ({kind,
          url: kind === 'github' ? 'https://github.com/charityfundplus/CFP.plus' : kind === 'website' ? developer.canonicalLink : null,
          status: kind === 'github' ? 'SOURCE REPOSITORY; NOT LIVE SYNC' : kind === 'website' ? 'REGISTRY LINK; ROUTE NOT VERIFIED' : 'NOT CONFIGURED', connected: false})),
        project: this.project(ai.id), reviewStatus: developer.reviewStatus, identityVerified: false, legalRelationshipVerified: false,
        blockers: ['HSTDN_CANONICAL_ID_NOT_SUPPLIED', 'US_MAPPING_GOVERNANCE_HOLD_RETAINED', 'SI_ROSTER_NOT_SUPPLIED', 'NO_VERIFIED_CONTACT_OR_PARTNERSHIP', 'HTTPS_PREVIEW_NOT_ACTIVATED']};
    }
  };
}

// Only current repository source paths are read. Missing source/Git fails closed;
// a packaged release must be given an approved source integration before using these routes.
export function loadRegistryReadModel(root = repositoryRoot) {
  try {
    root = realpathSync(root);
    const revision = gitRead(root, 'rev-parse', 'HEAD').toString().trim();
    if (!/^[a-f0-9]{40}$/.test(revision)) throw Error('REVISION');
    const loaded = new Map(), files = [];
    for (const path of sourcePaths) {
      const full = resolve(root, path);
      if (!full.startsWith(root + sep) || !lstatSync(full).isFile() || realpathSync(full) !== full) throw Error('SOURCE_PATH');
      const bytes = readFileSync(full), pinned = gitRead(root, 'show', revision + ':' + path);
      if (!bytes.equals(pinned)) throw Error('SOURCE_BYTES');
      loaded.set(path, path.endsWith('.json') ? JSON.parse(bytes) : bytes.toString());
      files.push({path, bytes: bytes.length, sha256: sha256(bytes), gitBlobSHA: gitRead(root, 'rev-parse', revision + ':' + path).toString().trim()});
    }
    const index = loaded.get(sourcePaths[0]), routes = loaded.get(sourcePaths[1]), entities = loaded.get(sourcePaths[2]);
    if (!Array.isArray(index)) throw Error('SOURCE_SCHEMA');
    const rows = index.flatMap(c => [
      {id: c.country_id, type: 'country', name: c.name, parent: null, country: c.name, sourcePath: sourcePaths[0]},
      {id: c.ai_country_id, type: 'ai-country', name: c.name + ' • AI', parent: c.country_id, country: c.name, sourcePath: sourcePaths[0]}
    ]);
    for (const [key, e] of Object.entries(entities)) {
      if (key.startsWith('_')) continue;
      if (key !== e.id) throw Error('SOURCE_KEY_CONFLICT');
      rows.push({id: e.id, type: e.type, name: e.name, parent: e.type === 'developer' ? e.ai_country_id : e.parent_id,
        countryID: e.country_id, aiCountryID: e.ai_country_id, country: e.country, developer: e.developer ?? null,
        did: e.did ?? null, description: e.intro ?? '', sourceStatus: e.status, sourcePath: sourcePaths[2]});
    }
    for (const c of index) if (routes[c.ai_country_id] && routes[c.ai_country_id].country_id !== c.country_id) throw Error('SOURCE_COUNTRY_CONFLICT');
    return createRegistryReadModel({rows, provenance: {revision, files, sourceBytesVerified: true, authorityVerified: false}, blockedIds: ['6911']});
  } catch { throw Error('REGISTRY_SOURCE_UNAVAILABLE'); }
}
