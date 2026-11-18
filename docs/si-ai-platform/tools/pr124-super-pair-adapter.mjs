// CFP+ • Adapter: Notion super-pair source inventory → PR #124 Core Registry read model.
// REVIEW CANDIDATE • read-only • no new IDs • no Parent inference.
// It does NOT implement a second registry: it produces rows in the exact shape that
// drafts/si-office/core/registry-read-model.mjs (PR #124) already accepts for type 'super-pair',
// and loads that module from a pinned PR #124 checkout.
import { readFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
export const PR124_PINNED_SHA = 'e994ea884fdf7a06ca5efe20674b96a0d51e24f8';
export const INVENTORY_PATH = 'docs/si-ai-platform/data/super-pair-source-inventory.json';

export function loadInventory(file = join(here, '..', 'data', 'super-pair-source-inventory.json')) {
  return JSON.parse(readFileSync(file, 'utf8'));
}

/** Convert inventory rows to PR #124 registry rows. Parent stays null: Notion marks it "chờ đối chiếu". */
export function toRegistryRows(inventory) {
  return inventory.rows.map((r) => ({
    id: r.id,
    type: 'super-pair',
    name: r.name,
    parent: null,
    chapter: r.chapter,
    sourceStatus: r.source_status,
    sourcePath: INVENTORY_PATH,
    description: r.note ?? (r.notion_url ? 'Notion: ' + r.notion_url : 'Notion link PENDING'),
  }));
}

/** Import createRegistryReadModel from a PR #124 checkout (path to the repository root of that checkout). */
export async function importPr124ReadModel(pr124Root) {
  const mod = await import(pathToFileURL(resolve(pr124Root, 'drafts/si-office/core/registry-read-model.mjs')).href);
  if (typeof mod.createRegistryReadModel !== 'function') throw Error('PR124_READ_MODEL_NOT_FOUND');
  return mod.createRegistryReadModel;
}

export async function buildSuperPairReadModel({ pr124Root, inventory = loadInventory(), revision = null }) {
  const createRegistryReadModel = await importPr124ReadModel(pr124Root);
  return createRegistryReadModel({
    rows: toRegistryRows(inventory),
    provenance: { source: INVENTORY_PATH, notionIndex: inventory._meta.index_page, revision, pr124: PR124_PINNED_SHA, verified: false },
  });
}
