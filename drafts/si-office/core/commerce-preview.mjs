import {catalog} from './commercial-intake.mjs';
import {hash} from './common.mjs';

// Read projection of existing workspace Office records, never a second catalogue.
// Internal keys are sandbox references; canonical identity is deliberately unbound.
export function commercePreview(state, input = {}) {
  if (!input || typeof input !== 'object' || Array.isArray(input) ||
      Object.keys(input).some(k => !['query','kind','limit','offset'].includes(k))) throw Error('COMMERCE_QUERY_INVALID');
  const {query = '', kind = 'all', limit = 30, offset = 0} = input;
  if (typeof query !== 'string' || query.length > 160 ||
      !['all','profile','hstdn','product','service'].includes(kind) ||
      !Number.isInteger(limit) || limit < 1 || limit > 100 ||
      !Number.isInteger(offset) || offset < 0 || offset > 10000) throw Error('COMMERCE_QUERY_INVALID');
  const normalized = value => value.normalize('NFKC').trim().toLocaleLowerCase('en');
  const q = normalized(query);
  const all = catalog(state).map(row => ({
    key: row.key, name: row.name, kind: row.kind,
    scope: typeof row.scope === 'string' ? row.scope : null,
    maturity: typeof row.maturity === 'string' ? row.maturity : null,
    status: 'SANDBOX_ONLY', id: null, parent: null, did: null, canonical: null,
    synthetic: true, verification: 'NOT VERIFIED'
  })).sort((a,b) => a.key.localeCompare(b.key));
  const filtered = all.filter(row => (kind === 'all' || row.kind === kind) && normalized(row.name).includes(q));
  return {items: filtered.slice(offset, offset + limit), total: filtered.length, limit, offset,
    catalogRevision: hash(all), sandbox: true, synthetic: true, readOnly: true,
    registryWrites: 0, activationAllowed: false};
}
