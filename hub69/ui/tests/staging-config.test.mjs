import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {createRequire} from 'node:module';
import {generateStaging,validateStaging} from '../staging-config.mjs';
const sourceSha='a'.repeat(40);

test('staging URL binds explicit HTTPS origin and exact App scope; production/local/credential inputs fail',()=>{
  assert.deepEqual(validateStaging({url:'https://staging.example.test/app/',expectedOrigin:'https://staging.example.test',sourceSha}),{url:'https://staging.example.test/app/',origin:'https://staging.example.test',sourceSha});
  for(const url of ['http://staging.example.test/app/','https://user:password@staging.example.test/app/','https://staging.example.test/app/?token=secret','https://staging.example.test/app/#x','https://cfp.plus/app/','https://cfp.plus./app/','https://localhost/app/','https://127.0.0.1/app/','https://[::1]/app/','https://staging.example.test/','https://staging.example.test/app'])assert.throws(()=>validateStaging({url,expectedOrigin:new URL(url).origin,sourceSha}),undefined,url);
  assert.throws(()=>validateStaging({url:'https://staging.example.test/app/',expectedOrigin:'https://different.example.test',sourceSha}));
  assert.throws(()=>validateStaging({url:'https://staging.example.test/app/',expectedOrigin:'https://staging.example.test',sourceSha:'HEAD'}));
});

test('generated staging assets/config use existing native projects without mutating default bundle/config',async()=>{
  const root=await mkdtemp(join(tmpdir(),'cfp-staging-config-'));
  try{
    await mkdir(join(root,'app-dist'));
    await writeFile(join(root,'app-dist','index.html'),'<main>Existing App</main>');
    await writeFile(join(root,'app-dist','config.js'),'window.HUB69_CONFIG={mode:"app"};\n');
    const base={appId:'plus.cfp.app',appName:'CFP+',webDir:'app-dist',server:{cleartext:false}};
    const original=JSON.stringify(base);
    await writeFile(join(root,'capacitor.config.json'),original);
    await writeFile(join(root,'package.json'),JSON.stringify({name:'cfp-hub69-ui',dependencies:{'@capacitor/core':'8.6.0'}}));
    const receipt=await generateStaging({url:'https://staging.example.test/app/',expectedOrigin:'https://staging.example.test',sourceSha},{root});
    assert.equal(receipt.deployed_source_verified,false);assert.equal(receipt.hosting_provisioned,false);
    assert.equal(await readFile(join(root,'capacitor.config.json'),'utf8'),original);
    assert.equal(await readFile(join(root,'app-dist','config.js'),'utf8'),'window.HUB69_CONFIG={mode:"app"};\n');
    assert.equal(await readFile(join(root,'staging-dist','index.html'),'utf8'),'<main>Existing App</main>');
    const runtime=await readFile(join(root,'staging-dist','config.js'),'utf8');assert.match(runtime,/approvedStagingOrigin/);assert.match(runtime,/sourceRevision/);assert.doesNotMatch(runtime,/<script/);
    const config=JSON.parse(await readFile(join(root,'staging-native','capacitor.config.json'),'utf8'));
    assert.equal(config.server.cleartext,false);assert.equal(config.android.allowMixedContent,false);assert.equal(config.webDir,'../staging-dist');
    assert.equal(resolve(root,'staging-native',config.android.path),join(root,'android'));
    assert.equal(resolve(root,'staging-native',config.ios.path),join(root,'ios'));
    // Exercise the actual pinned Capacitor loader, not a speculative --config flag.
    const require=createRequire(import.meta.url);
    const {loadConfig}=require('@capacitor/cli/dist/config.js');
    const previous=process.cwd();
    try{
      process.chdir(join(root,'staging-native'));
      const loaded=await loadConfig();
      assert.equal(loaded.app.webDirAbs,join(root,'staging-dist'));
      assert.equal(loaded.android.platformDirAbs,join(root,'android'));
      assert.equal(loaded.ios.platformDirAbs,join(root,'ios'));
      assert.equal(loaded.app.extConfig.server.url,'https://staging.example.test/app/');
    }finally{process.chdir(previous);}
  }finally{await rm(root,{recursive:true,force:true});}
});
