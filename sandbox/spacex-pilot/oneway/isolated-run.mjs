import {readFileSync,writeFileSync} from 'node:fs';
import {Adapter,hash,loadPinned} from './core.mjs';
// usage: isolated-run.mjs <source.json> <state-dir> <expected-source-sha256> --enable
const [source,state,pin,flag]=process.argv.slice(2);
const {raw,input}=loadPinned(source,pin);const before=hash(raw);
const a=new Adapter(`${state}/sandbox.sqlite`,()=>new Date(input.timestamp_utc),{enabled:flag==='--enable'});
const accepted=a.ingest(input);const reverse=a.ingest(input,'SANDBOX_TO_CFP');
let denied;
try{writeFileSync(source,'FORBIDDEN');throw Error('SOURCE_WRITE_SUCCEEDED');}
catch(e){if(e.code!=='ERR_ACCESS_DENIED')throw e;denied={code:e.code,permission:e.permission};}
const after=hash(readFileSync(source));if(before!==after)throw Error('SOURCE_CHANGED');
const snapshot=a.snapshot();a.close();
console.log(JSON.stringify({utc:new Date().toISOString(),accepted:accepted.result,reverse:reverse.result,direct_write:denied,source_pinned_sha256:pin,source_before_sha256:before,source_after_sha256:after,snapshot},null,2));
