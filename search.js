/* CFP+ • Tìm ID/tên trên website tĩnh. Dữ liệu: /search-index.json (chỉ trang ID đã xuất bản). Hiển thị dạng text. */
(function () {
  'use strict';
  var box = document.querySelector('[data-cfp-search]');
  if (!box) return;
  var input = box.querySelector('input'), list = box.querySelector('[data-cfp-results]'), note = box.querySelector('[data-cfp-count]');
  var items = null;
  function fold(s) { return s.replace(/đ/g, 'd').replace(/Đ/g, 'D').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function render(q) {
    list.textContent = '';
    q = q.trim();
    if (!q || !items) { note.textContent = items ? items.length + ' trang ID đã xuất bản' : 'Đang tải…'; return; }
    var k = fold(q), hits = items.filter(function (x) { return x.k.indexOf(k) !== -1; });
    hits.sort(function (a, b) { return (b.id.indexOf(q) === 0) - (a.id.indexOf(q) === 0) || a.id.length - b.id.length || (a.id < b.id ? -1 : 1); });
    note.textContent = hits.length ? hits.length + ' kết quả' : 'Không có trang ID đã xuất bản khớp "' + q + '" (CFP+ không tự cấp ID).';
    hits.slice(0, 30).forEach(function (x) {
      var li = document.createElement('li'), a = document.createElement('a'), s = document.createElement('small');
      a.href = '/' + x.id + '/'; a.textContent = x.id + ' • ' + x.t.replace(/ • CFP\+$/, '');
      s.textContent = ' — ' + x.s; li.appendChild(a); li.appendChild(s); list.appendChild(li);
    });
  }
  input.addEventListener('input', function () { render(input.value); });
  fetch('/search-index.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) {
    items = d.items.map(function (x) { x.k = fold(x.id + ' ' + x.t + ' ' + x.d); return x; });
    render(input.value);
  }).catch(function () { note.textContent = 'Chưa tải được danh mục — mở HUB 69 hoặc 10 Chương để điều hướng.'; });
})();
