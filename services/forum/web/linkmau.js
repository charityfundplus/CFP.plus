/* CFP+ Link Mẫu phổ thông • chỉ đọc API theo quyền; nội dung dạng text. */
(function () {
  'use strict';
  var root = document.querySelector('[data-lm-root]');
  if (!root) return;
  var cid = (location.pathname.match(/\/_internal\/linkmau\/([0-9]{1,32})\//) || [])[1];
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function sec(title, tid, kids) { return el('section', { class: 'section', 'data-testid': tid }, [el('h2', { text: title })].concat(kids)); }
  function list(items, fmt, empty) { return items.length ? el('ul', {}, items.map(function (x) { return el('li', { text: fmt(x) }); })) : el('p', { text: empty }); }
  fetch('/api/office/linkmau/' + cid, { headers: { Accept: 'application/json' }, credentials: 'same-origin' }).then(function (r) { if (!r.ok) throw new Error('Lỗi ' + r.status); return r.json(); }).then(function (d) {
    document.querySelector('[data-testid=lm-title]').textContent = 'Link Mẫu ' + d.id + ' • ' + d.profile.title;
    root.appendChild(sec('Trạng thái', 'lm-status', [
      el('p', { 'data-testid': 'lm-status-label', 'data-hold': String(d.status.hold), text: (d.status.hold ? '⛔ ' : '') + d.status.label }),
      el('p', {}, [el('a', { href: d.canonical_url, rel: 'noopener', text: d.canonical_url }), el('small', { text: '  ' + d.version + ' • ' + d.classification })]),
      el('small', { text: 'Quyền xem: ' + d.access })
    ]));
    root.appendChild(sec('Hồ sơ • Vai trò', 'lm-profile', [el('p', { text: d.profile.description || '(chưa có mô tả)' }),
      el('p', { text: 'Vai trò: ' + (d.role.registry_type ? d.role.registry_type + ' • ' + d.role.name + ' • ' + d.role.registry_status : 'trang công khai (chưa có trong Registry)') })]));
    root.appendChild(sec('Parent • Gia phả', 'lm-parent', [
      el('p', { text: 'Parent: ' + (d.parent.id || 'chưa xác minh') + ' • ' + d.parent.status }),
      list(d.parent.chain, function (x) { return x.id + ' • ' + x.name + (x.hold ? ' ⛔ HOLD' : ''); }, 'Không có chuỗi Registry.'),
      list(d.children, function (x) { return 'Con: ' + x.id + ' • ' + x.title; }, 'Không có trang con đã xuất bản.')
    ]));
    root.appendChild(sec('Nhiệm vụ', 'lm-tasks', [d.office.exists ? el('a', { href: d.office.path, text: 'Mở Văn Phòng ' + d.id }) : el('p', { text: 'Chưa có Văn Phòng cho ID này.' }),
      list(d.tasks, function (t) { return '#' + t.id + ' • ' + t.title + ' • ' + t.status; }, d.note)]));
    root.appendChild(sec('Diễn Đàn', 'lm-forum', [list(d.forum, function (f) { return f.forum + ' • ' + (f.title || ('bài #' + f.post_id)); }, 'Chưa có thảo luận (hoặc bạn chưa có quyền xem).')]));
    root.appendChild(sec('Tri thức', 'lm-knowledge', [list(d.knowledge, function (k) { return k; }, 'Chưa có liên kết tri thức.')]));
    root.appendChild(sec('Evidence • Review', 'lm-evidence', [list(d.evidence, function (e) { return 'Evidence #' + e.task_id + ' • ' + e.kind + ' • ' + e.url; }, 'Chưa có Evidence (hoặc chưa có quyền xem).'),
      list(d.reviews, function (v) { return 'Review #' + v.task_id + ' • ' + v.decision; }, 'Chưa có Review.')]));
    root.appendChild(sec('Lịch sử', 'lm-history', [list(d.history, function (h) { return '#' + h.task_id + ' ' + (h.from_status || '∅') + ' → ' + h.to_status + ' • ' + h.at; }, 'Chưa có lịch sử hiển thị.')]));
  }).catch(function (e) { root.textContent = e.message; });
})();
