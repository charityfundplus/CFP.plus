/* HUB 69 • existing public catalog only. No account or task data is read here. */
(function () {
  'use strict';
  var root = document.querySelector('[data-all-in-one]');
  if (!root) return;
  var cards = root.querySelector('[data-aio-categories]');
  var search = root.querySelector('#aio-search');
  var filter = root.querySelector('#aio-status');
  var summary = root.querySelector('[data-aio-summary]');
  var error = root.querySelector('[data-aio-error]');
  var retry = root.querySelector('[data-aio-retry]');
  var model;
  function el(tag, text, cls) {
    var n = document.createElement(tag);
    if (text) n.textContent = text;
    if (cls) n.className = cls;
    return n;
  }
  function fold(s) { return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase(); }
  function safePath(url) { return typeof url === 'string' && (url === '/' || /^\/(?!\/)[A-Za-z0-9_\-/.]+$/.test(url)) && url.indexOf('..') === -1; }
  function safeSource(url) { return typeof url === 'string' && /^https:\/\/cfp\.plus\/(?:[0-9]+\/)?$/.test(url); }
  function link(label, url, source) {
    if (!(source ? safeSource(url) : safePath(url))) return null;
    var a = el('a', label, 'aio-link' + (source ? ' aio-link-source' : ''));
    a.href = url;
    if (source) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
    return a;
  }
  function badge(status, label) {
    var b = el('span', label || model.statuses[status] || model.statuses.incomplete, 'aio-badge');
    b.dataset.status = Object.hasOwn(model.statuses, status) ? status : 'incomplete';
    return b;
  }
  function render() {
    cards.replaceChildren();
    var q = fold(search.value.trim());
    var rows = model.categories.filter(function (c) {
      return (!filter.value || c.status === filter.value) && (!q || fold(c.title + ' ' + c.note + ' ' + c.links.map(function (l) { return l.label + ' ' + (l.canonical_id || '') + ' ' + (l.note || ''); }).join(' ')).includes(q));
    });
    rows.forEach(function (c) {
      var card = el('article', null, 'aio-card');
      card.dataset.testid = 'aio-category'; card.dataset.key = c.key;
      card.append(el('h2', c.number + '. ' + c.title), badge(c.status, c.label), el('p', c.note, 'aio-note'));
      var list = el('ul');
      c.links.forEach(function (l) {
        var row = el('li');
        row.append(el('strong', l.label + (l.canonical_id ? ' • ID ' + l.canonical_id : '')), badge(l.status));
        if (l.note) row.append(el('p', l.note, 'aio-note'));
        if (l.parent_status === 'hold_conflict' || l.parent_status === 'parent_hold') row.append(el('p', l.parent_status === 'parent_hold' ? 'PARENT HOLD • Parent đang chờ thẩm định' : 'HOLD • ID đang chờ thẩm định', 'aio-hold'));
        var actions = el('div', null, 'aio-link-row');
        var local = link('Mở trong sandbox', l.sandbox_url, false);
        var canonical = link('Trang gốc CFP+', l.url, true);
        if (local) actions.append(local);
        if (canonical) actions.append(canonical);
        if (local || canonical) row.append(actions);
        if (l.source) row.append(el('p', l.source + (l.version ? ' • ' + l.version : ''), 'aio-source'));
        list.append(row);
      });
      card.append(list); cards.append(card);
    });
    summary.textContent = rows.length + ' / ' + model.categories.length + ' hạng mục' + (q || filter.value ? ' phù hợp' : ' trong HUB 69');
    if (!rows.length) cards.append(el('p', 'Chưa có kết quả. Thử tên nội dung hoặc ID khác.'));
  }
  function load() {
    error.hidden = true; retry.hidden = true;
    root.removeAttribute('data-ready'); summary.textContent = 'Đang đọc danh mục hiện hữu…';
    fetch('/api/ecosystem', { headers: { Accept: 'application/json' }, cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (data) {
      if (!data.all_in_one || !Array.isArray(data.all_in_one.categories) || data.all_in_one.categories.length !== 10) throw new Error('Danh mục chưa đầy đủ');
      model = data.all_in_one;
      search.disabled = false; filter.disabled = false;
      render(); root.dataset.ready = '1';
    }).catch(function () {
      cards.replaceChildren(); search.disabled = true; filter.disabled = true;
      error.textContent = 'Chưa đọc được trạng thái từ backend. Các lối vào ở trên vẫn mở được; hãy thử lại để xem danh mục.';
      error.hidden = false; retry.hidden = false; summary.textContent = 'Danh mục tạm thời chưa sẵn sàng';
    });
  }
  search.addEventListener('input', render); filter.addEventListener('change', render); retry.addEventListener('click', load);
  load();
})();
