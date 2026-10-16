import {CoreEngine} from '../core/core-engine.mjs';
const core=new CoreEngine();const editor={id:'demo-editor',role:'editor'},reviewer={id:'demo-independent-reviewer',role:'reviewer'};
const t=core.createTask(editor,'hub69-content-demo',{kind:'website-draft',title:'HUB 69 • fast content draft',text:'Synthetic VI/EN draft; preserve IDs, groups and chapter history.',scenario:'normal'});
const result=await core.runTask(editor,t.key);core.reviewTask(reviewer,t.key,'acknowledge-draft');
core.instantiate(editor,'training-demo');const drill=core.createTask(editor,'training-demo',{kind:'training-drill',title:'Deny unauthorized tool',scenario:'overreach'});const blocked=await core.runTask(editor,drill.key);core.recover(reviewer,'training-demo');
core.instantiate(editor,'us-hstdn-demo');const hst=core.createTask(editor,'us-hstdn-demo',{kind:'hst-us-draft',title:'US HSTDN synthetic profile',scenario:'normal'});const hstResult=await core.runTask(editor,hst.key);core.reviewTask(reviewer,hst.key,'acknowledge-draft');
core.upgrade(reviewer,'0.1.1-sandbox');core.rollback(reviewer);
const state=core.snapshot(editor);console.log(JSON.stringify({normalTask:result.status,websiteDraft:result.output,hstdnDraft:hstResult.output,independentChecks:result.checks.filter(x=>x.axis).length,blockedTask:blocked.status,pairs:state.pairs.map(p=>({key:p.key,status:p.status})),training:state.learning.evaluations,version:state.versions.version,auditValid:state.auditValid,production:'NO-GO'},null,2));
