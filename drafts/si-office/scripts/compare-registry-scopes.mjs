// Offline comparison of existing source exports. This is evidence, never an API
// input, Master Registry, identity allocation, membership import or writeback.
import {readFileSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {sha256} from './build-provenance.mjs';
const numeric = value => typeof value === 'string' && /^\d+$/.test(value);
const unique = values => [...new Set(values)];
function pageText(page) {
  if (typeof page?.text !== 'string' || page.truncated === true || page.unknown_block_count > 0) throw Error('SOURCE_PAGE_INCOMPLETE');
  return page.text;
}
export function reviewPositions(page) {
  const text = pageText(page);
  if (!text.includes('REVIEW ONLY')) throw Error('REVIEW_SOURCE_STATUS_UNEXPECTED');
  return [...text.matchAll(/<tr>\s*([\s\S]*?)\s*<\/tr>/g)].flatMap(match => {
    const cells = [...match[1].matchAll(/<td>([\s\S]*?)<\/td>/g)].map(c => c[1].trim());
    if (cells.length !== 9 || !numeric(cells[0]) || !numeric(cells[1])) return [];
    return [{sourceOrdinal: Number(cells[0]), id: cells[1], originalName: cells[2], proposedName: cells[3],
      sourceClass: cells[6], sourceStatus: cells[7], note: cells[8],
      parent: null, did: null, bindingStatus: 'REVIEW ONLY; NOT IMPORTED'}];
  });
}
export function masterPositions(page) {
  return pageText(page).split('\n').flatMap((line, index) => {
    const match = /^(\d+)\.\s+\*\*(\d+)\*\*/.exec(line);
    return match && line.includes('Agent ref:') ? [{id: match[2], sourceLine: index + 1, sourceOrdinal: Number(match[1])}] : [];
  });
}
const pageEvidence = page => ({id: page.id, url: page.url, title: page.title,
  pageLastEditedAt: page.page_last_edited_at ?? null, nativeVerification: page.verification ?? null,
  fetchedTextSha256: sha256(pageText(page)), hashScope: 'EXACT FETCHED ENHANCED MARKDOWN; NOT NATIVE NOTION BLOCK HASH',
  unknownBlockReporting: page.unknown_block_count === undefined ? 'NOT EXPOSED' : page.unknown_block_count});

export function reconcileRegistryScopes({entityRegistry, entityProvenance, reviewPage, masterPage}) {
  const bindings = Object.entries(entityRegistry).filter(([key]) => !key.startsWith('_')).map(([key, row]) => {
    if (!numeric(key) || key !== row.id) throw Error('ENTITY_SOURCE_KEY_CONFLICT'); return row;
  });
  const review = reviewPositions(reviewPage), master = masterPositions(masterPage);
  if (!review.length || !master.length) throw Error('SOURCE_ROWS_MISSING');
  const bindingIDs = bindings.map(r => r.id), reviewIDs = unique(review.map(r => r.id)), masterIDs = unique(master.map(r => r.id));
  const intersection = bindingIDs.filter(id => reviewIDs.includes(id));
  const additions = reviewIDs.filter(id => !masterIDs.includes(id));
  const duplicates = masterIDs.filter(id => master.filter(r => r.id === id).length > 1).map(id => ({id, sourceRows: master.filter(r => r.id === id)}));
  const check = (name, pass) => ({name, result: pass ? 'PASS' : 'FAIL'});
  return {
    schemaVersion: 1, scope: 'OFFLINE CROSS-SCOPE RECONCILIATION; NOT MEMBERSHIP OR ID AUTHORITY',
    generatedAt: new Date().toISOString(), registryWrites: 0, importedReviewRecords: 0, activationAllowed: false,
    source: {entityProvenance, review: pageEvidence(reviewPage), master: pageEvidence(masterPage)},
    entityBindings: {count: bindings.length, counts: Object.fromEntries(unique(bindings.map(r => r.type)).map(type => [type, bindings.filter(r => r.type === type).length])), ids: bindingIDs},
    reviewPositions: {count: review.length, distinctIDs: reviewIDs.length, status: 'REVIEW ONLY',
      sourceClasses: Object.fromEntries(unique(review.map(r => r.sourceClass)).map(kind => [kind, review.filter(r => r.sourceClass === kind).length])),
      rows: review},
    masterInventory: {sourceRows: master.length, distinctIDs: masterIDs.length, duplicateSourceIDs: duplicates,
      note: 'Source rows retained; the CFP+ 333 role clarification does not authorize automatic merge, deletion or Parent edits.'},
    comparison: {exactIDIntersection: intersection, reviewIDsAbsentFromMaster: additions,
      masterIDsAbsentFromReview: masterIDs.filter(id => !reviewIDs.includes(id)),
      countsAreCoverageRatio: false, membershipVerified: false, sourceScopesAreDistinct: true,
      conclusion: 'Developer/AI bindings and review positions describe different scopes. ID absence in this JSON does not reject a pair, and presence in a review queue does not authorize runtime binding.'},
    checks: [check('JSON_BINDINGS_26', bindings.length === 26), check('JSON_20_DEVELOPER_6_AI', bindings.filter(r => r.type === 'developer').length === 20 && bindings.filter(r => r.type === 'ai').length === 6),
      check('REVIEW_91_DISTINCT_POSITIONS', review.length === 91 && reviewIDs.length === 91),
      check('MASTER_84_ROWS_83_IDS', master.length === 84 && masterIDs.length === 83),
      check('REVIEW_COVERS_MASTER_IDS', masterIDs.every(id => reviewIDs.includes(id))),
      check('EIGHT_ADDITIONAL_REVIEW_IDS', additions.length === 8),
      check('REVIEW_SOURCE_CLASSES_MATCH_MASTER', review.every(r => r.sourceClass === (masterIDs.includes(r.id) ? 'Master hiện hữu' : 'Bổ sung đối chiếu'))),
      check('NO_REVIEW_BINDING_OR_PARENT_INFERENCE', review.every(r => r.parent === null && r.did === null))],
    blockers: ['NO_AUTHORITATIVE_RUNTIME_PAIR_BINDINGS', 'PARENT_DID_GRANTS_NOT_SUPPLIED', 'HUMAN_GOVERNANCE_REQUIRED_FOR_IDENTITY_CHANGES']
  };
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [entities, provenance, review, master, output] = process.argv.slice(2);
  if (!output) throw Error('USAGE: entities.json provenance.json review-page.json master-page.json NEW-private-output.json');
  const read = path => JSON.parse(readFileSync(path, 'utf8'));
  const result = reconcileRegistryScopes({entityRegistry: read(entities), entityProvenance: read(provenance), reviewPage: read(review), masterPage: read(master)});
  writeFileSync(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({bindings: result.entityBindings.count, review: result.reviewPositions.count,
    masterRows: result.masterInventory.sourceRows, exactIDIntersection: result.comparison.exactIDIntersection,
    checks: result.checks, importedReviewRecords: 0, registryWrites: 0}));
  if (result.checks.some(c => c.result === 'FAIL')) process.exitCode = 1;
}
