import { createHash } from 'node:crypto';

// Offline projection only: this module has no HTTP, filesystem or source-write capability.
const fields = ['id','type','parent_id','ai_country_id','country_id','country','developer','name','order','official_source','public_link','workspace_link','status','intro'];
const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
export const SOURCE_SHA = '835616308111f6851c0387fa9f5eda60c9ffa624';
const numeric = value => typeof value === 'string' && /^\d+$/.test(value);

export class Importer {
  #registry; #approved; #rows = new Map(); #events = []; #enabled = true;
  constructor(registry, approvedIds = []) {
    this.#registry = structuredClone(registry);
    this.#approved = new Set(approvedIds);
  }
  get rows() { return structuredClone([...this.#rows.values()]); }
  get events() { return structuredClone(this.#events); }
  stop() { this.#enabled = false; }
  import(records, {direction = 'CFP_TO_SPACEX', sourceSha} = {}) {
    const audit = (outcome, code, count = 0) => this.#events.push({utc:new Date().toISOString(),outcome,code,count,sourceSha:/^[a-f0-9]{40}$/.test(sourceSha || '') ? sourceSha : null});
    try {
      if (!this.#enabled) throw Error('KILL_SWITCH');
      if (direction !== 'CFP_TO_SPACEX') throw Error('WRITEBACK_BLOCKED');
      if (!/^[a-f0-9]{40}$/.test(sourceSha || '')) throw Error('SOURCE_SHA_REQUIRED');
      if (sourceSha !== SOURCE_SHA) throw Error('SOURCE_VERSION_MISMATCH');
      if (!Array.isArray(records) || records.length > 1000) throw Error('INVALID_BATCH');
      const pending = new Map();
      for (const record of records) {
        if (!record || typeof record !== 'object' || Array.isArray(record)) throw Error('INVALID_RECORD');
        if (Object.keys(record).some(key => !fields.includes(key))) throw Error('FIELD_NOT_ALLOWED');
        if (!numeric(record.id) || !this.#approved.has(record.id)) throw Error('NOT_APPROVED');
        if (pending.has(record.id)) throw Error('DUPLICATE_ID');
        const baseline = this.#registry[record.id];
        if (!baseline || record.id !== baseline.id) throw Error('REGISTRY_MISSING');
        const projected = {};
        for (const key of fields) if (Object.hasOwn(baseline,key)) projected[key] = baseline[key];
        // Exact snapshot matching prevents name/parent/status changes and implicit approval upgrades.
        if (Object.keys(record).length !== Object.keys(projected).length ||
            Object.keys(projected).some(key => record[key] !== projected[key])) throw Error('REGISTRY_MISMATCH');
        if (record.type === 'ai' && (!numeric(record.parent_id) || !this.#registry[record.parent_id] ||
            this.#registry[record.parent_id].type !== 'developer' ||
            this.#registry[record.parent_id].ai_country_id !== record.ai_country_id ||
            this.#registry[record.parent_id].country_id !== record.country_id)) throw Error('PARENT_INVALID');
        for (const key of ['official_source','public_link','workspace_link']) if (record[key]) {
          const url = new URL(record[key]);
          if (url.protocol !== 'https:' || url.username || url.password) throw Error('URL_INVALID');
          if (key === 'public_link' && (url.origin !== 'https://cfp.plus' || url.pathname !== `/${record.id}/` || url.search || url.hash)) throw Error('CANONICAL_INVALID');
        }
        pending.set(record.id, {record:structuredClone(projected), hash:digest(projected), sourceSha});
      }
      let changed = 0;
      for (const [id,row] of pending) if (this.#rows.get(id)?.hash !== row.hash || this.#rows.get(id)?.sourceSha !== row.sourceSha) { this.#rows.set(id,row); changed++; }
      audit('PASS', changed ? 'IMPORTED' : 'IDEMPOTENT', changed);
      return {changed, total:this.#rows.size};
    } catch (error) { audit('BLOCKED',error.message); throw error; }
  }
}
