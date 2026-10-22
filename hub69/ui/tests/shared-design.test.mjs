import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {harness} from './harness.mjs';
import {tokenCSS} from '../token-css.mjs';
const root=new URL('../',import.meta.url);

test('directory filters cover both countries and each business role without assigning identity',()=>{
  const h=harness(),W=h.ctx.HUB69Workspace,before=JSON.stringify(h.ctx.HUB69_DATA);
  for(const c of ['all','vn','us'])for(const role of ['all','supplier','buyer','seller']){
    h.go('#partners/'+c+'/'+role);
    const html=h.elements.get('partners-content').innerHTML;
    assert.match(html,new RegExp((c==='all'?2:1)*(role==='all'?3:1)+' mẫu minh họa'));
    assert.equal(h.elements.get('view-partners').hidden,false);
    assert.match(html,/0 đối tác được xác minh/);
    if(c==='vn')assert.doesNotMatch(html,/Hoa Kỳ<\/h2>/);
    if(c==='us')assert.doesNotMatch(html,/Việt Nam<\/h2>/);
  }
  for(const row of W.samples)for(const key of ['id','parent','did','canonical'])assert.equal(row[key],null);
  assert.equal(JSON.stringify(h.ctx.HUB69_DATA),before);
  assert.equal(h.values.size,0);
});
test('partner filter changes retain the other selection; malformed routes fail closed',()=>{
  const h=harness({hash:'#partners/vn/buyer'}),W=h.ctx.HUB69Workspace;
  h.events.change({target:{dataset:{catalogFilter:'partner-country'},value:'us'}});
  assert.equal(h.ctx.location.hash,'#partners/us/buyer');
  assert.equal(W.filterRoute({view:'partners',country:'us'},'partner-role','seller'),'#partners/us/seller');
  for(const route of ['#partners/984/buyer','#partners/vn/admin','#partners/__proto__/all','#reference/8282','#reference/8882/extra','#app/active'])assert.equal(h.ctx.HUB69P0.route(route).invalid,true);
});
test('8682 and 8882 have visible source and HOLD, with no clickable unverified canonical target',()=>{
  const h=harness();
  for(const id of ['8682','8882']){
    h.go('#reference/'+id);const html=h.elements.get('reference-content').innerHTML;
    assert.match(html,/PENDING REVIEW/);assert.match(html,/HOLD ACTIVATION/);
    assert.ok(html.includes('<code>https://cfp.plus/'+id+'</code>'));
    assert.ok(!html.includes('href="https://cfp.plus/'+id+'"'));
    assert.match(html,/href="https:\/\/github.com\/charityfundplus\/CFP.plus\/issues\/156"/);
  }
  h.go('#commerce');assert.match(h.elements.get('commerce-content').innerHTML,/#reference\/8882/);
});
test('all chapters retain tree navigation and contain useful overview actions, including Chi Hoi and countries',()=>{
  const h=harness(),W=h.ctx.HUB69Workspace;
  for(let i=0;i<10;i++){
    h.go('#chapter/'+i);const html=h.elements.get('chapter-map').innerHTML;
    assert.match(html,/chapter-overview/);assert.ok(html.includes('id="chapter-'+i+'"'));
    assert.ok(W.chapterOverview(String(i)).length>200);
  }
  h.go('#chapter/5');assert.match(h.elements.get('chapter-map').innerHTML,/Chi Hội/);assert.match(h.elements.get('chapter-map').innerHTML,/3fecaac9a557815ca9f6fbf60844d50b/);
  h.go('#chapter/9');assert.match(h.elements.get('chapter-map').innerHTML,/#hstdn\/vn/);assert.match(h.elements.get('chapter-map').innerHTML,/#hstdn\/us/);
});
test('browser App shell shares routes and disables login when no approved Core exists',()=>{
  const h=harness({hash:'#app'}),W=h.ctx.HUB69Workspace,html=h.elements.get('app-content').innerHTML;
  assert.equal(h.elements.get('view-app').hidden,false);
  assert.match(html,/<button class="btn" disabled/);assert.doesNotMatch(html,/type="password"|<form|href="\/p2"/);
  assert.match(html,/Chưa có App native/);
  assert.match(W.appView({coreMode:true,coreState:{phase:'error',status:401}}),/Core chưa sẵn sàng/);
  const before=JSON.stringify(h.ctx.HUB69_DATA);
  for(const [,href] of html.matchAll(/href="(#[^"]+)"/g))assert.equal(h.ctx.HUB69P0.route(href).invalid,undefined,href);
  assert.equal(JSON.stringify(h.ctx.HUB69_DATA),before);
});
test('every added view is in both bundles and has no independent transport or credential storage',async()=>{
  const js=await readFile(new URL('public/workspace.js',root),'utf8');
  assert.doesNotMatch(js,/\bfetch\s*\(|XMLHttpRequest|WebSocket|localStorage|sessionStorage|serviceWorker|signatureVerified/);
  for(const dir of ['dist','core-dist'])assert.equal(await readFile(new URL(dir+'/workspace.js',root),'utf8'),js);
  const css=await readFile(new URL('public/design-system.css',root),'utf8');
  for(const dir of ['dist','core-dist'])assert.equal(await readFile(new URL(dir+'/design-system.css',root),'utf8'),css);
  const html=await readFile(new URL('HUB69-review.html',root),'utf8');
  assert.ok(html.includes(js.trim()));assert.ok(html.includes(css.trim()));assert.doesNotMatch(html,/<script[^>]+src=/);
});
test('text and interaction color pairs meet WCAG normal text contrast in versioned tokens',async()=>{
  const tokens=JSON.parse(await readFile(new URL('public/design-tokens.json',root),'utf8')),v=tokens.cssVariables;
  const luminance=hex=>{const rgb=hex.slice(1).match(/../g).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];};
  for(const [fg,bg] of [['--ink','--paper'],['--muted','--paper'],['--muted','--surface'],['--amber','--warning-surface'],['--on-accent','--green'],['--ink','--lime']]){
    const a=luminance(v[fg]),b=luminance(v[bg]),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    assert.ok(ratio>=4.5,`${fg} on ${bg}: ${ratio}`);
  }
  assert.throws(()=>tokenCSS({...tokens,cssVariables:{'--unsafe':'red;display:none'}}),/INVALID_CSS_TOKEN/);
  assert.throws(()=>tokenCSS({...tokens,version:'<script>'}),/INVALID_TOKEN_VERSION/);
});
test('new visible navigation emits implemented routes and safe source links',()=>{
  const h=harness(),W=h.ctx.HUB69Workspace,P=h.ctx.HUB69P0;
  for(const hash of ['#app','#partners','#partners/vn/supplier','#partners/us/buyer','#reference/8682','#reference/8882']){
    const html=W.view(P.route(hash));
    for(const [,href] of html.matchAll(/href="([^"]*)"/g)){
      assert.ok(href&&href!=='#');if(href.startsWith('#'))assert.equal(P.route(href).invalid,undefined,href);
      else assert.ok(h.ctx.HUB69Model.safeURL(href));
    }
  }
});

test('menu toggle exposes state, Escape closes it and returns keyboard focus',()=>{
  const h=harness();
  h.events.click(h.click('#menu-toggle'));
  assert.equal(h.elements.get('menu-toggle').getAttribute('aria-expanded'),'true');
  h.events.keydown({key:'Escape'});
  assert.equal(h.elements.get('menu-toggle').getAttribute('aria-expanded'),'false');
  assert.equal(h.elements.get('menu-toggle').focused,true);
  h.events.click(h.click('#menu-toggle'));h.go('#partners');
  assert.equal(h.elements.get('menu-toggle').getAttribute('aria-expanded'),'false');
});
