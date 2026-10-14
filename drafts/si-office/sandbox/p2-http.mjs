import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {P2Sandbox} from './p2-service.mjs';
import {executionProvenance} from '../scripts/build-provenance.mjs';
const sourceRoot=fileURLToPath(new URL('../',import.meta.url));
const commands={'catalog-search':'catalogSearch','commerce-state':'commerceState','inquiry-create':'inquiryCreate','inquiry-match':'inquiryMatch','opportunity-create':'opportunityCreate','opportunity-status':'opportunityStatus',pairs:'instantiate',tasks:'createTask',run:'runTask',review:'reviewTask',stop:'stop',recover:'recover',retry:'retry',upgrade:'upgrade',rollback:'rollback',learn:'learn',feedback:'feedback',office:'officeSnapshot','office-create':'officeCreate','assessment-submit':'prepareAssessment','assessment-review':'reviewAssessment'};
const fields={'catalog-search':['pairKey','input'],'commerce-state':['pairKey'],'inquiry-create':['pairKey','input','idempotencyKey'],'inquiry-match':['pairKey','input'],'opportunity-create':['pairKey','input','idempotencyKey'],'opportunity-status':['pairKey','input'],pairs:['templateKey'],tasks:['pairKey','kind','title','text','scenario','resource','idempotencyKey'],run:['taskKey'],review:['taskKey','verdict'],stop:['pairKey'],recover:['pairKey'],retry:['taskKey'],upgrade:['target'],rollback:[],learn:['pairKey','lesson'],feedback:['taskKey','feedback'],office:['pairKey'],'office-create':['pairKey','kind','input'],'assessment-submit':['taskKey','input'],'assessment-review':['assessmentKey','input']};
export function createP2HTTP({service,previewOrigin=null}){
 let preview=null;if(previewOrigin){preview=new URL(previewOrigin);if(preview.protocol!=='https:'||preview.username||preview.password||preview.pathname!=='/'||preview.search||preview.hash)throw Error('PREVIEW_ORIGIN_INVALID');}
 const startupProvenance=executionProvenance(sourceRoot);
 const loginWindows=new Map();
 const server=http.createServer(async(req,res)=>{
  const send=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(data));};
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'");
  const previewRequest=!!preview&&req.headers.host===preview.host;const expectedOrigin=previewRequest?preview.origin:'http://'+req.headers.host;const secureCookie=previewRequest?'; Secure':'';
  if(!previewRequest&&!/^(localhost|127\.0\.0\.1)(:\d+)?$/.test(req.headers.host||'')){try{service.httpDenial('HOST_DENIED');}catch{}return send(403,{error:'LOOPBACK_ONLY'});}
  const path=new URL(req.url,'http://localhost').pathname;
  try{
   const assets={'/':'p2.html','/p2':'p2.html','/core.js':'core.js','/p2-office.js':'p2-office.js','/office-intake.js':'office-intake.js','/assessment-export.js':'assessment-export.js','/commercial-office.js':'commercial-office.js','/style.css':'style.css'};
   if(!path.startsWith('/api/')){if(req.method!=='GET'||!assets[path])return send(404,{error:'NOT_FOUND'});res.setHeader('Content-Type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':'text/html');return res.end(await readFile(new URL('../public/'+assets[path],import.meta.url)));}
   if(path==='/api/curriculum'&&req.method==='GET')return send(200,JSON.parse(await readFile(new URL('../configs/training-basic-v1.json',import.meta.url),'utf8')));
   let body={};if(req.method==='POST'){
    if(req.headers.origin!==expectedOrigin){service.httpDenial('ORIGIN_DENIED');return send(403,{error:'ORIGIN_DENIED'});}
    if(!req.headers['content-type']?.startsWith('application/json'))return send(415,{error:'JSON_REQUIRED'});
    const maxBytes=['/api/core/office-create','/api/core/assessment-submit'].includes(path)?32768:8192;
    let raw='';for await(const c of req){raw+=c;if(Buffer.byteLength(raw)>maxBytes)return send(413,{error:'PAYLOAD_TOO_LARGE'});}body=JSON.parse(raw||'{}');if(!body||typeof body!=='object'||Array.isArray(body))return send(400,{error:'INVALID_FIELDS'});
   }else if(req.method!=='GET')return send(405,{error:'METHOD_DENIED'});
   const exact=keys=>{if(Object.keys(body).some(k=>!keys.includes(k)))throw Error('INVALID_FIELDS');};
   if(path==='/api/session'&&req.method==='POST'){
    exact(['id','password']);const key=req.socket?.remoteAddress||'local';let w=loginWindows.get(key);if(!w||Date.now()-w.time>60000){w={time:Date.now(),count:0};loginWindows.set(key,w);}if(++w.count>30)return send(429,{error:'LOGIN_RATE_LIMIT'});
    const token=service.login(body.id,body.password);res.setHeader('Set-Cookie','cfp_p2='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=900'+secureCookie);return send(200,{auth:service.context(token),synthetic:true});
   }
   const cookies=String(req.headers.cookie||'').split(';').map(x=>x.trim());const matches=cookies.filter(x=>x.startsWith('cfp_p2='));if(matches.length!==1)throw Error('AUTH_DENIED');const token=matches[0].slice(7);const auth=service.context(token);
   if(path==='/api/logout'&&req.method==='POST'){exact([]);service.revoke(token);res.setHeader('Set-Cookie','cfp_p2=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'+secureCookie);return send(200,{loggedOut:true});}
   if(path==='/api/core/state'&&req.method==='GET'){const result=await service.execute(token,'snapshot');const current=executionProvenance(sourceRoot);result.buildProvenance=startupProvenance.verified&&current.verified&&startupProvenance.manifestSha256===current.manifestSha256?current:{verified:false,revision:null,manifest:null,manifestSha256:null,finding:'EXECUTION_SOURCE_UNVERIFIED_OR_CHANGED',authorityVerified:false,activationAllowed:false};return send(200,result);}
   const name=path.startsWith('/api/core/')?path.slice(10):'';if(req.method!=='POST'||!commands[name])return send(404,{error:'NOT_FOUND'});exact(fields[name]);let args=body,options={};if(['inquiry-create','opportunity-create'].includes(name)){const {idempotencyKey,...payload}=body;args=payload;options={idempotencyKey};}if(name==='tasks'){const {pairKey,idempotencyKey,...input}=body;args={pairKey,input};options={idempotencyKey};}
   return send(200,await service.execute(token,commands[name],args,options));
  }catch(e){try{service.httpDenial(/AUTH_DENIED/.test(e.message)?'AUTH_DENIED':'REQUEST_DENIED');}catch{}const code=/AUTH_DENIED/.test(e.message)?401:/PERMISSION|SCOPE_DENIED|MAINTAINER|INDEPENDENT/.test(e.message)?403:/BUSY|NOT_READY|CONFLICT/.test(e.message)?409:/INTEGRITY|STORAGE|SQLITE/.test(e.message)?503:400;return send(code,{error:code===503?'STORAGE_UNAVAILABLE':e.message});}
 });return server;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 if(!process.env.CFP_P2_DB)throw Error('CFP_P2_DB_REQUIRED: provision synthetic accounts locally first');
 const service=new P2Sandbox(process.env.CFP_P2_DB),server=createP2HTTP({service,previewOrigin:process.env.CFP_P2_PREVIEW_ORIGIN||null});server.listen(Number(process.env.CFP_P2_PORT||4174),'127.0.0.1');process.on('SIGTERM',()=>server.close(()=>{service.close();process.exit(0);}));
}

