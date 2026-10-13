import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {modules,registry,validateRegistration,safeURL,createState,authorize,transition} from './model.mjs';
export function createApp(){
 const state=createState(),sessions=new Map();
 function audit(role,action,result){const prev=state.audit.at(-1)?.hash||'GENESIS';const e={sequence:state.audit.length+1,time:new Date().toISOString(),role,action,result,previousHash:prev};e.hash=createHash('sha256').update(JSON.stringify(e)).digest('hex');state.audit.push(e);}
 const server=http.createServer(async(req,res)=>{
  const send=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(data));};
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'");
  const url=new URL(req.url,'http://localhost'),path=url.pathname;
  if(!path.startsWith('/api/')){const assets={'/':'index.html','/app.js':'app.js','/style.css':'style.css'};if(req.method!=='GET'||!assets[path])return send(404,{error:'Not found'});res.setHeader('Content-Type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':'text/html; charset=utf-8');return res.end(await readFile(new URL('./public/'+assets[path],import.meta.url)));}
  let body={};
  try{
   if(req.method!=='GET'){
    const expected='http://'+req.headers.host;if(req.headers.origin!==expected)return send(403,{error:'Origin bị từ chối'});
    if(!req.headers['content-type']?.startsWith('application/json'))return send(415,{error:'JSON required'});
    let raw='';for await(const c of req){raw+=c;if(Buffer.byteLength(raw)>8192)return send(413,{error:'Payload too large'});}body=JSON.parse(raw||'{}');
   }
   if(path==='/api/session'&&req.method==='POST'){if(!['viewer','editor','reviewer'].includes(body.role))throw Error('Vai trò không hợp lệ');const token=randomUUID();sessions.set(token,{role:body.role,expires:Date.now()+3600000});audit(body.role,'demo-session','created');return send(200,{token,role:body.role,demo:true});}
   const s=sessions.get(req.headers.authorization?.replace(/^Bearer /,''));if(!s||s.expires<Date.now())return send(401,{error:'Cần phiên demo'});const role=s.role;
   if(req.method==='GET'&&path==='/api/state')return send(200,{...state,modules,registry,role,mode:'SANDBOX • PRODUCTION NO-GO'});
   if(req.method==='GET'&&path==='/api/export')return send(200,{...state,mode:'SYNTHETIC DRAFT',identity:{id:null,did:null,canonical:null}});
   if(['/api/payment','/api/integrations/connect','/api/identity/bind'].includes(path)){audit(role,path,'blocked');return send(403,{error:'Human Governance required. Production NO-GO.'});}
   if(req.method==='POST'&&path==='/api/registrations'){
    if(!authorize(role,'write')){audit(role,'register','denied');return send(403,{error:'Không có quyền chỉnh sửa'});}const r=validateRegistration(body);r.key=randomUUID();state.registrations.push(r);audit(role,'register','pending');return send(201,r);
   }
   if(req.method==='POST'&&path==='/api/records'){
    if(!authorize(role,'write')){audit(role,'create','denied');return send(403,{error:'Không có quyền chỉnh sửa'});}
    if(Object.keys(body).some(k=>!['module','title','evidence','synthetic'].includes(k))||!Number.isInteger(body.module)||body.module<0||body.module>=12||typeof body.title!=='string'||!body.title.trim()||body.title.length>300||body.synthetic!==true||(body.evidence&&!safeURL(body.evidence)))throw Error('Record không hợp lệ; chỉ dữ liệu giả lập và HTTPS.');
    const r={key:randomUUID(),module:body.module,title:body.title,evidence:body.evidence||'',synthetic:true,status:'DRAFT'};state.records.push(r);audit(role,'create:'+r.key,'ok');return send(201,r);
   }
   if(req.method==='POST'&&path==='/api/transition'){
    if(!['submit','review'].includes(body.action))throw Error('Action invalid');if(!authorize(role,body.action==='review'?'review':'write')){audit(role,'transition','denied');return send(403,{error:'Không có quyền review'});}
    const r=state.records.find(r=>r.key===body.key);if(!r) return send(404,{error:'Record missing'});r.status=transition(r,body.action,body.evidence||r.evidence);if(body.evidence)r.evidence=body.evidence;audit(role,body.action+':'+r.key,r.status);return send(200,r);
   }
   return send(404,{error:'Not found'});
  }catch(e){audit('unknown',path,'invalid');send(400,{error:e.message});}
 });return {server,state};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const {server}=createApp();server.listen(Number(process.env.PORT||4173),'127.0.0.1',()=>console.log('CFP+ Sandbox: http://127.0.0.1:'+server.address().port));}
