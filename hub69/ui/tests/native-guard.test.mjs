import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../public/app-integration.js',import.meta.url),'utf8');

function run({protocol='https:',origin='https://review.example',approved}={}) {
  const events={},updates=[],requests=[],frame={hidden:false,src:undefined};
  const elements={'operations-frame':frame,'operations-runtime-note':{textContent:''}};
  const links=[{hidden:true}];
  const sandbox={HUB69_CONFIG:{mode:'app',approvedStagingOrigin:approved},Capacitor:{isNativePlatform:()=>true},location:{protocol,origin},CustomEvent:class {constructor(type,options){this.type=type;this.detail=options.detail;}},document:{getElementById:id=>elements[id],querySelector:()=>({hidden:true}),querySelectorAll:()=>links,addEventListener(){}},fetch:async(...args)=>{requests.push(args);return {ok:false,status:401};}};
  const context=vm.createContext(sandbox);context.window=context;context.addEventListener=(type,fn)=>events[type]=fn;context.dispatchEvent=event=>updates.push(event.detail);
  vm.runInContext(source,context);events.DOMContentLoaded();return {events,updates,requests,frame,links};
}
test('native default/mismatched/HTTP origins never open backend frame or request Registry',()=>{
  for(const input of [{},{approved:'https://another.example'},{protocol:'http:',origin:'http://review.example',approved:'http://review.example'}]) {
    const x=run(input);assert.equal(x.frame.hidden,true);assert.equal(x.frame.src,undefined);assert.equal(x.requests.length,0);assert.equal(x.links[0].hidden,true);assert.equal(x.updates.at(-1).phase,'blocked');
  }
});
test('only exact configured HTTPS origin allows the shared native backend surface',async()=>{
  const x=run({approved:'https://review.example'});await new Promise(resolve=>setImmediate(resolve));assert.equal(x.frame.src,'/#operations');assert.equal(x.requests.length,1);assert.equal(x.requests[0][0],'/api/app/registry');assert.equal(x.links[0].hidden,false);assert.equal(x.updates.at(-1).phase,'blocked');
});
