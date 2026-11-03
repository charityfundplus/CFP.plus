// Temporary loopback-only integrated Core/UI fixture. Never a deployment.
import {mkdtempSync,rmSync,readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {execFileSync,spawn} from 'node:child_process';
const source=resolve(process.env.CFP_COMMERCE_CORE_SOURCE||'');
if(!process.env.CFP_COMMERCE_CORE_SOURCE)throw Error('CFP_COMMERCE_CORE_SOURCE_REQUIRED');
const office=join(source,'drafts/si-office'),ui=fileURLToPath(new URL('../',import.meta.url));
const {P2Sandbox}=await import(pathToFileURL(join(office,'sandbox/p2-service.mjs')));
const {createP2HTTP}=await import(pathToFileURL(join(office,'sandbox/p2-http.mjs')));
const {registry}=await import(pathToFileURL(join(office,'model.mjs')));
const revision=execFileSync('git',['-C',source,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const dir=mkdtempSync(join(tmpdir(),'cfp-browser-core-')),service=new P2Sandbox(join(dir,'state.db'),{registrySource:{root:source,revision}});
const pairKey='hub69-content-demo',password='Synthetic-Browser-Only';
service.provision({id:'editor',password,role:'editor',workspace:'browser-fixture',pairs:[pairKey]});
const token=service.login('editor',password),developer=registry.entities.find(r=>r.type==='developer'&&!registry.blockedCountries.includes(r.ai_country_id));
const profile=await service.execute(token,'officeCreate',{pairKey,kind:'profile',input:{name:'Synthetic browser supplier',country:developer.ai_country_id,developer:developer.id,source:'https://example.invalid/private',identityEvidence:'https://example.invalid/private',synthetic:true}});
for(const [kind,name] of [['product','Core learning kit'],['service','Core training service']])await service.execute(token,'officeCreate',{pairKey,kind,input:{name,source:'https://example.invalid/private',officeRef:profile.key,scope:'Synthetic test service',maturity:'prototype',synthetic:true}});
const server=createP2HTTP({service}),handler=server.listeners('request')[0];server.removeAllListeners('request');
const assets=new Set(['index.html','design-tokens.css','style.css','design-system.css','design-tokens.json','manifest.webmanifest','icon-192.png','icon-512.png','offline.html','sw.js','pwa.js','config.js','registry.js','training-data.js','model.js','workspace.js','hstdn-review.js','commerce.js','explore.js','p0.js','core-binding.js','training.js','app.js']);
server.on('request',(req,res)=>{
  const url=new URL(req.url,'http://localhost'),name=url.pathname.slice('/hub69/'.length);
  if(req.method==='GET'&&url.pathname.startsWith('/hub69/')&&assets.has(name)){
    const mime=name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':name.endsWith('.png')?'image/png':name.endsWith('.webmanifest')?'application/manifest+json':name.endsWith('.json')?'application/json':'text/html';
    res.writeHead(200,{'Content-Type':mime,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(readFileSync(join(ui,'core-dist',name)));return;
  }
  handler(req,res);
});
try{
  await new Promise((done,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',done);});
  const origin='http://127.0.0.1:'+server.address().port;
  mkdirSync(join(ui,'evidence/commerce'),{recursive:true});writeFileSync(join(ui,'evidence/commerce/core-source.json'),JSON.stringify({revision,registryWrites:0,mode:'Temporary loopback fixture; real Core/Registry source and synthetic Office drafts'},null,2)+'\n');
  if(process.env.CFP_BROWSER_SERVER_ONLY==='1'){writeFileSync(join(ui,'evidence/commerce/loopback-origin.txt'),origin);console.log('LOOPBACK_TEST_READY '+origin);await new Promise(done=>process.once('SIGTERM',done));}
  else await new Promise((done,reject)=>{const child=spawn('python',[join(ui,'integration/core-browser.py'),origin],{stdio:'inherit'});const timer=setTimeout(()=>{child.kill('SIGTERM');reject(Error('BROWSER_TIMEOUT'));},60000);child.on('error',error=>{clearTimeout(timer);reject(error);});child.on('exit',code=>{clearTimeout(timer);code===0?done():reject(Error('BROWSER_TEST_FAILED '+code));});});
}finally{server.closeAllConnections();await new Promise(done=>server.close(done));service.close();rmSync(dir,{recursive:true,force:true});}
