// CFP+ • Siêu Bộ Đôi shared installer (sandbox). One command:
//   node scripts/superpair-install.mjs [--sample 69103] [--out DIR]
// Steps: env doctor → every test suite → sample pair → batch pairs → evidence pack.
// Stops at the first failing gate. Local only: no network, accounts, push or deploy.
import {spawnSync} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {diagnose} from './env-doctor.mjs';
import {run} from './superpair-init.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const SUITES=['scripts/run-tests.mjs','tests/p2.test.mjs','tests/p2-http.test.mjs','tests/review-round1.test.mjs','tests/training-basic-v1.test.mjs','tests/forum-foundation-loopback.test.mjs','tests/forum-independent-qa.test.mjs','tests/superpair-factory.test.mjs'];
const sha=s=>createHash('sha256').update(s).digest('hex');

function suite(file){
 const r=spawnSync(process.execPath,[file],{cwd:root,encoding:'utf8',timeout:300000,windowsHide:true});
 const n=k=>Number((r.stdout.match(new RegExp(`^# ${k} (\\d+)`,'m'))||[])[1]??NaN);
 return {suite:file,exit:r.status,tests:n('tests'),pass:n('pass'),fail:n('fail'),ok:r.status===0&&n('fail')===0};
}

const args=process.argv.slice(2);const opt=k=>{const i=args.indexOf(k);return i>=0?args[i+1]:undefined;};
const out=resolve(opt('--out')||mkdtempSync(join(tmpdir(),'cfp-superpair-install-')));mkdirSync(out,{recursive:true});
const sampleId=opt('--sample')||'69103';
const report={tool:'cfp-superpair-install',time:new Date().toISOString(),out,gates:[]};
const gate=(name,ok,detail)=>{report.gates.push({name,ok,detail});console.log(`${ok?'PASS':'FAIL'}  ${name}`);return ok;};

const env=await diagnose();
let ok=gate('environment',env.ready,{missingRequired:env.required.filter(c=>!c.ok).map(c=>c.name),missingOptional:env.optional.filter(c=>!c.ok).map(c=>c.name),host:env.host});
report.environment=env;
if(ok){const suites=SUITES.map(suite);report.suites=suites;ok=gate('test-suites',suites.every(s=>s.ok),suites.map(s=>`${s.suite} ${s.pass}/${s.tests}`));}
if(ok){const s=await run(['--sample',sampleId,'--out',out]);ok=gate(`sample-pair-${sampleId}`,s.evidence.pass,{file:s.file,held:s.evidence.held});}
if(ok){const b=await run(['--batch','--out',out]);ok=gate('batch-pairs',b.evidence.pass,{file:b.file,built:b.evidence.built,held:b.evidence.held.length});}
// Forum service (Python/PostgreSQL) is advisory: reported, never silently passed.
const pyOk=env.optional.find(c=>c.name==='python')?.ok,pgOk=env.optional.find(c=>c.name.startsWith('postgresql'))?.ok;
report.forumService={status:pyOk&&pgOk?'READY TO RUN (not executed by installer)':'BLOCKED',needs:[!pyOk&&'python',!pgOk&&'postgresql'].filter(Boolean),source:'origin/claude/forum-schema-location-guard:services/forum'};
console.log(`INFO  forum-service: ${report.forumService.status}${report.forumService.needs.length?' (missing '+report.forumService.needs.join(', ')+')':''}`);
report.pass=ok&&report.gates.every(g=>g.ok);
report.governance='SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO GO';
const body=JSON.stringify(report,null,2);writeFileSync(join(out,'install-report.json'),body);writeFileSync(join(out,'install-report.json.sha256'),sha(body)+'  install-report.json\n');
console.log(`${report.pass?'INSTALL PASS':'INSTALL FAIL'} • evidence: ${out}`);
process.exitCode=report.pass?0:1;
