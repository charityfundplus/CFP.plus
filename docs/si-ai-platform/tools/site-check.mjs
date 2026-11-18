#!/usr/bin/env node
// CFP+ • static site checks • REVIEW CANDIDATE • zero dependencies, read-only.
// Usage: node docs/si-ai-platform/tools/site-check.mjs [--json out.json]
// Strict scope (must pass): files changed by the SI AI platform proposal.
// Baseline scope (report only): every HTML file in the repository.

import { readFileSync, readdirSync, statSync, existsSync, writeFileSync } from 'node:fs';
import { join, dirname, resolve, relative, posix } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(here, '..', '..', '..');
export const STRICT = ['index.html', 'docs/si-ai-platform/mockups/forum.html', 'docs/si-ai-platform/mockups/office.html', 'docs/si-ai-platform/mockups/super-pairs.html'];
const SECRET_RE = /(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[bp]-[A-Za-z0-9-]{10,})/;

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (name === '.git' || name === 'node_modules') continue;
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) walk(p, out);
    else if (name.endsWith('.html')) out.push(relative(ROOT, p).split('\\').join('/'));
  }
  return out;
}

/** Resolve a site path the way the repository Dockerfile's nginx config does. */
export function resolveSitePath(urlPath) {
  const clean = decodeURIComponent(urlPath.split('#')[0].split('?')[0]);
  if (/^\/[0-9]+(?:\/[0-9]+)*\/?$/.test(clean)) {
    const dir = clean.replace(/\/$/, '');
    if (existsSync(join(ROOT, dir, 'index.html'))) return { ok: true, kind: 'numeric' };
    if (existsSync(join(ROOT, dir)) && statSync(join(ROOT, dir)).isFile()) return { ok: true, kind: 'numeric-file' };
    return { ok: true, kind: 'numeric-fallback-/id/' }; // nginx falls back to /id/index.html (dynamic page)
  }
  if (clean === '/' || clean === '') return { ok: existsSync(join(ROOT, 'index.html')), kind: 'root' };
  const target = join(ROOT, clean);
  if (existsSync(join(target, 'index.html'))) return { ok: true, kind: 'dir' };
  if (existsSync(target) && statSync(target).isFile()) return { ok: true, kind: 'file' };
  return { ok: false, kind: 'missing' };
}

export function checkFile(file) {
  const html = readFileSync(join(ROOT, file), 'utf8');
  const issues = [];
  const links = [];
  const tagRe = /<(a|link|script|img)\b([^>]*)>/gi;
  let m;
  while ((m = tagRe.exec(html))) {
    const attrs = m[2];
    const url = (attrs.match(/\b(?:href|src)\s*=\s*"([^"]*)"/i) || [])[1];
    if (url === undefined) continue;
    links.push(url);
    const blank = /target\s*=\s*"_blank"/i.test(attrs);
    if (blank && !/rel\s*=\s*"[^"]*noopener/i.test(attrs)) issues.push({ code: 'BLANK_WITHOUT_NOOPENER', url });
    if (/^http:\/\//i.test(url)) issues.push({ code: 'INSECURE_HTTP', url });
    if (/^javascript:/i.test(url)) issues.push({ code: 'JAVASCRIPT_URL', url });
    if (/^(https?:|mailto:|tel:|#)/i.test(url) || url === '') continue;
    if (/['+{}$]/.test(url)) continue; // JS template strings inside inline scripts, not real links
    const sitePath = url.startsWith('/') ? url : '/' + posix.normalize(posix.join(posix.dirname(file), url));
    const r = resolveSitePath(sitePath);
    if (!r.ok) issues.push({ code: 'BROKEN_INTERNAL', url });
    else if (r.kind === 'numeric-fallback-/id/') issues.push({ code: 'NUMERIC_FALLBACK', url, note: 'no folder; served by /id/ dynamic page' });
  }
  if (SECRET_RE.test(html)) issues.push({ code: 'POSSIBLE_SECRET' });
  if (!/<meta[^>]+name="viewport"/i.test(html)) issues.push({ code: 'NO_VIEWPORT' });
  if (!/<title>[^<]+<\/title>/i.test(html)) issues.push({ code: 'NO_TITLE' });
  return { file, links: links.length, issues };
}

/** Every Vietnamese UI string in a mockup must have an English counterpart and vice versa. */
export function bilingualBalance(file) {
  const html = readFileSync(join(ROOT, file), 'utf8').replace(/<html[^>]*>/i, '');
  const vi = (html.match(/<(span|p|div|li|h[1-6])[^>]*\blang="vi"/g) || []).length;
  const en = (html.match(/<(span|p|div|li|h[1-6])[^>]*\blang="en"/g) || []).length;
  return { file, vi, en, balanced: vi === en && vi > 0 };
}

function main() {
  const all = walk(ROOT).sort();
  const strict = STRICT.map(checkFile);
  const strictFail = strict.flatMap((r) => r.issues.filter((i) => i.code !== 'NUMERIC_FALLBACK').map((i) => ({ file: r.file, ...i })));
  const bilingual = STRICT.filter((f) => f.includes('mockups/')).map(bilingualBalance);
  const baseline = all.map(checkFile);
  const summarize = (rows) => {
    const counts = {};
    for (const r of rows) for (const i of r.issues) counts[i.code] = (counts[i.code] ?? 0) + 1;
    return counts;
  };
  const report = {
    root: '.',
    strict: { files: strict.length, failures: strictFail, fallbacks: strict.flatMap((r) => r.issues.filter((i) => i.code === 'NUMERIC_FALLBACK').map((i) => ({ file: r.file, url: i.url }))) },
    bilingual,
    baseline: {
      htmlFiles: all.length,
      issueCounts: summarize(baseline),
      brokenInternal: baseline.flatMap((r) => r.issues.filter((i) => i.code === 'BROKEN_INTERNAL').map((i) => `${r.file} -> ${i.url}`)),
      blankWithoutNoopener: baseline.flatMap((r) => r.issues.filter((i) => i.code === 'BLANK_WITHOUT_NOOPENER').map((i) => `${r.file} -> ${i.url}`)),
    },
  };
  const out = process.argv.indexOf('--json');
  if (out > -1) writeFileSync(process.argv[out + 1], JSON.stringify(report, null, 2) + '\n');
  const ok = strictFail.length === 0 && bilingual.every((b) => b.balanced);
  console.log(JSON.stringify({ ok, strictFailures: strictFail.length, bilingual, baseline: { htmlFiles: all.length, issueCounts: report.baseline.issueCounts } }, null, 2));
  process.exitCode = ok ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
