// CFP+ • Environment doctor for the Siêu Bộ Đôi installer (read-only).
// Reports required vs optional tooling; never reads credentials or changes config.
import {spawnSync} from 'node:child_process';
import {mkdtempSync,rmSync,writeFileSync,existsSync} from 'node:fs';
import {tmpdir,platform,release,arch,cpus,totalmem} from 'node:os';
import {join} from 'node:path';
import {createServer} from 'node:net';

function probe(cmd,args=['--version']){
 const r=spawnSync(cmd,args,{encoding:'utf8',timeout:15000,windowsHide:true});
 if(r.error||r.status!==0)return {found:false};
 return {found:true,version:(r.stdout||r.stderr).trim().split(/\r?\n/)[0].slice(0,120)};
}
function portFree(port){return new Promise(res=>{const s=createServer();s.once('error',()=>res(false));s.listen(port,'127.0.0.1',()=>s.close(()=>res(true)));});}

export async function diagnose({port=4173}={}){
 const major=Number(process.versions.node.split('.')[0]);
 let sqlite=false;try{await import('node:sqlite');sqlite=true;}catch{}
 let tempWritable=false;try{const d=mkdtempSync(join(tmpdir(),'cfp-doctor-'));writeFileSync(join(d,'probe'),'ok');rmSync(d,{recursive:true,force:true});tempWritable=true;}catch{}
 const git=probe('git');
 const autocrlf=git.found?(spawnSync('git',['config','--get','core.autocrlf'],{encoding:'utf8',windowsHide:true}).stdout||'').trim()||'unset':'n/a';
 const python=probe(platform()==='win32'?'python':'python3');
 const chromiumCandidates=[process.env.CHROMIUM_PATH,'/usr/bin/chromium','/usr/bin/chromium-browser','C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe'].filter(Boolean);
 const browser=chromiumCandidates.find(p=>existsSync(p))||null;
 const required=[
  {name:'node>=22',ok:major>=22,detail:process.version},
  {name:'node:sqlite',ok:sqlite,detail:sqlite?'available (experimental in Node 22)':'missing: P2 sandbox tests need it'},
  {name:'temp-writable',ok:tempWritable,detail:tmpdir()},
  {name:`port-${port}-free`,ok:await portFree(port),detail:'loopback preview port'}
 ];
 const optional=[
  {name:'git',ok:git.found,detail:git.version||'missing'},
  {name:'git core.autocrlf',ok:autocrlf!=='true',detail:autocrlf==='true'?'true: CRLF checkout breaks byte-exact website tests; use PYTHONUTF8=1 and LF checkout for parity with CI':autocrlf},
  {name:'python',ok:python.found,detail:python.version||'missing: website/CTTTC Python tests unavailable'},
  {name:'docker',ok:probe('docker').found,detail:probe('docker').version||'missing: nginx container gate runs only on CI'},
  {name:'chromium/edge',ok:!!browser,detail:browser||'missing: browser QA unavailable (set CHROMIUM_PATH)'}
 ];
 return {
  tool:'cfp-env-doctor',time:new Date().toISOString(),
  host:{platform:platform(),release:release(),arch:arch(),cpus:cpus().length,memoryGB:Math.round(totalmem()/2**30)},
  required,optional,ready:required.every(c=>c.ok),
  missing:[...required,...optional].filter(c=>!c.ok).map(c=>c.name),
  scope:'Read-only probe. No credentials, accounts or network writes.'
 };
}

if(import.meta.url===`file:///${process.argv[1]?.replace(/\\/g,'/').replace(/^\//,'')}`||process.argv[1]?.endsWith('env-doctor.mjs')){
 const report=await diagnose();
 console.log(JSON.stringify(report,null,2));
 process.exitCode=report.ready?0:2;
}
