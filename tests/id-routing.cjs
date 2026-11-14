// Run: node tests/id-routing.cjs (requires Playwright and Chromium).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'id/index.html'), 'utf8');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  let passed = 0;
  try {
    for (const scenario of [
      { url: '/691181', title: 'ChatGPT' },
      { url: '/691181/', title: 'ChatGPT' },
      { url: '/691181/691186', title: 'Đường dẫn ID không hợp lệ', requests: 0 },
      { url: '/691181/extra', title: 'Đường dẫn ID không hợp lệ', requests: 0 },
      { url: '/691181/', failure: 'http', title: 'Chưa thể xác minh ID' },
      { url: '/691181/', failure: 'json', title: 'Chưa thể xác minh ID' },
      { url: '/691181/', failure: 'shape', title: 'Chưa thể xác minh ID' },
      { url: '/999999999999/', title: 'CFP+ Stable ID • Chưa định vị' },
    ]) {
      const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
      const errors = []; let requests = 0;
      page.on('pageerror', error => errors.push(error.message));
      await page.route('http://id-test.local/**', route => {
        const pathname = new URL(route.request().url()).pathname;
        if (pathname.startsWith('/registry/')) {
          requests++;
          if (scenario.failure === 'http') return route.fulfill({ status: 503, body: '{}' });
          if (scenario.failure === 'json') return route.fulfill({ body: '{broken', contentType: 'application/json' });
          if (scenario.failure === 'shape') return route.fulfill({ body: 'null', contentType: 'application/json' });
          return route.fulfill({ body: fs.readFileSync(path.join(root, pathname)), contentType: 'application/json' });
        }
        if (pathname === '/styles.css') return route.fulfill({ body: fs.readFileSync(path.join(root, 'styles.css')), contentType: 'text/css' });
        return route.fulfill({ body: html, contentType: 'text/html' });
      });
      await page.goto('http://id-test.local' + scenario.url);
      await page.waitForFunction(() => document.getElementById('identity').textContent !== 'Đang đọc registry…');
      assert.equal(await page.locator('#title').textContent(), scenario.title);
      assert.deepEqual(errors, []);
      if (scenario.requests !== undefined) assert.equal(requests, scenario.requests);
      if (scenario.failure || scenario.requests === 0) assert.equal(await page.locator('#office').isVisible(), false);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      console.log('PASS', scenario.url, scenario.failure || 'normal'); passed++;
      await page.close();
    }
    const docker = fs.readFileSync(path.join(root, 'Dockerfile'), 'utf8');
    assert(docker.includes('location ~ ^/[0-9]+/?$'));
    assert(!docker.includes('(?:/[0-9]+)*'));
    console.log(`PASS ${passed} browser scenarios + single-ID nginx config check`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
