// Node/VM + source assertions only. No browser layout or real iPhone acceptance.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {harness} from './harness.mjs';
const root=new URL('../',import.meta.url);
const tick=()=>new Promise(resolve=>setImmediate(resolve));

test('P0 deep links resolve only allowlisted countries, brands and technologies',()=>{
  const h=harness(),P=h.ctx.HUB69P0;
  for(const route of ['#hstdn','#hstdn/vn','#hstdn/us','#hstdn/unknown','#commerce','#commerce/vn','#commerce/us','#commerce/unknown','#brand/sample-vn','#brand/sample-us','#brand/amazon','#technology','#technology/quantum','#technology/space','#technology/future'])assert.equal(P.route(route).invalid,undefined,route);
  for(const route of ['#hstdn/69118','#brand/69118','#brand/amazon/extra','#technology/<script>','#hstdn/%76%6e','#technology/quantum?token=x','#commerce/unknown/extra','#technology/__proto__'])assert.equal(P.route(route).invalid,true,route);
});

test('existing HUB/group/chapter navigation reaches both P0 lanes and 8682',()=>{
  const h=harness();
  for(const route of ['#chapters','#group/789','#chapter/7']){h.go(route);assert.match(h.elements.get('chapter-map').innerHTML,/href="#hstdn"/);}
  h.go('#hstdn');assert.match(h.elements.get('hstdn-content').innerHTML,/href="#commerce"/);
  h.go('#commerce');assert.match(h.elements.get('commerce-content').innerHTML,/href="#reference\/8682"/);
  h.go('#group/246');assert.match(h.elements.get('chapter-map').innerHTML,/href="#technology"/);
});

test('country selection changes the route and shows only the matching sample profile',()=>{
  const h=harness({hash:'#hstdn'});
  h.events.change({target:{dataset:{catalogFilter:'country'},value:'us'}});
  assert.equal(h.ctx.location.hash,'#hstdn/us');h.windowEvents.hashchange();
  let html=h.elements.get('hstdn-content').innerHTML;
  assert.match(html,/Thương hiệu minh họa Hoa Kỳ/);assert.doesNotMatch(html,/Thương hiệu minh họa Việt Nam/);
  h.go('#brand/sample-us');html=h.elements.get('hstdn-content').innerHTML;
  assert.match(html,/MẪU MINH HỌA/);assert.match(html,/Chưa có Evidence tồn kho/);assert.match(html,/Chưa có Evidence giao hàng/);
  assert.match(html,/href="#hstdn\/us"/);
});

test('market country filters fail closed when local supply or delivery is not evidenced',()=>{
  const h=harness({hash:'#commerce'});
  for(const country of ['vn','us']){
    h.go('#commerce/'+country);const html=h.elements.get('commerce-content').innerHTML;
    assert.match(html,/0 sàn tham chiếu/);assert.match(html,/Chưa có sàn được xác minh/);assert.doesNotMatch(html,/href="#brand\/amazon"/);
  }
  h.go('#commerce/unknown');assert.match(h.elements.get('commerce-content').innerHTML,/href="#brand\/amazon"/);
  h.go('#brand/amazon');assert.match(h.elements.get('hstdn-content').innerHTML,/href="https:\/\/www\.amazon\.com\/"/);
});

test('technology filters preserve entity/product distinctions and research provenance',()=>{
  const h=harness();
  h.go('#technology/quantum');let html=h.elements.get('technology-content').innerHTML;
  assert.match(html,/IBM Quantum/);assert.match(html,/Google Quantum AI/);assert.doesNotMatch(html,/>Starlink</);
  h.go('#technology/space');html=h.elements.get('technology-content').innerHTML;
  for(const name of ['SpaceX','Starlink','NASA','ESA'])assert.ok(html.includes(name));
  assert.match(html,/Nguồn sản phẩm \/ dịch vụ/);assert.match(html,/Tổ chức \/ nguồn nghiên cứu/);
  h.go('#technology/future');assert.match(h.elements.get('technology-content').innerHTML,/Hướng nghiên cứu đề xuất/);
  assert.ok(h.elements.get('technology-content').innerHTML.includes(h.ctx.HUB69Explore.sources.inbox.replace(/&/g,'&amp;')));
});

test('new navigation keeps one active view and correct sidebar state including commerce',()=>{
  const h=harness();
  for(const route of ['#hstdn','#commerce','#brand/amazon','#technology/space']){
    h.go(route);const state=h.ctx.HUB69P0.route(route);
    for(const [id,el] of h.elements)if(id.startsWith('view-'))assert.equal(el.hidden,id!=='view-'+state.view,id);
    const active=h.nav.filter(n=>n.attributes['aria-current']==='page');assert.equal(active.length,1);
    assert.equal(active[0].dataset.nav,state.view==='commerce'?'hstdn':state.view);
    assert.doesNotMatch(h.ctx.document.title,/undefined/);
  }
});

test('catalog navigation never changes Registry, identity, training or commerce authority',()=>{
  const h=harness(),before=JSON.stringify(h.ctx.HUB69_DATA),X=h.ctx.HUB69Explore;
  for(const route of ['#hstdn/vn','#brand/sample-vn','#commerce','#technology/space'])h.go(route);
  assert.equal(JSON.stringify(h.ctx.HUB69_DATA),before);assert.equal(h.values.size,0);
  for(const r of [...X.brands,...X.markets])for(const field of ['id','parent','did','canonical'])assert.equal(r[field],null);
  assert.equal(X.brands.length,2);assert.ok(X.brands.every(r=>r.sample===true));
  assert.equal(X.filterRoute({view:'hstdn'},'country','__proto__'),null);
});

test('public design content during Core errors cannot show stale authenticated records',async()=>{
  const api={snapshot:async()=>{throw Object.assign(Error('No auth'),{status:401});},openai:async()=>({}),logout:async()=>{}};
  const h=harness({hash:'#hstdn',coreClient:api});await tick();await tick();
  assert.match(h.elements.get('hstdn-content').innerHTML,/Hai thương hiệu.*minh họa/);
  assert.equal(h.elements.get('records').innerHTML,'');assert.equal(h.elements.get('profile').innerHTML,'');
  h.go('#technology/space');await tick();await tick();
  assert.match(h.elements.get('technology-content').innerHTML,/NASA/);assert.equal(h.elements.get('saved-items').innerHTML.includes('691181'),false);
});

test('all new hrefs have implemented destinations or safe explicit external references',()=>{
  const h=harness(),X=h.ctx.HUB69Explore,P=h.ctx.HUB69P0;
  const routes=['#hstdn','#hstdn/vn','#hstdn/us','#hstdn/unknown','#brand/sample-vn','#brand/sample-us','#brand/amazon','#commerce','#commerce/vn','#commerce/us','#commerce/unknown','#technology','#technology/quantum','#technology/space','#technology/future'];
  for(const route of routes){
    const html=X.view(P.route(route));assert.ok(html.length>200);
    for(const [,href] of html.matchAll(/href="([^"]*)"/g)){
      assert.ok(href&&href!=='#',route);
      if(href.startsWith('#'))assert.equal(P.route(href).invalid,undefined,href);
      else assert.ok(h.ctx.HUB69Model.safeURL(href),href);
    }
    for(const [,attrs] of html.matchAll(/<a ([^>]*target="_blank"[^>]*)>/g))assert.match(attrs,/rel="noopener noreferrer"/);
    assert.doesNotMatch(html,/<form|data-save=|data-copy=|mailto:|affiliate=/);
  }
});

test('untrusted labels are escaped and unsafe source URL schemes are not made clickable',()=>{
  const h=harness(),X=h.ctx.HUB69Explore;
  const html=X.brandCard({...X.brands[0],key:'<svg onload=alert(1)>',name:'<img src=x>',description:'<script>x</script>'});
  assert.doesNotMatch(html,/<img|<script>|<svg/);assert.match(html,/&lt;img/);
  for(const url of ['javascript:alert(1)','data:text/html,x','https://user:password@example.com/','http://example.com/'])assert.doesNotMatch(X.out(url,'<img src=x>'),/href=/);
  assert.doesNotMatch(X.out('https://example.com/','<img src=x>'),/<img/);
});

test('versioned tokens are the single source of the generated CSS in both bundles',async()=>{
  const tokens=JSON.parse(await readFile(new URL('public/design-tokens.json',root),'utf8'));
  const {tokenCSS}=await import('../token-css.mjs');
  assert.equal(tokens.version,'1.1.0');
  for(const dir of ['public','dist','core-dist'])assert.equal(await readFile(new URL(dir+'/design-tokens.css',root),'utf8'),tokenCSS(tokens));
  assert.ok(Object.keys(tokens.cssVariables).length>=30);
});

test('standalone, snapshot and Core bundles all contain the same new UI without new network clients',async()=>{
  const js=await readFile(new URL('public/explore.js',root),'utf8');
  assert.doesNotMatch(js,/\bfetch\s*\(|XMLHttpRequest|WebSocket|localStorage|\/api\/|signatureVerified/);
  for(const dir of ['dist','core-dist'])assert.equal(await readFile(new URL(dir+'/explore.js',root),'utf8'),js);
  const standalone=await readFile(new URL('HUB69-review.html',root),'utf8');
  assert.ok(standalone.includes(js.trim()));assert.doesNotMatch(standalone,/<script[^>]+src=/);
  assert.doesNotMatch(standalone,/<link[^>]+stylesheet/);
  assert.match(await readFile(new URL('core-dist/registry.js',root),'utf8'),/records:\[\]/);
});

test('responsive source includes safe area, minimum touch targets, one-column mobile cards and readable forms',async()=>{
  const css=await readFile(new URL('public/style.css',root),'utf8'),html=await readFile(new URL('public/index.html',root),'utf8');
  assert.match(html,/width=device-width,initial-scale=1,viewport-fit=cover/);
  assert.match(css,/safe-area-inset-top/);assert.match(css,/safe-area-inset-bottom/);
  assert.match(css,/\.catalog-filter select\{[^}]*min-height:44px[^}]*font-size:16px/);
  assert.match(css,/@media\(max-width:700px\)\{\s*\.sidebar\{[\s\S]*?\.catalog-grid\{grid-template-columns:minmax\(0,1fr\)/);
  assert.match(css,/prefers-reduced-motion:reduce/);assert.match(css,/focus-visible/);
  assert.match(css,/\.catalog-view \.btn\{[^}]*max-width:100%[^}]*white-space:normal/);
});
