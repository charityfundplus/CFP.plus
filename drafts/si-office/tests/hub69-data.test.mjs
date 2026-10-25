import {test} from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync} from 'node:crypto';
import {mkdtempSync, rmSync, readFileSync, writeFileSync, statSync, existsSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createRecoveryPoint, replicateRecoveryPoint, restoreRecoveryPoint} from '../scripts/hub69-data.mjs';
const password = 'Synthetic-recovery-password';
const keys = generateKeyPairSync('rsa', {modulusLength: 3072, publicKeyEncoding: {type: 'spki', format: 'pem'}, privateKeyEncoding: {type: 'pkcs8', format: 'pem'}});
function fixture() {
  const dir = mkdtempSync(join(tmpdir(), 'cfp-hub69-data-')), service = new P2Sandbox(join(dir, 'original.db'));
  for (const [id, role, maintainer, pairs] of [['admin', 'reviewer', true, ['*']], ['limited', 'reviewer', true, ['hub69-content-demo']], ['editor', 'editor', false, ['*']]]) service.provision({id, password, role, maintainer, pairs, workspace: 'alpha'});
  return {dir, service, token: id => service.login(id, password), clean() { service.close(); rmSync(dir, {recursive: true, force: true}); }};
}
test('encrypted checkpoint -> second local replica -> isolated restore retains output/audit, revokes sessions and keeps original DB', async () => {
  const x = fixture(); let restored; try {
    const editor = x.token('editor'), admin = x.token('admin');
    const task = await x.service.execute(editor, 'createTask', {pairKey: 'hub69-content-demo', input: {kind: 'website-draft', title: 'PRIVATE-RECOVERY-OUTPUT', text: 'Synthetic retained evidence', resource: 'website-demo'}}, {idempotencyKey: 'recovery'});
    await x.service.execute(editor, 'runTask', {taskKey: task.key}); await x.service.execute(admin, 'reviewTask', {taskKey: task.key, verdict: 'acknowledge-draft'});
    x.service.readRegistry(editor, 'project', {id: '691181'}); const before = x.service.verify();
    const point = join(x.dir, 'point'), replica = join(x.dir, 'replica');
    const receipt = createRecoveryPoint({service: x.service, token: admin, destination: point, publicKey: keys.publicKey});
    assert.equal(receipt.registry.sourceBytesVerified, true); assert.equal(receipt.remoteSynchronized, false);
    assert(!readFileSync(join(point, 'backup.encrypted'), 'utf8').includes('PRIVATE-RECOVERY-OUTPUT'));
    assert.equal(statSync(point).mode & 0o777, 0o700); assert.equal(statSync(join(point, 'backup.encrypted')).mode & 0o777, 0o600);
    const sync = replicateRecoveryPoint(point, replica); assert.equal(sync.readbackMatched, true); assert.equal(sync.externalCalls, 0);
    const result = restoreRecoveryPoint({source: replica, destination: join(x.dir, 'restored.db'), privateKey: keys.privateKey}); restored = result.service;
    assert.equal(result.sessionsRevoked, true); await assert.rejects(restored.execute(editor, 'snapshot'), /AUTH_DENIED/);
    const snapshot = await restored.execute(restored.login('editor', password), 'snapshot');
    assert.equal(snapshot.tasks[0].key, task.key); assert.equal(snapshot.tasks[0].status, 'REVIEWED DRAFT'); assert.equal(snapshot.tasks[0].output.title, 'PRIVATE-RECOVERY-OUTPUT');
    assert.deepEqual(x.service.verify(), before); assert(existsSync(join(x.dir, 'original.db')));
    assert.throws(() => restoreRecoveryPoint({source: point, destination: join(x.dir, 'restored.db'), privateKey: keys.privateKey}), /DESTINATION_EXISTS/);
    assert.throws(() => replicateRecoveryPoint(point, replica), /EEXIST/);
  } finally { restored?.close(); x.clean(); }
});
test('full-database backup and recovery point deny a maintainer with limited pair grants and ordinary editors', () => {
  const x = fixture(); try {
    for (const id of ['limited', 'editor']) {
      const token = x.token(id); assert.throws(() => x.service.backup(token, join(x.dir, id + '.db')), /MAINTAINER_REQUIRED/);
      assert.throws(() => createRecoveryPoint({service: x.service, token, destination: join(x.dir, id), publicKey: keys.publicKey}), /MAINTAINER_REQUIRED/);
      assert.equal(existsSync(join(x.dir, id + '.db')), false); assert.equal(existsSync(join(x.dir, id)), false);
    }
  } finally { x.clean(); }
});
test('tampering and wrong private key fail before restore; corrupt replica cannot be synchronized or overwrite original state', () => {
  const x = fixture(); try {
    const point = join(x.dir, 'point'); createRecoveryPoint({service: x.service, token: x.token('admin'), destination: point, publicKey: keys.publicKey});
    const wrong = generateKeyPairSync('rsa', {modulusLength: 3072, privateKeyEncoding: {type: 'pkcs8', format: 'pem'}}).privateKey;
    assert.throws(() => restoreRecoveryPoint({source: point, destination: join(x.dir, 'wrong.db'), privateKey: wrong}), /RECIPIENT_MISMATCH/);
    assert.equal(existsSync(join(x.dir, 'wrong.db')), false);
    const path = join(point, 'backup.encrypted'), bytes = readFileSync(path); bytes[10] ^= 1; writeFileSync(path, bytes);
    assert.throws(() => replicateRecoveryPoint(point, join(x.dir, 'replica')), /READBACK_MISMATCH/);
    assert.throws(() => restoreRecoveryPoint({source: point, destination: join(x.dir, 'bad.db'), privateKey: keys.privateKey}), /READBACK_MISMATCH/);
    assert.equal(existsSync(join(x.dir, 'bad.db')), false); assert.equal(existsSync(join(x.dir, 'replica')), false);
  } finally { x.clean(); }
});
test('rehashed public receipt cannot forge Registry provenance or activation status outside the authenticated archive', () => {
  const x = fixture(); try {
    const point = join(x.dir, 'point'); createRecoveryPoint({service: x.service, token: x.token('admin'), destination: point, publicKey: keys.publicKey});
    const path = join(point, 'receipt.json'), receipt = JSON.parse(readFileSync(path));
    receipt.registry.revision = 'f'.repeat(40); receipt.activationAllowed = true; writeFileSync(path, JSON.stringify(receipt));
    assert.throws(() => restoreRecoveryPoint({source: point, destination: join(x.dir, 'forged.db'), privateKey: keys.privateKey}), /METADATA_MISMATCH/);
    assert.equal(existsSync(join(x.dir, 'forged.db')), false);
  } finally { x.clean(); }
});
