// CFP+ • Super-pair directory (read-only). Renders data/super-pair-source-inventory.json
// joined with evidence/link-audit.json. No writes, no external requests besides same-origin JSON.
(function () {
  'use strict';
  var CH = { 0: 'Nền Tảng', 1: 'Sự Sống', 2: 'Con Người', 3: 'Ba Quỹ', 4: 'Tôn Giáo', 5: 'Cộng Đồng', 6: 'AI & Công Nghệ', 7: 'Doanh Nghiệp', 8: 'Tổ Chức', 9: 'Quốc Gia' };
  var CH_EN = { 0: 'Foundation', 1: 'Life', 2: 'Humanity', 3: 'Three Funds', 4: 'Religion', 5: 'Community', 6: 'AI & Technology', 7: 'Enterprise', 8: 'Organisations', 9: 'Nations' };
  var rows = [], audit = {}, $ = function (id) { return document.getElementById(id); };

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs, k)) n.setAttribute(k, attrs[k]);
    (children || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function bi(vi, en) { return [el('span', { lang: 'vi' }, [vi]), el('span', { lang: 'en' }, [en])]; }
  function chip(cls, kids) { return el('span', { 'class': 'chip ' + cls }, kids); }
  function norm(s) { return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase(); }

  function render() {
    var q = norm($('q').value.trim()), ch = $('ch').value, st = $('st').value;
    var list = $('list'); list.textContent = '';
    var shown = rows.filter(function (r) {
      var live = audit[r.id] && audit[r.id].live;
      return (!ch || r.chapter === ch) && (!st || live === st) && (!q || norm(r.id + ' ' + r.name).indexOf(q) > -1);
    });
    for (var c = 0; c <= 9; c++) {
      var group = shown.filter(function (r) { return r.chapter === String(c); });
      if (!group.length) continue;
      var sec = el('section', { 'class': 'card', 'aria-label': 'Chương ' + c });
      sec.appendChild(el('h2', null, [String(c) + ' • '].concat(bi(CH[c], CH_EN[c])).concat([' (' + group.length + ')'])));
      var tbody = el('tbody');
      group.forEach(function (r) {
        var a = audit[r.id] || {}, live = a.live || 'UNKNOWN';
        var notion = r.notion_url
          ? el('a', { href: r.notion_url, target: '_blank', rel: 'noopener noreferrer' }, ['Notion'])
          : chip('bad', ['PENDING']);
        var site = el('a', { href: '/' + r.id + '/' }, ['cfp.plus/' + r.id]);
        var status = chip(live === 'OWN_PAGE' ? 'ok' : 'warn', [live]);
        var nameCell = el('td', null, [r.name]);
        if (r.note) nameCell.appendChild(el('small', { 'class': 'note' }, ['⚠️ ' + r.note]));
        tbody.appendChild(el('tr', null, [el('td', null, [el('strong', null, [r.id])]), nameCell, el('td', null, [notion]), el('td', null, [site, el('br'), status])]));
      });
      var head = el('tr', null, [el('th', null, ['ID']), el('th', null, bi('Tên (nguồn Notion)', 'Name (Notion source)')), el('th', null, ['Notion']), el('th', null, ['Website'])]);
      sec.appendChild(el('div', { 'class': 'table-wrap' }, [el('table', null, [el('thead', null, [head]), tbody])]));
      list.appendChild(sec);
    }
    $('count').textContent = shown.length + ' / ' + rows.length;
  }

  function summary(meta) {
    var own = rows.filter(function (r) { return (audit[r.id] || {}).live === 'OWN_PAGE'; }).length;
    var fb = rows.filter(function (r) { return (audit[r.id] || {}).live === 'ID_FALLBACK'; }).length;
    var pend = rows.filter(function (r) { return !r.notion_url; }).length;
    var s = $('summary'); s.textContent = '';
    [chip('', [rows.length + ' Siêu Bộ Đôi']), chip('ok', ['OWN_PAGE ' + own]), chip('warn', ['ID_FALLBACK ' + fb]), chip('bad', ['Notion PENDING ' + pend]), chip('bad', ['VERIFIED 0'])]
      .forEach(function (c) { s.appendChild(c); s.appendChild(document.createTextNode(' ')); });
    if (meta) $('checked').textContent = 'cfp.plus checked (UTC): ' + meta;
  }

  for (var c = 0; c <= 9; c++) $('ch').appendChild(el('option', { value: String(c) }, [c + ' • ' + CH[c]]));
  ['q', 'ch', 'st'].forEach(function (id) { $(id).addEventListener('input', render); });

  Promise.all([
    fetch('../data/super-pair-source-inventory.json').then(function (r) { if (!r.ok) throw Error('inventory ' + r.status); return r.json(); }),
    fetch('../evidence/link-audit.json').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
  ]).then(function (res) {
    rows = res[0].rows;
    if (res[1]) res[1].rows.forEach(function (a) { audit[a.id] = a; });
    summary(res[1] && res[1].checkedAtUTC);
    render();
  }).catch(function (e) {
    $('summary').textContent = '';
    $('summary').appendChild(chip('bad', ['ERROR: ' + e.message]));
  });
})();
