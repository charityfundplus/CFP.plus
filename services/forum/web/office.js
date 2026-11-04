/* CFP+ Văn Phòng SI AI • P0 — chỉ đọc qua API; nội dung người dùng luôn hiển thị dạng text. */
(function () {
  'use strict';
  var root = document.querySelector('[data-office-root]');
  if (!root) return;
  var CID = (location.pathname.match(/\/_internal\/office\/([0-9]+)\//) || [])[1];

  function api(path) {
    return fetch('/api/office' + path, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : 'Lỗi ' + r.status); return j; }); });
  }
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function section(title, testid, kids) {
    return el('section', { 'class': 'section', 'data-testid': testid }, [el('h2', { text: title })].concat(kids));
  }
  function safeHref(u) { return /^https:\/\//.test(u || '') ? u : null; }
  function ext(u, label) { var h = safeHref(u); return h ? el('a', { href: h, rel: 'noopener noreferrer', target: '_blank', text: label || u }) : el('span', { text: '—' }); }
  function refLink(ref) {
    var a = el('a', { href: '#' + ref, 'data-ref': ref, 'data-testid': 'ref-link', text: ref });
    a.addEventListener('click', function (ev) {
      ev.preventDefault();
      if (decodeURIComponent(location.hash.slice(1)) === ref) showRef(ref); else location.hash = ref;  // Back quay lại được
    });
    return a;
  }
  function linksBlock(links) {
    if (!links) return null;
    var items = links.outgoing.map(function (l) { return el('li', {}, ['→ ' + l.relation + ' ', refLink(l.ref)]); })
      .concat(links.incoming.map(function (l) { return el('li', {}, ['← ' + l.relation + ' ', refLink(l.ref)]); }));
    return el('ul', { 'data-testid': 'links' }, items.length ? items : [el('li', { text: 'Chưa có liên kết.' })]);
  }

  var detail = el('section', { 'class': 'section forum-form', id: 'detail', 'data-testid': 'detail', 'aria-live': 'polite' });

  function showRef(ref) {
    var kind = ref.split(':')[0], id = ref.split(':')[1];
    var path = { enterprise: '/enterprises/', topic: '/topics/', dataset: '/datasets/', registry: '/registry/' }[kind];
    if (kind === 'office') { location.href = '/_internal/office/' + id + '/'; return; }
    if (!path) { detail.replaceChildren(el('p', { text: ref }), linksOf(ref)); return; }
    api(path + id).then(function (d) {
      var e = d.entity || d;
      var kids = [el('h3', { 'data-testid': 'detail-title', text: (e.name || e.title || ref) }), el('p', { 'class': 'forum-meta', text: ref })];
      if (d.chain) kids.push(el('p', { text: d.chain.map(function (x) { return x.name + ' (' + x.id + ')'; }).join(' → ') }));
      if (d.children && d.children.length) kids.push(el('h4', { text: 'Nhánh con trong Registry (' + d.children.length + ')' }),
        el('ul', { 'data-testid': 'registry-children' }, d.children.map(function (x) { return el('li', {}, [refLink('registry:' + x.id), ' ' + x.name + ' • ' + x.type]); })));
      if (d.office) kids.push(el('p', {}, [el('a', { href: '/_internal/office/' + e.id + '/', 'data-testid': 'office-link', text: 'Mở Văn Phòng ' + e.name })]));
      if (d.chapter_name) kids.push(el('p', { text: 'Chương ' + d.chapter + ' • ' + d.chapter_name + (d.group ? ' • ' + d.group.name : '') }));
      if (d.official_url) kids.push(el('p', {}, ['Trang chính thức: ', ext(d.official_url)]));
      if (d.url) kids.push(el('p', {}, ['Tài liệu: ', ext(d.url)]));
      if (d.source_url) kids.push(el('p', {}, ['Nguồn: ', ext(d.source_url)]));
      if (d.needs) kids.push(el('p', { text: 'Nhu cầu hợp tác: ' + d.needs }));
      kids.push(d.links ? linksBlock(d.links) : null);
      detail.replaceChildren.apply(detail, kids.filter(Boolean));
      if (!d.links && kind !== 'registry') linksOf(ref);
      detail.scrollIntoView({ block: 'start' });
    }).catch(function (e) { detail.replaceChildren(el('p', { 'class': 'forum-msg error', text: e.message })); });
  }
  function linksOf(ref) { api('/links?ref=' + encodeURIComponent(ref)).then(function (l) { detail.appendChild(linksBlock(l)); }); return el('span'); }

  function render(d, tax) {
    var o = d.office;
    document.querySelector('[data-testid=office-title]').textContent = 'Văn Phòng ' + o.display_name + ' • ' + o.canonical_id;
    var groupCards = tax.groups.map(function (g) {
      return el('li', { 'class': d.taxonomy.group && g.code === d.taxonomy.group.code ? 'forum-tag active' : 'forum-tag' }, [g.name]);
    });
    var kids = [
      section('5 Nhóm • 10 Chương', 'taxonomy', [el('ul', { 'class': 'forum-tags' }, groupCards),
        el('p', { text: 'Chương ' + d.taxonomy.chapter.id + ' • ' + d.taxonomy.chapter.name + ' • HUB 69 • CMP 267' })]),
      section('Gia phả định danh (Registry)', 'chain', [el('ol', {}, d.registry_chain.map(function (x) {
        return el('li', {}, [refLink('registry:' + x.id), ' ' + x.name + ' • ' + x.type]);
      }))]),
      section('Hồ sơ SI AI', 'profile', [
        el('p', { text: 'Nền tảng: ' + o.platform }), el('p', { text: 'Chuyên môn: ' + (o.specialties || '—') }),
        el('p', { text: 'Năng lực: ' + (o.capabilities || '—') }), el('p', { text: 'Giới hạn: ' + (o.limits || '—') }),
        el('p', {}, [el('strong', { 'data-testid': 'verification', text: 'Xác minh: ' + o.verification })]),
        el('p', {}, ['Link công khai: ', ext(d.public_link)])]),
      section('Thương hiệu • Sản phẩm • Dịch vụ', 'brand', d.brand.length ? d.brand.map(function (b) {
        return el('article', { 'class': 'chapter-card', 'data-testid': 'brand-item' }, [
          el('strong', { text: b.name + ' • ' + b.kind }), el('span', { 'class': 'forum-tag', 'data-testid': 'source-label', text: b.source_label }),
          el('p', { text: b.description }), el('p', {}, [ext(b.url, 'Trang sản phẩm'), ' • ', ext(b.source_url, 'Nguồn')])]);
      }) : [el('p', { text: 'Chưa có.' })]),
      section('Văn Phòng Siêu Bộ Đôi • Nhiệm Vụ', 'tasks', d.tasks.length ? d.tasks.map(function (t) {
        var pair = d.pairs.filter(function (p) { return p.id === t.pair_id; })[0];
        return el('article', { 'class': 'chapter-card', 'data-testid': 'task' }, [
          el('strong', { text: t.title }), el('span', { 'class': 'forum-tag', 'data-testid': 'task-status', text: t.status }),
          el('p', { text: 'Siêu Bộ Đôi: ' + o.display_name + ' + ' + (pair ? pair.software : '?') }),
          el('p', { text: 'Tiêu chí nghiệm thu: ' + t.acceptance }),
          el('h4', { text: 'Evidence' }), el('ul', {}, t.evidence.map(function (e) { return el('li', { 'data-testid': 'evidence' }, [e.kind + ': ', ext(e.url), ' — ' + e.description]); })),
          el('h4', { text: 'Review' }), el('ul', {}, t.reviews.map(function (r) { return el('li', { 'data-testid': 'review', text: r.decision + ' — ' + r.notes }); })),
          el('h4', { text: 'Lịch sử' }), el('p', { 'class': 'forum-meta', text: t.history.map(function (h) { return h.to_status; }).join(' → ') }),
          el('p', {}, [refLink('task:' + t.id)])]);
      }) : [el('p', { text: 'Chưa có nhiệm vụ.' })]),
      section('Liên kết hai chiều', 'office-links', [linksBlock(d.links)]),
      section('Kết nối hệ sinh thái', 'connections', [el('ul', {}, tax.connections.map(function (c) {
        var href = /^https:\/\//.test(c.link) || /^\/_internal\//.test(c.link) ? c.link : null;
        return el('li', {}, [href ? el('a', { href: href, 'data-testid': 'connection', text: c.name }) : c.name, c.status ? ' • ' + c.status : '']);
      }))]),
      detail
    ];
    root.replaceChildren.apply(root, kids);
    root.setAttribute('data-ready', '1');
  }

  if (!CID) { root.textContent = 'Thiếu ID.'; return; }
  window.addEventListener('hashchange', function () { if (location.hash.length > 1) showRef(decodeURIComponent(location.hash.slice(1))); });
  Promise.all([api('/offices/' + CID), api('/taxonomy')]).then(function (r) { render(r[0], r[1]); if (location.hash.length > 1) showRef(decodeURIComponent(location.hash.slice(1))); })
    .catch(function (e) { root.replaceChildren(el('p', { 'class': 'forum-msg error', 'data-testid': 'error', text: e.message })); root.setAttribute('data-ready', '1'); });
})();
