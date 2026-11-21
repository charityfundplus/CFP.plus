// Kiểm manifest mới cho PR #124 @ e994ea8 (chỉ toàn vẹn byte). Dùng:
//   node verify.mjs <đường dẫn tới drafts/si-office đã checkout ở e994ea8>
import {readFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import path from 'node:path';import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(process.argv[2]||'.');
const raw=await readFile(path.join(here,'PR124_HEAD_E994EA8_MANIFEST.json'));
const want=(await readFile(path.join(here,'PR124_HEAD_E994EA8_MANIFEST.sha256'),'utf8')).split(/\s+/)[0];
if(createHash('sha256').update(raw).digest('hex')!==want)throw Error('Manifest checksum mismatch');
const m=JSON.parse(raw);const bad=[];
for(const f of m.files){const p=path.resolve(root,f.path);if(!p.startsWith(root+path.sep))throw Error('Unsafe path');let b;try{b=await readFile(p)}catch{bad.push(f.path+' (missing)');continue}
 if(b.length!==f.bytes||createHash('sha256').update(b).digest('hex')!==f.sha256)bad.push(f.path);}
if(bad.length){console.log('MISMATCH '+bad.length+'/'+m.files.length+': '+bad.join(', '));process.exit(1)}
console.log('VERIFIED '+m.files.length+'/'+m.files.length+' @ '+m.sourceCommit.slice(0,7)+'; integrity only.');
