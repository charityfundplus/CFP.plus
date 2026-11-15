import {mkdirSync,existsSync,statSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,join} from 'node:path';import {randomBytes} from 'node:crypto';import {fileURLToPath} from 'node:url';
import {executionProvenance} from './build-provenance.mjs';
import {P2Sandbox} from '../sandbox/p2-service.mjs';import {createP2HTTP} from '../sandbox/p2-http.mjs';
export function createReviewSandbox({database,origin,revision}){
 if(typeof database!=='string'||!database||!/^https:\/\//.test(origin||'')||! /^[a-f0-9]{40}$/.test(revision||''))throw Error('PINNED_PRIVATE_PREVIEW_REQUIRED');
 const build=executionProvenance(fileURLToPath(new URL('../',import.meta.url)));if(!build.verified||revision!==build.revision)throw Error('EXECUTION_REVISION_UNVERIFIED');
 const directory=dirname(database);if(!existsSync(directory))mkdirSync(directory,{recursive:true,mode:0o700});if(statSync(directory).mode&0o077)throw Error('PRIVATE_STATE_DIRECTORY_REQUIRED');
 const accountsFile=join(directory,'synthetic-review-accounts.json');const fresh=!existsSync(database);if(!fresh&&!existsSync(accountsFile))throw Error('EXISTING_ACCOUNT_RECEIPT_REQUIRED');
 const service=new P2Sandbox(database);try{
  if(fresh){const accounts=[['cfp-editor','editor'],['cfp-reviewer','reviewer'],['cfp-viewer','viewer']].map(([id,role])=>({id,role,password:randomBytes(18).toString('base64url'),workspace:'cfp-review1',pairs:['*']}));for(const account of accounts)service.provision(account);writeFileSync(accountsFile,JSON.stringify({synthetic:true,revision,accounts},null,2),{mode:0o600,flag:'wx'});}
  const server=createP2HTTP({service,previewOrigin:origin});const handler=server.listeners('request')[0];server.removeAllListeners('request');server.on('request',(req,res)=>{const current=executionProvenance(fileURLToPath(new URL('../',import.meta.url)));if(current.verified&&current.manifestSha256===build.manifestSha256)res.setHeader('X-CFP-Preview-Revision',build.revision);return handler(req,res);});return {service,server,accountsFile};
 }catch(e){service.close();throw e;}
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const p=createReviewSandbox({database:process.env.CFP_P2_DB,origin:process.env.CFP_P2_PREVIEW_ORIGIN,revision:process.env.CFP_PREVIEW_REVISION});p.server.listen(Number(process.env.CFP_P2_PORT||4189),'127.0.0.1',()=>console.log(JSON.stringify({mode:'SYNTHETIC PREVIEW / PRODUCTION NO-GO',url:process.env.CFP_P2_PREVIEW_ORIGIN+'/p2',revision:process.env.CFP_PREVIEW_REVISION,accountsFile:p.accountsFile,passwordsPrinted:false})));process.on('SIGTERM',()=>p.server.close(()=>{p.service.close();process.exit(0);}));
}

