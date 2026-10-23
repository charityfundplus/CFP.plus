import {iconPNG} from './pwa-icon.mjs';
import {tokenCSS} from './token-css.mjs';
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {existsSync} from 'node:fs';
const root=new URL('./',import.meta.url);
const tokens=JSON.parse(await readFile(new URL('public/design-tokens.json',root),'utf8'));
await writeFile(new URL('public/design-tokens.css',root),tokenCSS(tokens));
const pins=JSON.parse(await readFile(new URL('integration/source-pins.json',root),'utf8'));
const trainingRaw=await readFile(new URL('evidence/training-basic-v1.json',root));
const trainingPin=pins.files.find(f=>f.path.endsWith('/training-basic-v1.json'));
if(createHash('sha256').update(trainingRaw).digest('hex')!==trainingPin.sha256)throw Error('TRAINING_SOURCE_INTEGRITY_FAILURE');
const training={curriculum:JSON.parse(trainingRaw),source:{revision:pins.codex1Revision,sha256:trainingPin.sha256,url:'https://github.com/charityfundplus/CFP.plus/blob/'+pins.codex1Revision+'/'+trainingPin.path}};
await writeFile(new URL('public/training-data.js',root),'window.HUB69_TRAINING='+JSON.stringify(training).replace(/</g,'\\u003c')+';\n');
await writeFile(new URL('public/config.js',root),'window.HUB69_CONFIG={mode:"snapshot"};\n');
// In CFP.plus use the existing Registry. A Site export carries only its pinned evidence copy.
const canonical=new URL('../../registry/ai-entity-registry.json',root);
const registryPath=existsSync(canonical)?canonical:new URL('evidence/ai-entity-registry.json',root);
const raw=await readFile(registryPath,'utf8');
const bytes=Buffer.from(raw),registryBlobSHA=createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');
if(registryBlobSHA!=='1f18068d66379ce90bb079dc56c77b4c4d66dcdf')throw Error('SOURCE_BLOB_INTEGRITY_FAILURE: review a new revision explicitly');
const sourceCommit='835616308111f6851c0387fa9f5eda60c9ffa624';
const sourceURL='https://github.com/charityfundplus/CFP.plus/blob/'+sourceCommit+'/registry/ai-entity-registry.json';
const records=Object.values(JSON.parse(raw)).filter(r=>r.id).map(r=>({...r,sourceCanonical:r.public_link||'https://cfp.plus/'+r.id,conflict:r.ai_country_id==='6911',identityVerified:false,operationsAllowed:false,chapter:null,hstdn:null,provenance:{registryURL:sourceURL,sourceRevision:sourceCommit,registryBlobSHA,sourceSHA256:createHash('sha256').update(raw).digest('hex')}}));
if(records.length!==26||new Set(records.map(r=>r.id)).size!==26)throw Error('SOURCE_RECORD_COUNT_OR_DUPLICATE_CHANGED');
const data={sourceCommit,registryBlobSHA,sourceSHA256:createHash('sha256').update(raw).digest('hex'),sourceURL,activationAllowed:false,published:false,records};
await writeFile(new URL('public/registry.js',root),'window.HUB69_DATA='+JSON.stringify(data).replace(/</g,'\\u003c')+';\n');
await mkdir(new URL('dist/',root),{recursive:true});
for(const size of [192,512])await writeFile(new URL('public/icon-'+size+'.png',root),iconPNG(size));
const names=['manifest.webmanifest','pwa.js','sw.js','offline.html','icon-192.png','icon-512.png','index.html','design-tokens.css','style.css','design-system.css','design-tokens.json','config.js','registry.js','training-data.js','model.js','workspace.js','hstdn-review.js','explore.js','p0.js','core-binding.js','training.js','app.js'];
for(const name of names)await copyFile(new URL('public/'+name,root),new URL('dist/'+name,root));
// A same-origin mount for Codex 1. No snapshot rows are shipped in Core mode.
await mkdir(new URL('core-dist/',root),{recursive:true});
for(const name of names)await copyFile(new URL('public/'+name,root),new URL('core-dist/'+name,root));
await writeFile(new URL('core-dist/config.js',root),'window.HUB69_CONFIG={mode:"core"};\n');
await writeFile(new URL('core-dist/registry.js',root),'window.HUB69_DATA={records:[],activationAllowed:false,published:false};\n');
let html=await readFile(new URL('public/index.html',root),'utf8');
// Standalone file review never installs a worker or loads external PWA assets.
html=html.replace(/  <link rel="(?:manifest|apple-touch-icon)"[^>]*>\n/g,'');
for(const name of ['design-tokens.css','style.css','design-system.css'])html=html.replace('<link rel="stylesheet" href="'+name+'">','<style>'+await readFile(new URL('public/'+name,root),'utf8')+'</style>');
const scripts=[];
for(const name of names.filter(n=>n.endsWith('.js'))){
  html=html.replace('<script src="'+name+'" defer></script>','');
  scripts.push('<script>'+String(await readFile(new URL('public/'+name,root),'utf8')).replace(/<\/script/gi,'<\\/script')+'</script>');
}
await writeFile(new URL('HUB69-review.html',root),html.replace('</body>',scripts.join('\n')+'\n</body>'));
console.log(JSON.stringify({records:records.length,ai:6,developers:20,registryBlobSHA,sourceSHA256:data.sourceSHA256,published:false}));

