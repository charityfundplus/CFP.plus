'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let chapters = [], groups = {}, records = [], source = null, structureReady = false;
  const numeric = value => /^[0-9]+$/.test(value);
  const fold = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLocaleLowerCase('vi');
  const node = (tag, value, cls) => { const n = document.createElement(tag); if (value !== undefined) n.textContent = value; if (cls) n.className = cls; return n; };
  const link = (href, label) => { const n = node('a', label); n.href = href; return n; };
  const localID = id => '/website/' + encodeURIComponent(id);
  const profile = record => {
    const card = node('article', undefined, 'card'); card.dataset.registryId = record.id;
    card.append(node('h3', record.id + ' • ' + record.name), node('p', record.status || 'Trạng thái theo nguồn'), node('p', record.intro || ''));
    card.append(link(localID(record.id), 'Mở đúng hồ sơ ' + record.id), node('br'), link(record.sourceCanonical, 'Liên kết nguồn hiện hữu'));
    card.append(node('small', 'SOURCE REGISTRY • chưa xác minh danh tính hoặc quyền vận hành; không tự cấp Canonical.', 'source-label'));
    if (record.parent_id) card.append(node('p', 'Parent theo nguồn: ' + record.parent_id));
    if (record.conflict) card.append(node('p', 'CONFLICT / HUMAN GOVERNANCE • giữ nguyên ID hiện hữu.', 'note'));
    return card;
  };
  function position(id, chapter) {
    const card = node('article', undefined, 'card'); card.dataset.positionId = id;
    card.append(node('h3', 'Vị trí ' + id + ' • Chương ' + chapter.id), node('p', chapter.title), node('small', 'VỊ TRÍ CẤU TRÚC • tên chủ đề và allocation chưa được Registry xác minh.', 'source-label'), link(localID(id), 'Mở vị trí ' + id));
    return card;
  }
  function chapterCard(ch) {
    const card = node('article', undefined, 'card'); card.id = 'chapter' + ch.id; card.dataset.chapterId = ch.id;
    const h = node('h3'); h.append(link(localID(ch.id), 'Chương ' + ch.id + ' • ' + ch.title)); card.append(h);
    card.append(node('p', '10 vị trí cấu trúc cấp 1 • chưa phải danh mục hồ sơ Canonical.'));
    const ids = node('div', undefined, 'ids');
    for (const id of ch.children) { const a = link(localID(id), id); a.title = 'Vị trí cấu trúc ' + id + ' • chưa xác minh allocation'; a.dataset.positionId = id; ids.append(a); }
    card.append(ids); return card;
  }
  function render() {
    const q = $('search').value.trim(), isNumber = numeric(q), lowered = fold(q);
    $('chapterGrid').replaceChildren(); $('registryGrid').replaceChildren();
    const group = location.hash.startsWith('#group-') ? location.hash.slice(7) : null;
    const visibleChapters = !q && group && Array.isArray(groups[group]) ? chapters.filter(ch => groups[group].includes(ch.id)) : chapters;
    for (const ch of visibleChapters) {
      if (!q || (isNumber ? ch.id === q : fold(ch.title).includes(lowered))) $('chapterGrid').append(chapterCard(ch));
      else if (isNumber && ch.children.includes(q)) $('chapterGrid').append(position(q, ch));
    }
    for (const r of records) if (!q || (isNumber ? r.id === q : fold(r.name).includes(lowered))) $('registryGrid').append(profile(r));
    $('empty').hidden = !structureReady || $('chapterGrid').childElementCount + $('registryGrid').childElementCount > 0;
    renderRoute();
  }
  function renderRoute() {
    const path = location.pathname, panel = $('routePanel'); panel.replaceChildren();
    if (path === '/website/' || path === '/website' || path === '/website/index.html') return;
    const id = decodeURIComponent(path.slice('/website/'.length));
    if (!numeric(id)) return;
    if (id === '69') {
      const card = node('article', undefined, 'card'); card.append(node('h2', 'HUB 69 • Cổng điều hướng CFP+'), node('p', 'HUB 69 hiện hữu; không tạo HUB hoặc định danh SpaceX mới.'), link('https://cfp.plus/69', 'HUB 69 • liên kết chuẩn')); panel.append(card); return;
    }
    const record = records.find(r => r.id === id);
    if (record) { panel.append(profile(record)); return; }
    const chapter = chapters.find(ch => ch.id === id);
    if (chapter) { const card = chapterCard(chapter); card.id = 'routeChapter' + id; panel.append(card); return; }
    const parent = chapters.find(ch => ch.children.includes(id));
    if (parent) { panel.append(position(id, parent)); return; }
    panel.append(node('p', 'ID ' + id + ': chưa tải được đúng hồ sơ Registry. Đăng nhập qua App rồi đọc lại; không dùng dữ liệu Parent hoặc snapshot thay thế.', 'note'));
  }
  async function registry() {
    records = []; source = null; $('registryRefresh').disabled = true; $('registryStatus').textContent = 'Đang đọc Registry từ Backend…'; render();
    try {
      const r = await fetch('/api/app/registry', {credentials: 'same-origin', cache: 'no-store'});
      if (!r.ok) throw new Error(r.status === 401 ? 'Cần phiên đăng nhập dùng chung. Mở App → Vận hành để đăng nhập rồi đọc lại Registry.' : 'Registry API HTTP ' + r.status + ' • không dùng snapshot dự phòng.');
      const data = await r.json();
      if (!Array.isArray(data.records) || data.registryBlobSHA !== '1f18068d66379ce90bb079dc56c77b4c4d66dcdf' || data.activationAllowed !== false || data.records.some(row => typeof row.id !== 'string')) throw new Error('Nguồn Registry không đúng contract; chưa hiển thị hồ sơ.');
      records = data.records; source = data; $('registryStatus').textContent = records.length + ' hồ sơ từ nguồn hiện hữu • pin ' + source.registryBlobSHA + ' • READ ONLY';
    } catch (e) { $('registryStatus').textContent = e.message || 'Registry chưa khả dụng.'; }
    finally { $('registryRefresh').disabled = false; render(); }
  }
  window.addEventListener('hashchange', () => { $('search').value = ''; render(); });
  $('search').addEventListener('input', render); $('registryRefresh').addEventListener('click', registry);
  fetch('/website/chapters.json', {cache: 'no-store'}).then(r => { if (!r.ok) throw Error('Không tải được khung Chương.'); return r.json(); }).then(data => {
    if (!Array.isArray(data.chapters) || data.chapters.length !== 10 || data.positionsAreCanonical !== false) throw Error('Khung Chương không đúng contract.');
    chapters = data.chapters; groups = data.groups || {}; structureReady = true; render();
  }).catch(e => { $('empty').hidden = false; $('empty').textContent = e.message; });
  registry();
})();
