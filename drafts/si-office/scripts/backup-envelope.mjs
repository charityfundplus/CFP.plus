import {randomBytes,createCipheriv,createDecipheriv,publicEncrypt,privateDecrypt,createPublicKey,createHash,constants} from 'node:crypto';
const aad=Buffer.from('CFP-PREVIEW-RECIPIENT-BACKUP-v1');
const hash=b=>createHash('sha256').update(b).digest('hex');
// Public recipient only on host. Private key belongs to off-host custodian.
// Bounded in-memory preview archives; refuse large payloads instead of OOM.
export function encryptBackup(payload,publicKey){
 if(!Buffer.isBuffer(payload)||payload.length>32*1024*1024)throw Error('ARCHIVE_LIMIT');
 const recipient=createPublicKey(publicKey);if(recipient.asymmetricKeyType!=='rsa'||recipient.asymmetricKeyDetails.modulusLength<3072)throw Error('RECIPIENT_RSA3072_REQUIRED');
 const key=randomBytes(32),iv=randomBytes(12);try{
  const c=createCipheriv('aes-256-gcm',key,iv);c.setAAD(aad);const body=Buffer.concat([c.update(payload),c.final()]);
  const wrapped=publicEncrypt({key:recipient,oaepHash:'sha256',padding:constants.RSA_PKCS1_OAEP_PADDING},key);
  return Buffer.from(JSON.stringify({format:1,algorithm:'RSA-OAEP-SHA256/AES-256-GCM',recipient:hash(recipient.export({type:'spki',format:'der'})),iv:iv.toString('base64'),tag:c.getAuthTag().toString('base64'),wrapped:wrapped.toString('base64'),body:body.toString('base64')}));
 }finally{key.fill(0);}
}
export function decryptBackup(envelope,privateKey){
 if(envelope.length>48*1024*1024)throw Error('ARCHIVE_LIMIT');
 const e=JSON.parse(envelope);if(e.format!==1||e.algorithm!=='RSA-OAEP-SHA256/AES-256-GCM')throw Error('FORMAT');
 const recipient=createPublicKey(privateKey);if(hash(recipient.export({type:'spki',format:'der'}))!==e.recipient)throw Error('RECIPIENT_MISMATCH');
 const key=privateDecrypt({key:privateKey,oaepHash:'sha256',padding:constants.RSA_PKCS1_OAEP_PADDING},Buffer.from(e.wrapped,'base64'));
 try{const d=createDecipheriv('aes-256-gcm',key,Buffer.from(e.iv,'base64'));d.setAAD(aad);d.setAuthTag(Buffer.from(e.tag,'base64'));return Buffer.concat([d.update(Buffer.from(e.body,'base64')),d.final()]);}finally{key.fill(0);}
}
