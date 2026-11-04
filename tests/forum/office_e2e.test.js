// CFP+ Văn Phòng SI AI • E2E: seed qua API thật → restart server → UI mobile → điều hướng hai chiều.
// Env: CFP_FORUM_AUTH_DB, CFP_FORUM_DB_SIEU_BO_DOI, CFP_FORUM_DB_SI_AI_HSTDN, CFP_OFFICE_DB, CFP_OFFICE_ADMIN_DB
const { chromium, devices } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const path = require('path');
const net = require('net');

const ROOT = path.resolve(__dirname, '..', '..');
for (const k of ['CFP_FORUM_AUTH_DB', 'CFP_FORUM_DB_SIEU_BO_DOI', 'CFP_FORUM_DB_SI_AI_HSTDN', 'CFP_OFFICE_DB']) {
  if (!process.env[k]) { console.error('Thiếu ' + k); process.exit(2); }
}
const ENV = { ...process.env, CFP_FORUM_COOKIE_SECURE: '0', PYTHONPATH: ROOT, CFP_FORUM_RL_AUTH_PER_MIN: '100', CFP_FORUM_RL_WRITE_PER_MIN: '200' };
const freePort = () => new Promise((res) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); });
async function start(port) {
  const p = spawn('python3', ['-m', 'uvicorn', 'services.forum.asgi:app', '--host', '127.0.0.1', '--port', String(port)], { cwd: ROOT, env: ENV, stdio: ['ignore', 'ignore', 'pipe'] });
  let log = ''; p.stderr.on('data', (d) => { log += d; });
  for (let i = 0; i < 100; i++) { try { if ((await fetch(`http://127.0.0.1:${port}/api/health`)).ok) return p; } catch (e) { /* đợi */ } await new Promise((r) => setTimeout(r, 100)); }
  p.kill(); throw new Error(log);
}
const stop = (p) => new Promise((r) => { p.once('exit', r); p.kill('SIGTERM'); });
let passed = 0, failed = 0;
async function check(label, fn) { try { await fn(); console.log('[PASS] ' + label); passed++; } catch (e) { console.log('[FAIL] ' + label + ' — ' + e.message.split('\n')[0]); failed++; } }
const assert = (c, m) => { if (!c) throw new Error(m || 'assertion failed'); };

(async () => {
  const port = await freePort(); const base = `http://127.0.0.1:${port}`;
  let server = await start(port);
  const prefix = 'e2e' + Date.now().toString(36);
  let seeded;
  await check('Seed luồng xuyên suốt qua API thật (5 Nhóm → … → Review)', async () => {
    const out = execFileSync('python3', ['-m', 'tests.forum.office_flow', '--base', base, '--prefix', prefix], { cwd: ROOT, env: ENV }).toString();
    seeded = JSON.parse(out.trim().split('\n').pop());
    assert(seeded.task && seeded.enterprise && seeded.dataset, out);
  });
  await check('Khởi động lại server', async () => { await stop(server); server = await start(port); });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 13'] });
  const page = await ctx.newPage();
  const jsErrors = []; page.on('pageerror', (e) => jsErrors.push(e.message));
  const URL = base + '/_internal/office/691121/';

  await check('Văn Phòng Claude 691121 hiển thị sau restart (iPhone 13 viewport)', async () => {
    await page.goto(URL); await page.locator('[data-ready="1"]').waitFor();
    assert((await page.getByTestId('office-title').textContent()).includes('Claude • 691121'));
    const vw = await page.evaluate(() => [window.innerWidth, document.documentElement.scrollWidth, Math.round(visualViewport.width)]);
    assert(vw[0] === 390 && vw[1] <= 390 && vw[2] === 390, 'layout bị kéo rộng/thu nhỏ trên iPhone: ' + vw.join(','));
  });
  await check('5 Nhóm + Chương 6 + gia phả Registry 911 → 6911 → 69112 → 691121', async () => {
    assert((await page.locator('.forum-tag.active').textContent()) === 'Nhóm 246');
    const chain = await page.getByTestId('chain').locator('[data-testid=ref-link]').allTextContents();
    assert(chain.join(',') === 'registry:911,registry:6911,registry:69112,registry:691121', chain.join(','));
  });
  await check('Thương hiệu gắn nhãn nguồn công khai, không phải quảng bá ủy quyền', async () => {
    const labels = await page.getByTestId('source-label').allTextContents();
    assert(labels.length >= 3 && labels.every((l) => l === 'Hồ sơ CFP+ tổng hợp từ nguồn công khai'), labels.join('|'));
  });
  await check('Nhiệm vụ ACCEPTED có Evidence + Review + lịch sử', async () => {
    const task = page.locator('[data-testid=task]', { hasText: `[${prefix}] Luồng Link Mẫu SI AI xuyên suốt` });
    assert((await task.getByTestId('task-status').textContent()) === 'ACCEPTED');
    assert((await task.getByTestId('evidence').count()) === 1 && (await task.getByTestId('review').textContent()).startsWith('ACCEPT'));
    assert((await task.locator('.forum-meta').textContent()) === 'QUEUED → ACKED → IN_PROGRESS → IN_REVIEW → ACCEPTED');
  });
  await check('Điều hướng hai chiều: Nhiệm vụ → HSTDN → Quốc gia → Back về HSTDN', async () => {
    await page.goto('about:blank'); await page.goto(URL + `#task:${seeded.task}`); await page.locator('[data-ready="1"]').waitFor();
    await page.getByTestId('detail').getByTestId('ref-link').filter({ hasText: `enterprise:${seeded.enterprise}` }).tap();
    await page.getByTestId('detail-title').filter({ hasText: `[${prefix}] Anthropic PBC` }).waitFor();
    const back = page.getByTestId('detail').getByTestId('ref-link').filter({ hasText: `task:${seeded.task}` });
    assert(await back.count() === 1, 'thiếu liên kết ngược về nhiệm vụ');
    const country = page.getByTestId('detail').getByTestId('ref-link').filter({ hasText: 'registry:911' });
    await country.tap(); await page.getByTestId('detail-title').filter({ hasText: 'Hoa Kỳ' }).waitFor();
    await page.goBack(); await page.getByTestId('detail-title').filter({ hasText: `[${prefix}] Anthropic PBC` }).waitFor();
  });
  await check('Điều hướng: Kho dữ liệu → Chủ đề nghiên cứu (Chương 6 • Nhóm 246)', async () => {
    await page.goto('about:blank'); await page.goto(URL + `#dataset:${seeded.dataset}`); await page.locator('[data-ready="1"]').waitFor();
    const w = await page.evaluate(() => [window.innerWidth, document.documentElement.scrollWidth]);
    assert(w[0] === 390 && w[1] <= 390, 'URL dài làm vỡ layout: ' + w.join(','));
    await page.getByTestId('detail').getByTestId('ref-link').filter({ hasText: `topic:${seeded.topic}` }).tap();
    await page.getByTestId('detail').getByText('Chương 6 • AI • Nhóm 246').waitFor();
  });
  await check('ID không có trong Registry → 404, không tự cấp', async () => {
    const r = await page.request.get(base + '/api/office/registry/99999999');
    assert(r.status() === 404);
  });
  await check('Diễn đàn vẫn độc lập: Văn Phòng không ghi vào hai diễn đàn', async () => {
    for (const k of ['sieu-bo-doi', 'si-ai-hstdn']) {
      const r = await page.request.get(`${base}/api/forums/${k}/posts`);
      if (k === 'sieu-bo-doi') assert((await r.json()).posts.every((p) => !p.title.includes(prefix)));
      else assert(r.status() === 401);
    }
  });
  await check('Không có lỗi JavaScript', async () => { assert(jsErrors.length === 0, jsErrors.join('; ')); });
  await page.screenshot({ path: process.env.CFP_E2E_SCREENSHOT || path.join(require('os').tmpdir(), 'cfp-office-iphone.png') });
  await browser.close(); await stop(server);
  console.log(`\nTỔNG: ${passed} PASS • ${failed} FAIL`);
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
