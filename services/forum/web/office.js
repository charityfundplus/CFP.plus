/* CFP+ Văn Phòng SI AI • P0 — chỉ đọc qua API; nội dung người dùng luôn hiển thị dạng text. */
(function () {
  'use strict';
  var root = document.querySelector('[data-office-root]');
  if (!root) return;
  var CID = (location.pathname.match(/\/_internal\/office\/([0-9]+)\//) || [])[1];

  var currentUser = null;
  function write(path, body) {
    return fetch('/api' + path, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CFP-Forum': '1' }, body: JSON.stringify(body) }).then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : 'Lỗi ' + r.status); return j; }); });
  }
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
    function one(arrow, l) {
      if (l.source) {  // bản gốc Link Mẫu: tiêu đề/version hiện hành, mở trang gốc (link không lưu bản sao)
        return el('li', { 'data-testid': 'source-link' }, [arrow + ' ' + l.relation + ' ',
          el('a', { href: '/' + l.source.canonical_id + '/', text: l.source.canonical_id + ' • ' + l.source.title }),
          el('small', { text: ' • ' + l.source.version })]);
      }
      return el('li', {}, [arrow + ' ' + l.relation + ' ', refLink(l.ref)]);
    }
    var items = links.outgoing.map(function (l) { return one('→', l); })
      .concat(links.incoming.map(function (l) { return one('←', l); }));
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
      sessionPanel(),
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
          el('h4', { text: 'Thảo luận trên Diễn Đàn' }), el('ul', {}, (t.discussions || []).map(function (x) {
            return el('li', { 'data-testid': 'task-discussion' }, [el('a', { href: x.url, 'data-testid': 'discussion-link', text: x.forum + ' • bài #' + x.post_id })]);
          })),
          el('h4', { text: 'Trao đổi' }), el('ul', {}, t.history.filter(function (h) { return h.to_status === 'COMMENT'; }).map(function (h) {
            return el('li', { 'data-testid': 'task-comment', text: '#' + h.actor_id + ': ' + h.note });
          })),
          el('h4', { text: 'Lịch sử' }), el('p', { 'class': 'forum-meta', text: t.history.filter(function (h) { return h.to_status !== 'COMMENT'; }).map(function (h) { return h.to_status; }).join(' → ') }),
          loopBlock(t), el('p', {}, [refLink('task:' + t.id)]), taskControls(t)]);
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

  function sessionPanel() {
    var box = el('section', { 'class': 'forum-form' });
    if (currentUser) {
      box.appendChild(el('p', { text: 'Đã đăng nhập: ' + currentUser.name }));
      var logout = el('button', { type: 'button', text: 'Đăng xuất' });
      logout.addEventListener('click', function () { write('/auth/logout', {}).then(function () { currentUser = null; root.replaceChildren(sessionPanel()); }); });
      box.appendChild(logout); return box;
    }
    var form = el('form', { 'class': 'forum-form' });
    var email = el('input', { type: 'email', required: '', autocomplete: 'username' });
    var password = el('input', { type: 'password', required: '', autocomplete: 'current-password' });
    var button = el('button', { type: 'submit', text: 'Đăng nhập' });
    var msg = el('p', { role: 'status' });
    form.append(el('label', {}, ['Email', email]), el('label', {}, ['Mật khẩu', password]), button, msg);
    form.addEventListener('submit', function (ev) {
      ev.preventDefault(); button.disabled = true;
      write('/auth/login', { email: email.value, password: password.value }).then(function (u) { currentUser = u; password.value = ''; return load(); })
        .catch(function (e) { msg.textContent = e.message; }).finally(function () { button.disabled = false; });
    }); box.appendChild(form); return box;
  }
  function loopBlock(t) {  // vòng khép kín: dữ liệu thật từ /tasks/{id}/loop (chỉ người xem được nhiệm vụ)
    var box = el('div', { 'data-testid': 'task-loop' }, [el('h4', { text: 'Vòng khép kín' })]);
    if (!currentUser) return box;
    api('/tasks/' + t.id + '/loop').then(function (l) {
      box.appendChild(el('ol', {}, l.stages.map(function (x) {
        return el('li', { 'data-testid': 'loop-stage', 'data-key': x.key, 'data-done': x.done ? '1' : '0',
          text: (x.done ? '✓ ' : '⏳ ') + x.label });
      })));
      box.appendChild(el('p', { 'class': 'loop-summary', 'data-testid': 'loop-summary',
        text: l.closed_loop ? 'Vòng đã khép kín.' : 'Bước tiếp theo: ' + l.next_stage }));
    }).catch(function () {});
    return box;
  }
  function taskControls(t) {
    var box = el('div', { 'class': 'forum-form compact' });
    if (!currentUser) return box;
    var msg = el('p', { role: 'status' });
    function action(label, endpoint, body) {
      var button = el('button', { type: 'button', text: label });
      button.addEventListener('click', function () {
        button.disabled = true;
        write('/office/tasks/' + t.id + '/' + endpoint, body()).then(load)
          .catch(function (e) { msg.textContent = e.message; }).finally(function () { button.disabled = false; });
      }); box.appendChild(button);
    }
    if (currentUser.id === t.assignee_id) {
      if (t.status === 'QUEUED') action('ACK nhiệm vụ', 'ack', function () { return { note: 'ACK từ tài khoản đang đăng nhập' }; });
      if (t.status === 'ACKED' || t.status === 'CHANGES_REQUESTED') action('Bắt đầu', 'start', function () { return {}; });
      if (t.status === 'ACKED' || t.status === 'IN_PROGRESS') {
        var url = el('input', { type: 'url', placeholder: 'https://…', 'aria-label': 'URL Evidence' });
        var sha = el('input', { 'aria-label': 'SHA Evidence', placeholder: 'SHA commit hoặc SHA256' });
        var desc = el('textarea', { 'aria-label': 'Mô tả Evidence' });
        box.append(el('label', {}, ['URL Evidence', url]), el('label', {}, ['SHA Evidence', sha]), el('label', {}, ['Mô tả Evidence', desc]));
        action('Nộp Evidence', 'evidence', function () { return { kind: 'test_report', url: url.value, sha: sha.value || null, description: desc.value }; });
        action('Gửi Review', 'submit', function () { return { note: 'Gửi kiểm tra độc lập' }; });
      }
    }
    if (currentUser.id === t.reviewer_id && t.status === 'IN_REVIEW') {
      var notes = el('textarea', { 'aria-label': 'Nhận xét Review' }); box.append(el('label', {}, ['Nhận xét Review', notes]));
      action('Chấp nhận kết quả', 'review', function () { return { decision: 'ACCEPT', notes: notes.value }; });
      action('Yêu cầu sửa', 'review', function () { return { decision: 'CHANGES_REQUESTED', notes: notes.value }; });
    }
    if (t.can_close) {  // backend tính quyền Closure; UI chỉ hiển thị
      var closeNote = el('textarea', { 'aria-label': 'Ghi chú Closure' }); box.append(el('label', {}, ['Ghi chú Closure', closeNote]));
      action('Đóng nhiệm vụ (Closure)', 'close', function () { return { note: closeNote.value }; });
    }
    if (t.status === 'CLOSED') {  // tri thức • bài học (chủ đề theo Chương), rồi nhiệm vụ tiếp theo tham chiếu lại
      var lTitle = el('input', { 'aria-label': 'Tiêu đề bài học', maxlength: '200' });
      var lChapter = el('select', { 'aria-label': 'Chương của bài học' }, ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'].map(function (n) {
        return el('option', { value: n, text: 'Chương ' + n });
      }));
      var lSummary = el('textarea', { 'aria-label': 'Nội dung bài học', maxlength: '4000' });
      box.append(el('label', {}, ['Tiêu đề bài học', lTitle]), el('label', {}, ['Chương của bài học', lChapter]),
        el('label', {}, ['Nội dung bài học', lSummary]));
      action('Ghi bài học', 'lessons', function () { return { title: lTitle.value, chapter: lChapter.value, summary: lSummary.value }; });
    }
    if (t.status !== 'CLOSED') {
      var forum = el('select', { 'aria-label': 'Mở thảo luận ở' }, [el('option', { value: 'sieu-bo-doi', text: 'Diễn Đàn Siêu Bộ Đôi (công khai)' }),
        el('option', { value: 'si-ai-hstdn', text: 'Diễn Đàn SI AI • HSTDN (thành viên)' })]);
      var dTitle = el('input', { 'aria-label': 'Tiêu đề thảo luận', maxlength: '200' });
      var dBody = el('textarea', { 'aria-label': 'Nội dung thảo luận', maxlength: '10000' });
      var dHstdn = el('input', { 'aria-label': 'HSTDN (chỉ Diễn Đàn SI AI • HSTDN)', maxlength: '200' });
      box.append(el('label', {}, ['Mở thảo luận ở', forum]), el('label', {}, ['Tiêu đề thảo luận', dTitle]),
        el('label', {}, ['Nội dung thảo luận', dBody]), el('label', {}, ['HSTDN (chỉ Diễn Đàn SI AI • HSTDN)', dHstdn]));
      action('Mở thảo luận', 'discussions', function () {
        var b = { forum: forum.value, title: dTitle.value, body: dBody.value };
        if (forum.value === 'si-ai-hstdn') b.hstdn = dHstdn.value;
        return b;
      });
    }
    var talk = el('textarea', { 'aria-label': 'Trao đổi nhiệm vụ', maxlength: '2000' });
    box.append(el('label', {}, ['Trao đổi', talk]));
    action('Gửi trao đổi', 'comments', function () { return { body: talk.value }; });
    box.appendChild(msg); return box;
  }
  function load() {
    root.removeAttribute('data-ready');
    return Promise.all([api('/offices/' + CID), api('/taxonomy')]).then(function (r) {
      render(r[0], r[1]); if (location.hash.length > 1) showRef(decodeURIComponent(location.hash.slice(1)));
    }).catch(function (e) { root.replaceChildren(sessionPanel(), el('p', { 'class': 'forum-msg error', 'data-testid': 'error', text: e.message })); root.setAttribute('data-ready', '1'); });
  }
  if (!CID) { root.textContent = 'Thiếu ID.'; return; }
  window.addEventListener('hashchange', function () { if (location.hash.length > 1) showRef(decodeURIComponent(location.hash.slice(1))); });
  fetch('/api/auth/me', { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (d) { currentUser = d.user; return load(); });
})();
