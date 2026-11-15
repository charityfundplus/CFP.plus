const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('id/index.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
async function render(path, failure){
  const nodes={}; const links=[]; let requests=0;
  const document={title:'',head:{appendChild:x=>links.push(x)},createElement:()=>({}),getElementById:id=>nodes[id]??=( {textContent:'',innerHTML:'',classList:{remove(){}}})};
  await vm.runInNewContext(script,{location:{pathname:path},document,fetch:async url=>{
    requests++;
    if(failure==='network')throw Error('offline');
    return {ok:failure!=='http',status:503,json:async()=>failure==='shape'?null:JSON.parse(fs.readFileSync('.'+url,'utf8'))};
  }});
  return {nodes,links,requests,document};
}
test('registered AI resolves the same identity with either trailing slash',async()=>{
  for(const path of ['/691181','/691181/']){
    const r=await render(path);assert.match(r.nodes.title.textContent,/ChatGPT/);
    assert.match(r.nodes.identity.textContent,/691181.*69118/);
    assert.equal(r.links[0].href,'https://cfp.plus/691181');
  }
});
test('leading zeros remain part of the ID',async()=>{
  const r=await render('/005');assert.equal(r.nodes.id.textContent,'005');assert.equal(r.links[0].href,'https://cfp.plus/005');
});
test('nested, nonnumeric and direct template paths cannot impersonate an ID',async()=>{
  for(const path of ['/691181/9','/id/','/abc','/691181<script>']){
    const r=await render(path);assert.equal(r.requests,0);assert.match(r.nodes.title.textContent,/không hợp lệ/);assert.equal(r.links.length,0);
  }
});
test('registry failures never become reserved or bound identities',async()=>{
  for(const failure of ['network','http','shape']){
    const r=await render('/691181',failure);assert.equal(r.nodes.title.textContent,'Chưa thể xác minh ID');assert.equal(r.nodes.office,undefined);assert.equal(r.links.length,0);
  }
});
