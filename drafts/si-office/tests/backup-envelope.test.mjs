import {test} from 'node:test';import assert from 'node:assert/strict';
import {generateKeyPairSync,randomBytes,createHash} from 'node:crypto';
import {mkdtempSync,readFileSync,writeFileSync,rmSync} from 'node:fs';import {join} from 'node:path';import {tmpdir} from 'node:os';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {encryptBackup,decryptBackup} from '../scripts/backup-envelope.mjs';
test('Recipient-public-only encrypted consistent DB/receipt archive restores latest intake in separate generation',async()=>{
 const directory=mkdtempSync(join(tmpdir(),'cfp-recipient-backup-'));let service,restored;try{
 const password=randomBytes(24).toString('hex');service=new P2Sandbox(join(directory,'live.db'));service.provision({id:'custodian',password,role:'editor',workspace:'synthetic-space',maintainer:true});const token=service.login('custodian',password);
 await service.execute(token,'officeCreate',{pairKey:'hub69-content-demo',kind:'application',input:{name:'Synthetic recovery intake',entityType:'enterprise',contact:'https://example.org',relationships:[],commitment:true,synthetic:true}});
 const path=join(directory,'snapshot.db'),manifest=service.backup(token,path),before=service.verify();
 const {publicKey,privateKey}=generateKeyPairSync('rsa',{modulusLength:3072,publicKeyEncoding:{type:'spki',format:'pem'},privateKeyEncoding:{type:'pkcs8',format:'pem'}});
 const payload=Buffer.from(JSON.stringify({database:readFileSync(path).toString('base64'),manifest,receipt:{synthetic:true,accounts:[{id:'custodian',password}]}}));
 const envelope=encryptBackup(payload,publicKey);assert(!envelope.includes(Buffer.from(password)));assert(!envelope.includes(Buffer.from('PRIVATE KEY')));
 const stored=join(directory,'receiver.enc');writeFileSync(stored,envelope,{flag:'wx',mode:0o600});assert.deepEqual(readFileSync(stored),envelope);
 const wrong=generateKeyPairSync('rsa',{modulusLength:3072});assert.throws(()=>decryptBackup(envelope,wrong.privateKey),/RECIPIENT_MISMATCH/);
 const damaged=JSON.parse(envelope),body=Buffer.from(damaged.body,'base64');body[0]^=1;damaged.body=body.toString('base64');assert.throws(()=>decryptBackup(Buffer.from(JSON.stringify(damaged)),privateKey));
 const decoded=JSON.parse(decryptBackup(readFileSync(stored),privateKey)),downloaded=join(directory,'downloaded.db');writeFileSync(downloaded,Buffer.from(decoded.database,'base64'),{mode:0o600});writeFileSync(downloaded+'.json',JSON.stringify(decoded.manifest),{mode:0o600});
 assert.equal(createHash('sha256').update(readFileSync(downloaded)).digest('hex'),manifest.sha256);restored=P2Sandbox.restore(downloaded,join(directory,'isolated.db'));assert.throws(()=>restored.context(token),/AUTH_DENIED/);
 const fresh=restored.login('custodian',decoded.receipt.accounts[0].password),office=await restored.execute(fresh,'officeSnapshot',{pairKey:'hub69-content-demo'});assert.equal(office.registrations[0].name,'Synthetic recovery intake');assert.equal(office.registrations[0].id,null);assert.deepEqual(service.verify(),before);
 }finally{restored?.close();service?.close();rmSync(directory,{recursive:true,force:true});}
});
