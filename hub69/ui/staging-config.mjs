import {readFile,writeFile,mkdir,cp,lstat,symlink,access,readlink} from 'node:fs/promises';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';

const defaultRoot=dirname(fileURLToPath(import.meta.url));
const productionHosts=new Set(['cfp.plus','www.cfp.plus']);

export function validateStaging({url,expectedOrigin,sourceSha}) {
  let target,origin;
  try {target=new URL(url);origin=new URL(expectedOrigin);} catch {throw Error('STAGING_HTTPS_URL_AND_EXACT_ORIGIN_REQUIRED');}
  if(target.protocol!=='https:'||origin.protocol!=='https:'||target.username||target.password||origin.username||origin.password||target.search||target.hash||origin.search||origin.hash||origin.pathname!=='/'||target.origin!==origin.origin||target.pathname!=='/app/'||target.href!==target.origin+'/app/')throw Error('STAGING_HTTPS_URL_AND_EXACT_ORIGIN_REQUIRED');
  if(productionHosts.has(target.hostname)||target.hostname.endsWith('.')||target.hostname==='localhost'||target.hostname.endsWith('.localhost')||target.hostname.endsWith('.local')||target.hostname.includes(':')||/^\d+(?:\.\d+){3}$/.test(target.hostname))throw Error('PUBLIC_STAGING_HOST_REQUIRED_NOT_PRODUCTION_OR_LOOPBACK');
  if(typeof sourceSha!=='string'||! /^[0-9a-f]{40}$/.test(sourceSha))throw Error('EXPECTED_APPLICATION_SOURCE_SHA_REQUIRED');
  return {url:target.href,origin:origin.origin,sourceSha};
}

export async function generateStaging(options,{root=defaultRoot}={}) {
  const approved=validateStaging(options);
  const source=join(root,'app-dist'),web=join(root,'staging-dist'),workspace=join(root,'staging-native');
  await access(join(source,'index.html'));
  for(const path of [source,web,workspace]){
    const stat=await lstat(path).catch(e=>{if(e.code!=='ENOENT')throw e;});
    if(stat?.isSymbolicLink())throw Error('STAGING_BUILD_SYMLINK_DENIED');
  }
  const base=JSON.parse(await readFile(join(root,'capacitor.config.json'),'utf8'));
  if(base.server?.url||base.server?.cleartext!==false)throw Error('DEFAULT_NATIVE_CONFIG_MUST_REMAIN_UNCONFIGURED_AND_TLS_ONLY');
  await mkdir(web,{recursive:true});
  await cp(source,web,{recursive:true,force:true,dereference:false});
  const runtime={mode:'app',approvedStagingOrigin:approved.origin,sourceRevision:approved.sourceSha};
  await writeFile(join(web,'config.js'),'window.HUB69_CONFIG='+JSON.stringify(runtime).replace(/</g,'\\u003c')+';\n');
  const config={...base,webDir:'../staging-dist',server:{url:approved.url,cleartext:false},android:{...base.android,path:'../android',allowMixedContent:false},ios:{...base.ios,path:'../ios'}};
  await mkdir(workspace,{recursive:true});
  await writeFile(join(workspace,'capacitor.config.json'),JSON.stringify(config,null,2)+'\n');
  const pkg=JSON.parse(await readFile(join(root,'package.json'),'utf8'));
  await writeFile(join(workspace,'package.json'),JSON.stringify({name:pkg.name+'-staging-build',private:true,dependencies:pkg.dependencies,devDependencies:pkg.devDependencies},null,2)+'\n');
  const modules=join(workspace,'node_modules');
  const modulesStat=await lstat(modules).catch(e=>{if(e.code!=='ENOENT')throw e;});
  if(!modulesStat)await symlink(join(root,'node_modules'),modules,'dir');
  else if(!modulesStat.isSymbolicLink())throw Error('STAGING_NODE_MODULES_LINK_REQUIRED');
  if(resolve(workspace,await readlink(modules))!==resolve(root,'node_modules'))throw Error('STAGING_NODE_MODULES_LINK_REQUIRED');
  const receipt={status:'CONFIG_CANDIDATE_ONLY',expected_origin:approved.origin,server_url:approved.url,expected_application_source_sha:approved.sourceSha,deployed_source_verified:false,hosting_provisioned:false,governance_approval_verified:false,default_config_unchanged:true,staging_assets:web,build_workspace:workspace,next_command:{cwd:workspace,argv:['../node_modules/.bin/cap','copy','android']},scope:'Existing App/native projects; staging build workspace only, no new database or deployment'};
  await writeFile(join(workspace,'staging-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  return receipt;
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const args=process.argv.slice(2),values={};
  for(let i=0;i<args.length;i+=2){if(!['--url','--expected-origin','--source-sha'].includes(args[i])||!args[i+1])throw Error('EXPECTED_URL_ORIGIN_SOURCE_SHA_ARGUMENTS');values[args[i]]=args[i+1];}
  const receipt=await generateStaging({url:values['--url'],expectedOrigin:values['--expected-origin'],sourceSha:values['--source-sha']});
  console.log(JSON.stringify(receipt,null,2));
}
