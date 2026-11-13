// HUB 69 working office • localStorage regression (P1, PR #203 → #206 → this branch).
// Runs the REAL inline script from index.html in a VM with a fake DOM + storage.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "Expected the HUB 69 inline browser script");
const KEY = "cfp-hub69-local-office-v1";
const QKEY = KEY + ".quarantine";

function run(raw, opts = {}) {
  const elements = new Map();
  const store = new Map();
  if (raw !== null) store.set(KEY, raw);
  const writes = [];
  const el = id => {
    if (!elements.has(id)) {
      elements.set(id, {
        value: "", textContent: "", children: [],
        replaceChildren() { this.children = []; },
        append(child) { this.children.push(child); }
      });
    }
    return elements.get(id);
  };
  const document = { getElementById: el, createElement: () => ({
    textContent: "", children: [], append(child) { this.children.push(child); }
  }) };
  const localStorage = {
    getItem(k) { if (opts.getThrows) throw new Error("SecurityError"); return store.has(k) ? store.get(k) : null; },
    setItem(k, v) { if (opts.setThrows) throw new Error("QuotaExceededError"); writes.push({ key: k, value: v }); store.set(k, v); }
  };
  const context = { document, localStorage, navigator: {}, console, Date, JSON, URL, Blob, setTimeout, String };
  vm.runInNewContext(match[1], context, { timeout: 1000 });
  return { el, writes, store };
}

function save(result) {
  result.el("task").value = "Test sandbox";
  result.el("agent").value = "2633";
  result.el("save").onclick();
}

// [label, raw, expected valid rows, expect quarantine]
const cases = [
  ["empty", null, 0, false],
  ["object", "{}", 0, true],
  ["null", "null", 0, true],
  ["broken JSON", "{bad", 0, true],
  ["invalid array entries", '[null,4,{},{"task":4}]', 0, true],
  ["valid row", '[{"time":"2026-11-11T00:00:00Z","agent":"2633","status":"OPEN","task":"Review"}]', 1, false],
  ["mixed", '[{"time":"t","agent":"2633","status":"OPEN","task":"Review"},null,{"time":"bad","task":"none"}]', 1, true]
];
let n = 0;
for (const [label, input, expected, expectQ] of cases) {
  const result = run(input);
  assert.equal(result.el("entries").children.length, expected, label + " rendered rows");
  const q = result.writes.filter(w => w.key === QKEY);
  assert.equal(q.length, expectQ ? 1 : 0, label + " quarantine write");
  if (expectQ) {
    assert.equal(JSON.parse(q[0].value).raw, input, label + " quarantine keeps the exact original bytes");
    assert.match(result.el("msg").textContent, /cách ly/, label + " user is told data was quarantined");
  }
  save(result);
  const main = result.writes.filter(w => w.key === KEY);
  assert.equal(main.length, 1, label + " should save");
  assert.equal(JSON.parse(main[0].value).length, expected + 1, label + " should persist the filtered array");
  // Original malformed bytes must still be recoverable after the overwrite.
  if (expectQ) assert.equal(JSON.parse(result.store.get(QKEY)).raw, input, label + " original recoverable after save");
  console.log("PASS", label); n++;
}

// Storage blocked (Safari private mode / disabled cookies): page must still render and not crash.
{
  const result = run(null, { getThrows: true });
  assert.equal(result.el("entries").children.length, 0);
  save(result);
  console.log("PASS getItem throws"); n++;
}
// Quota exceeded on write: user gets an explicit message, no crash.
{
  const result = run(null, { setThrows: true });
  save(result);
  assert.equal(result.el("msg").textContent, "Không lưu được trên thiết bị");
  console.log("PASS setItem throws"); n++;
}
// Delete button removes exactly the clicked row and persists.
{
  const two = JSON.stringify([
    { time: "a", agent: "1", status: "OPEN", task: "first" },
    { time: "b", agent: "2", status: "OPEN", task: "second" }
  ]);
  const result = run(two);
  const rows = result.el("entries").children;
  rows[0].children[0].onclick();
  const saved = JSON.parse(result.store.get(KEY));
  assert.deepEqual(saved.map(x => x.task), ["second"]);
  console.log("PASS delete row"); n++;
}

// The "copy for forum" text must be the #201 template so hub69-dispatch can parse it.
{
  const result = run(null);
  let copied = null;
  const ctx = result; // reuse elements
  ctx.el("agent").value = "Claude Code"; ctx.el("link").value = "691121";
  ctx.el("task").value = "Sửa P1"; ctx.el("status").value = "ACK"; ctx.el("evidence").value = "https://e/x"; ctx.el("taskref").value = "201#6813472700";
  // navigator.clipboard is absent in the VM → the handler must not throw
  ctx.el("copy").onclick();
  const text = ctx.el("msg").textContent;
  for (const line of ["**SI AI / Siêu Bộ Đôi:** Claude Code", "**Link riêng / ID:** 691121", "**Nhiệm vụ:** Sửa P1",
                      "**Trạng thái:** ACK", "**Task:** 201#6813472700", "**Kết quả và Evidence URL:** https://e/x"])
    assert.ok(text.includes(line), "copy text has #201 template line: " + line);
  fs.writeFileSync(path.join(__dirname, "evidence", "copy-template-sample.txt"), text.split("\n").slice(1).join("\n") + "\n");
  console.log("PASS copy produces the #201 template (fallback when clipboard API is absent)"); n++;
}

console.log(`PASS: ${n} localStorage regression cases using the real inline HUB 69 script`);
