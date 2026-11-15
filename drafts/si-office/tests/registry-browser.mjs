import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdtempSync, rmSync, mkdirSync, writeFileSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
const require = createRequire(import.meta.url);
let playwright; try { playwright = require('playwright'); } catch { playwright = createRequire(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES + '/')('playwright'); }
const temp = mkdtempSync(join(tmpdir(), 'cfp-registry-browser-'));
const output = process.argv[2] ? resolve(process.argv[2]) : join(temp, 'evidence'); mkdirSync(output, {recursive: true});
const password = 'Synthetic-browser-only-password', service = new P2Sandbox(join(temp, 'state.db'));
service.provision({id: 'viewer', password, role: 'viewer', workspace: 'alpha'});
const server = createP2HTTP({service}); await new Promise(done => server.listen(0, '127.0.0.1', done));
const origin = 'http://127.0.0.1:' + server.address().port;
let browser;
const report = {scope: 'Loopback Chromium; mobile is emulation, not Safari or real iPhone', externalServiceRequests: 0, checks: [], activationAllowed: false};
try {
  browser = await playwright.chromium.launch({headless: true, args: ['--no-sandbox']});
  for (const [name, device] of [['desktop', {viewport: {width: 1440, height: 1000}}], ['mobile', {...playwright.devices['iPhone 13'], defaultBrowserType: undefined}]]) {
    const context = await browser.newContext(device), page = await context.newPage(), errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await context.route('**/*', async route => {
      if (new URL(route.request().url()).origin === origin) await route.continue(); else { report.externalServiceRequests++; await route.abort(); }
    });
    await page.goto(origin + '/p2');
    assert(await page.locator('#registry-office form button').isDisabled());
    await page.locator('#p2-login-form [name=id]').fill('viewer'); await page.locator('#p2-login-form [name=password]').fill(password);
    await page.locator('#p2-login-form button').click(); await page.locator('#p2-login-panel').waitFor({state: 'hidden'});
    await page.locator('#core-pairs article').first().waitFor();
    assert(await page.locator('#core-pairs button').filter({hasText: 'Làm Dự Án tại ChatGPT'}).first().isDisabled());
    await page.locator('#registry-office input').fill('691181'); await page.locator('#registry-office form button').click();
    await page.locator('#registry-office article').first().waitFor();
    assert((await page.locator('#registry-office article h3').allTextContents()).includes('691181 • ChatGPT'));
    await page.locator('#registry-office article button').filter({hasText: 'Làm Dự Án tại ChatGPT'}).click();
    const instructions = page.locator('#registry-office textarea'); await instructions.waitFor();
    assert((await instructions.inputValue()).includes('ID 691181')); assert((await instructions.inputValue()).includes('Parent theo nguồn: 69118'));
    assert.equal(await page.locator('#registry-office a').filter({hasText: 'Mở ChatGPT'}).getAttribute('href'), 'https://chatgpt.com/');
    await page.locator('#registry-office > button').click();
    await page.locator('#registry-office h3').filter({hasText: 'HSTDN OpenAI'}).waitFor();
    const headings = await page.locator('#registry-office article h3').allTextContents();
    for (const text of ['911 • Hoa Kỳ', '6911 • Hoa Kỳ • AI', '69118 • OpenAI', '691181 • ChatGPT']) assert(headings.includes(text));
    assert(await page.locator('#registry-office').innerText().then(text => text.includes('HSTDN ID: chưa có')));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.locator('#registry-office').screenshot({path: join(output, 'registry-' + name + '.png')});
    assert.deepEqual(errors, []); report.checks.push({name, pass: true, checks: ['login', 'unbound pair action blocked', 'ID lookup', 'ChatGPT handoff reuses ID/link', 'OpenAI reference chain', 'no horizontal overflow', 'no page errors']});
    await context.close();
  }
  assert.equal(report.externalServiceRequests, 0); report.pass = true;
} catch (error) {
  report.pass = false;
  report.blocker = error.message.includes("Executable doesn't exist") ? 'BROWSER_EXECUTABLE_UNAVAILABLE' : 'BROWSER_QA_FAILED';
  report.error = error.message.split('\n').slice(0, 2).join('\n'); process.exitCode = 1;
} finally {
  await browser?.close(); await new Promise(done => server.close(done)); service.close(); rmSync(temp, {recursive: true, force: true});
}
writeFileSync(join(output, 'browser-results.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify(report));
