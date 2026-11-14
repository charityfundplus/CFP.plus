// Runs the real /id/index.html resolver script in Node with a minimal DOM,
// reading registry JSON from the repo. Usage: node resolve_id.mjs <repoRoot> <ID>
import fs from 'node:fs'; import path from 'node:path';
const [root, id] = process.argv.slice(2);
const html = fs.readFileSync(path.join(root, 'id/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const els = {};
const el = () => ({ textContent: '', innerHTML: '', classList: { remove() {}, add() {} } });
globalThis.document = { title: '', getElementById: k => (els[k] ??= el()) };
globalThis.location = { pathname: '/' + id };
globalThis.fetch = async u => { const f = path.join(root, u.replace(/^\//, ''));
  return { json: async () => JSON.parse(fs.readFileSync(f, 'utf8')) }; };
await eval('(async()=>{' + script.replace(/^\s*\(async\(\)=>\{/, '').replace(/\}\)\(\);\s*$/, '') + '})()');
console.log(JSON.stringify({ id, title: els.title?.textContent, doc: document.title, identity: els.identity?.textContent, body: els['entity-body']?.innerHTML || '' }));
