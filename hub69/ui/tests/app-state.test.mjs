// Application state tests with explicit DOM stubs. These are not browser or device QA.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const root=new URL('../',import.meta.url);
const html=await readFile(new URL('public/index.html',root),'utf8');
const scripts=await Promise.all(['registry.js','model.js','p0.js','app.js'].map(f=>readFile(new URL('public/'+f,root),'utf8')));
function harness({hash='#home',storageBlocked=false,clipboardBlocked=false}={}){
  const elements=new Map(),events={},windowEvents={},values=new Map();
  const element=id=>{if(elements.has(id))return elements.get(id);const e={id,hidden:false,textContent:'',value:id==='type'?'all':'',listeners:{},attributes:{},focused:false,classList:{toggle(){}},setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this.attributes[k];},addEventListener(k,fn){this.listeners[k]=fn;},focus(){this.focused=true;}};let markup='';Object.defineProperty(e,'innerHTML',{get:()=>markup,set:v=>{markup=v;for(const m of v.matchAll(/\bid="([^"]+)"/g))element(m[1]);}});elements.set(id,e);return e;};
  for(const m of html.matchAll(/\bid="([^"]+)"/g))element(m[1]);
  const nav=['home','master','id','chapters','vaults'].map(id=>Object.assign(element('nav-'+id),{dataset:{nav:id}}));
  const input={value:'',focus(){this.focused=true;}};
  const form=Object.assign(element('lookup'),{elements:{id:input}});
  const document={title:'',getElementById:id=>elements.get(id)||null,querySelectorAll:s=>s==='[data-nav]'?nav:s==='[data-lookup]'?[form]:[],addEventListener:(k,fn)=>events[k]=fn};
  const copied=[];
  const sandbox={URL,document,location:{hash,href:'file:///unit/HUB69-review.html'+hash},setTimeout:()=>1,clearTimeout(){},localStorage:{getItem:k=>values.get(k)||null,setItem(k,v){if(storageBlocked)throw Error('blocked');values.set(k,v);}},navigator:{clipboard:{writeText:async v=>{if(clipboardBlocked)throw Error('blocked');copied.push(v);}}}};
  const ctx=vm.createContext(sandbox);ctx.window=ctx;ctx.addEventListener=(k,fn)=>windowEvents[k]=fn;ctx.scrollTo=()=>{};
  for(const script of scripts)vm.runInContext(script,ctx);
  const go=path=>{ctx.location.hash=path;windowEvents.hashchange();};
  const click=selector=>({target:{closest:q=>q===selector?selector==='[data-save]'?{dataset:{save:'691181'}}:selector==='[data-copy]'?{dataset:{copy:'691181'}}:{}:null},preventDefault(){}});
  return {ctx,elements,events,windowEvents,nav,form,input,go,click,copied,values};
}
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
