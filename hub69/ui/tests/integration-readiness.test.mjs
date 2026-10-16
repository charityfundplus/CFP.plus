import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {harness} from './harness.mjs';
const ctx=vm.createContext({});
vm.runInContext(await readFile(new URL('../public/core-binding.js',import.meta.url),'utf8'),ctx);
const {createController}=ctx.HUB69CoreBinding;
const provenance={revision:'a'.repeat(40),files:[]};
const ready=()=>({snapshot:async()=>({records:[{id:'003'}],sourceCommit:provenance.revision,provenance}),openai:async()=>({provenance}),detail:async id=>({record:{id},provenance}),logout:async()=>{}});
const tick=()=>new Promise(resolve=>setImmediate(resolve));
test('Core transitions clear data before every load and retain no snapshot on 401/404/503',async()=>{
  for(const status of [401,403,404,503]){
    const api=ready(),states=[];const c=createController({client:async()=>api,onChange:s=>states.push(s)});
    await c.load('003');assert.equal(c.getState().phase,'ready');
    api.snapshot=async()=>{throw Object.assign(Error('fixture'),{status});};
    const pending=c.load('000');assert.equal(c.getState().data,null);assert.equal(c.getState().phase,'loading');await pending;
    assert.equal(c.getState().status,status);assert.equal(c.getState().data,null);
  }
});
test('Core rejects revision changes between list, detail and OpenAI instead of mixing sources',async()=>{
  for(const method of ['openai','detail']){
    const api=ready();api[method]=async()=>({record:{id:'003'},provenance:{...provenance,revision:'b'.repeat(40)}});
    const c=createController({client:async()=>api,onChange(){}});await c.load('003');assert.equal(c.getState().phase,'error');assert.equal(c.getState().data,null);
  }
});
test('Core rejects mismatched identity and ignores delayed success after logout or a newer request',async()=>{
  const api=ready();api.detail=async()=>({record:{id:'3'},provenance});
  const c=createController({client:async()=>api,onChange(){}});await c.load('003');assert.equal(c.getState().phase,'error');
  let release;api.snapshot=()=>new Promise(resolve=>{release=resolve;});api.detail=ready().detail;
  const pending=c.load('003');await tick();c.invalidate();release({records:[{id:'003'}],provenance});await pending;
  assert.equal(c.getState().phase,'signed-out');assert.equal(c.getState().data,null);
});
test('Core read responses never replace leading-zero IDs or require a new project identity',async()=>{
  const c=createController({client:async()=>ready(),onChange(){}});await c.load('003');assert.equal(c.getState().data.records[0].id,'003');
});
test('navigation while logout is pending cannot repopulate records from the earlier session',async()=>{
  let finish;const api=ready();api.logout=()=>new Promise(resolve=>{finish=resolve;});
  const c=createController({client:async()=>api,onChange(){}});await c.load('003');
  const pending=c.logout();await tick();await c.load('003');assert.equal(c.getState().data,null);
  finish();await pending;assert.equal(c.getState().phase,'signed-out');
});
test('training inherits exactly five lessons, twelve exercises and six unassessed tracks',()=>{
  const h=harness();h.go('#training');const T=h.ctx.HUB69Training,data=h.ctx.HUB69_TRAINING;
  assert.equal(data.curriculum.basic.lessons.length,5);assert.equal(data.curriculum.exercises.length,12);assert.equal(data.curriculum.advanced.length,6);
  assert.ok(data.curriculum.advanced.every(a=>a.assessmentStatus==='NOT ASSESSED'&&a.privilegeChange===false));
  assert.ok(h.elements.get('training-content').innerHTML.includes(data.source.revision.slice(0,7)));
  assert.equal(T.validKey('invented-lesson'),false);h.go('#lesson/security');assert.ok(h.elements.get('training-content').innerHTML.includes('Bảo mật &amp; Phục hồi'));
  assert.equal(h.ctx.HUB69P0.route('#lesson/invented-lesson').invalid,true);
});
test('study acknowledgement persists locally without changing Registry identity or granting assessment',()=>{
  const h=harness();h.go('#training');const before=JSON.stringify(h.ctx.HUB69_DATA);
  h.events.change({target:{dataset:{study:'security'},checked:true}});
  assert.deepEqual(JSON.parse(h.values.get('hub69.study.v1')),['security']);
  assert.ok(h.elements.get('training-content').innerHTML.includes('1 / 5'));
  assert.equal(JSON.stringify(h.ctx.HUB69_DATA),before);
  h.events.change({target:{dataset:{study:'security'},checked:false}});assert.deepEqual(JSON.parse(h.values.get('hub69.study.v1')),[]);
});
test('blocked storage retains study acknowledgement in the current session and reports the limit',()=>{
  const h=harness({storageBlocked:true});h.go('#training');h.events.change({target:{dataset:{study:'evidence'},checked:true}});
  assert.ok(h.elements.get('training-content').innerHTML.includes('1 / 5'));assert.ok(h.elements.get('notice').textContent.includes('phiên này'));assert.equal(h.values.size,0);
});
test('Core bundle starts empty and contains no snapshot fallback or embedded credentials',async()=>{
  const js=await readFile(new URL('../core-dist/registry.js',import.meta.url),'utf8');
  assert.ok(js.includes('records:[]'));assert.ok(!js.includes('691181'));
  const config=await readFile(new URL('../core-dist/config.js',import.meta.url),'utf8');assert.ok(config.includes('mode:"core"'));
});
