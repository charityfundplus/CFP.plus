import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import https from 'node:https';
import {createLocalHTTPSPreview} from '../scripts/local-https-preview.mjs';
import {registry} from '../model.mjs';

test('New local HTTPS transport: trusted TLS, secure session, exact Host/Origin and read-only viewer',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'cfp-local-tls-'));
 const certificate=join(dir,'cert.pem'),key=join(dir,'key.pem');let p;
 try{
  execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes','-keyout',key,'-out',certificate,'-days','1','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'],{stdio:'ignore'});
  // Allocate a loopback port without exposing a wildcard listener.
  const probe=https.createServer();await new Promise(r=>probe.listen(0,'127.0.0.1',r));const port=probe.address().port;await new Promise(r=>probe.close(r));
  const origin='https://localhost:'+port,revision='b75b780eb64430355f0b51a4b58b9e5269e0db43';
  assert.throws(()=>createLocalHTTPSPreview({database:join(dir,'bad.db'),origin:'https://public.example',revision,certificate,key}),/LOCAL_HTTPS_ORIGIN_REQUIRED/);
  p=createLocalHTTPSPreview({database:join(dir,'state.db'),origin,revision,certificate,key});
  await new Promise((resolve,reject)=>{p.server.once('error',reject);p.server.listen(port,'127.0.0.1',resolve);});
  const req=(path,{method='GET',headers={},body}={})=>new Promise((resolve,reject)=>{
   const r=https.request({hostname:'127.0.0.1',servername:'localhost',port,path,method,ca:readFileSync(certificate),headers:{Host:'localhost:'+port,...headers}},res=>{let raw='';res.on('data',c=>raw+=c);res.on('end',()=>resolve({status:res.statusCode,headers:res.headers,raw}));});r.on('error',reject);if(body)r.write(JSON.stringify(body));r.end();
  });
  const page=await req('/p2');assert.equal(page.status,200);assert.equal(page.headers['x-cfp-preview-revision'],revision);assert.equal(page.headers['x-robots-tag'],'noindex, nofollow');assert.match(page.raw,/id="p2-hstdn-form"/);assert.match(page.raw,/id="p2-lesson-form"/);
  const host=await req('/p2',{headers:{Host:'127.0.0.1:'+port}});assert.equal(host.status,403);
  const accounts=JSON.parse(readFileSync(p.accountsFile)).accounts,viewer=accounts.find(x=>x.role==='viewer');
  const wrongOrigin=await req('/api/session',{method:'POST',headers:{Origin:'http://localhost:'+port,'Content-Type':'application/json'},body:{id:viewer.id,password:viewer.password}});assert.equal(wrongOrigin.status,403);
  const login=await req('/api/session',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:{id:viewer.id,password:viewer.password}});assert.equal(login.status,200);const cookie=login.headers['set-cookie'][0];assert.match(cookie,/Secure/);assert.match(cookie,/HttpOnly/);assert.match(cookie,/SameSite=Strict/);assert(!login.raw.includes(viewer.password));
  const state=await req('/api/core/state',{headers:{Cookie:cookie.split(';')[0]}});assert.equal(state.status,200);assert.equal(JSON.parse(state.raw).auth.role,'viewer');
  const denied=await req('/api/core/pairs',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json',Cookie:cookie.split(';')[0]},body:{templateKey:'office12'}});assert.equal(denied.status,403);
  assert(!page.raw.includes(viewer.password));assert(!state.raw.includes(viewer.password));
  // One scoped integration rehearsal over the NEW HTTPS transport, not a full
  // repeat of the already accepted Core/training suites.
  const session=async role=>{const a=accounts.find(x=>x.role===role),r=await req('/api/session',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:{id:a.id,password:a.password}});assert.equal(r.status,200);return r.headers['set-cookie'][0].split(';')[0];};
  const editorCookie=await session('editor'),reviewerCookie=await session('reviewer');
  const post=async(path,body,cookie=editorCookie)=>{const r=await req(path,{method:'POST',headers:{Origin:origin,'Content-Type':'application/json',Cookie:cookie},body});assert.equal(r.status,200,r.raw);return JSON.parse(r.raw);};
  const pairKey='hub69-content-demo',source='https://github.com/charityfundplus/CFP.plus/issues/130',developer=registry.entities.find(x=>x.type==='developer'&&!registry.blockedCountries.includes(x.ai_country_id));
  const profile=await post('/api/core/office-create',{pairKey,kind:'profile',input:{name:'Synthetic HTTPS Research SI',country:developer.ai_country_id,developer:developer.id,source,identityEvidence:source,synthetic:true}});
  assert.equal(profile.id,null);assert.equal(profile.did,null);assert.equal(profile.parent,null);assert.equal(profile.canonical,null);
  const hstdn=await post('/api/core/office-create',{pairKey,kind:'hstdn',input:{name:'Synthetic HTTPS HSTDN',jurisdiction:'Synthetic only',members:[profile.key],relation_type:'proposed-collaboration',source,synthetic:true}});assert.equal(hstdn.legalRelationshipVerification,'NOT VERIFIED');
  const learn=await post('/api/core/learn',{pairKey,lesson:'security'});assert.equal(learn.privilegeChange,false);
  const task=await post('/api/core/tasks',{pairKey,kind:'training-drill',title:'HTTPS supervised sample',text:'Synthetic only',scenario:'normal',resource:'website-demo',idempotencyKey:'https-transport-review'});
  await post('/api/core/run',{taskKey:task.key});await post('/api/core/feedback',{taskKey:task.key,feedback:'Synthetic TLS transport rehearsal; no competence or authority claim'});
  const reviewed=await post('/api/core/review',{taskKey:task.key,verdict:'acknowledge-draft'},reviewerCookie);assert.equal(reviewed.status,'REVIEWED DRAFT');assert.equal(p.service.verify().sequence>0,true);
 }finally{await p?.close();rmSync(dir,{recursive:true,force:true});}
});
