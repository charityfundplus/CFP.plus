// Kiểm giao diện điện thoại trên URL HTTPS THẬT của sandbox (Chromium giả lập iPhone 13 — không thay Safari thật).
// Mỗi trang: HTTP 200, không lỗi JS, không cuộn ngang; /69/: ô Tìm ID gõ "tmtc" ra 8682. Ảnh chụp lưu làm Evidence.
const { chromium, devices } = require('playwright');
const fs = require('fs');
const base = (process.argv[2] || '').replace(/\/$/, '');
const out = process.argv[3] || 'https-mobile';
const PAGES = ['/69/', '/0123456789/', '/_internal/van-phong-sieu-bo-doi/', '/_internal/linkmau/691121/',
  '/_internal/forum/sieu-bo-doi/', '/_internal/forum/si-ai-hstdn/', '/_internal/office/', '/_internal/map/',
  '/_internal/catalog/', '/_internal/agent/meta-business-agent/', '/267/', '/28882/'];
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const ctx = await b.newContext({ ...devices['iPhone 13'] });
  const p = await ctx.newPage(); const rows = []; let fail = 0;
  for (const path of PAGES) {
    const errs = []; p.removeAllListeners('pageerror'); p.on('pageerror', (e) => errs.push(e.message));
    const r = await p.goto(base + path, { waitUntil: 'networkidle', timeout: 90000 });
    await p.waitForTimeout(800);
    const sw = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    const ok = r.status() === 200 && sw <= 1 && errs.length === 0;
    if (!ok) fail++;
    rows.push({ path, status: r.status(), hscroll: sw, js_errors: errs.slice(0, 3), ok });
    console.log(`[${ok ? 'PASS' : 'FAIL'}] ${path} • ${r.status()} • cuộn ngang ${sw}px • lỗi JS ${errs.length}`);
    await p.screenshot({ path: `${out}/${path.replace(/[^0-9a-z]+/gi, '_') || 'root'}.png` });
  }
  await p.goto(base + '/69/'); await p.locator('#cfp-q').fill('tmtc');
  const found = await p.locator('[data-cfp-results] a[href="/8682/"]').waitFor({ timeout: 15000 }).then(() => true, () => false);
  if (!found) fail++;
  console.log(`[${found ? 'PASS' : 'FAIL'}] /69/ ô Tìm ID: "tmtc" → 8682`);
  await p.screenshot({ path: `${out}/69_search_tmtc.png` });
  rows.push({ path: '/69/#search tmtc', ok: found });
  fs.writeFileSync(`${out}/result.json`, JSON.stringify({ base, rows }, null, 1));
  await b.close();
  console.log(`HTTPS_MOBILE=${fail ? 'FAIL' : 'PASS'} pages=${PAGES.length} failed=${fail}`);
  process.exit(fail ? 1 : 0);
})();
