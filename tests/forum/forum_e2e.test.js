// CFP+ Forum P0 • Playwright E2E với backend thật (uvicorn + FastAPI) và database thật.
// Luồng: đăng ký/đăng nhập → tham gia → đăng bài → bình luận → tải lại → KHỞI ĐỘNG LẠI SERVER → dữ liệu còn.
// Env: CFP_FORUM_AUTH_DB, CFP_FORUM_DB_SIEU_BO_DOI, CFP_FORUM_DB_SI_AI_HSTDN (database test riêng).
// Chạy: NODE_PATH=$(npm root -g) node tests/forum/forum_e2e.test.js
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const path = require('path');
const net = require('net');

const ROOT = path.resolve(__dirname, '..', '..');
for (const k of ['CFP_FORUM_AUTH_DB', 'CFP_FORUM_DB_SIEU_BO_DOI', 'CFP_FORUM_DB_SI_AI_HSTDN']) {
  if (!process.env[k]) { console.error('Thiếu ' + k); process.exit(2); }
}
const ENV = { ...process.env, CFP_FORUM_COOKIE_SECURE: '0', PYTHONPATH: ROOT };

function freePort() {
  return new Promise((res) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); });
}
async function startServer(port) {
  const proc = spawn('python3', ['-m', 'uvicorn', 'services.forum.asgi:app', '--host', '127.0.0.1', '--port', String(port)], { cwd: ROOT, env: ENV, stdio: ['ignore', 'ignore', 'pipe'] });
  let log = ''; proc.stderr.on('data', (d) => { log += d; });
  for (let i = 0; i < 100; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/api/health`); if (r.ok) return proc; } catch (e) { /* chưa sẵn sàng */ }
    await new Promise((r) => setTimeout(r, 100));
  }
  proc.kill(); throw new Error('Server không khởi động: ' + log);
}
async function stopServer(proc) { proc.kill('SIGTERM'); await new Promise((r) => proc.once('exit', r)); }

let passed = 0, failed = 0;
async function check(label, fn) {
  try { await fn(); console.log('[PASS] ' + label); passed++; } catch (e) { console.log('[FAIL] ' + label + ' — ' + e.message.split('\n')[0]); failed++; }
}
function assert(c, m) { if (!c) throw new Error(m || 'assertion failed'); }

(async () => {
  const port = await freePort();
  const base = `http://127.0.0.1:${port}`;
  const SBD = base + '/_internal/forum/sieu-bo-doi/';
  const HST = base + '/_internal/forum/si-ai-hstdn/';
  let server = await startServer(port);
  const browser = await chromium.launch(process.env.CFP_BROWSER ? { executablePath: process.env.CFP_BROWSER } : {});
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const jsErrors = [];
  page.on('pageerror', (e) => jsErrors.push(e.message));
  const tid = (id) => page.getByTestId(id);
  const ready = async (url) => { await page.goto(url); await page.locator('[data-forum][data-ready="1"]').waitFor(); };
  const stamp = Date.now().toString(36);
  const email = `e2e-${stamp}@example.org`, adminEmail = `admin-${stamp}@example.org`;
  const T_SBD = 'Bài E2E Siêu Bộ Đôi ' + stamp, T_HST = 'Bài E2E HSTDN ' + stamp;

  async function auth(mode, em, name) {
    await tid('auth-mode').selectOption(mode);
    await tid('auth-email').fill(em); await tid('auth-password').fill('matkhau-e2e');
    if (name) await tid('auth-name').fill(name);
    await tid('auth-submit').click(); await tid('user-name').waitFor();
  }

  await check('Server dùng database thật, mỗi diễn đàn một DB đã đóng dấu', async () => {
    const h = await (await fetch(base + '/api/health')).json();
    assert(h.forums['sieu-bo-doi'].stamp === 'sieu-bo-doi' && h.forums['si-ai-hstdn'].stamp === 'si-ai-hstdn', JSON.stringify(h));
    console.log('       health=' + JSON.stringify(h));
  });

  await check('Khách: đọc được Siêu Bộ Đôi, không có form đăng bài', async () => {
    await ready(SBD);
    assert((await page.title()).includes('Diễn Đàn Siêu Bộ Đôi'));
    assert(await tid('post-form').count() === 0);
    await tid('login-hint').waitFor();
  });

  await check('Khách: SI AI • HSTDN từ chối đọc', async () => {
    await ready(HST);
    assert((await tid('read-denied').textContent()).includes('đăng nhập'));
  });

  await check('Đăng ký tài khoản → đăng nhập (cookie HttpOnly)', async () => {
    await ready(SBD);
    await auth('register', email, 'Thành Viên E2E');
    const ck = (await ctx.cookies()).find((c) => c.name === 'cfp_forum_session');
    assert(ck && ck.httpOnly && ck.sameSite === 'Strict', JSON.stringify(ck));
    assert(await page.evaluate(() => document.cookie.includes('cfp_forum_session')) === false, 'JS đọc được cookie');
  });

  await check('Tham gia Siêu Bộ Đôi (mở) → đăng bài', async () => {
    await tid('join').click(); await tid('post-form').waitFor();
    assert(await tid('post-hstdn').count() === 0, 'Siêu Bộ Đôi không có trường HSTDN');
    await tid('post-title').fill(T_SBD);
    await tid('post-body').fill('Nội dung <img src=x onerror="window.__xss=1">');
    await tid('post-submit').click();
    await page.locator('[data-testid=post-title-view]', { hasText: T_SBD }).waitFor();
  });

  await check('Bình luận', async () => {
    const post = page.locator('[data-testid=post]', { hasText: T_SBD });
    await post.getByTestId('comment-input').fill('Bình luận E2E');
    await post.getByTestId('comment-submit').click();
    await post.getByTestId('comment-body').filter({ hasText: 'Bình luận E2E' }).waitFor();
  });

  await check('Tải lại trang → phiên, bài, bình luận còn', async () => {
    await ready(SBD);
    assert((await tid('user-name').textContent()) === 'Thành Viên E2E');
    const post = page.locator('[data-testid=post]', { hasText: T_SBD });
    assert(await post.count() === 1);
    assert((await post.getByTestId('comment-body').first().textContent()) === 'Bình luận E2E');
  });

  await check('Không dùng localStorage để lưu dữ liệu diễn đàn', async () => {
    const n = await page.evaluate(() => localStorage.length + sessionStorage.length);
    assert(n === 0, 'storage length=' + n);
  });

  await check('XSS không thực thi', async () => {
    assert(await page.evaluate(() => window.__xss) === undefined);
  });

  await check('KHỞI ĐỘNG LẠI server → đăng nhập lại → dữ liệu vẫn còn', async () => {
    await stopServer(server);
    server = await startServer(port);
    await ready(SBD);
    assert((await tid('user-name').textContent()) === 'Thành Viên E2E', 'phiên mất sau restart');
    await tid('logout').click(); await tid('login-form').waitFor();
    await auth('login', email);
    const post = page.locator('[data-testid=post]', { hasText: T_SBD });
    assert(await post.count() === 1, 'bài mất sau restart');
    assert((await post.getByTestId('comment-body').first().textContent()) === 'Bình luận E2E');
  });

  await check('SI AI • HSTDN: yêu cầu tham gia → chờ duyệt, chưa đọc/đăng được', async () => {
    await ready(HST);
    await tid('join').click();
    await tid('member-status').filter({ hasText: 'chờ' }).waitFor();
    assert(await tid('post-form').count() === 0);
    await tid('read-denied').waitFor();
  });

  await check('Admin riêng của HSTDN duyệt (qua CLI + API)', async () => {
    const c2 = await browser.newContext(); const p2 = await c2.newPage();
    await p2.goto(HST); await p2.locator('[data-ready="1"]').waitFor();
    await p2.getByTestId('auth-mode').selectOption('register');
    await p2.getByTestId('auth-email').fill(adminEmail); await p2.getByTestId('auth-password').fill('matkhau-e2e');
    await p2.getByTestId('auth-name').fill('Quản Trị HSTDN'); await p2.getByTestId('auth-submit').click();
    await p2.getByTestId('user-name').waitFor();
    execFileSync('python3', ['-m', 'services.forum.admin', 'grant-admin', 'si-ai-hstdn', adminEmail], { cwd: ROOT, env: ENV });
    const me = await (await page.request.get(base + '/api/auth/me')).json();
    const r = await p2.request.post(`${base}/api/forums/si-ai-hstdn/members/${me.user.id}/approve`, { headers: { 'X-CFP-Forum': '1' } });
    assert(r.status() === 200, 'approve ' + r.status());
    const r2 = await p2.request.get(`${base}/api/forums/sieu-bo-doi/members`);
    assert(r2.status() === 403, 'admin HSTDN lại có quyền ở Siêu Bộ Đôi: ' + r2.status());
    await c2.close();
  });

  await check('SI AI • HSTDN: đăng bài phải có HSTDN → bình luận → tải lại còn', async () => {
    await ready(HST);
    await tid('post-form').waitFor();
    await tid('post-title').fill(T_HST); await tid('post-body').fill('Nội dung HSTDN');
    await tid('post-hstdn').fill('HSTDN Thử Nghiệm'); await tid('post-country').fill('6984');
    await tid('post-submit').click();
    const post = page.locator('[data-testid=post]', { hasText: T_HST });
    await post.waitFor();
    await post.getByTestId('comment-input').fill('Bình luận HSTDN');
    await post.getByTestId('comment-submit').click();
    await post.getByTestId('comment-body').filter({ hasText: 'Bình luận HSTDN' }).waitFor();
    await ready(HST);
    const p = page.locator('[data-testid=post]', { hasText: T_HST });
    assert(await p.count() === 1);
    assert((await p.getByTestId('post-hstdn-view').textContent()).includes('HSTDN Thử Nghiệm'));
  });

  await check('Hai diễn đàn không thấy bài của nhau', async () => {
    await ready(HST);
    assert(await page.locator('[data-testid=post]', { hasText: T_SBD }).count() === 0);
    await ready(SBD);
    assert(await page.locator('[data-testid=post]', { hasText: T_HST }).count() === 0);
  });

  await check('Đăng xuất → khách vẫn đọc được Siêu Bộ Đôi nhưng không ghi được', async () => {
    await tid('logout').click(); await tid('login-form').waitFor();
    assert(await tid('comment-form').count() === 0);
    const r = await page.request.post(`${base}/api/forums/sieu-bo-doi/posts`, { headers: { 'X-CFP-Forum': '1' }, data: { title: 'a', body: 'b' } });
    assert(r.status() === 401, 'status ' + r.status());
  });

  await check('iPhone 13 (mô phỏng viewport + touch): đăng ký → đăng bài → bình luận → tải lại', async () => {
    const { devices } = require('playwright');
    const m = await browser.newContext({ ...devices['iPhone 13'] });
    const mp = await m.newPage();
    mp.on('pageerror', (e) => jsErrors.push('iphone: ' + e.message));
    await mp.goto(SBD); await mp.locator('[data-ready="1"]').waitFor();
    const noHScroll = await mp.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
    assert(noHScroll, 'có cuộn ngang trên iPhone');
    await mp.getByTestId('auth-mode').selectOption('register');
    await mp.getByTestId('auth-email').fill(`iphone-${stamp}@example.org`);
    await mp.getByTestId('auth-password').fill('matkhau-e2e');
    await mp.getByTestId('auth-name').fill('iPhone E2E');
    await mp.getByTestId('auth-submit').tap();
    await mp.getByTestId('join').tap();
    await mp.getByTestId('post-title').fill('Bài iPhone ' + stamp);
    await mp.getByTestId('post-body').fill('Gửi từ iPhone');
    await mp.getByTestId('post-submit').tap();
    const post = mp.locator('[data-testid=post]', { hasText: 'Bài iPhone ' + stamp });
    await post.getByTestId('comment-input').fill('Bình luận iPhone');
    await post.getByTestId('comment-submit').tap();
    await post.getByTestId('comment-body').filter({ hasText: 'Bình luận iPhone' }).waitFor();
    await mp.reload(); await mp.locator('[data-ready="1"]').waitFor();
    assert(await mp.locator('[data-testid=post]', { hasText: 'Bài iPhone ' + stamp }).getByTestId('comment-body').count() === 1);
    await mp.screenshot({ path: process.env.CFP_E2E_SCREENSHOT || path.join(require('os').tmpdir(), 'cfp-forum-iphone.png'), fullPage: false });
    await m.close();
  });

  await check('Không có lỗi JavaScript', async () => { assert(jsErrors.length === 0, jsErrors.join('; ')); });

  await browser.close();
  await stopServer(server);
  console.log(`\nTỔNG: ${passed} PASS • ${failed} FAIL`);
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
