import test from 'node:test';
import assert from 'node:assert/strict';
import {harness} from './harness.mjs';
test('application initializes all seven views and navigation state without missing controls',()=>{
  const h=harness();
  for(const view of ['home','master','id','chapters','vaults','openai','template']){
    h.go('#'+view);assert.equal(h.elements.get('view-'+view).hidden,false,view);
    for(const other of ['home','master','id','chapters','vaults','openai','template'].filter(v=>v!==view))assert.equal(h.elements.get('view-'+other).hidden,true);
  }
  h.go('#group/000');assert.ok(h.elements.get('chapter-map').innerHTML.includes('chapter-0'));
  assert.equal(h.nav.find(n=>n.dataset.nav==='chapters').attributes['aria-current'],'page');
});
test('lookup submission preserves leading zeroes and rejects nonnumeric input',()=>{
  const h=harness();h.input.value='000691181';h.form.listeners.submit({preventDefault(){}});
  assert.equal(h.ctx.location.hash,'#id/000691181');h.windowEvents.hashchange();
  assert.ok(h.elements.get('profile').innerHTML.includes('chưa có trong snapshot'));
  h.input.value='1e3';h.form.listeners.submit({preventDefault(){}});assert.equal(h.ctx.location.hash,'#id/000691181');assert.ok(h.input.focused);
});
test('source ID profile opens with correct Parent and returning to directory works',()=>{
  const h=harness({hash:'#id/691181'});assert.ok(h.elements.get('profile').innerHTML.includes('href="#id/69118"'));
  h.go('#id/69118');assert.ok(h.ctx.document.title.includes('OpenAI'));h.go('#id');
  assert.equal(h.elements.get('directory').hidden,false);assert.equal(h.elements.get('profile').hidden,true);
});
test('saved item action works with unavailable local storage and reports session-only persistence',async()=>{
  const h=harness({hash:'#id/691181',storageBlocked:true});await h.events.click(h.click('[data-save]'));
  assert.ok(h.elements.get('saved-items').innerHTML.includes('691181'));
  assert.ok(h.elements.get('notice').textContent.includes('tạm trong phiên'));assert.equal(h.values.size,0);
});
test('template type selection updates project fields and returns focus to control',()=>{
  const h=harness({hash:'#template'});assert.ok(h.elements.get('common-template').innerHTML.includes('Làm Dự Án'));
  h.events.change({target:{id:'template-type',value:'hstdn'}});
  assert.ok(!h.elements.get('common-template').innerHTML.includes('Làm Dự Án'));assert.ok(h.elements.get('template-type').focused);
});
test('copy failure leaves a clear message and skip navigation keeps the current route',async()=>{
  const h=harness({hash:'#id/691181',clipboardBlocked:true});await h.events.click(h.click('[data-copy]'));
  assert.ok(h.elements.get('notice').textContent.includes('Chưa sao chép được'));assert.equal(h.copied.length,0);
  await h.events.click(h.click('a.skip'));assert.equal(h.ctx.location.hash,'#id/691181');assert.ok(h.elements.get('content').focused);
});

 test('shared template routes, language and search use application events',()=>{
  const h=harness({hash:'#template'});
  assert.ok(h.elements.get('common-template').innerHTML.includes('Mẫu Website Chung'));
  h.events.input({target:{id:'template-search',value:'van phong'}});
  assert.ok(h.elements.get('template-results').innerHTML.includes('1 / 10'));
  h.events.change({target:{id:'template-language',value:'en'}});
  assert.ok(h.elements.get('common-template').innerHTML.includes('Shared Website Template'));
  h.go('#template/office');
  assert.ok(h.elements.get('common-template').innerHTML.includes('#template/office/tasks'));
  assert.ok(!h.elements.get('common-template').innerHTML.includes('template-type'));
  h.go('#template/office/evidence');
  assert.ok(h.elements.get('common-template').innerHTML.includes('href="#vaults"'));
  h.go('#template/forum');
  assert.ok(h.elements.get('common-template').innerHTML.includes('not implemented'));
});
