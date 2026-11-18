// Run: node --test docs/si-ai-platform/tools/link-audit.test.mjs  (offline: no network request is made)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { auditUrl, requireNumericId, repoPresence, loadInventory } from './link-audit.mjs';

test('LA-1 only https://cfp.plus/<digits>/ can be built', () => {
  assert.equal(auditUrl('003'), 'https://cfp.plus/003/');
  for (const bad of ['../etc', '69/../1', '-o/tmp/x', '1?x=1', 'abc', '', '1'.repeat(33), 12, null]) {
    assert.throws(() => auditUrl(bad), /NUMERIC_ID_REQUIRED/, String(bad));
    assert.throws(() => repoPresence(bad), /NUMERIC_ID_REQUIRED/, String(bad));
  }
});

test('LA-2 every committed inventory ID passes validation (leading zeros kept)', () => {
  const rows = loadInventory().rows;
  assert.equal(rows.length, 91);
  for (const r of rows) assert.equal(requireNumericId(r.id), r.id);
});
