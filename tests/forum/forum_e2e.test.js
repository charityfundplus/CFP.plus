// CFP+ Forum P0 • E2E: đăng nhập → đăng bài → bình luận → tải lại → dữ liệu còn.
// Chạy: node tests/forum/forum_e2e.test.js  (cần Playwright + Chromium)
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css' };

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      let f = path.join(ROOT, p);
      if (!f.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
      if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
      if (!fs.existsSync(f)) { res.writeHead(404); return res.end('404'); }
      res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
      fs.createReadStream(f).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

let passed = 0, failed = 0;
async function check(label, fn) {
  try { await fn(); console.log('[PASS] ' + label); passed++; }
  catch (e) { console.log('[FAIL] ' + label + ' — ' + e.message); failed++; }
}
function assert(c, m) { if (!c) throw new Error(m || 'assertion failed'); }

(async () => {
  const srv = await serve();
  const base = 'http://127.0.0.1:' + srv.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const SBD = base + '/forum/sieu-bo-doi/';
  const HST = base + '/forum/si-ai-hstdn/';

  await check('Trang Siêu Bộ Đôi tải được, chưa đăng nhập thì không có form đăng bài', async () => {
    await page.goto(SBD);
    assert((await page.title()).includes('Diễn Đàn Siêu Bộ Đôi'));
    await page.getByTestId('login-form').waitFor();
    assert(await page.getByTestId('post-form').count() === 0, 'post-form hiển thị khi chưa đăng nhập');
  });

  await check('Đăng nhập với tên rỗng bị từ chối', async () => {
    await page.getByTestId('login-name').fill(' ');
    await page.getByTestId('login-name').evaluate((n) => n.removeAttribute('required'));
    await page.getByTestId('login-name').evaluate((n) => n.removeAttribute('minlength'));
    await page.getByTestId('login-submit').click();
    assert((await page.getByTestId('msg').textContent()).includes('ít nhất 2'));
  });

  await check('Đăng nhập thành công', async () => {
    await page.getByTestId('login-name').fill('Thành Viên CFP');
    await page.getByTestId('login-email').fill('member@example.org');
    await page.getByTestId('login-submit').click();
    assert((await page.getByTestId('user-name').textContent()) === 'Thành Viên CFP');
  });

  const xss = '<img src=x onerror="window.__xss=1">';
  await check('Đăng bài', async () => {
    await page.getByTestId('post-title').fill('Bài P0 Siêu Bộ Đôi');
    await page.getByTestId('post-body').fill('Nội dung thử nghiệm ' + xss);
    await page.getByTestId('post-submit').click();
    await page.getByTestId('post').first().waitFor();
    assert((await page.getByTestId('post-title-view').first().textContent()) === 'Bài P0 Siêu Bộ Đôi');
  });

  await check('Bình luận', async () => {
    await page.getByTestId('comment-input').first().fill('Bình luận P0 đầu tiên');
    await page.getByTestId('comment-submit').first().click();
    assert((await page.getByTestId('comment-body').first().textContent()) === 'Bình luận P0 đầu tiên');
  });

  await check('Tải lại trang → phiên, bài viết, bình luận vẫn tồn tại', async () => {
    await page.reload();
    await page.getByTestId('post').first().waitFor();
    assert((await page.getByTestId('user-name').textContent()) === 'Thành Viên CFP', 'mất phiên');
    assert(await page.getByTestId('post').count() === 1);
    assert((await page.getByTestId('post-title-view').first().textContent()) === 'Bài P0 Siêu Bộ Đôi');
    assert((await page.getByTestId('comment-body').first().textContent()) === 'Bình luận P0 đầu tiên');
  });

  await check('Nội dung người dùng được hiển thị dạng text (không thực thi HTML/XSS)', async () => {
    assert((await page.getByTestId('post-body-view').first().textContent()).includes(xss));
    assert(await page.evaluate(() => window.__xss) === undefined, 'XSS đã thực thi');
  });

  await check('Diễn Đàn SI AI • HSTDN tách biệt: không thấy bài của Siêu Bộ Đôi', async () => {
    await page.goto(HST);
    assert((await page.title()).includes('SI AI • HSTDN'));
    await page.getByTestId('empty').waitFor();
    assert(await page.getByTestId('post').count() === 0);
  });

  await check('Đăng bài + bình luận ở SI AI • HSTDN, tải lại vẫn còn', async () => {
    await page.getByTestId('post-title').fill('Bài P0 HSTDN');
    await page.getByTestId('post-body').fill('Nội dung HSTDN');
    await page.getByTestId('post-submit').click();
    await page.getByTestId('comment-input').first().fill('Bình luận HSTDN');
    await page.getByTestId('comment-submit').first().click();
    await page.reload();
    await page.getByTestId('post').first().waitFor();
    assert(await page.getByTestId('post').count() === 1);
    assert((await page.getByTestId('post-title-view').first().textContent()) === 'Bài P0 HSTDN');
    assert((await page.getByTestId('comment-body').first().textContent()) === 'Bình luận HSTDN');
  });

  await check('Quay lại Siêu Bộ Đôi: chỉ còn đúng bài của Siêu Bộ Đôi', async () => {
    await page.goto(SBD);
    await page.getByTestId('post').first().waitFor();
    assert(await page.getByTestId('post').count() === 1);
    assert((await page.getByTestId('post-title-view').first().textContent()) === 'Bài P0 Siêu Bộ Đôi');
  });

  await check('Hai namespace lưu trữ riêng biệt', async () => {
    const keys = await page.evaluate(() => Object.keys(localStorage).sort());
    assert(keys.includes('cfp.forum.v1.sieu-bo-doi') && keys.includes('cfp.forum.v1.si-ai-hstdn'), JSON.stringify(keys));
  });

  await check('Đăng xuất → ẩn form đăng bài, dữ liệu vẫn còn sau tải lại', async () => {
    await page.getByTestId('logout').click();
    await page.reload();
    await page.getByTestId('login-form').waitFor();
    assert(await page.getByTestId('post-form').count() === 0);
    assert(await page.getByTestId('comment-form').count() === 0);
    assert(await page.getByTestId('post').count() === 1);
  });

  await check('Engine chặn đăng bài khi chưa đăng nhập (API)', async () => {
    const msg = await page.evaluate(() => {
      try { new CFPForum.Forum('sieu-bo-doi').createPost('a', 'b'); return 'no-error'; } catch (e) { return e.message; }
    });
    assert(msg.includes('đăng nhập'), msg);
  });

  await check('Trang chỉ mục /forum/ liên kết tới cả hai diễn đàn', async () => {
    await page.goto(base + '/forum/');
    assert(await page.locator('a[href="/forum/sieu-bo-doi/"]').count() === 1);
    assert(await page.locator('a[href="/forum/si-ai-hstdn/"]').count() === 1);
  });

  await check('Không có lỗi JavaScript trên trang', async () => {
    assert(errors.length === 0, errors.join('; '));
  });

  await browser.close();
  srv.close();
  console.log(`\nTỔNG: ${passed} PASS • ${failed} FAIL`);
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
