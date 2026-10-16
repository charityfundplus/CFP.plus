// Thin Codex 1 integration. All identity/lineage comes from the authenticated Core API.
const $ = selector => document.querySelector(selector);
const node = (tag, text = '') => { const n = document.createElement(tag); n.textContent = text; return n; };
const section = node('section'); section.id = 'registry-office'; section.className = 'workspace';
section.append(node('h2', 'Registry • Tra cứu ID / ID lookup'));
const form = node('form'), label = node('label', 'ID hoặc tên / ID or name'), query = node('input');
query.name = 'query'; query.maxLength = 160; label.append(query);
const search = node('button', 'Tra cứu / Search'); search.disabled = true; form.append(label, search);
const openai = node('button', 'HSTDN OpenAI • Hồ sơ mẫu / Reference profile'); openai.disabled = true;
const status = node('p', 'Đăng nhập để tra cứu Registry. / Sign in to search the Registry.'); status.setAttribute('role', 'status');
const results = node('div'), packet = node('div'); results.className = 'records';
section.append(form, openai, status, results, packet); $('#p2-office').before(section);
let generation = 0;
async function api(path, body) {
  const response = await fetch('/api/core/' + path, body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  const value = await response.json(); if (!response.ok) throw Error(value.error); return value;
}
function external(text, href) { const a = node('a', text); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
async function project(id) {
  try {
    const value = await api('chatgpt-project', {id}); packet.replaceChildren(node('h3', value.label));
    packet.append(node('p', 'Sao chép hướng dẫn vào Dự án ChatGPT được chọn. / Copy the instructions into your chosen ChatGPT project.'),
      node('p', 'Dùng ID hiện hữu: ' + value.id + ' • ' + value.reviewStatus));
    const text = node('textarea'); text.readOnly = true; text.rows = 12; text.value = value.instructions;
    text.setAttribute('aria-label', 'Hướng dẫn Dự án ChatGPT / ChatGPT project instructions'); text.style.width = '100%';
    const copy = node('button', 'Sao chép / Copy');
    copy.onclick = async () => { try { await navigator.clipboard.writeText(value.instructions); status.textContent = 'Đã sao chép / Copied'; } catch { text.focus(); text.select(); status.textContent = 'Chọn và sao chép hướng dẫn. / Select and copy the instructions.'; } };
    packet.append(text, copy, external('Mở ChatGPT / Open ChatGPT', value.entryURL), external('Hướng dẫn chính thức / Official guidance', value.documentationURL));
  } catch (error) { status.textContent = error.message; }
}
function card(row) {
  const article = node('article'); article.append(node('h3', row.id + ' • ' + row.name), node('p', row.type + ' • Parent: ' + (row.parent ?? 'CHƯA CÓ / UNAVAILABLE')),
    node('p', row.reviewStatus + ' • Identity NOT VERIFIED'), external('Link Mẫu: ' + row.id, row.canonicalLink));
  const detail = node('button', 'Con/Cháu & Evidence / Descendants & evidence');
  detail.onclick = async () => { try { const value = await api('registry/' + row.id); const pre = node('pre', JSON.stringify(value, null, 2)); pre.className = 'mock-receipt'; packet.replaceChildren(pre); } catch (e) { status.textContent = e.message; } };
  const action = node('button', 'Làm Dự Án tại ChatGPT'); action.onclick = () => project(row.id); article.append(detail, action); return article;
}
form.onsubmit = async event => {
  event.preventDefault(); const request = ++generation;
  try {
    const value = await api('registry?' + new URLSearchParams({query: query.value, limit: '30'})); if (request !== generation) return;
    results.replaceChildren(...value.records.map(card)); packet.replaceChildren();
    status.textContent = value.total + ' hồ sơ khớp; hiển thị ' + value.records.length + '. Registry revision: ' + value.provenance.revision + ' • Quyền vận hành CHƯA XÁC MINH.';
  } catch (error) { if (request === generation) { results.replaceChildren(); status.textContent = error.message; } }
};
openai.onclick = async () => {
  const request = ++generation;
  try {
    const value = await api('hstdn-openai'); if (request !== generation) return; results.replaceChildren(); packet.replaceChildren();
    results.append(node('h3', value.name), node('p', value.introduction), node('p', 'HSTDN ID: chưa có / unavailable • ' + value.reviewStatus),
      ...[value.country, value.aiCountry, value.developer, ...value.ai].map(card));
    results.append(node('p', value.capabilities.map(c => c.name + ': ' + c.scope).join(' • ')), node('p', value.limits.join(' • ')),
      node('p', 'Liên hệ / Contacts: ' + value.contactVerification), external('Học & thực hành / Learn & practice', value.learning.basic));
    const vaults = node('ul'); for (const vault of value.vaults) vaults.append(node('li', vault.kind + ' • ' + vault.status));
    results.append(vaults, node('p', 'Còn thiếu / Blockers: ' + value.blockers.join(' • ')));
    status.textContent = 'Nguồn Registry / Registry source: ' + value.provenance.revision;
  } catch (error) { if (request === generation) status.textContent = error.message; }
};
document.addEventListener('p2-state', event => {
  search.disabled = openai.disabled = false;
  // Every pair gets the action. Unbound synthetic pairs stay visibly blocked; no ID is invented.
  [...$('#core-pairs').children].forEach((card, index) => {
    const id = event.detail.pairs[index]?.identity?.id;
    const action = node('button', 'Làm Dự Án tại ChatGPT'); action.disabled = typeof id !== 'string' || !/^\d+$/.test(id);
    action.onclick = () => project(id); card.append(action);
    if (action.disabled) card.append(node('p', 'Chờ ID số đã xác minh và Link Mẫu hiện hữu. / Awaiting an existing verified numeric ID and template link.'));
  });
});
