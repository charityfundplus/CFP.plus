/* CFP+ read-only directory: no invented IDs, roles or public routes. */
(function () {
  'use strict';
  var root = document.querySelector('[data-directory-root]');
  if (!root) return;
  function el(tag, text, attrs) {
    var n = document.createElement(tag);
    if (text) n.textContent = text;
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    return n;
  }
  function api(path) {
    return fetch(path, { credentials: 'same-origin', headers: { Accept: 'application/json' } }).then(function (r) {
      if (!r.ok) throw new Error('Không tải được dữ liệu (' + r.status + ').');
      return r.json();
    });
  }
  function section(title) { var s = el('section', '', { 'class': 'section' }); s.appendChild(el('h2', title)); root.appendChild(s); return s; }
  function render(h, d) {
    root.replaceChildren();
    root.appendChild(el('p', h.status, { 'role': 'status' }));
    var taxonomy = section('5 Nhóm • 10 Chương');
    taxonomy.appendChild(el('p', h.groups.map(function (g) { return g.name; }).join(' • ')));
    var chapters = el('ul');
    h.chapters.forEach(function (c) { var li = el('li'); li.appendChild(el('a', 'Chương ' + c.id + ' • ' + c.name, { href: 'https://cfp.plus/' + encodeURIComponent(c.id) + '/' })); chapters.appendChild(li); });
    taxonomy.appendChild(chapters);
    var offices = section('Văn Phòng • Link riêng cố định');
    offices.appendChild(el('label', 'Tìm theo tên hoặc ID Registry', { 'for': 'office-search' }));
    var input = el('input', '', { id: 'office-search', type: 'search', autocomplete: 'off', 'aria-controls': 'office-list' });
    offices.appendChild(input);
    var count = el('p', '', { 'role': 'status', 'aria-live': 'polite', 'data-testid': 'directory-count' }); offices.appendChild(count);
    var list = el('ul', '', { id: 'office-list', 'class': 'office-grid' }); offices.appendChild(list);
    function filter() {
      var q = input.value.trim().toLocaleLowerCase('vi');
      var found = h.offices.filter(function (o) { return (o.name + ' ' + o.canonical_id).toLocaleLowerCase('vi').includes(q); });
      list.replaceChildren();
      found.forEach(function (o) {
        var li = el('li', '', { 'class': 'chapter-card' });
        // Derive only a technical route from an existing API office ID, never accept arbitrary hrefs.
        if (!/^[0-9]{1,32}$/.test(o.canonical_id)) return;
        li.appendChild(el('a', o.name + ' • ' + o.canonical_id, { href: '/_internal/office/' + o.canonical_id + '/', 'data-testid': 'directory-office' }));
        li.appendChild(el('p', 'Xác minh: ' + o.verification)); list.appendChild(li);
      });
      count.textContent = found.length ? found.length + ' Văn Phòng' : 'Chưa có Văn Phòng phù hợp.';
    }
    input.addEventListener('input', filter); filter();
    var countries = section('Danh bạ quốc gia • Registry chỉ đọc');
    var countryList = el('ul');
    d.countries.forEach(function (c) {
      var li = el('li');
      li.appendChild(el('a', c.name + ' • ' + c.country_id, { href: 'https://cfp.plus/' + encodeURIComponent(c.country_id) + '/' }));
      li.appendChild(el('span', ' • ' + c.coverage + ' • ' + c.developers + ' nhà phát triển'));
      countryList.appendChild(li);
    }); countries.appendChild(countryList);
    var modules = section('Trạng thái module • Theo API sandbox');
    var ml = el('ul'); h.modules.forEach(function (m) { ml.appendChild(el('li', m.name + ' • ' + m.status + (m.note ? ' • ' + m.note : ''))); }); modules.appendChild(ml);
    root.setAttribute('data-ready', '1'); root.setAttribute('aria-busy', 'false');
  }
  function load() {
    Promise.all([api('/api/hub/69'), api('/api/directory/countries')]).then(function (r) { render(r[0], r[1]); }).catch(function (e) {
      root.replaceChildren(el('p', e.message, { role: 'alert' }));
      var retry = el('button', 'Thử lại', { type: 'button' }); retry.addEventListener('click', load); root.appendChild(retry);
      root.setAttribute('aria-busy', 'false');
    });
  }
  load();
})();
