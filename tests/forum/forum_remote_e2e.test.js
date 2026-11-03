// CFP+ Forum P0 • E2E trên hosting thật (URL HTTPS), giả lập iPhone.
// Không khởi động server cục bộ; không cần quyền database.
// Env:
//   FORUM_BASE   URL gốc, vd. https://cfp-forum-sandbox.onrender.com
//   FORUM_SCOPE  sieu-bo-doi | all  (mặc định all)
//   CHECK_STAMP  (tuỳ chọn) stamp của lần chạy trước → chỉ kiểm tra dữ liệu còn sau khi server khởi động lại
// Chạy: NODE_PATH=$(npm root -g) node tests/forum/forum_remote_e2e.test.js
const { chromium, devices } = require('playwright');

const BASE = (process.env.FORUM_BASE || '').replace(/\/+$/, '');
const IS_HTTPS = /^https:\/\//.test(BASE);
// http chỉ cho phép với máy cục bộ (để CI tự kiểm chứng script này).
if (!IS_HTTPS && !/^http:\/\/127\.0\.0\.1:\d+$/.test(BASE)) { console.error('FORUM_BASE phải là URL https://'); process.exit(2); }
const SCOPE = process.env.FORUM_SCOPE || 'all';
const CHECK = process.env.CHECK_STAMP || '';
const SBD = BASE + '/_internal/forum/sieu-bo-doi/';
const HST = BASE + '/_internal/forum/si-ai-hstdn/';
const PW = 'matkhau-e2e-remote';
const H = { 'X-CFP-Forum': '1' };

let passed = 0, failed = 0;
async function check(label, fn) {
  try { await fn(); console.log('[PASS] ' + label); passed++; } catch (e) { console.log('[FAIL] ' + label + ' — ' + e.message.split('\n')[0]); failed++; }
}
function assert(c, m) { if (!c) throw new Error(m || 'assertion failed'); }

(async () => {
  // Gói Free có thể đang ngủ: đánh thức trước (tối đa ~2 phút).
  let health = null;
  for (let i = 0; i < 24 && !health; i++) {
    try { const r = await fetch(BASE + '/api/health'); if (r.ok) health = await r.json(); } catch (e) { /* đang khởi động */ }
    if (!health) await new Promise((r) => setTimeout(r, 5000));
  }
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 13'] });
  const page = await ctx.newPage();
  const jsErrors = [];
  page.on('pageerror', (e) => jsErrors.push(e.message));
  const tid = (id) => page.getByTestId(id);
  const ready = async (url) => { await page.goto(url); await page.locator('[data-forum][data-ready="1"]').waitFor({ timeout: 30000 }); };
  async function auth(mode, em, name) {
    await tid('auth-mode').selectOption(mode);
    await tid('auth-email').fill(em); await tid('auth-password').fill(PW);
    if (name) await tid('auth-name').fill(name);
    await tid('auth-submit').click(); await tid('user-name').waitFor();
  }

  await check((IS_HTTPS ? 'HTTPS' : 'HTTP cục bộ') + ' + health: 3 kho ở 3 schema riêng, mỗi diễn đàn đúng dấu', async () => {
    assert(health, 'không gọi được /api/health');
    console.log('       health=' + JSON.stringify(health));
    const s = health.forums;
    assert(s['sieu-bo-doi'].stamp === 'sieu-bo-doi' && s['si-ai-hstdn'].stamp === 'si-ai-hstdn');
    const schemas = [health.auth_schema, s['sieu-bo-doi'].schema, s['si-ai-hstdn'].schema];
    assert(new Set(schemas).size === 3 && !schemas.includes('public'), 'schema: ' + schemas);
  });

  if (CHECK) {
    // Lần chạy kiểm tra sau khi server khởi động lại (redeploy hoặc ngủ → thức).
    const email = `remote-${CHECK}@example.org`;
    await check('Sau khởi động lại: đăng nhập lại được, bài + bình luận Siêu Bộ Đôi còn', async () => {
      await ready(SBD); await auth('login', email);
      const post = page.locator('[data-testid=post]', { hasText: 'Bài Remote SBD ' + CHECK });
      assert(await post.count() === 1, 'bài mất');
      assert((await post.getByTestId('comment-body').first().textContent()) === 'Bình luận Remote ' + CHECK);
    });
    await check('Sau khởi động lại: HSTDN vẫn từ chối thành viên chờ duyệt', async () => {
      await ready(HST); await tid('read-denied').waitFor();
    });
  } else {
    const stamp = Date.now().toString(36);
    const email = `remote-${stamp}@example.org`;
    const T = 'Bài Remote SBD ' + stamp, C = 'Bình luận Remote ' + stamp;
    console.log('       STAMP=' + stamp);

    await check('Khách: đọc được Siêu Bộ Đôi, không có form đăng bài', async () => {
      await ready(SBD);
      assert((await page.title()).includes('Diễn Đàn Siêu Bộ Đôi'));
      assert(await tid('post-form').count() === 0); await tid('login-hint').waitFor();
    });
    await check('Đăng ký → cookie HttpOnly + Secure + SameSite=Strict', async () => {
      await auth('register', email, 'Thành Viên Remote');
      const ck = (await ctx.cookies()).find((c) => c.name === 'cfp_forum_session');
      assert(ck && ck.httpOnly && (ck.secure || !IS_HTTPS) && ck.sameSite === 'Strict', JSON.stringify(ck));
    });
    await check('Siêu Bộ Đôi: tham gia → đăng bài', async () => {
      await tid('join').click(); await tid('post-form').waitFor();
      await tid('post-title').fill(T); await tid('post-body').fill('Nội dung <img src=x onerror="window.__xss=1">');
      await tid('post-submit').click();
      await page.locator('[data-testid=post-title-view]', { hasText: T }).waitFor();
    });
    await check('Siêu Bộ Đôi: bình luận', async () => {
      const post = page.locator('[data-testid=post]', { hasText: T });
      await post.getByTestId('comment-input').fill(C); await post.getByTestId('comment-submit').click();
      await post.getByTestId('comment-body').filter({ hasText: C }).waitFor();
    });
    await check('Tải lại → phiên, bài, bình luận còn', async () => {
      await ready(SBD);
      assert((await tid('user-name').textContent()) === 'Thành Viên Remote');
      const post = page.locator('[data-testid=post]', { hasText: T });
      assert(await post.count() === 1 && (await post.getByTestId('comment-body').first().textContent()) === C);
    });
    await check('Đăng xuất → đăng nhập lại (thiết bị/phiên mới) → dữ liệu còn', async () => {
      await tid('logout').click(); await tid('login-form').waitFor();
      const c2 = await browser.newContext({ ...devices['iPhone 13'] }); const p2 = await c2.newPage();
      await p2.goto(SBD); await p2.locator('[data-ready="1"]').waitFor();
      await p2.getByTestId('auth-mode').selectOption('login');
      await p2.getByTestId('auth-email').fill(email); await p2.getByTestId('auth-password').fill(PW);
      await p2.getByTestId('auth-submit').click(); await p2.getByTestId('user-name').waitFor();
      assert(await p2.locator('[data-testid=post]', { hasText: T }).count() === 1);
      await c2.close();
      await ready(SBD); await auth('login', email);
    });
    await check('Sai mật khẩu bị từ chối; thiếu header CSRF bị từ chối', async () => {
      const r1 = await fetch(BASE + '/api/auth/login', { method: 'POST', headers: { ...H, 'content-type': 'application/json' }, body: JSON.stringify({ email, password: 'sai-mat-khau' }) });
      assert(r1.status === 401, 'login sai ' + r1.status);
      const r2 = await page.request.post(BASE + '/api/forums/sieu-bo-doi/posts', { data: { title: 'a', body: 'b' } });
      assert(r2.status() === 403, 'csrf ' + r2.status());
    });
    await check('XSS không thực thi; không lưu dữ liệu ở localStorage', async () => {
      assert(await page.evaluate(() => window.__xss) === undefined);
      assert(await page.evaluate(() => localStorage.length + sessionStorage.length) === 0);
    });

    if (SCOPE === 'all') {
      await check('SI AI • HSTDN: khách bị từ chối đọc (API 401)', async () => {
        const r = await fetch(BASE + '/api/forums/si-ai-hstdn/posts');
        assert(r.status === 401, 'status ' + r.status);
      });
      await check('SI AI • HSTDN: tham gia → chờ duyệt; chưa đọc/đăng được', async () => {
        await ready(HST); await tid('join').click();
        await tid('member-status').filter({ hasText: 'chờ' }).waitFor();
        assert(await tid('post-form').count() === 0); await tid('read-denied').waitFor();
        const r = await page.request.post(BASE + '/api/forums/si-ai-hstdn/posts', { headers: H, data: { title: 'x', body: 'y', hstdn: 'z' } });
        assert(r.status() === 403, 'đăng khi chờ duyệt: ' + r.status());
      });
      await check('Cách ly: thành viên Siêu Bộ Đôi không có quyền ở HSTDN; bài không lẫn', async () => {
        const r = await page.request.get(BASE + '/api/forums/si-ai-hstdn/members');
        assert(r.status() === 403, 'members ' + r.status());
        const sbd = await (await page.request.get(BASE + '/api/forums/sieu-bo-doi/posts')).json();
        assert(sbd.posts.every((p) => p.hstdn === null), 'bài HSTDN lẫn vào Siêu Bộ Đôi');
        const bad = await page.request.post(BASE + '/api/forums/sieu-bo-doi/posts', { headers: H, data: { title: 'x', body: 'y', hstdn: 'z' } });
        assert(bad.status() === 422, 'Siêu Bộ Đôi nhận trường HSTDN: ' + bad.status());
      });
    }
    await check('Không có lỗi JavaScript', async () => { assert(jsErrors.length === 0, jsErrors.join('; ')); });
  }

  await browser.close();
  console.log(`\nTỔNG: ${passed} PASS • ${failed} FAIL`);
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
