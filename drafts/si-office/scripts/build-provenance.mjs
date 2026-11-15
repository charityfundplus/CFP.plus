import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFileSync,lstatSync,realpathSync,mkdtempSync,openSync,closeSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,relative,sep} from 'node:path';
export function gitRead(root,...args){
 const temp=mkdtempSync(resolve(tmpdir(),'cfp-git-read-')),fd=openSync(resolve(temp,'output'),'wx',0o600);
 try{execFileSync('git',['-C',root,...args],{stdio:['ignore',fd,'ignore']});return readFileSync(resolve(temp,'output'));}finally{closeSync(fd);rmSync(temp,{recursive:true,force:true});}
}
export const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const source=path=>!/(^|\/)(docs|tests|node_modules|\.git)\//.test(path)&&/\.(mjs|cjs|js|jsx|ts|tsx|mts|json|html|css|py|sql|wasm)$/.test(path);
// Git object bytes are the independent reference; supplied SHA strings cannot attest execution.
export function executionProvenance(sourceRoot){
 try{
  const root=realpathSync(sourceRoot);let git=(...args)=>gitRead(root,...args);
  const top=git('rev-parse','--show-toplevel').toString().trim(),prefix=relative(top,root).split(sep).join('/');
  if(prefix.startsWith('..'))throw Error('SOURCE_ROOT_INVALID');git=(...args)=>gitRead(top,...args);
  const revision=git('rev-parse','HEAD').toString().trim();
  if(!/^[a-f0-9]{40}$/.test(revision))throw Error('GIT_REVISION_INVALID');
  const names=git('ls-tree','-r','--name-only','-z',revision,'--',prefix||'.').toString().split('\0').filter(Boolean).map(p=>prefix?p.slice(prefix.length+1):p).filter(source).sort();
  if(!names.length)throw Error('RUNTIME_SOURCE_EMPTY');
  const untracked=git('ls-files','--others','-z','--',prefix||'.').toString().split('\0').filter(Boolean).map(p=>prefix?p.slice(prefix.length+1):p);
  if(untracked.some(path=>source(path)&&!names.includes(path)))throw Error('UNTRACKED_RUNTIME_SOURCE');
  const files=names.map(path=>{
   const full=resolve(root,path);if(!full.startsWith(root+sep)||!lstatSync(full).isFile()||realpathSync(full)!==full)throw Error('SOURCE_FILE_INVALID');
   const actual=readFileSync(full),pinned=git('show',revision+':'+(prefix?prefix+'/':'')+path);
   if(!actual.equals(pinned))throw Error('SOURCE_BYTES_DIFFER');
   return {path,bytes:actual.length,sha256:sha256(actual)};
  });
  const manifest={schemaVersion:1,algorithm:'sha256',scope:'tracked runtime source; excludes docs/tests',revision,files};
  return {verified:true,verificationScope:'EXPORT_PROCESS_SOURCE_BYTES',taskExecutionVerified:false,revision,manifest,manifestSha256:sha256(JSON.stringify(manifest)),authorityVerified:false,activationAllowed:false};
 }catch(e){return {verified:false,revision:null,manifest:null,manifestSha256:null,finding:e.message?.split('\n')[0]||'SOURCE_PROVENANCE_UNAVAILABLE',authorityVerified:false,activationAllowed:false};}
}
export function verifyExportProvenance(claim,sourceRoot){
 const actual=executionProvenance(sourceRoot);
 if(!actual.verified||claim?.verified!==true||claim.revision!==actual.revision||claim.manifestSha256!==actual.manifestSha256||JSON.stringify(claim.manifest)!==JSON.stringify(actual.manifest))throw Error('EXPORT_SOURCE_PROVENANCE_MISMATCH');
 return actual;
}
