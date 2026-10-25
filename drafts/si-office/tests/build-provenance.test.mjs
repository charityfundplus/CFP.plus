import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {trainingWorksheet} from '../scripts/training-export-worksheet.mjs';
import {createHash} from 'node:crypto';
import {executionProvenance,verifyExportProvenance,gitRead} from '../scripts/build-provenance.mjs';
function fixture(fn){
 const root=mkdtempSync(join(tmpdir(),'provenance-'));
 const git=(...args)=>gitRead(root,...args);
 try{git('init','-q');git('config','user.name','Synthetic Fixture');git('config','user.email','fixture@example.invalid');mkdirSync(join(root,'public'));writeFileSync(join(root,'public','app.js'),'export const synthetic=true;\n');writeFileSync(join(root,'main.mjs'),'import "./public/app.js";\n');git('add','.');git('commit','-qm','synthetic source fixture');fn(root,git);}finally{rmSync(root,{recursive:true,force:true});}
}
test('derives revision and manifest from exact checkout bytes without granting authority',()=>fixture((root,git)=>{
 const p=executionProvenance(root);assert.equal(p.verified,true);assert.equal(p.revision,git('rev-parse','HEAD').toString().trim());assert.equal(p.manifest.files.length,2);assert.equal(p.authorityVerified,false);assert.equal(p.activationAllowed,false);assert.deepEqual(verifyExportProvenance(p,root),p);assert.equal(executionProvenance(join(root,'public')).manifest.files.length,1);
 const forged=structuredClone(p);forged.revision='a'.repeat(40);assert.throws(()=>verifyExportProvenance(forged,root),/PROVENANCE_MISMATCH/);
}));
test('tampered runtime source, untracked runtime and symlinks fail closed',()=>fixture(root=>{
 const original='import "./public/app.js";\n';
 writeFileSync(join(root,'main.mjs'),'tampered');assert.equal(executionProvenance(root).verified,false);writeFileSync(join(root,'main.mjs'),original);
 writeFileSync(join(root,'injected.mjs'),'injected');assert.equal(executionProvenance(root).finding,'UNTRACKED_RUNTIME_SOURCE');rmSync(join(root,'injected.mjs'));
 rmSync(join(root,'main.mjs'));symlinkSync(join(root,'public','app.js'),join(root,'main.mjs'));assert.equal(executionProvenance(root).finding,'SOURCE_FILE_INVALID');
}));
test('rehashed forged manifest and absent Git cannot become verified',()=>fixture(root=>{
 const forged=executionProvenance(root);forged.manifest.files[0].sha256='f'.repeat(64);assert.throws(()=>verifyExportProvenance(forged,root),/PROVENANCE_MISMATCH/);
 const missing=mkdtempSync(join(tmpdir(),'no-git-'));try{assert.equal(executionProvenance(missing).verified,false);}finally{rmSync(missing,{recursive:true,force:true});}
}));

test('worksheet verifies independent Git bytes and binds export revision, retaining HOLD and unassessed',()=>fixture(root=>{
 const build=executionProvenance(root);const p={format:'cfp-training-evidence-v1',journey:{subject:'synthetic-learner',pairKey:'fixture',basicDraftReady:true},tasks:[],observations:[],feedback:[],sourceRevision:build.revision,buildProvenance:build};
 const envelope=()=>{const payloadJSON=JSON.stringify(p);return {payloadJSON,digestOf:'UTF-8 payloadJSON bytes',sha256:createHash('sha256').update(payloadJSON).digest('hex')};};
 const program={basic:{lessons:[]},exercises:[],advanced:[{key:'fixture',prerequisites:[]}]},scope={developmentRevision:build.revision,allowedPairs:['fixture'],sourceRoot:root};
 const w=trainingWorksheet(envelope(),program,scope);assert.equal(w.sourceRevisionVerified,true);assert.equal(w.buildManifestSha256,build.manifestSha256);assert.equal(w.activation,'HOLD');assert.equal(w.advanced[0].competencyPass,false);
 p.sourceRevision='a'.repeat(40);assert.throws(()=>trainingWorksheet(envelope(),program,scope),/SOURCE_REVISION_MISMATCH/);p.sourceRevision=build.revision;writeFileSync(join(root,'main.mjs'),'tampered');assert.throws(()=>trainingWorksheet(envelope(),program,scope),/PROVENANCE_MISMATCH/);
}));
