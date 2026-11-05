/* CFP+ Danh mục Link Mẫu • chỉ đọc qua API; nội dung luôn hiển thị dạng text. */
(function () {
  'use strict';
  var root = document.querySelector('[data-catalog-root]');
  var input = document.getElementById('q');
  if (!root || !input) return;
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function get(p) { return fetch(p, { headers: { Accept: 'application/json' } }).then(function (r) { if (!r.ok) throw new Error('Lỗi ' + r.status); return r.json(); }); }
  var list = el('ul', { 'data-testid': 'catalog-list' }), meta = el('div', {});
  var count = el('p', { 'data-testid': 'catalog-count' });
  root.appendChild(count); root.appendChild(list); root.appendChild(meta);
  function item(r) {
    return el('li', { 'data-testid': 'catalog-item', 'data-id': r.canonical_id }, [
      el('strong', { text: r.canonical_id }), ' • ', el('a', { href: r.sandbox_url, text: r.title }),
      el('br'), el('small', { text: 'Gốc: ' + r.canonical_url + ' • Parent: ' + (r.parent_id || 'chưa xác minh') + ' • ' + r.classification + ' • ' + r.version })]);
  }
  var t = null;
  function load() {
    var q = input.value.trim();
    get('/api/catalog?limit=200' + (q ? '&q=' + encodeURIComponent(q) : '')).then(function (j) {
      list.textContent = '';
      count.textContent = j.items.length + ' / ' + j.total + ' mục' + (q ? ' khớp "' + q + '"' : '');
      j.items.forEach(function (r) { list.appendChild(item(r)); });
    }).catch(function (e) { count.textContent = 'Không tải được: ' + e.message; });
  }
  input.addEventListener('input', function () { clearTimeout(t); t = setTimeout(load, 200); });
  load();
  get('/api/catalog/meta').then(function (m) {
    meta.appendChild(el('section', { 'class': 'section', 'data-testid': 'catalog-modules' }, [el('h2', { text: '10 module chức năng (trạng thái thật)' }),
      el('ul', {}, m.modules.map(function (x) { return el('li', { text: x.n + ' • ' + x.name + ' — ' + x.status }); }))]));
    meta.appendChild(el('section', { 'class': 'section' }, [el('h2', { text: 'Thành phần sandbox (INTERNAL)' }),
      el('ul', {}, m.sandbox.map(function (x) { return el('li', {}, [el('a', { href: x.path, text: x.name })]); }))]));
    meta.appendChild(el('section', { 'class': 'section', 'data-testid': 'catalog-pending' }, [el('h2', { text: 'Chờ xác minh (chưa có ID/URL)' }),
      el('ul', {}, m.pending.map(function (x) { return el('li', { text: x.name + ' — ' + x.note }); }))]));
  });
})();
