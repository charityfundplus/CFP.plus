/* CFP+ Bản đồ hệ sinh thái • chỉ đọc API; nội dung dạng text. */
(function () {
  'use strict';
  var root = document.querySelector('[data-map-root]');
  if (!root) return;
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  fetch('/api/ecosystem', { headers: { Accept: 'application/json' } }).then(function (r) { if (!r.ok) throw new Error('Lỗi ' + r.status); return r.json(); }).then(function (m) {
    root.appendChild(el('p', { 'data-testid': 'map-counts', text: m.mode + ' • thử nghiệm: ' + m.counts.sandbox + ' • một phần: ' + m.counts.partial + ' • chờ hoàn thiện: ' + m.counts.planned }));
    var list = el('ol', { 'data-testid': 'map-list' });
    m.components.forEach(function (c) {
      var pages = c.public_pages.map(function (p) {
        return p.url ? el('a', { href: p.url, rel: 'noopener', text: p.id + (p.parent_status === 'hold_conflict' ? ' ⛔HOLD' : '') }) : el('span', { text: p.id + ' (chưa có trang)' });
      });
      var kids = [el('strong', { text: c.n + '. ' + c.name }), el('br'), el('small', { 'data-testid': 'map-status', 'data-status': c.function.status, text: c.label })];
      if (c.function.sandbox_path) kids.push(el('br'), el('a', { href: c.function.sandbox_path, 'data-testid': 'map-open', text: 'Mở trong sandbox' }));
      if (pages.length) { kids.push(el('br'), el('small', { text: 'Trang công khai: ' })); pages.forEach(function (a, i) { if (i) kids.push(' • '); kids.push(a); }); }
      kids.push(el('p', { text: c.note }));
      list.appendChild(el('li', { 'data-testid': 'map-item', 'data-key': c.key }, kids));
    });
    root.appendChild(list);
  }).catch(function (e) { root.textContent = e.message; });
})();
