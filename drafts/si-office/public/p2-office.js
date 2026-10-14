import {scopedAssessmentEvidence} from './assessment-export.js';
const $=s=>document.querySelector(s);let state,office;const el=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
async function api(command,args){const r=await fetch('/api/core/'+command,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(args)});const v=await r.json();if(!r.ok)throw Error(v.error);return v;}
const pair=()=>$('#core-pair-select').value;
function fill(select,rows,label){const old=select.value;select.replaceChildren(...rows.map(r=>{const n=el('option',label(r));n.value=r.key??r.id??'';return n;}));if(rows.some(r=>(r.key??r.id??'')===old))select.value=old;}
function developers(){fill($('#p2-developer'),office.registry.entities.filter(d=>d.type==='developer'&&d.ai_country_id===$('#p2-country').value),r=>r.name||r.id);}
function showLesson(){if(!state?.learning.program)return;const lang=$('#core-language').value,row=state.learning.program.basic.lessons.find(l=>l.key===$('#p2-lesson-form [name=lesson]').value);$('#p2-lesson-content').replaceChildren(el('h3',row.title[lang]),...row.steps[lang].map(t=>el('p',t)),el('p','Evidence: '+row.expectedEvidence));}
async function refresh(){if(!state||!pair())return;const requested=pair(),next=await api('office',{pairKey:requested});if(pair()!==requested)return;office=next;const lang=$('#core-language').value;
 $('#p2-module-contracts').replaceChildren(...office.moduleContracts.map(c=>{const a=el('article','');a.append(el('h3',(c.index+1)+' • '+office.modules[c.index]),el('p',c.function[lang]),el('p','Input: '+c.inputs[lang]),el('p','Output: '+c.outputs[lang]),el('p',c.access[lang]+' • '+c.verification));return a;}));
 fill($('#p2-country'),office.registry.countries.filter(c=>!office.registry.blockedCountries.includes(c.id)&&office.registry.entities.some(d=>d.type==='developer'&&d.ai_country_id===c.id)),r=>r.label||r.name||r.id);developers();
 fill($('#p2-profile-member'),office.registrations,r=>r.name);fill($('#p2-catalog-office'),office.registrations,r=>r.name);catalogHSTDN();
 $('#p2-office-records').replaceChildren(...[...office.registrations,...office.hstdn,...office.records.filter(r=>r.kind)].map(r=>{const a=el('article','');a.append(el('strong',r.name),el('p',(r.kind||'profile/HSTDN')+' • '+r.status+' • '+(r.legalRelationshipVerification||'NOT VERIFIED')));return a;}));
 const done=state.tasks.filter(t=>['AWAITING HUMAN REVIEW','REVIEWED DRAFT','REJECTED DRAFT','BLOCKED','FAILED','INTERRUPTED'].includes(t.status)&&t.pairKey===pair());fill($('#p2-feedback-task'),done,r=>r.title+' • '+r.status);
 fill($('#p2-exercise'),state.learning.program.exercises.map(e=>({...e,key:e.localKey})),r=>String(r.officeModule+1)+' • '+r.name);$('#p2-load-exercise').disabled=state.auth.role==='viewer';showLesson();$('#p2-learning-evidence').textContent=JSON.stringify({learning:state.learning.observations.filter(x=>x.pairKey===pair()),practice:state.learning.evaluations.filter(x=>x.pairKey===pair()),feedback:state.learning.feedback.filter(x=>x.pairKey===pair()),autoPromotion:false},null,2);
 showJourney(lang);
 for(const f of ['p2-lesson-form','p2-feedback-form','p2-profile-form','p2-hstdn-form','p2-catalog-form'])$('#'+f+' button').disabled=state.auth.role==='viewer';
}
function catalogHSTDN(){fill($('#p2-catalog-hstdn'),[{key:'',name:'None / Không liên kết'},...office.hstdn.filter(h=>h.members.includes($('#p2-catalog-office').value))],r=>r.name);}
async function save(fn){try{await fn();$('#p2-office-status').textContent='SAVED SYNTHETIC EVIDENCE / ĐÃ LƯU';document.dispatchEvent(new Event('p2-refresh'));}catch(e){$('#p2-office-status').textContent=e.message;}}
document.addEventListener('p2-state',e=>{state=e.detail;refresh().catch(e=>$('#p2-office-status').textContent=e.message);});$('#core-pair-select').addEventListener('change',()=>refresh().catch(e=>$('#p2-office-status').textContent=e.message));$('#core-language').addEventListener('change',()=>refresh().catch(e=>$('#p2-office-status').textContent=e.message));$('#p2-country').onchange=developers;$('#p2-catalog-office').onchange=catalogHSTDN;
$('#p2-lesson-form').onsubmit=e=>{e.preventDefault();save(()=>api('learn',{pairKey:pair(),lesson:new FormData(e.target).get('lesson')}));};
$('#p2-feedback-form').onsubmit=e=>{e.preventDefault();save(()=>api('feedback',Object.fromEntries(new FormData(e.target))));};
$('#p2-profile-form').onsubmit=e=>{e.preventDefault();const input=Object.fromEntries(new FormData(e.target));input.synthetic=true;input.identityEvidence=input.source;save(()=>api('office-create',{pairKey:pair(),kind:'profile',input}));};
$('#p2-hstdn-form').onsubmit=e=>{e.preventDefault();const {member,...input}=Object.fromEntries(new FormData(e.target));Object.assign(input,{members:[member],synthetic:true});save(()=>api('office-create',{pairKey:pair(),kind:'hstdn',input}));};
$('#p2-catalog-form').onsubmit=e=>{e.preventDefault();const {kind,...input}=Object.fromEntries(new FormData(e.target));Object.assign(input,{maturity:'research',synthetic:true});save(()=>api('office-create',{pairKey:pair(),kind,input}));};

$('#p2-lesson-form [name=lesson]').addEventListener('change',showLesson);

$('#p2-load-exercise').onclick=()=>{const exercise=state.learning.program.exercises.find(e=>e.localKey===$('#p2-exercise').value);if(!state.pairs.some(p=>p.key===exercise.pairTemplate)){ $('#p2-office-status').textContent='Pair not available in authorized scope';return; }$('#core-pair-select').value=exercise.pairTemplate;$('#core-pair-select').dispatchEvent(new Event('change'));$('#core-kind').value=exercise.task.kind;for(const name of ['title','text','scenario'])$('#core-task-form [name='+name+']').value=exercise.task[name];$('#core-task-form').scrollIntoView({behavior:'smooth'});};

// Display-only progress from retained evidence. This never changes permissions.
function journeyEvidence(snapshot=state,pairKey=pair()){
 const subject=snapshot.auth.id,program=snapshot.learning.program;
 const lessons=program.basic.lessons.filter(l=>snapshot.learning.observations.some(o=>o.subject===subject&&o.pairKey===pairKey&&o.lesson===l.key)).map(l=>l.key);
 const exercises=program.exercises.map(e=>{
  const tasks=snapshot.tasks.filter(t=>t.owner===subject&&t.pairKey===pairKey&&t.pairKey===e.pairTemplate&&t.kind===e.task.kind&&t.title===e.task.title&&t.text===e.task.text&&t.scenario===e.task.scenario&&t.resource===e.task.resource);
  const reviewed=tasks.find(t=>t.status==='REVIEWED DRAFT'&&t.review?.actor!==subject&&t.review?.verdict==='acknowledge-draft'&&t.checks.length===18&&t.checks.every(c=>c.pass===true||c.result==='PASS')&&snapshot.learning.feedback.some(f=>f.subject===subject&&f.taskKey===t.key&&f.outputHash===t.proposalHash));
  return {exercise:e.localKey,taskKey:reviewed?.key||null,status:reviewed?'REVIEWED SYNTHETIC DRAFT':'EVIDENCE PENDING'};
 });
 return {subject,pairKey,lessons,exercises,basicDraftReady:lessons.length===program.basic.lessons.length&&exercises.every(e=>e.taskKey),advancedStatus:'CURRICULUM DRAFT / NOT ASSESSED',privilegeChange:false,certification:false};
}
function showJourney(lang){
 const j=journeyEvidence(),vi=lang==='vi';
 $('#p2-journey').replaceChildren(el('p',vi?`Đã ghi nhận học: ${j.lessons.length}/5. Bài tập có phản hồi và reviewer riêng: ${j.exercises.filter(e=>e.taskKey).length}/12.`:`Study records: ${j.lessons.length}/5. Exercises with feedback and a separate reviewer: ${j.exercises.filter(e=>e.taskKey).length}/12.`),el('p',j.basicDraftReady?(vi?'Đủ bằng chứng nháp cơ bản để đề nghị đánh giá nâng cao.':'Basic draft evidence ready for an advanced assessment request.'):(vi?'Tiếp tục học, thực hành, phản hồi và review riêng.':'Continue study, practice, feedback and separate review.')),el('p',vi?'Nhận nhiệm vụ theo quyền server đã cấp; lưu bằng chứng trước bàn giao. Nâng cao chưa được đánh giá; không tự cấp quyền.':'Receive tasks within existing server grants; export evidence before handoff. Advanced competence is unassessed; no automatic grants.'));
 $('#p2-advanced').replaceChildren(...state.learning.program.advanced.map(a=>{const n=el('article','');n.append(el('h4',a.title?.[lang]||a.key),el('p',a.scope),...((a.steps?.[lang])||[]).map(s=>el('p',s)),el('p',a.status));return n;}));
}
$('#p2-export-evidence').onclick=async()=>{
 try{
  // Fetch current server-filtered state; never export cookies or account secrets.
  if(!state?.auth)throw Error('AUTHENTICATED STATE REQUIRED');
  const exportScope={pairKey:pair(),subject:state.auth.id,workspace:state.auth.workspace};
  const assertScope=auth=>{if(pair()!==exportScope.pairKey||state?.auth.id!==exportScope.subject||state?.auth.workspace!==exportScope.workspace||auth.id!==exportScope.subject||auth.workspace!==exportScope.workspace)throw Error('EXPORT_SCOPE_CHANGED');};
  const response=await fetch('/api/core/state');if(!response.ok)throw Error('AUTHENTICATED STATE REQUIRED');const snapshot=await response.json();assertScope(snapshot.auth);
  const j=journeyEvidence(snapshot,exportScope.pairKey),tasks=snapshot.tasks.filter(t=>t.pairKey===j.pairKey&&t.owner===j.subject),keys=new Set(tasks.map(t=>t.key));
  const scopedOffice=await api('office',{pairKey:j.pairKey});const ownApplications=scopedOffice.registrations.filter(r=>r.subject===j.subject),ownRefs=new Set(ownApplications.map(r=>r.key));
  const commercial=await api('commerce-state',{pairKey:j.pairKey});
  const authReadback=await fetch('/api/core/state');if(!authReadback.ok)throw Error('AUTHENTICATED STATE REQUIRED');const finalSnapshot=await authReadback.json();assertScope(finalSnapshot.auth);if(JSON.stringify(finalSnapshot.buildProvenance)!==JSON.stringify(snapshot.buildProvenance))throw Error('EXPORT_BUILD_CHANGED');
  const commerce={synthetic:true,approval:'NOT AUTHORIZED',inquiries:commercial.inquiries.filter(r=>r.subject===j.subject),opportunities:commercial.opportunities.filter(r=>r.subject===j.subject)};
  for(const row of [...commerce.inquiries,...commerce.opportunities]){const link=row.auditLink,event=finalSnapshot.audit.find(a=>a.sequence===link?.sequence&&a.sha256===link?.sha256);const record={...row};delete record.auditLink;const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(record)))),b=>b.toString(16).padStart(2,'0')).join('');if(!event||event.details?.recordKey!==row.key||event.details?.recordHash!==digest||link.recordHash!==digest)throw Error('COMMERCE_AUDIT_READBACK_FAILED');}
  const payload={format:'cfp-training-evidence-v1',workspace:snapshot.auth.workspace,exportedAt:new Date().toISOString(),mode:snapshot.mode,journey:j,tasks,commerce,assessments:scopedAssessmentEvidence(snapshot,j.subject,j.pairKey),office:{applications:ownApplications,hstdn:scopedOffice.hstdn.filter(r=>r.members.some(k=>ownRefs.has(k))),records:scopedOffice.records.filter(r=>r.subject===j.subject||ownRefs.has(r.officeRef))},feedback:snapshot.learning.feedback.filter(f=>keys.has(f.taskKey)),observations:snapshot.learning.observations.filter(o=>o.subject===j.subject&&o.pairKey===j.pairKey),audit:finalSnapshot.audit.filter(a=>a.details?.pairKey===j.pairKey||keys.has(a.details?.taskKey)),auditValid:finalSnapshot.auditValid,sourceRevision:snapshot.buildProvenance?.verified===true?snapshot.buildProvenance.revision:null,buildProvenance:snapshot.buildProvenance||{verified:false,finding:'BUILD_PROVENANCE_MISSING'}};
  const payloadJSON=JSON.stringify(payload),digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(payloadJSON))),b=>b.toString(16).padStart(2,'0')).join('');
  assertScope(snapshot.auth);
  const url=URL.createObjectURL(new Blob([JSON.stringify({sha256:digest,digestOf:'UTF-8 payloadJSON bytes',payloadJSON},null,2)],{type:'application/json'}));
  const a=el('a','');a.href=url;a.download='cfp-training-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('#p2-export-status').textContent='SHA-256 '+digest;
 }catch(e){$('#p2-export-status').textContent=e.message;}
};

