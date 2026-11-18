#!/usr/bin/env node
// CFP+ • security checks for the SI AI platform proposal • read only • exit 1 on any failure.
// 1. secret patterns in docs/si-ai-platform and index.html
// 2. mockup pages: CSP present, no inline <script>, no http:// resources, target=_blank has noopener
// 3. PR #124 patch scope: only drafts/si-office/**, adapter has no network / write calls
// 4. evidence must not contain local machine paths or credentials
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(here, '..', '..', '..');
const BASE = join(ROOT, 'docs', 'si-ai-platform');
const failures = [];
const fail = (check, file, detail) => failures.push({ check, file: relative(ROOT, file), detail });
const walk = (d, out = []) => { for (const n of readdirSync(d)) { const p = join(d, n); statSync(p).isDirectory() ? walk(p, out) : out.push(p); } return out; };
const text = (p) => /\.(md|mjs|js|json|html|css|patch|txt|tap|yml)$/.test(p);

const SECRETS = [
  /AKIA[0-9A-Z]{16}/, /gh[pousr]_[A-Za-z0-9]{30,}/, /github_pat_[A-Za-z0-9_]{40,}/, /sk-[A-Za-z0-9]{20,}/, /xox[abpr]-[A-Za-z0-9-]{10,}/,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/, /eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}/, /(password|passwd|secret|api[_-]?key)\s*[:=]\s*["'][^"'\s]{8,}["']/i,
];
const files = [...walk(BASE).filter(text), join(ROOT, 'index.html')];
for (const f of files) {
  const s = readFileSync(f, 'utf8');
  for (const re of SECRETS) if (re.test(s) && !f.endsWith('security-check.mjs')) fail('secret-pattern', f, String(re));
}

for (const f of walk(join(BASE, 'mockups')).filter((p) => p.endsWith('.html'))) {
  const s = readFileSync(f, 'utf8');
  if (!/http-equiv="Content-Security-Policy"[^>]*default-src 'self'/.test(s)) fail('csp-missing', f, '');
  if (/<script(?![^>]*\bsrc=)[^>]*>/i.test(s)) fail('inline-script', f, '');
  if (/(src|href)="http:\/\//i.test(s)) fail('insecure-http', f, '');
  for (const m of s.matchAll(/<a\b[^>]*target="_blank"[^>]*>/g)) if (!/rel="[^"]*noopener/.test(m[0])) fail('blank-noopener', f, m[0].slice(0, 80));
}

const patchPath = join(BASE, 'patches', 'pr124-ack-readonly.patch');
const patch = readFileSync(patchPath, 'utf8');
for (const m of patch.matchAll(/^diff --git a\/(\S+) b\/(\S+)$/gm)) if (!m[1].startsWith('drafts/si-office/')) fail('patch-scope', patchPath, m[1]);
const adapter = patch.split('diff --git').find((c) => c.includes('core/readonly-source-adapter.mjs b/')) || '';
const added = adapter.split('\n').filter((l) => l.startsWith('+')).join('\n');
if (!added) fail('patch-adapter-missing', patchPath, '');
if (/from\s+['"]node:(http|https|net|tls|dgram|child_process)['"]|\bfetch\(|XMLHttpRequest|WebSocket/.test(added)) fail('adapter-network', patchPath, 'network or process API in adapter');
if (/writeFile|appendFile|unlink|rmSync|mkdir|rename/.test(added)) fail('adapter-write', patchPath, 'write API in adapter');

for (const f of walk(join(BASE, 'evidence')).filter(text)) {
  const s = readFileSync(f, 'utf8');
  if (/\/tmp\/claude|scratchpad|\/root\/|\/home\/[a-z]+\//.test(s)) fail('local-path-in-evidence', f, '');
}

const report = { ok: failures.length === 0, checkedFiles: files.length, failures };
console.log(JSON.stringify(report, null, 2));
process.exitCode = report.ok ? 0 : 1;
