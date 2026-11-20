// Real-browser check of the P1 localStorage fix (Chromium, iPhone 13 emulation). Not iPhone Safari.
// node sandbox/hub69-working-office/browser-localstorage.cjs <outdir>
const { chromium, devices } = require("playwright");
const http = require("node:http"), fs = require("node:fs"), path = require("node:path");
const out = process.argv[2] || ".";
const html = fs.readFileSync(path.join(__dirname, "index.html"));
const KEY = "cfp-hub69-local-office-v1";
(async () => {
  const srv = http.createServer((q, r) => { r.writeHead(200, { "content-type": "text/html; charset=utf-8" }); r.end(html); });
  await new Promise(r => srv.listen(0, "127.0.0.1", r));
  const url = `http://127.0.0.1:${srv.address().port}/`;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices["iPhone 13"] });
  const page = await ctx.newPage();
  const errors = []; page.on("pageerror", e => errors.push(String(e)));
  const results = [];
  const check = (name, ok, detail) => { results.push({ name, ok: !!ok, detail }); console.log(ok ? "PASS" : "FAIL", name, detail ?? ""); };

  await page.goto(url);
  const bad = '[{"time":"t","agent":"2633","status":"OPEN","task":"giữ"},null,{"task":4},"x"]';
  await page.evaluate(([k, v]) => localStorage.setItem(k, v), [KEY, bad]);
  await page.reload();
  check("malformed rows filtered, valid row rendered", (await page.locator("#entries li").count()) === 1);
  const q = await page.evaluate(k => localStorage.getItem(k + ".quarantine"), KEY);
  check("original bytes quarantined", q && JSON.parse(q).raw === bad);
  check("user told about quarantine", /cách ly 3 mục/.test(await page.locator("#msg").textContent()));
  await page.fill("#task", "Thử P1 trên Chromium iPhone 13");
  await page.click("#save");
  await page.reload();
  check("new row persists across reload", (await page.locator("#entries li").count()) === 2);
  const q2 = await page.evaluate(k => localStorage.getItem(k + ".quarantine"), KEY);
  check("quarantine still recoverable after save", JSON.parse(q2).raw === bad);
  const sw = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  check("no horizontal scroll at 390px", sw[0] <= sw[1], sw.join("/"));
  check("no JS errors", errors.length === 0, errors.join("; "));
  await page.screenshot({ path: path.join(out, "p1-localstorage-iphone13-chromium.png"), fullPage: true });
  await browser.close(); srv.close();
  fs.writeFileSync(path.join(out, "p1-browser-results.json"), JSON.stringify({ engine: "chromium (Playwright) iPhone 13 emulation — NOT real iPhone Safari", url_served: "local http", results }, null, 2));
  process.exit(results.every(r => r.ok) ? 0 : 1);
})().catch(e => { console.error(e); process.exit(1); });
