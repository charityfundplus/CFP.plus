import {createHash} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
export const fields=['record_id','source','status','timestamp_utc','version'];
export const hash = value => createHash('sha256').update(value,'utf8').digest('hex');
export function normalize(p) {
 if(!p || Array.isArray(p) || typeof p!=='object' || Object.keys(p).length!==6 || ![...fields,'content_hash'].every(k=>typeof p[k]==='string')) throw Error('INVALID_PAYLOAD');
 const n=Object.fromEntries(fields.map(k=>[k,p[k].trim().normalize('NFC')]));
 if(!/^SIM-[0-9]{8}-[0-9]{3}$/.test(n.record_id) || n.source!=='CFP+_SANDBOX' || !['sandbox_practice','review_pending'].includes(n.status) || n.version!=='0.1' || !/^[0-9a-f]{64}$/.test(p.content_hash)) throw Error('INVALID_PAYLOAD');
 return n;
}
// Fixed, alphabetically sorted flat string fields; not a general RFC 8785 implementation.
export const canonical = n => JSON.stringify(Object.fromEntries([...fields].sort().map(k=>[k,n[k]])));
export const sign = n => ({...n,content_hash:hash(canonical(n))});
export class Adapter {
 constructor(path, now=()=>new Date()) {
  this.now=now; this.db=new DatabaseSync(path);
  this.db.exec(`PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL;
   CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,payload TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY,utc TEXT,source TEXT,version TEXT,hash TEXT,result TEXT,record_id TEXT);
   CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'APPEND_ONLY'); END;
   CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'APPEND_ONLY'); END;`);
 }
 audit(n,result) {this.db.prepare('INSERT INTO audit(utc,source,version,hash,result,record_id) VALUES(?,?,?,?,?,?)').run(this.now().toISOString(),n?.source??null,n?.version??null,n?.content_hash??null,result,n?.record_id??null);}
 ingest(p, direction='CFP_TO_SANDBOX', fault=false) {
  let n;
  this.db.exec('BEGIN IMMEDIATE');
  try {
   if(direction!=='CFP_TO_SANDBOX') throw Error('WRITEBACK_BLOCKED');
   n=normalize(p);
   const t=Date.parse(n.timestamp_utc);
   if(!Number.isFinite(t) || new Date(t).toISOString().replace('.000Z','Z')!==n.timestamp_utc || Math.abs(this.now().getTime()-t)>300000) throw Error('INVALID_TIMESTAMP');
   if(hash(canonical(n))!==p.content_hash) throw Error('HASH_MISMATCH');
   n={...n,content_hash:p.content_hash};
   const old=this.db.prepare('SELECT payload FROM records WHERE id=?').get(n.record_id);
   if(old && JSON.parse(old.payload).content_hash!==n.content_hash) throw Error('CONFLICT');
   const result=old?'IDEMPOTENT':'IMPORTED';
   if(!old) this.db.prepare('INSERT INTO records VALUES(?,?)').run(n.record_id,JSON.stringify(n));
   if(fault) throw Error('INJECTED_FAILURE');
   this.audit(n,result); this.db.exec('COMMIT'); return {result,record:n};
  } catch(e) {
   this.db.exec('ROLLBACK');
   // A failure to persist audit propagates; never acknowledge success without durable audit.
   this.audit(n,e.message); return {result:e.message};
  }
 }
 rollback(id) {
  this.db.exec('BEGIN IMMEDIATE');
  try {this.db.prepare('DELETE FROM records WHERE id=?').run(id);this.audit({record_id:id},'ROLLED_BACK');this.db.exec('COMMIT');}
  catch(e){this.db.exec('ROLLBACK');throw e;}
 }
 snapshot(){return {records:this.db.prepare('SELECT payload FROM records ORDER BY id').all().map(x=>JSON.parse(x.payload)),audit:this.db.prepare('SELECT * FROM audit ORDER BY seq').all()};}
 close(){this.db.close();}
}
