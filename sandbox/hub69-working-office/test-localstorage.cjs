const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "Expected the HUB 69 inline browser script");

function run(raw) {
  const elements = new Map();
  let writes = [];
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
    getItem() { return raw; },
    setItem(key, value) { writes.push({key, value}); }
  };
  const context = { document, localStorage, navigator: {}, console, Date, JSON, URL, Blob, setTimeout };
  vm.runInNewContext(match[1], context, {timeout: 1000});
  return { el, writes };
}

const cases = [
  ["empty", null, 0],
  ["object", "{}", 0],
  ["null", "null", 0],
  ["broken JSON", "{bad", 0],
  ["invalid array entries", '[null,4,{},{"task":4}]', 0],
  ["valid row", '[{"time":"2026-11-11T00:00:00Z","agent":"2633","status":"OPEN","task":"Review"}]', 1],
  ["mixed", '[{"time":"t","agent":"2633","status":"OPEN","task":"Review"},null,{"time":"bad","task":"none"}]', 1]
];
for (const [label, input, expected] of cases) {
  const result = run(input);
  assert.equal(result.el("entries").children.length, expected, label);
  result.el("task").value = "Test sandbox";
  result.el("agent").value = "2633";
  result.el("save").onclick();
  assert.equal(result.writes.length, 1, label + " should save");
  assert.equal(JSON.parse(result.writes[0].value).length, expected + 1, label + " should persist the filtered array");
  console.log("PASS", label);
}
console.log("PASS: 7 localStorage regression cases using the real inline HUB 69 script");
