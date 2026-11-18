#!/usr/bin/env node
// CFP+ • Super-pair link audit • REVIEW CANDIDATE • read-only.
// For every ID in data/super-pair-source-inventory.json:
//   - repo:     does the repository have a route folder <ID>/index.html, a registry/<ID>.md, a website/<ID>.md?
//   - live:     GET https://cfp.plus/<ID>/ (via curl, honours the sandbox proxy) and classify the answer as
//               OWN_PAGE (served page differs from the /id/ fallback), ID_FALLBACK (byte-identical to the
//               dynamic /id/ page that nginx serves for unknown numeric routes), HTTP_<code>, or UNREACHABLE.
// Usage: node docs/si-ai-platform/tools/link-audit.mjs [--offline] [--json out.json]
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(here, '..', '..', '..');
const sha = (b) => createHash('sha256').update(b).digest('hex');

export function loadInventory(file = join(here, '..', 'data', 'super-pair-source-inventory.json')) {
  return JSON.parse(readFileSync(file, 'utf8'));
}

export function repoPresence(id, root = ROOT) {
  return {
    routeFolder: existsSync(join(root, id, 'index.html')),
    registryDoc: existsSync(join(root, 'registry', `${id}.md`)),
    websiteDoc: existsSync(join(root, 'website', `${id}.md`)),
  };
}

function get(url) {
  try {
    const out = execFileSync('curl', ['-s', '-m', '25', '-w', '\n%{http_code}', url], { maxBuffer: 8 << 20 });
    const text = out.toString('utf8');
    const cut = text.lastIndexOf('\n');
    return { status: Number(text.slice(cut + 1)), body: text.slice(0, cut) };
  } catch {
    return { status: 0, body: '' };
  }
}

/** Classify one live response against the known /id/ fallback fingerprint. */
export function classify(resp, fallbackHash) {
  if (!resp.status) return 'UNREACHABLE';
  if (resp.status !== 200) return `HTTP_${resp.status}`;
  return sha(resp.body) === fallbackHash ? 'ID_FALLBACK' : 'OWN_PAGE';
}

function main() {
  const offline = process.argv.includes('--offline');
  const inv = loadInventory();
  let fallbackHash = null;
  if (!offline) {
    // A numeric route that certainly has no folder: the response is the /id/ fallback page.
    const probe = get('https://cfp.plus/909090909/');
    fallbackHash = probe.status === 200 ? sha(probe.body) : null;
  }
  const rows = inv.rows.map((r) => {
    const out = { id: r.id, name: r.name, chapter: r.chapter, notion: r.notion_url ? 'LINK_PRESENT' : 'LINK_PENDING', repo: repoPresence(r.id) };
    if (!offline) {
      const resp = get(`https://cfp.plus/${r.id}/`);
      out.live = fallbackHash ? classify(resp, fallbackHash) : 'FALLBACK_PROBE_FAILED';
      out.liveTitle = (resp.body.match(/<title>([^<]*)<\/title>/i) || [])[1] ?? null;
    }
    return out;
  });
  const tally = (f) => rows.reduce((a, r) => ((a[f(r)] = (a[f(r)] ?? 0) + 1), a), {});
  const report = {
    checkedAtUTC: new Date().toISOString(),
    source: inv._meta.index_page,
    total: rows.length,
    notion: tally((r) => r.notion),
    repoRouteFolder: tally((r) => (r.repo.routeFolder ? 'YES' : 'NO')),
    live: offline ? 'SKIPPED' : tally((r) => r.live),
    fallbackFingerprintSha256: fallbackHash,
    rows,
    readOnly: true,
  };
  const i = process.argv.indexOf('--json');
  if (i > -1) writeFileSync(process.argv[i + 1], JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ total: report.total, notion: report.notion, repoRouteFolder: report.repoRouteFolder, live: report.live }, null, 2));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
