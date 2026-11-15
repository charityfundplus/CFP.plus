// Same-origin client for the EXISTING authenticated Core. No snapshot fallback,
// credentials store, identity writer, external request or alternate API service.
const idPattern = /^\d{1,256}$/;
function id(value) { if (typeof value !== 'string' || !idPattern.test(value)) throw Error('NUMERIC_ID_STRING_REQUIRED'); return value; }
function envelope(value) {
  if (!value || value.readOnly !== true || value.registryWrites !== 0 || value.activationAllowed !== false ||
      value.provenance?.sourceBytesVerified !== true || !/^[a-f0-9]{40}$/.test(value.provenance.revision) || !Array.isArray(value.provenance.files)) throw Error('CORE_SOURCE_UNVERIFIED');
  return value;
}
const fingerprint = value => JSON.stringify([value.provenance.revision, value.provenance.files]);

// Codex 2's parent_id/pair/intro fields are display projections, not a registry.
export function projectCoreRecord(record, provenance) {
  id(record.id); if (record.parent !== null) id(record.parent);
  if (record.id.length > 80 || (record.parent?.length ?? 0) > 80) throw Error('UI_ID_LENGTH_UNSUPPORTED');
  const file = provenance.files.find(f => f.path === record.sourcePath);
  if (!file || !/^registry\/[a-zA-Z0-9_.-]+$/.test(file.path) || !/^[a-f0-9]{64}$/.test(file.sha256) || !/^[a-f0-9]{40}$/.test(file.gitBlobSHA)) throw Error('CORE_RECORD_SOURCE_UNVERIFIED');
  return {id: record.id, parent_id: record.parent, type: record.type === 'super-pair' ? 'pair' : record.type,
    coreType: record.type, name: record.name, country: record.country ?? null, country_id: record.countryID ?? null,
    ai_country_id: record.aiCountryID ?? null, developer: record.developer ?? null, did: record.did ?? null,
    intro: record.description ?? '', status: record.sourceStatus ?? record.reviewStatus, sourceCanonical: record.canonicalLink,
    chapter: record.chapter, group: record.group, conflict: record.issues?.length > 0, issues: structuredClone(record.issues ?? []),
    hstdn: null, identityVerified: false, authorityVerified: false, operationsAllowed: false,
    provenance: {sourceRevision: provenance.revision, registryURL: 'https://github.com/charityfundplus/CFP.plus/blob/' + provenance.revision + '/' + file.path,
      registryBlobSHA: file.gitBlobSHA, sourceSHA256: file.sha256}, evidence: []};
}

export function createRegistryClient({fetchImpl = globalThis.fetch} = {}) {
  if (typeof fetchImpl !== 'function') throw Error('FETCH_REQUIRED');
  async function request(path, body) {
    const response = await fetchImpl('/api/core/' + path, {credentials: 'same-origin', cache: 'no-store',
      ...(body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)})});
    const value = await response.json();
    if (!response.ok) { const error = Error(value.error || 'CORE_REQUEST_FAILED'); error.status = response.status; throw error; }
    return envelope(value);
  }
  async function search(input = {}) {
    if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(k => !['query', 'type', 'chapter', 'limit', 'offset'].includes(k))) throw Error('REGISTRY_INVALID_FIELDS');
    const value = await request('registry?' + new URLSearchParams(input));
    if (!Array.isArray(value.records) || !Number.isInteger(value.total) || value.total < 0 || value.total > 10000) throw Error('CORE_RESPONSE_INVALID');
    return value;
  }
  return {
    search,
    detail: value => request('registry/' + id(value)),
    validation: () => request('registry-validation'),
    openai: () => request('hstdn-openai'),
    project: value => request('chatgpt-project', {id: id(value)}),
    async snapshot() {
      let first, offset = 0; const records = [];
      do {
        const page = await search({limit: 100, offset});
        if (!first) first = page;
        if (fingerprint(page) !== fingerprint(first) || page.total !== first.total || page.offset !== offset ||
            page.records.length > 100 || page.records.length === 0 && offset < first.total) throw Error('CORE_SOURCE_CHANGED_DURING_READ');
        records.push(...page.records); offset += page.records.length;
        if (records.length > first.total) throw Error('CORE_RESPONSE_INVALID');
      } while (offset < first.total);
      if (new Set(records.map(r => r.id)).size !== records.length) throw Error('CORE_DUPLICATE_ID');
      return {sourceCommit: first.provenance.revision, provenance: first.provenance,
        published: false, activationAllowed: false, connectionStatus: 'AUTHENTICATED_CORE_READ',
        records: records.map(r => projectCoreRecord(r, first.provenance))};
    }
  };
}
