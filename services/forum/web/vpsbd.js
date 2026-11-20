/* CFP+ Văn Phòng Siêu Bộ Đôi • dữ liệu từ /api/office/sieu-bo-doi; nội dung dạng text. */
(function () {
  'use strict';
  var root = document.querySelector('[data-vpsbd-root]');
  if (!root) return;
  var LABEL = { open: 'mở được', login: 'cần đăng nhập', approval: 'cần duyệt', not_connected: 'chưa kết nối' };
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function btn(b) {
    return el('li', { class: 'vpsbd-btn' }, [
      el('a', { href: b.path, 'data-testid': 'vpsbd-button', 'data-key': b.key, 'data-status': b.status, text: b.label }),
      el('small', { text: ' • ' + LABEL[b.status] + (b.note ? ' — ' + b.note : '') })]);
  }
  fetch('/api/office/sieu-bo-doi', { headers: { Accept: 'application/json' } }).then(function (r) { if (!r.ok) throw new Error('Lỗi ' + r.status); return r.json(); }).then(function (d) {
    root.appendChild(el('p', { 'data-testid': 'vpsbd-counts', text: d.counts.entries + ' SI AI có trang ID • ' + d.counts.with_office + ' có Văn Phòng trong sandbox • ' + d.counts.pairs + ' Siêu Bộ Đôi đã tạo. ' + d.ephemeral_note }));
    root.appendChild(el('section', { class: 'section', 'data-testid': 'vpsbd-common' }, [el('h2', { text: 'Lối vào chung' }), el('ul', {}, d.common.map(btn))]));
    var list = el('ol', { 'data-testid': 'vpsbd-list' });
    d.entries.forEach(function (e) {
      list.appendChild(el('li', { 'data-testid': 'vpsbd-entry', 'data-id': e.id }, [
        el('strong', { text: e.id + ' • ' + e.name }),
        el('small', { text: '  ' + (e.id_status === 'HOLD' || e.id_status === 'PARENT_HOLD' ? '⚠️ ' + e.id_status + ' — đang xác minh' : e.id_status) }),
        el('p', { text: e.pairs.length ? 'Siêu Phần Mềm: ' + e.pairs.map(function (p) { return p.software; }).join(', ') : 'Chưa ghép Siêu Phần Mềm trong sandbox.' }),
        el('ul', {}, e.buttons.map(btn))]));
    });
    root.appendChild(el('section', { class: 'section' }, [el('h2', { text: 'Danh sách Siêu Bộ Đôi • Link Mẫu riêng' }), list]));
    root.appendChild(el('section', { class: 'section', 'data-testid': 'vpsbd-nav' }, [el('h2', { text: '5 Nhóm • 10 Chương' }),
      el('ul', {}, d.nav.map(function (n) { return el('li', {}, [el('a', { href: n.url, rel: 'noopener', 'data-testid': 'vpsbd-nav-link', text: n.label })]); }))]));
  }).catch(function (e) { root.textContent = e.message; });
})();
