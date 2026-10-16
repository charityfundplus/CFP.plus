// Private sandbox filesystem recovery points. Uses the existing SQLite, audit and encryption mechanisms.
// No cloud adapter, network synchronization, key storage, production activation or Registry writes.
import {mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, lstatSync, realpathSync, openSync, fsyncSync, closeSync} from 'node:fs';
import {join, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {sha256} from './build-provenance.mjs';
import {encryptBackup, decryptBackup} from './backup-envelope.mjs';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {loadRegistryReadModel} from '../core/registry-read-model.mjs';

function checkedFile(dir, name, maximum) {
  const path = join(dir, name), stat = lstatSync(path);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > maximum) throw Error('RECOVERY_FILE_INVALID');
  return readFileSync(path);
}
function readPoint(directory) {
  const dir = realpathSync(directory), raw = checkedFile(dir, 'receipt.json', 65536), receipt = JSON.parse(raw);
  if (receipt.format !== 'cfp-hub69-recovery-v1' || !/^[a-f0-9]{64}$/.test(receipt.sha256)) throw Error('RECOVERY_RECEIPT_INVALID');
  const encrypted = checkedFile(dir, 'backup.encrypted', 48 * 1024 * 1024);
  if (encrypted.length !== receipt.bytes || sha256(encrypted) !== receipt.sha256) throw Error('RECOVERY_READBACK_MISMATCH');
  return {raw, receipt, encrypted};
}
function writePoint(directory, encrypted, receiptBytes) {
  // A point is immutable by convention and exclusive creation, not WORM storage.
  mkdirSync(directory, {mode: 0o700});
  writeFileSync(join(directory, 'backup.encrypted'), encrypted, {flag: 'wx', mode: 0o600});
  writeFileSync(join(directory, 'receipt.json'), receiptBytes, {flag: 'wx', mode: 0o600});
  for (const path of [join(directory, 'backup.encrypted'), join(directory, 'receipt.json'), directory, dirname(directory)]) {
    const fd = openSync(path, 'r'); try { fsyncSync(fd); } finally { closeSync(fd); }
  }
  const readback = readPoint(directory);
  if (!readback.encrypted.equals(encrypted) || !readback.raw.equals(receiptBytes)) throw Error('RECOVERY_READBACK_MISMATCH');
  return readback.receipt;
}
export function createRecoveryPoint({service, token, destination, publicKey}) {
  const registry = loadRegistryReadModel().validation().provenance;
  const lease = service.maintenanceLease(token), temp = mkdtempSync(join(tmpdir(), 'cfp-recovery-'));
  try {
    const database = join(temp, 'checkpoint.db'), manifest = lease.backup(database);
    if (lstatSync(database).size > 20 * 1024 * 1024) throw Error('RECOVERY_DB_LIMIT');
    const metadata = {format: 'cfp-hub69-recovery-v1', scope: 'PRIVATE SANDBOX / LOCAL FILESYSTEM REPLICA',
      checkpoint: manifest.checkpoint, registry, remoteSynchronized: false, externalCalls: 0,
      activationAllowed: false, independentCustodyVerified: false};
    const payload = Buffer.from(JSON.stringify({format: 'cfp-hub69-db-v1', database: readFileSync(database).toString('base64'), manifest, metadata}));
    let encrypted;
    try { encrypted = encryptBackup(payload, publicKey); } finally { payload.fill(0); }
    const receipt = {...metadata, sha256: sha256(encrypted), bytes: encrypted.length};
    return writePoint(destination, encrypted, Buffer.from(JSON.stringify(receipt)));
  } finally { lease.release(); rmSync(temp, {recursive: true, force: true}); }
}
export function replicateRecoveryPoint(source, destination) {
  const {raw, receipt, encrypted} = readPoint(source);
  writePoint(destination, encrypted, raw);
  return {sha256: receipt.sha256, bytes: receipt.bytes, readbackMatched: true, contentAuthenticated: false, remoteSynchronized: false, externalCalls: 0};
}
export function restoreRecoveryPoint({source, destination, privateKey}) {
  const {receipt, encrypted} = readPoint(source), payload = decryptBackup(encrypted, privateKey);
  const temp = mkdtempSync(join(tmpdir(), 'cfp-restore-'));
  try {
    const archive = JSON.parse(payload), database = join(temp, 'checkpoint.db');
    if (archive.format !== 'cfp-hub69-db-v1' || typeof archive.database !== 'string') throw Error('RECOVERY_ARCHIVE_INVALID');
    const {sha256: ciphertextHash, bytes: ciphertextBytes, ...metadata} = receipt;
    if (JSON.stringify(metadata) !== JSON.stringify(archive.metadata)) throw Error('RECOVERY_METADATA_MISMATCH');
    const bytes = Buffer.from(archive.database, 'base64');
    if (sha256(bytes) !== archive.manifest?.sha256 || JSON.stringify(archive.manifest.checkpoint) !== JSON.stringify(receipt.checkpoint)) throw Error('RECOVERY_ARCHIVE_MISMATCH');
    try { writeFileSync(database, bytes, {flag: 'wx', mode: 0o600}); } finally { bytes.fill(0); }
    writeFileSync(database + '.json', JSON.stringify(archive.manifest), {flag: 'wx', mode: 0o600});
    const service = P2Sandbox.restore(database, destination);
    return {service, receipt, restoredToNewGeneration: true, sessionsRevoked: true, activationAllowed: false};
  } finally { payload.fill(0); rmSync(temp, {recursive: true, force: true}); }
}
