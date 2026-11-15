import {readFileSync} from 'node:fs';import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url),digest=b=>createHash('sha256').update(b).digest('hex');
const bytes=readFileSync(new URL('docs/OFFICE_INTAKE_MANIFEST.json',root));
if(digest(bytes)!==readFileSync(new URL('docs/OFFICE_INTAKE_MANIFEST.sha256',root),'utf8').trim())throw Error('MANIFEST_DIGEST_MISMATCH');
const manifest=JSON.parse(bytes);for(const f of manifest.files){if(f.path.includes('..')||f.path.startsWith('/')||digest(readFileSync(new URL(f.path,root)))!==f.sha256)throw Error('FILE_DIGEST_MISMATCH:'+f.path);}
console.log(JSON.stringify({status:'PASS',files:manifest.files.length,upstreamBase:manifest.upstreamBase,manifestSHA256:digest(bytes),scope:'File integrity; does not certify identity or operational readiness'}));
