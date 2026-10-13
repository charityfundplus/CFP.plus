import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {modules,registry,validateRegistration,safeURL,createState,authorize,transition,validateHSTDN,validateProposal} from './model.mjs';
import {moduleContracts} from './public/office-contracts.js';
import {executeMock} from './adapters.mjs';
import {CoreEngine} from './core/core-engine.mjs';
import {requireKeys} from './core/common.mjs';
export function createApp(){
 const state=createState(),sessions=new Map(),core=new CoreEngine();
 function audit(role,action,result){const prev=state.audit.at(-1)?.hash||'GENESIS';const e={sequence:state.audit.length+1,time:new Date().toISOString(),role,action,result,previousHash:prev};e.hash=createHash('sha256').update(JSON.stringify(e)).digest('hex');state.audit.push(e);}
 const server=http.createServer(async(req,res)=>{
  const send=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(data));};
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'");
  if(!/^(127\.0\.0\.1|localhost)(:\d+)?$/.test(req.headers.host||'')){audit('unknown','host','denied');return send(403,{error:'LOOPBACK_HOST_ONLY'});}
  const url=new URL(req.url,'http://localhost'),path=url.pathname;
  if(!path.startsWith('/api/')){const assets={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/i18n.js':'i18n.js','/office-contracts.js':'office-contracts.js','/core':'core.html','/core.js':'core.js'};if(req.method!=='GET'||!assets[path])return send(404,{error:'Not found'});res.setHeader('Content-Type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':'text/html; charset=utf-8');return res.end(await readFile(new URL('./public/'+assets[path],import.meta.url)));}
  let body={};
  try{
   if(req.method!=='GET'){
    const expected='http://'+req.headers.host;if(req.headers.origin!==expected){audit('unknown','origin','denied');return send(403,{error:'ORIGIN_DENIED'});}
    if(!req.headers['content-type']?.startsWith('application/json')){audit('unknown','content-type','denied');return send(415,{error:'JSON required'});}
    let raw='';for await(const c of req){raw+=c;if(Buffer.byteLength(raw)>8192){audit('unknown','payload','denied');return send(413,{error:'Payload too large'});}}body=JSON.parse(raw||'{}');
   }
   if(path==='/api/session'&&req.method==='POST'){if(!['viewer','editor','reviewer'].includes(body.role))throw Error('Vai trò không hợp lệ');const token=randomUUID();sessions.set(token,{role:body.role,actorId:randomUUID(),expires:Date.now()+3600000});audit(body.role,'demo-session','created');return send(200,{token,role:body.role,demo:true});}
   const s=sessions.get(req.headers.authorization?.replace(/^Bearer /,''));if(!s||s.expires<Date.now()){audit('unknown','session','denied');return send(401,{error:'DEMO_SESSION_REQUIRED'});}const role=s.role;
   if(path.startsWith('/api/core/')){
    const actor={role,id:s.actorId};
    if(req.method==='GET'&&path==='/api/core/state')return send(200,core.snapshot(actor));
    if(req.method!=='POST')return send(404,{error:'Not found'});
    let result;
    switch(path){
     case '/api/core/pairs':requireKeys(body,['templateKey']);result=core.instantiate(actor,body.templateKey);break;
     case '/api/core/tasks':requireKeys(body,['pairKey','kind','title','text','scenario','resource']);{const {pairKey,...input}=body;result=core.createTask(actor,pairKey,input);}break;
     case '/api/core/run':requireKeys(body,['taskKey']);result=await core.runTask(actor,body.taskKey);break;
     case '/api/core/review':requireKeys(body,['taskKey','verdict']);result=core.reviewTask(actor,body.taskKey,body.verdict);break;
     case '/api/core/stop':requireKeys(body,['pairKey']);result=core.stop(actor,body.pairKey);break;
     case '/api/core/recover':requireKeys(body,['pairKey']);result=core.recover(actor,body.pairKey);break;
     case '/api/core/retry':requireKeys(body,['taskKey']);result=core.retry(actor,body.taskKey);break;
     case '/api/core/upgrade':requireKeys(body,['target']);result=core.upgrade(actor,body.target);break;
     case '/api/core/rollback':requireKeys(body,[]);result=core.rollback(actor);break;
     default:return send(404,{error:'Not found'});
    }
    audit(role,path,'core-sandbox');return send(200,result);
   }
   if(req.method==='GET'&&path==='/api/state')return send(200,{...state,modules,moduleContracts,registry,role,mode:'SANDBOX • PRODUCTION NO-GO'});
   if(req.method==='GET'&&path==='/api/export')return send(200,{...state,mode:'SYNTHETIC DRAFT',identity:{id:null,did:null,canonical:null}});
   if(['/api/payment','/api/integrations/connect','/api/identity/bind'].includes(path)){audit(role,path,'blocked');return send(403,{error:'Human Governance required. Production NO-GO.'});}
   if(req.method==='POST'&&path==='/api/registrations'){
    if(!authorize(role,'write')){audit(role,'register','denied');return send(403,{error:'Không có quyền chỉnh sửa'});}const r=validateRegistration(body);if(state.registrations.some(x=>x.developer===r.developer&&x.name.trim().toLocaleLowerCase()===r.name.trim().toLocaleLowerCase())){audit(role,'register','duplicate');return send(409,{error:'DUPLICATE_PROFILE'});}r.key=randomUUID();state.registrations.push(r);audit(role,'register','pending');return send(201,r);
   }
   if(req.method==='POST'&&path==='/api/proposals'){
    if(!authorize(role,'write')){audit(role,'proposal','denied');return send(403,{error:'Write access denied'});}
    const r=validateProposal(body,state);r.key=randomUUID();state.proposals.push(r);audit(role,'proposal:'+r.key,'pending');return send(201,r);
   }
   if(req.method==='POST'&&path==='/api/hstdn'){
    if(!authorize(role,'write')){audit(role,'hstdn','denied');return send(403,{error:'Không có quyền chỉnh sửa'});}
    const r=validateHSTDN(body,state);r.key=randomUUID();state.hstdn.push(r);audit(role,'hstdn:'+r.key,'pending');return send(201,r);
   }
   if(req.method==='POST'&&path==='/api/adapters/mock'){
    if(!authorize(role,'write')){audit(role,'mock','denied');return send(403,{error:'Không có quyền chỉnh sửa'});}
    const receipt=executeMock(body);audit(role,'mock:'+receipt.provider,'mock-only');return send(200,receipt);
   }
   if(req.method==='POST'&&path==='/api/records'){
    if(!authorize(role,'write')){audit(role,'create','denied');return send(403,{error:'Không có quyền chỉnh sửa'});}
    if(Object.keys(body).some(k=>!['module','title','evidence','synthetic','kind','maturity','scope','officeRef','hstdnRef'].includes(k))||!Number.isInteger(body.module)||body.module<0||body.module>=12||typeof body.title!=='string'||!body.title.trim()||body.title.length>300||body.synthetic!==true||(body.evidence&&!safeURL(body.evidence)))throw Error('Record không hợp lệ; chỉ dữ liệu giả lập và HTTPS.');
    if(body.kind&&!['product','service','record'].includes(body.kind))throw Error('CATALOG: invalid kind');
    if(body.kind==='product'&&(!['concept','research','prototype'].includes(body.maturity)||body.module!==2))throw Error('CATALOG: research maturity required');
    if(body.kind==='service'&&(body.module!==3||typeof body.scope!=='string'||!body.scope.trim()||body.scope.length>300))throw Error('CATALOG: service scope required');
    if(body.officeRef&&!state.registrations.some(r=>r.key===body.officeRef))throw Error('CATALOG: unknown office');
    if(body.hstdnRef&&!state.hstdn.some(r=>r.key===body.hstdnRef))throw Error('CATALOG: unknown HSTDN');
    if(body.officeRef&&body.hstdnRef&&!state.hstdn.find(r=>r.key===body.hstdnRef).members.includes(body.officeRef))throw Error('CATALOG: office not member of HSTDN');
    const r={officeRef:body.officeRef||null,hstdnRef:body.hstdnRef||null,kind:body.kind||'record',maturity:body.maturity||null,scope:body.scope||null,key:randomUUID(),module:body.module,title:body.title,evidence:body.evidence||'',synthetic:true,status:'DRAFT'};state.records.push(r);audit(role,'create:'+r.key,'ok');return send(201,r);
   }
   if(req.method==='POST'&&path==='/api/transition'){
    if(!['submit','review'].includes(body.action))throw Error('Action invalid');if(!authorize(role,body.action==='review'?'review':'write')){audit(role,'transition','denied');return send(403,{error:'Không có quyền review'});}
    const r=state.records.find(r=>r.key===body.key);if(!r) return send(404,{error:'Record missing'});r.status=transition(r,body.action,body.evidence||r.evidence);if(body.evidence)r.evidence=body.evidence;audit(role,body.action+':'+r.key,r.status);return send(200,r);
   }
   return send(404,{error:'Not found'});
  }catch(e){audit('unknown',path,'invalid');send(e.message==='PERMISSION_DENIED'?403:400,{error:e.message});}
 });return {server,state,core};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const {server}=createApp();server.listen(Number(process.env.PORT||4173),'127.0.0.1',()=>console.log('CFP+ Sandbox: http://127.0.0.1:'+server.address().port));}
