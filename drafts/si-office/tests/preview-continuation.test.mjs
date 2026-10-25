import {test} from 'node:test';import assert from 'node:assert/strict';
import {rehearseIntakePractice} from '../scripts/intake-team-practice.mjs';
import {assessRetainedPractice} from '../scripts/assess-retained-practice.mjs';
import {verifyRenderActivation} from '../scripts/guarded-preview.mjs';
import {suspendPreview} from '../scripts/render-suspend.mjs';
import program from '../configs/training-basic-v1.json' with {type:'json'};
test('New evidence export retains actual task keys/output/checks/review without competency promotion',async()=>{
 const r=await rehearseIntakePractice({teams:2});assert.equal(r.results.length,2);
 for(const team of r.results){assert.equal(team.taskEvidence.length,6);for(const evidence of team.taskEvidence){assert.equal(evidence.taskKey,evidence.task.key);assert(evidence.task.output);assert(evidence.task.checks.length);assert.notEqual(evidence.task.review.actor,evidence.task.owner);assert.equal(evidence.competencyPass,false);}}
 const assessment=assessRetainedPractice(r,program);assert.equal(assessment.notAssessed,12);assert.equal(assessment.competencyPass,0);assert(assessment.rows.every(r=>r.retainedTaskEvidence));
});
test('Render activation fails closed without approval or on revision mismatch',()=>{
 const sha='c'.repeat(40),env={RENDER:'true',CFP_RENDER_APPROVED_COMMIT:sha,CFP_PREVIEW_REVISION:sha,RENDER_GIT_COMMIT:sha};
 assert.throws(()=>verifyRenderActivation(env),/APPROVAL/);assert.throws(()=>verifyRenderActivation({...env,CFP_PREVIEW_ACTIVATION_APPROVED:'true',RENDER_GIT_COMMIT:'d'.repeat(40)}),/MISMATCH/);verifyRenderActivation({...env,CFP_PREVIEW_ACTIVATION_APPROVED:'true'});
});
test('Suspend adapter mock verifies exact target, admission close and202 plus readback; never creates',async()=>{
 const calls=[],target={id:'srv-synthetic',ownerId:'synthetic-owner',name:'cfp-hub69-preview',type:'web_service',suspended:'not_suspended'};
 const fetcher=async(url,options)=>{calls.push(options.method||'GET');if(options.method==='POST'){assert(url.endsWith('/suspend'));target.suspended='suspended';return {status:202};}return {status:200,json:async()=>({...target})};};
 const cfg={serviceId:target.id,ownerId:target.ownerId,name:target.name,apiKey:'synthetic-test-only',approved:true,fetcher,closeAdmission:async()=>calls.push('CLOSE')};assert((await suspendPreview(cfg)).suspended);assert.deepEqual(calls,['GET','CLOSE','POST','GET']);
 calls.length=0;await assert.rejects(suspendPreview({...cfg,ownerId:'wrong'}),/TARGET_MISMATCH/);assert.deepEqual(calls,['GET']);
 await assert.rejects(suspendPreview({...cfg,approved:false}),/APPROVED/);
});
