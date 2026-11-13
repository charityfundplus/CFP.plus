// Browser half of canva_e2e.py. Drives the Canva client (canva-code.html, the exact file pasted into Canva Code)
// inside a SANDBOXED iframe on another origin (Origin: null — the strictest embedding case), iPhone 13 emulation.
// node canva_e2e_browser.cjs <phase 1|2> <args.json>  → prints one JSON line with checks + writes screenshots
"use strict";
const { chromium, devices } = require("playwright");
const fs = require("fs");
const path = require("path");

const [phase, argsFile] = process.argv.slice(2);
const A = JSON.parse(fs.readFileSync(argsFile, "utf8"));
const checks = [];
const ok = (name, pass, detail) => { checks.push({ name, pass: !!pass, detail }); };

async function open(browser, label) {
  const ctx = await browser.newContext({ ...devices["iPhone 13"] });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto(A.host_url);
  const f = page.frameLocator("iframe#canva");
  return { ctx, page, f, errors, label };
}
async function shot(u, name) {
  await u.page.screenshot({ path: path.join(A.out, `${phase}-${name}.png`), fullPage: true });
}
async function tab(u, t) { await u.f.locator(`nav [data-tab="${t}"]`).click(); }
async function login(u, acct, register) {
  await tab(u, "account");
  await u.f.locator("#u-email").fill(acct.email);
  await u.f.locator("#u-pass").fill(acct.password);
  if (register) await u.f.locator("#u-name").fill(acct.name);
  await u.f.locator(register ? "#u-register" : "#u-login").click();
  await u.f.locator("#who").filter({ hasText: acct.name }).waitFor({ timeout: 15000 });
}
async function noHScroll(u) {
  return u.page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
}

(async () => {
  const browser = await chromium.launch();
  try {
    if (phase === "1") {
      const a = await open(browser, "A");
      await login(a, A.userA, true);
      await a.f.locator("#p-title").fill(A.post_title);
      await a.f.locator("#p-body").fill("Bài đăng từ giao diện Canva (iframe sandbox, Origin: null).");
      await a.f.locator("#p-send").click();
      await a.f.locator("#posts article h3", { hasText: A.post_title }).waitFor({ timeout: 15000 });
      ok("A đăng bài từ Canva", true, A.post_title);
      const diag = await (async () => { await tab(a, "account"); await a.f.locator("#diag", { hasText: "Kết nối:" }).waitFor(); return a.f.locator("#diag").innerText(); })();
      ok("Chẩn đoán kết nối trong iframe", /Kết nối: OK/.test(diag) && /iframe/.test(diag), diag);
      await tab(a, "forum");
      await shot(a, "A-posted");

      const b = await open(browser, "B");
      await login(b, A.userB, true);
      const post = b.f.locator("article", { has: b.f.locator("h3", { hasText: A.post_title }) });
      await post.waitFor({ timeout: 15000 });
      ok("B (tài khoản khác) đọc được bài của A", await post.locator(".meta").first().innerText().then((t) => t.includes(A.userA.name)), A.userA.name);
      await post.locator("textarea").fill(A.reply_text);
      await post.locator("button", { hasText: "Phản hồi" }).click();
      await b.f.locator(".comment", { hasText: A.reply_text }).waitFor({ timeout: 15000 });
      ok("B phản hồi", true, A.reply_text);
      await shot(b, "B-replied");

      await a.f.locator("#f-reload").click();
      await a.f.locator(".comment", { hasText: A.reply_text }).waitFor({ timeout: 15000 });
      ok("A thấy phản hồi của B", true);
      await tab(a, "assign");
      await a.f.locator("#a-title").fill(A.task_title);
      await a.f.locator("#a-cap").selectOption("registry_check");
      await a.f.locator("#a-pri").selectOption("P1");
      await a.f.locator("#a-acc").fill("Chuỗi 691121 đúng, không ID phi số; Evidence sha256");
      await a.f.locator("#a-send").click();
      await a.f.locator("#posts article h3", { hasText: A.task_title }).waitFor({ timeout: 15000 });
      ok("A giao việc qua Diễn Đàn (mẫu HUB 69)", true, A.task_title);
      await shot(a, "A-assigned");
      ok("Không cuộn ngang (iPhone 13)", (await noHScroll(a)) && (await noHScroll(b)));
      ok("Không lỗi JavaScript", !a.errors.length && !b.errors.length, a.errors.concat(b.errors));
    } else {
      const b = await open(browser, "B");
      await login(b, A.userB, false);
      const post = b.f.locator("article", { has: b.f.locator("h3", { hasText: A.post_title }) });
      await post.waitFor({ timeout: 15000 });
      ok("Sau khởi động lại backend: bài + phản hồi còn", await post.locator(".comment", { hasText: A.reply_text }).count() === 1);
      const task = b.f.locator("article", { has: b.f.locator("h3", { hasText: A.task_title }) });
      const bot = task.locator(".comment", { hasText: "CHỜ REVIEW ĐỘC LẬP" });
      ok("Phản hồi tự động của bộ điều phối hiển thị dưới bài nhiệm vụ", await bot.count() === 1, await bot.count() ? await bot.first().innerText() : null);
      await task.scrollIntoViewIfNeeded();
      await shot(b, "B-after-restart");
      await tab(b, "tasks");
      await b.f.locator("#board-counts").waitFor();
      ok("B không thấy nhiệm vụ ngoài phạm vi (máy chủ lọc)", (await b.f.locator("#board .card").count()) === 0);

      const r = await open(browser, "ReviewSI");
      await login(r, A.reviewer, false);
      await tab(r, "tasks");
      const card = r.f.locator("#board .card", { hasText: A.task_title });
      await card.waitFor({ timeout: 15000 });
      ok("Reviewer thấy nhiệm vụ ở 'Chờ review' trong Canva", (await card.innerText()).includes("Chờ review"), await card.innerText());
      await card.locator("button", { hasText: "Mở" }).click();
      const det = r.f.locator("#task-detail");
      await det.locator("text=Bạn là reviewer").waitFor({ timeout: 15000 });
      ok("Nút review hiện đúng cho reviewer được chỉ định", (await det.locator("button", { hasText: "Đạt (ACCEPT)" }).count()) === 1);
      ok("Evidence đã có", (await det.innerText()).includes("✓ Evidence"));
      await shot(r, "ReviewSI-task");
      ok("Không lỗi JavaScript", !b.errors.length && !r.errors.length, b.errors.concat(r.errors));
      // dừng ở đây: review là việc của reviewer thật, kịch bản không bấm.
    }
  } catch (e) {
    ok("exception", false, String(e && e.stack || e));
  } finally {
    await browser.close();
  }
  console.log(JSON.stringify({ phase, checks }));
})();
