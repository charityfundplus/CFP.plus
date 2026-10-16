import {test} from 'node:test';
import assert from 'node:assert/strict';
import {reconcileRegistryScopes, reviewPositions} from '../scripts/compare-registry-scopes.mjs';
const page = text => ({id: 'synthetic', text, verification: {state: 'unverified'}});
const row = (ordinal, id) => '<tr>' + [ordinal, id, 'Name', 'Proposed', 'Full', 'Link', 'Master hiện hữu', 'REVIEW REQUIRED', 'Note'].map(c => '<td>' + c + '</td>').join('') + '</tr>';
test('offline comparison preserves scopes, zeros, duplicate source rows and unknown Parent/DID', () => {
  const reviewPage = page('REVIEW ONLY' + row(1, '003') + row(2, '333'));
  const masterPage = page('1. **003** • Agent ref: synthetic\n2. **333** • Agent ref: first\n3. **333** • Agent ref: second');
  const entityRegistry = {'69118': {id: '69118', type: 'developer'}, '691181': {id: '691181', type: 'ai'}};
  const before = JSON.stringify({reviewPage, masterPage, entityRegistry});
  const result = reconcileRegistryScopes({entityRegistry, reviewPage, masterPage, entityProvenance: {synthetic: true}});
  assert.deepEqual(result.comparison.exactIDIntersection, []); assert.equal(result.comparison.countsAreCoverageRatio, false);
  assert.equal(result.masterInventory.sourceRows, 3); assert.equal(result.masterInventory.duplicateSourceIDs[0].id, '333');
  assert.equal(result.reviewPositions.rows[0].id, '003'); assert(result.reviewPositions.rows.every(r => r.parent === null && r.did === null));
  assert.equal(result.registryWrites, 0); assert.equal(result.importedReviewRecords, 0);
  assert.equal(JSON.stringify({reviewPage, masterPage, entityRegistry}), before);
});
test('incomplete pages, wrong source status and entity key conflicts cannot be used as evidence', () => {
  assert.throws(() => reviewPositions({...page('REVIEW ONLY'), truncated: true}), /INCOMPLETE/);
  assert.throws(() => reviewPositions({...page('REVIEW ONLY'), unknown_block_count: 1}), /INCOMPLETE/);
  assert.throws(() => reviewPositions(page('APPROVED')), /STATUS_UNEXPECTED/);
  assert.throws(() => reconcileRegistryScopes({entityRegistry: {'003': {id: '3'}}, reviewPage: page(''), masterPage: page('')}), /KEY_CONFLICT/);
});
