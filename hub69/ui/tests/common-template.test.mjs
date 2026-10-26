import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const base=new URL('../',import.meta.url);
function load(config=JSON.parse(readFileSync(new URL('template.config.json',base)))){
  const ctx=vm.createContext({window:{HUB69_TEMPLATE_CONFIG:config}});
  for(const file of ['model.js','workspace.js','commerce.js','explore.js','p0.js','common-template.js'])vm.runInContext(readFileSync(new URL('public/'+file,base),'utf8'),ctx);
  return ctx.window;
}
test('ten sections and seven office children resolve through existing router',()=>{
  const w=load(),c=w.HUB69_TEMPLATE_CONFIG;
  assert.equal(c.modules.length,10);
  for(const m of c.modules){
    const state=w.HUB69P0.route('#template/'+m.key);
    assert.equal(state.module,m.key);
    assert.ok(w.HUB69CommonTemplate.view(state).includes(w.HUB69Model.esc(m.title.vi)));
  }
  for(const c of w.HUB69_TEMPLATE_CONFIG.officeChildren){
    const s=w.HUB69P0.route('#template/office/'+c.key);
    assert.equal(s.child,c.key);
    assert.ok(w.HUB69CommonTemplate.view(s).includes(c.target));
  }
});
test('disabled module is absent from search and direct/deep links are rejected',()=>{
  const c=load().HUB69_TEMPLATE_CONFIG;
  c.modules.find(m=>m.key==='forum').enabled=false;
  const w=load(c);
  assert.doesNotMatch(w.HUB69CommonTemplate.results(),/#template\/forum/);
  for(const hash of ['#template/forum','#template/forum/ack','#template/office/unknown','#template/office/tasks/extra','#template/%3Cscript%3E'])assert.equal(w.HUB69P0.route(hash).templateInvalid,true);
});
test('query and labels cannot inject HTML or unsafe links',()=>{
  const c=load().HUB69_TEMPLATE_CONFIG;
  c.modules[0].title.vi='<img src=x onerror=alert(1)>';
  c.modules[0].target='javascript:alert(1)';
  const w=load(c),U=w.HUB69CommonTemplate;
  assert.doesNotMatch(U.results(),/<img|javascript:/);
  assert.doesNotMatch(U.view({module:'home'}),/<img|javascript:/);
  assert.match(U.view({},'vi','"><script>'),/&quot;&gt;&lt;script&gt;/);
});
test('accent-insensitive search, English labels, empty results and forum limits',()=>{
  const U=load().HUB69CommonTemplate;
  assert.match(U.results('vi','van phong'),/1 \/ 10/);
  assert.match(U.results('en','office'),/1 \/ 10/);
  assert.match(U.results('en','doesnotexist'),/No matching sections/);
  const forum=U.view({module:'forum'});
  assert.equal((forum.match(/href="#chapter\//g)||[]).length,10);
  assert.match(forum,/chưa triển khai/);
  assert.match(forum,/Ẩn menu không thay thế/);
});
test('all configured destinations use supported existing routes or sole intake',()=>{
  const w=load(),c=w.HUB69_TEMPLATE_CONFIG;
  for(const m of [...c.modules,...c.officeChildren]){
    if(m.target==='https://cfp.plus/69')continue;
    const s=w.HUB69P0.route(m.target);
    assert.ok(s.view);
    assert.ok(!s.invalid&&!s.templateInvalid);
    if(m.target!=='#home')assert.notEqual(s.view,'home',m.target);
  }
  assert.deepEqual(Object.values(c.identity),[null,null,null,null]);
});
test('standalone and both bundles include identical template code/config',()=>{
  const source=readFileSync(new URL('public/common-template.js',base),'utf8');
  for(const dir of ['dist','core-dist'])assert.equal(readFileSync(new URL(dir+'/common-template.js',base),'utf8'),source);
  const html=readFileSync(new URL('HUB69-review.html',base),'utf8');
  assert.ok(html.includes(source));
  assert.match(html,/window.HUB69_TEMPLATE_CONFIG=/);
});
