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

  const browser = await chromium.launch(process.env.CFP_BROWSER ? { executablePath: process.env.CFP_BROWSER } : {});
  const ctx = await browser.newContext({ ...devices['iPhone 13'] });
  await ctx.request.post(base + '/api/auth/login', { data: { email: prefix + '-lead@example.org', password: 'matkhau-office-p0' }, headers: { 'X-CFP-Forum': '1' } });
  const page = await ctx.newPage();
  const jsErrors = []; page.on('pageerror', (e) => jsErrors.push(e.message));
  const URL = base + '/_internal/office/691121/';

  await check('Khách (chưa đăng nhập) không thấy nhiệm vụ/Evidence/Review (SEC-P0-195-01)', async () => {
    const anon = await browser.newContext({ ...devices['iPhone 13'] }); const ap = await anon.newPage();
    await ap.goto(URL); await ap.locator('[data-ready="1"]').waitFor();
    assert(await ap.getByTestId('task').count() === 0, 'khách thấy nhiệm vụ');
    const d = await (await ap.request.get(base + '/api/office/offices/691121')).json();
    assert(d.tasks.length === 0 && d.maintainers === null, 'API lộ dữ liệu nội bộ cho khách');
    await anon.close();
  });
  await check('Đăng nhập người thực thi (lead) qua API thật', async () => {
    const r = await page.request.post(base + '/api/auth/login', { headers: { 'X-CFP-Forum': '1' },
      data: { email: `${prefix}-lead@example.org`, password: 'matkhau-office-p0' } });
    assert(r.status() === 200, 'login ' + r.status());
  });
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
  await check('Trao đổi trong nhiệm vụ qua giao diện (lưu DB, còn sau tải lại, không đổi trạng thái)', async () => {
    const sel = () => page.locator('[data-testid=task]', { hasText: `[${prefix}] Luồng Link Mẫu SI AI xuyên suốt` });
    await sel().getByLabel('Trao đổi nhiệm vụ').fill('Trao đổi E2E ' + prefix);
    await sel().getByRole('button', { name: 'Gửi trao đổi' }).click();
    await sel().getByTestId('task-comment').filter({ hasText: 'Trao đổi E2E ' + prefix }).waitFor();
    await page.reload(); await page.locator('[data-ready="1"]').waitFor();
    assert((await sel().getByTestId('task-comment').allTextContents()).some((t) => t.endsWith('Trao đổi E2E ' + prefix)), 'mất sau reload');
    assert((await sel().getByTestId('task-status').textContent()) === 'ACCEPTED');
    assert((await sel().locator('.forum-meta').textContent()) === 'QUEUED → ACKED → IN_PROGRESS → IN_REVIEW → ACCEPTED');
  });
  await check('Nhiệm vụ → mở thảo luận ở Diễn Đàn Siêu Bộ Đôi → phản hồi → quay lại nhiệm vụ', async () => {
    const sel = () => page.locator('[data-testid=task]', { hasText: `[${prefix}] Luồng Link Mẫu SI AI xuyên suốt` });
    const j = await page.request.post(base + '/api/forums/sieu-bo-doi/join', { headers: { 'X-CFP-Forum': '1' } });
    assert([200, 409].includes(j.status()), 'join ' + j.status());
    await sel().getByLabel('Mở thảo luận ở').selectOption('sieu-bo-doi');
    await sel().getByLabel('Tiêu đề thảo luận').fill('Thảo luận E2E ' + prefix);
    await sel().getByLabel('Nội dung thảo luận').fill('Nhờ góp ý tiêu chí nghiệm thu.');
    await sel().getByRole('button', { name: 'Mở thảo luận' }).click();
    const link = sel().getByTestId('discussion-link').last();
    await link.waitFor();
    await link.click();
    await page.waitForURL(/\/_internal\/forum\/sieu-bo-doi\/#post-\d+$/);
    await page.locator('[data-ready="1"]').waitFor();
    const pid = page.url().split('#post-')[1];
    const post = page.locator('#post-' + pid);
    assert((await post.getByTestId('post-title-view').textContent()) === 'Thảo luận E2E ' + prefix);
    await post.getByTestId('comment-input').fill('Phản hồi E2E ' + prefix);
    await post.getByTestId('comment-submit').click();
    await page.locator('#post-' + pid + ' [data-testid=comment-body]', { hasText: 'Phản hồi E2E ' + prefix }).waitFor();
    const back = page.locator('#post-' + pid).getByTestId('task-backlink');
    assert((await back.count()) === 1, 'thiếu liên kết ngược về nhiệm vụ');
    await back.click();
    await page.waitForURL(/\/_internal\/office\/691121\/#task:\d+$/);
    await page.locator('[data-ready="1"]').waitFor();
    assert((await sel().getByTestId('task-discussion').count()) >= 1);
    const vw = await page.evaluate(() => [window.innerWidth, document.documentElement.scrollWidth]);
    assert(vw[0] === 390 && vw[1] <= 390, 'layout iPhone: ' + vw.join(','));
  });
  await check('Khách: không thấy liên kết ngược bài diễn đàn → nhiệm vụ', async () => {
    const anon = await browser.newContext({ ...devices['iPhone 13'] });
    const ap = await anon.newPage();
    await ap.goto(base + '/_internal/forum/sieu-bo-doi/'); await ap.locator('[data-ready="1"]').waitFor();
    assert((await ap.getByTestId('task-backlink').count()) === 0, 'khách thấy liên kết nhiệm vụ');
    const r = await ap.request.get(base + '/api/office/forum-links?forum=sieu-bo-doi');
    assert(JSON.stringify((await r.json()).links) === '[]');
    await anon.close();
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
  await check('Gia phả: Hoa Kỳ 911 → AI Hoa Kỳ 6911 → Anthropic 69112 → Claude 691121 → Văn Phòng', async () => {
    await page.goto('about:blank'); await page.goto(URL + '#registry:6911'); await page.locator('[data-ready="1"]').waitFor();
    await page.getByTestId('registry-children').getByTestId('ref-link').filter({ hasText: 'registry:69112' }).tap();
    await page.getByTestId('detail-title').filter({ hasText: 'Anthropic' }).waitFor();
    await page.getByTestId('registry-children').getByTestId('ref-link').filter({ hasText: 'registry:691121' }).tap();
    await page.getByTestId('office-link').tap(); await page.waitForURL('**/_internal/office/691121/'); await page.locator('[data-ready="1"]').waitFor();
  });
  await check('Kết nối hệ sinh thái: HUB 69, CMP 267, Sàn TMTC 8682, hai diễn đàn', async () => {
    const hrefs = await page.getByTestId('connection').evaluateAll((as) => as.map((a) => a.getAttribute('href')));
    for (const h of ['https://cfp.plus/69/', 'https://cfp.plus/267/', 'https://cfp.plus/8682/', '/_internal/forum/sieu-bo-doi/', '/_internal/forum/si-ai-hstdn/'])
      assert(hrefs.includes(h), 'thiếu ' + h);
    const r = await page.request.get(base + '/_internal/forum/sieu-bo-doi/'); assert(r.status() === 200);
  });
  await check('HUB 69 API: Văn Phòng 691121 + 2 diễn đàn + module thiếu được ghi trung thực', async () => {
    const h = await (await page.request.get(base + '/api/hub/69')).json();
    assert(h.offices.some((o) => o.canonical_id === '691121'), 'thiếu Văn Phòng 691121');
    assert(h.forums.length === 2 && h.status === 'SANDBOX • NOT DEPLOYED');
    assert(h.modules.find((m) => m.key === 'tmtc').status === 'missing');
    const spec = await (await page.request.get(base + '/api/openapi.json')).json();
    assert(Object.keys(spec.paths).length >= 37, 'openapi thiếu path');
  });
  await check('ID không có trong Registry → 404, không tự cấp', async () => {
    const r = await page.request.get(base + '/api/office/registry/99999999');
    assert(r.status() === 404);
  });
  await check('Diễn đàn vẫn độc lập: Văn Phòng chỉ ghi khi người dùng chủ động mở thảo luận', async () => {
    for (const k of ['sieu-bo-doi', 'si-ai-hstdn']) {
      const r = await page.request.get(`${base}/api/forums/${k}/posts`);
      if (k === 'sieu-bo-doi') {
        const mine = (await r.json()).posts.filter((p) => p.title.includes(prefix));
        assert(mine.length === 1 && mine[0].title === 'Thảo luận E2E ' + prefix, mine.map((p) => p.title).join('|'));
      }
      else assert([401, 403].includes(r.status()), 'HSTDN phải từ chối người không phải thành viên: ' + r.status());
    }
  });
  await check('Website sandbox: trang 691121 có lối vào Siêu Bộ Đôi → mở Văn Phòng 691121 (không cuộn ngang)', async () => {
    const wp = await ctx.newPage(); wp.on('pageerror', (e) => jsErrors.push('site: ' + e.message));
    await wp.goto(base + '/');
    await wp.getByTestId('sandbox-entry').waitFor();
    await wp.goto(base + '/691121/');
    const bar = wp.getByTestId('sandbox-entry');
    assert(await bar.getByRole('link', { name: 'Diễn Đàn Siêu Bộ Đôi' }).count() === 1, 'thiếu lối vào diễn đàn');
    const sw = await wp.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert(sw <= 1, 'cuộn ngang ' + sw + 'px');
    await bar.getByRole('link', { name: 'Văn Phòng 691121' }).click();
    await wp.getByTestId('office-title').waitFor();
    assert(wp.url().split('#')[0].endsWith('/_internal/office/691121/'), wp.url());
    await wp.close();
  });
  await check('Vòng khép kín hiển thị trên nhiệm vụ (dữ liệu thật: Evidence + Review xong, bước kế tiếp rõ)', async () => {
    await page.goto(base + '/_internal/office/691121/');
    const st = page.getByTestId('task').first().getByTestId('loop-stage');
    await st.first().waitFor();
    assert(await st.count() === 12, 'số bước ' + await st.count());
    for (const k of ['hub69', 'office', 'evidence', 'review', 'acceptance']) {
      const d = await page.getByTestId('task').first().locator(`[data-testid="loop-stage"][data-key="${k}"]`).getAttribute('data-done');
      assert(d === '1', k + ' chưa xong');
    }
    const sum = await page.getByTestId('task').first().getByTestId('loop-summary').textContent();
    assert(/Bước tiếp theo|khép kín/.test(sum), sum);
  });
  await check('Danh mục Link Mẫu: tìm "tmtc" → 8682 → mở trang gốc (iPhone, không cuộn ngang)', async () => {
    const cp = await ctx.newPage(); cp.on('pageerror', (e) => jsErrors.push('catalog: ' + e.message));
    await cp.goto(base + '/_internal/catalog/');
    await cp.getByTestId('catalog-item').first().waitFor();
    await cp.getByTestId('catalog-q').fill('tmtc');
    await cp.getByTestId('catalog-count').filter({ hasText: 'tmtc' }).waitFor();  // locator: không cần eval (CSP)
    const item = cp.locator('[data-testid="catalog-item"][data-id="8682"]');
    await item.waitFor();
    const sw = await cp.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert(sw <= 1, 'cuộn ngang ' + sw + 'px');
    assert(await cp.getByTestId('catalog-pending').count() === 1, 'thiếu mục chờ xác minh');
    await item.getByRole('link').click();
    await cp.waitForURL(/\/8682\/$/);
    await cp.getByTestId('sandbox-entry').waitFor();
    await cp.close();
  });
  await check('Văn Phòng Agent (TRAINING): Knowledge loại ID HOLD, chạy bộ tình huống, chặn bản nháp sai (iPhone, không cuộn ngang)', async () => {
    const gp = await ctx.newPage(); gp.on('pageerror', (e) => jsErrors.push('agent: ' + e.message));
    await gp.goto(base + '/_internal/agent/meta-business-agent/');
    await gp.getByTestId('agent-knowledge').getByText('loại (ID HOLD)').first().waitFor();
    assert((await gp.getByTestId('agent-flags').textContent()).includes('AUTO REPLY HOLD'), 'thiếu cờ AUTO REPLY HOLD');
    await gp.getByTestId('agent-run').click();
    await gp.getByTestId('agent-run-out').filter({ hasText: 'Evidence URL' }).waitFor();
    assert(/ 0 FAIL/.test(await gp.getByTestId('agent-run-out').textContent()), 'bộ tình huống có FAIL');
    await gp.getByTestId('agent-draft').fill('App CFP+ đã hoạt động. https://cfp.plus/69115/');
    await gp.getByTestId('agent-check').click();
    await gp.getByTestId('agent-check-out').filter({ hasText: 'block' }).waitFor();
    const sw = await gp.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert(sw <= 1, 'cuộn ngang ' + sw + 'px');
    await gp.close();
  });
  await check('Bảng điều phối: ONLINE thật + nhiệm vụ REVIEWED theo quyền; khách không thấy nhiệm vụ', async () => {
    const op = await ctx.newPage(); op.on('pageerror', (e) => jsErrors.push('ops: ' + e.message));
    await op.goto(base + '/_internal/ops/');
    await op.getByTestId('ops-online').getByText('ONLINE').first().waitFor();
    const reviewed = op.getByTestId('ops-reviewed').getByTestId('ops-task');
    await reviewed.first().waitFor();
    assert((await reviewed.count()) >= 1, 'thiếu nhiệm vụ REVIEWED');
    assert(await op.getByTestId('ops-scheduled').getByTestId('worker-state').count() === 1, 'thiếu trạng thái worker');
    await op.close();
    const anon = await browser.newContext({ ...devices['iPhone 13'] }); const ap = await anon.newPage();
    await ap.goto(base + '/_internal/ops/'); await ap.getByTestId('ops-reviewed').waitFor();
    assert(await ap.getByTestId('ops-task').count() === 0, 'khách thấy nhiệm vụ');
    await anon.close();
  });
  await check('Không có lỗi JavaScript', async () => { assert(jsErrors.length === 0, jsErrors.join('; ')); });
  await page.screenshot({ path: process.env.CFP_E2E_SCREENSHOT || path.join(require('os').tmpdir(), 'cfp-office-iphone.png') });
  await browser.close(); await stop(server);
  console.log(`\nTỔNG: ${passed} PASS • ${failed} FAIL`);
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
