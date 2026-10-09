const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('playwright');
(async () => {
  const root = process.env.PUBLIC_ROOT;
  assert(root);
  const browser = await chromium.launch();
  let checks = 0;
  const rows = [], errors = [];
  const ids = fs.readdirSync(root).filter(id => (/^[0-9]+$/.test(id) || id === 'V') && fs.existsSync(path.join(root, id, 'index.html')));
  try {
    // Bounded parallel workers test every page; no cases are skipped on failure.
    await Promise.all([1280, 390].map(async width => {
      const context = await browser.newContext({viewport: {width, height: 900}});
      let cursor = 0;
      await Promise.all(Array.from({length: 4}, async () => {
        const page = await context.newPage();
        while (cursor < ids.length) {
          const id = ids[cursor++];
          try {
            const response = await page.goto('http://127.0.0.1:8080/' + id, {waitUntil: 'networkidle'});
            assert.equal(response.status(), 200); checks++;
            const expected = fs.readFileSync(path.join(root, id, 'index.html'), 'utf8');
            assert(expected.match(/<h1[^>]*>([\s\S]*?)<\/h1>/), 'missing h1 ' + id);
            assert(await page.locator('h1').first().isVisible(), 'hidden heading ' + id); checks++;
            assert.equal((await page.locator('h1').first().textContent()).trim(),
              await page.evaluate(source => new DOMParser().parseFromString(source, 'text/html').querySelector('h1').textContent.trim(), expected), 'heading mismatch ' + id); checks++;
            assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2), 'overflow ' + id + ' width ' + width); checks++;
            if (['000','69','5272','6535','6735','343','267', ...Array.from({length: 10}, (_, i) => String(i))].includes(id)) {
              assert((await page.locator('h1').first().innerText()).startsWith(id + ' • ')); checks++;
            }
            rows.push({id, viewport: width, result: 'PASS', scope: 'candidate container only; not production'});
            if (id === '6535') await page.screenshot({path: 'container-6535-' + width + '.png', fullPage: true});
          } catch (error) {
            rows.push({id, viewport: width, result: 'FAIL', error: error.message});
            errors.push(error.message);
          }
        }
        await page.close();
      }));
      const page = await context.newPage();
      assert.equal((await page.goto('http://127.0.0.1:8080/999')).status(), 404); checks++;
      await context.close();
    }));
    rows.sort((a, b) => a.viewport - b.viewport || a.id.localeCompare(b.id));
    fs.writeFileSync('container-browser-evidence.json', JSON.stringify({result: errors.length ? 'FAIL' : 'PASS', checks, errors, rows}, null, 2));
    assert.equal(errors.length, 0, errors.join('\n'));
    console.log('PASS', checks, 'actual container browser checks;', rows.length, 'page/viewport observations');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
