// CFP+ • Siêu Phần Mềm work modules • REVIEW CANDIDATE • READ ONLY
// Deterministic analyzers used by the pilot. They never write to the Registry, Notion or any store.
// Each module returns {module, inputs:[{path|url, sha256}], findings:[...], counts, readOnly:true}.
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const here = dirname(fileURLToPath(import.meta.url));
export const ROOT = resolve(here, '..', '..', '..');
export const sha256 = (s) => createHash('sha256').update(typeof s === 'string' ? s : JSON.stringify(s)).digest('hex');
const readText = (p) => readFileSync(join(ROOT, p), 'utf8');
const input = (p) => ({ path: p, sha256: sha256(readText(p)) });
const norm = (s) => String(s ?? '').normalize('NFKC').replace(/\s+/g, ' ').trim().toLowerCase();

/** Group display rule copied from PR #124 registry-read-model (display only). */
export function groupOf(id) {
  const c = id[0];
  return c === '0' ? '000' : '135'.includes(c) ? '135' : '246'.includes(c) ? '246' : '789';
}

/** Module 4 + 5 on GitHub: registry entities vs route folders (title) vs parents. */
export function githubRegistryAudit(root = ROOT) {
  const regPath = 'registry/ai-entity-registry.json';
  const reg = JSON.parse(readFileSync(join(root, regPath), 'utf8'));
  const entities = Object.entries(reg).filter(([k]) => k !== '_meta').map(([id, v]) => ({ id, ...v }));
  const findings = [];
  const titleOf = (id) => {
    const f = join(root, id, 'index.html');
    if (!existsSync(f)) return null;
    return (readFileSync(f, 'utf8').match(/<title>([^<]*)<\/title>/i) || [])[1] ?? '';
  };
  const byId = new Map(entities.map((e) => [e.id, e]));
  for (const e of entities) {
    const title = titleOf(e.id);
    if (title === null) findings.push({ code: 'ENTITY_WITHOUT_ROUTE_PAGE', id: e.id, name: e.name, severity: 'MEDIUM' });
    else if (!norm(title).includes(norm(e.name))) findings.push({ code: 'REGISTRY_NAME_VS_PAGE_TITLE', id: e.id, registryName: e.name, pageTitle: title, severity: 'HIGH' });
    if (e.type === 'ai' && e.parent_id && !byId.has(e.parent_id)) findings.push({ code: 'PARENT_NOT_IN_REGISTRY', id: e.id, parent: e.parent_id, severity: 'HIGH' });
    if (e.type === 'ai' && e.parent_id && !e.id.startsWith(e.parent_id)) findings.push({ code: 'PARENT_NOT_PREFIX', id: e.id, parent: e.parent_id, severity: 'LOW' });
  }
  // Same name used by more than one ID across registry + page titles (possible duplicate entity).
  const names = new Map();
  const addName = (name, id, where) => { const k = norm(name); if (!k) return; if (!names.has(k)) names.set(k, []); names.get(k).push({ id, where }); };
  for (const e of entities) addName(e.name, e.id, 'registry');
  for (const d of readdirSync(root)) {
    if (!/^69\d+$/.test(d) || !statSync(join(root, d)).isDirectory()) continue;
    const t = titleOf(d);
    const m = t && t.match(/^\s*\d+\s*•\s*([^•]+?)\s*•\s*CFP\+/);
    if (m) addName(m[1], d, 'page-title');
  }
  for (const [name, refs] of names) {
    const ids = [...new Set(refs.map((r) => r.id))];
    if (ids.length > 1) findings.push({ code: 'SAME_NAME_MULTIPLE_IDS', name, ids, refs, severity: 'HIGH' });
  }
  return {
    module: 'github-registry-audit', readOnly: true,
    inputs: [input(regPath)],
    counts: { registryEntities: entities.length, findings: findings.length },
    findings,
  };
}

/** Module 5 on Notion: three Notion lists vs each other. */
export function notionCrossCheck() {
  const invPath = 'docs/si-ai-platform/data/super-pair-source-inventory.json';
  const snapPath = 'docs/si-ai-platform/data/notion-snapshots.json';
  const inv = JSON.parse(readText(invPath)).rows;
  const snap = JSON.parse(readText(snapPath));
  const danh = snap.danh_muc.rows, bando = snap.ban_do_link_goc.rows;
  const ids91 = new Set(inv.map((r) => r.id));
  const findings = [];
  // Duplicate source profiles inside one list.
  const seen = new Map();
  for (const r of bando) { if (!seen.has(r.id)) seen.set(r.id, []); seen.get(r.id).push(r.name); }
  for (const [id, ns] of seen) if (ns.length > 1) findings.push({ code: 'DUPLICATE_SOURCE_PROFILE', id, names: ns, source: 'ban_do_link_goc', severity: 'HIGH' });
  // Lists disagree on membership.
  for (const r of danh) if (!ids91.has(r.id)) findings.push({ code: 'IN_DANH_MUC_NOT_IN_91', id: r.id, name: r.name, severity: 'HIGH' });
  const bandoIds = new Set(bando.map((r) => r.id));
  for (const r of inv) if (!bandoIds.has(r.id)) findings.push({ code: 'IN_91_NOT_IN_BAN_DO', id: r.id, name: r.name, severity: 'LOW' });
  for (const r of inv) if (!r.notion_url) findings.push({ code: 'NOTION_LINK_MISSING', id: r.id, name: r.name, severity: 'MEDIUM' });
  // Same ID, two Notion pages (Danh Mục profile vs chapter learning page).
  const invById = new Map(inv.map((r) => [r.id, r]));
  for (const r of danh) {
    const i = invById.get(r.id);
    if (i && i.notion_url && i.notion_url !== r.notion_url) findings.push({ code: 'TWO_NOTION_PAGES_SAME_ID', id: r.id, pages: [r.notion_url, i.notion_url], severity: 'MEDIUM' });
  }
  // Name disagreement across the three lists (ignores "NAME REVIEW REQUIRED" markers and emoji).
  const clean = (s) => norm(s).replace(/name review required/g, '').replace(/[^\p{L}\p{N}+& ]/gu, ' ').replace(/\s+/g, ' ').trim();
  for (const r of inv) {
    const names = new Set([clean(r.name)]);
    for (const b of bando.filter((x) => x.id === r.id)) names.add(clean(b.name));
    const d = danh.find((x) => x.id === r.id);
    if (d) names.add(clean(d.name));
    const list = [...names].filter(Boolean);
    const contained = list.every((a) => list.some((b) => b !== a && (b.includes(a) || a.includes(b))) || list.length === 1);
    if (list.length > 1 && !contained) findings.push({ code: 'NAME_DIFFERS_ACROSS_NOTION_LISTS', id: r.id, names: list, severity: 'MEDIUM' });
  }
  // New standardised 91-row table (Notion, 2026-11-18): must match the inventory 1:1; linked page title must match the name.
  const bang = snap.bang_link_91?.rows ?? [];
  const bangById = new Map(bang.map((r) => [r.id, r]));
  for (const r of inv) {
    const b = bangById.get(r.id);
    if (!b) { findings.push({ code: 'MISSING_IN_BANG_LINK_91', id: r.id, severity: 'HIGH' }); continue; }
    if (b.notion_url !== r.notion_url) findings.push({ code: 'BANG_LINK_URL_DIFFERS', id: r.id, inventory: r.notion_url, table: b.notion_url, severity: 'HIGH' });
    if (b.linked_title) {
      const t = clean(b.linked_title.split(' • Link Học Hỏi')[0].replace(/^\S+\s*•\s*/, ''));
      const n = clean(r.name);
      if (!(t.includes(n) || n.includes(t))) findings.push({ code: 'LINKED_PAGE_TITLE_DIFFERS_FROM_NAME', id: r.id, name: r.name, linkedTitle: b.linked_title, severity: 'HIGH' });
    }
  }
  for (const b of bang) if (!ids91.has(b.id)) findings.push({ code: 'EXTRA_IN_BANG_LINK_91', id: b.id, severity: 'HIGH' });
  return {
    module: 'notion-cross-check', readOnly: true,
    inputs: [input(invPath), input(snapPath), { url: snap.danh_muc.page }, { url: snap.ban_do_link_goc.page }, ...(snap.bang_link_91 ? [{ url: snap.bang_link_91.page }] : [])],
    counts: { list91: inv.length, danhMuc: danh.length, banDo: bando.length, banDoUniqueIds: bandoIds.size, bangLink91: bang.length, findings: findings.length },
    findings,
  };
}

/** Module 4: classify each of the 91 by chapter + group, join GitHub/web presence. */
export function classifyAndJoin() {
  const invPath = 'docs/si-ai-platform/data/super-pair-source-inventory.json';
  const auditPath = 'docs/si-ai-platform/evidence/link-audit.json';
  const inv = JSON.parse(readText(invPath)).rows;
  const audit = new Map(JSON.parse(readText(auditPath)).rows.map((r) => [r.id, r]));
  const rows = inv.map((r) => {
    const a = audit.get(r.id) || {};
    const action = !r.notion_url ? 'CREATE_OR_LINK_NOTION_PROFILE (HG)'
      : a.live === 'OWN_PAGE' ? 'KEEP • REVIEW CONTENT'
      : 'PROPOSE_ROUTE_PAGE (needs HG; no ID change)';
    return { id: r.id, name: r.name, chapter: r.chapter, group: groupOf(r.id), notion: !!r.notion_url, github: !!a.repo?.routeFolder, web: a.live ?? 'UNKNOWN', proposedAction: action };
  });
  const tally = (f) => rows.reduce((m, r) => ((m[f(r)] = (m[f(r)] ?? 0) + 1), m), {});
  return { module: 'classify-and-join', readOnly: true, inputs: [input(invPath), input(auditPath)], counts: { rows: rows.length, byGroup: tally((r) => r.group), byAction: tally((r) => r.proposedAction) }, rows };
}
