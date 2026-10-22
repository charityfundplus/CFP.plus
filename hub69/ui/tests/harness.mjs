// Application state tests with explicit DOM stubs. These are not browser or device QA.
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const root=new URL('../',import.meta.url);
const html=await readFile(new URL('public/index.html',root),'utf8');
const scripts=await Promise.all(['config.js','registry.js','training-data.js','model.js','workspace.js','hstdn-review.js','explore.js','p0.js','core-binding.js','training.js','app.js'].map(f=>readFile(new URL('public/'+f,root),'utf8')));
export function harness({hash='#home',storageBlocked=false,clipboardBlocked=false,coreClient=null}={}){
  const elements=new Map(),events={},windowEvents={},values=new Map();
  const element=id=>{if(elements.has(id))return elements.get(id);const e={id,hidden:false,textContent:'',value:id==='type'?'all':'',listeners:{},attributes:{},focused:false,classList:{toggle(){}},getAttribute(k){return this.attributes[k]??null;},setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this.attributes[k];},addEventListener(k,fn){this.listeners[k]=fn;},focus(){this.focused=true;}};let markup='';Object.defineProperty(e,'innerHTML',{get:()=>markup,set:v=>{markup=v;for(const m of v.matchAll(/\bid="([^"]+)"/g))element(m[1]);}});elements.set(id,e);return e;};
  for(const m of html.matchAll(/\bid="([^"]+)"/g))element(m[1]);
  const nav=['home','master','id','chapters','hstdn','technology','vaults','training','partners','app'].map(id=>Object.assign(element('nav-'+id),{dataset:{nav:id}}));
  const input={value:'',focus(){this.focused=true;}};
  const form=Object.assign(element('lookup'),{elements:{id:input}});
  const document={title:'',getElementById:id=>elements.get(id)||null,querySelectorAll:s=>s==='[data-nav]'?nav:s==='[data-lookup]'?[form]:[],addEventListener:(k,fn)=>events[k]=fn};
  const copied=[];
  const sandbox={URL,document,location:{hash,href:'file:///unit/HUB69-review.html'+hash},setTimeout:()=>1,clearTimeout(){},localStorage:{getItem:k=>values.get(k)||null,setItem(k,v){if(storageBlocked)throw Error('blocked');values.set(k,v);}},navigator:{clipboard:{writeText:async v=>{if(clipboardBlocked)throw Error('blocked');copied.push(v);}}}};
  const ctx=vm.createContext(sandbox);ctx.window=ctx;ctx.addEventListener=(k,fn)=>windowEvents[k]=fn;ctx.scrollTo=()=>{};
  for(const script of scripts.slice(0,-1))vm.runInContext(script,ctx);
  if(coreClient){ctx.HUB69_CONFIG={mode:'core'};ctx.HUB69CoreBinding={...ctx.HUB69CoreBinding,sameOriginClient:async()=>coreClient};}
  vm.runInContext(scripts.at(-1),ctx);
  const go=path=>{ctx.location.hash=path;windowEvents.hashchange();};
  const click=selector=>({target:{closest:q=>q===selector?selector==='[data-save]'?{dataset:{save:'691181'}}:selector==='[data-copy]'?{dataset:{copy:'691181'}}:{}:null},preventDefault(){}});
  return {ctx,elements,events,windowEvents,nav,form,input,go,click,copied,values};
}
