import {readdirSync,readFileSync,writeFileSync,mkdirSync,copyFileSync,existsSync,renameSync,lstatSync,openSync,fsyncSync,closeSync} from 'node:fs';
import {join,resolve,relative,dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash,randomUUID} from 'node:crypto';
import {P2Sandbox} from './p2-service.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
function walk(root,base=root){return readdirSync(base,{withFileTypes:true}).flatMap(e=>{const p=join(base,e.name);if(e.isSymbolicLink())throw Error('SYMLINK_FORBIDDEN');return e.isDirectory()?walk(root,p):e.isFile()?[relative(root,p)]:[];});}
function contained(root,p){const r=relative(resolve(root),resolve(root,p));if(r.startsWith('..')||r===''||r.startsWith('/'))throw Error('UNSAFE_PATH');return resolve(root,p);}
export function packRelease(source,destination){if(existsSync(destination))throw Error('RELEASE_EXISTS');mkdirSync(destination,{recursive:true,mode:0o700});const paths=walk(source).filter(p=>['core','sandbox','public','configs'].includes(p.split('/')[0])||['package.json','model.mjs','adapters.mjs','server.mjs','ai-entity-registry.json','country-route-map.json','global-country-ai-index.json'].includes(p));for(const p of paths){const d=contained(destination,p);mkdirSync(dirname(d),{recursive:true});copyFileSync(contained(source,p),d);}
 if(!existsSync(join(destination,'sandbox/release-health.mjs')))copyFileSync(new URL('./release-health.mjs',import.meta.url),join(destination,'sandbox/release-health.mjs'));
 const files=walk(destination).sort().map(path=>({path,sha256:sha(readFileSync(contained(destination,path)))}));const raw=JSON.stringify({format:1,files});writeFileSync(join(destination,'release.json'),raw,{flag:'wx',mode:0o600});return sha(raw);}
export function verifyRelease(root,expected){const raw=readFileSync(join(root,'release.json'));if(sha(raw)!==expected)throw Error('RELEASE_MANIFEST_MISMATCH');const m=JSON.parse(raw);if(m.format!==1)throw Error('RELEASE_FORMAT');const actual=walk(root).filter(p=>p!=='release.json').sort();if(JSON.stringify(actual)!==JSON.stringify(m.files.map(f=>f.path).sort()))throw Error('RELEASE_FILE_SET');for(const f of m.files)if(sha(readFileSync(contained(root,f.path)))!==f.sha256)throw Error('RELEASE_BYTES_MISMATCH');return m;}
function writePointer(path,value){const tmp=path+'.'+randomUUID();const fd=openSync(tmp,'wx',0o600);try{writeFileSync(fd,JSON.stringify(value));fsyncSync(fd);}finally{closeSync(fd);}renameSync(tmp,path);const dir=openSync(dirname(path),'r');try{fsyncSync(dir);}finally{closeSync(dir);}}
export class SandboxReleaseControl {
 constructor(directory){this.directory=resolve(directory);mkdirSync(this.directory,{recursive:true,mode:0o700});}
 current(){const p=join(this.directory,'active.json');return existsSync(p)?JSON.parse(readFileSync(p)):null;}
 async activate({service,token,release,digest}){
  const lease=service.maintenanceLease(token);try{
  verifyRelease(release,digest);const {smoke}=await import(pathToFileURL(join(resolve(release),'sandbox/release-health.mjs')));const health=await smoke();if(!health.pass)throw Error('RELEASE_HEALTH_FAILED');verifyRelease(release,digest);
  const previous=this.current(),checkpoint=join(this.directory,'checkpoint-'+randomUUID()+'.db');lease.backup(checkpoint);
  const event={operation:'activate',time:new Date().toISOString(),previous,release:resolve(release),digest,checkpoint,health};const eventPath=join(this.directory,'event-'+randomUUID()+'.json');writeFileSync(eventPath,JSON.stringify(event),{flag:'wx',mode:0o600});writePointer(join(this.directory,'active.json'),{release:resolve(release),digest,eventPath});return event;}finally{lease.release();}
 }
 async rollback({service,token}){
  const lease=service.maintenanceLease(token);try{
  const active=this.current();if(!active)throw Error('NO_ACTIVE_RELEASE');const event=JSON.parse(readFileSync(active.eventPath));if(event.operation!=='activate'||!event.previous)throw Error('NO_EXECUTABLE_ROLLBACK');
  const previous=event.previous;verifyRelease(previous.release,previous.digest);const {smoke}=await import(pathToFileURL(join(previous.release,'sandbox/release-health.mjs')));const health=await smoke();if(!health.pass)throw Error('ROLLBACK_HEALTH_FAILED');verifyRelease(previous.release,previous.digest);
  // Preserve current DB/audit as a new consistent backup; restore old snapshot into a new generation only.
  const retained=join(this.directory,'retained-'+randomUUID()+'.db');lease.backup(retained);const destination=join(this.directory,'restored-'+randomUUID()+'.db');const restored=P2Sandbox.restore(event.checkpoint,destination);restored.close();
  const result={operation:'rollback',previous:active,release:previous.release,digest:previous.digest,health,restoredDatabase:destination,retainedCurrentDatabase:retained,time:new Date().toISOString()};const eventPath=join(this.directory,'event-'+randomUUID()+'.json');writeFileSync(eventPath,JSON.stringify(result),{flag:'wx',mode:0o600});writePointer(join(this.directory,'active.json'),{release:previous.release,digest:previous.digest,eventPath,database:destination});return result;}finally{lease.release();}
 }
}
