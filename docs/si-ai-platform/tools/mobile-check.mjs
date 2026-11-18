#!/usr/bin/env node
// CFP+ • mobile layout check with Playwright (pre-installed Chromium in the sandbox).
// Usage: node docs/si-ai-platform/tools/mobile-check.mjs http://127.0.0.1:8080 <outDir>
// Checks: no horizontal page scroll at 360/390 px, no console errors, VI/EN toggle works,
// tap targets in the bottom bar >= 44px. Saves full-page screenshots as evidence.
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.argv[2] || 'http://127.0.0.1:8080';
const outDir = process.argv[3] || 'mobile-evidence';
mkdirSync(outDir, { recursive: true });

const pages = [
  { name: 'home', path: '/' },
  { name: 'forum', path: '/docs/si-ai-platform/mockups/forum.html', bilingual: true },
  { name: 'office', path: '/docs/si-ai-platform/mockups/office.html', bilingual: true },
  { name: 'super-pairs', path: '/docs/si-ai-platform/mockups/super-pairs.html', bilingual: true, waitFor: '#list table' },
];
const widths = [360, 390];
const results = [];
const browser = await chromium.launch();
try {
  for (const width of widths) {
    const ctx = await browser.newContext({ viewport: { width, height: 800 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
    for (const p of pages) {
      const page = await ctx.newPage();
      const consoleErrors = [];
      page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
      page.on('pageerror', (e) => consoleErrors.push(String(e)));
      const resp = await page.goto(base + p.path, { waitUntil: 'load' });
      if (p.waitFor) await page.waitForSelector(p.waitFor, { timeout: 10000 });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      const r = { page: p.name, width, status: resp.status(), horizontalOverflowPx: overflow, consoleErrors };
      if (p.waitFor) {
        r.renderedRows = await page.locator('#list tbody tr').count();
        await page.fill('#q', 'luat thep');
        r.searchLuatThepIds = await page.locator('#list tbody tr td:first-child').allTextContents();
        await page.fill('#q', '');
        await page.selectOption('#ch', '6');
        r.chapter6Rows = await page.locator('#list tbody tr').count();
        await page.selectOption('#ch', '');
      }
      if (p.bilingual) {
        const visVi = await page.locator('h1 [lang="vi"]').isVisible();
        await page.click('.lang button[data-lang="en"]');
        const visEn = await page.locator('h1 [lang="en"]').isVisible();
        const hidVi = !(await page.locator('h1 [lang="vi"]').isVisible());
        r.toggle = { viDefault: visVi, enAfterToggle: visEn, viHiddenAfterToggle: hidVi };
        r.overflowEnPx = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        if (width === 390) await page.screenshot({ path: join(outDir, `${p.name}-en-${width}.png`), fullPage: true });
        await page.click('.lang button[data-lang="vi"]');
        r.minBottomTapPx = await page.evaluate(() => Math.min(...[...document.querySelectorAll('.bottom a')].map((a) => a.getBoundingClientRect().height)));
      }
      if (width === 390) await page.screenshot({ path: join(outDir, `${p.name}-vi-${width}.png`), fullPage: true });
      r.pass = r.status === 200 && overflow <= 0 && (r.overflowEnPx ?? 0) <= 0 && consoleErrors.length === 0 &&
        (!r.toggle || (r.toggle.viDefault && r.toggle.enAfterToggle && r.toggle.viHiddenAfterToggle)) &&
        (r.minBottomTapPx === undefined || r.minBottomTapPx >= 44) &&
        (r.renderedRows === undefined || (r.renderedRows === 91 && r.chapter6Rows === 9 && r.searchLuatThepIds.join() === '4742'));
      results.push(r);
      await page.close();
    }
    await ctx.close();
  }
} finally {
  await browser.close();
}
const ok = results.every((r) => r.pass);
writeFileSync(join(outDir, 'mobile-check.json'), JSON.stringify({ ok, base, results }, null, 2) + '\n');
console.log(JSON.stringify({ ok, results }, null, 2));
process.exitCode = ok ? 0 : 1;
