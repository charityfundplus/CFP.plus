/* CFP+ Forum UI • P0 — client gọi API của CFP+ Forum Service (không lưu dữ liệu ở trình duyệt). */
(function () {
  'use strict';
  var root = document.querySelector('[data-forum]');
  if (!root) return;
  var KEY = root.getAttribute('data-forum');
  var API = '/api';
  var state = { user: null, forum: null, posts: [], readError: null };

  function api(method, path, body) {
    var opts = { method: method, credentials: 'same-origin', headers: { 'Accept': 'application/json' } };
    if (method !== 'GET') opts.headers['X-CFP-Forum'] = '1';
    if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    return fetch(API + path, opts).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) {
          var d = j.detail;
          var msg = typeof d === 'string' ? d : (Array.isArray(d) ? d.map(function (x) { return x.msg; }).join('; ') : 'Lỗi ' + r.status);
          var e = new Error(msg); e.status = r.status; throw e;
        }
        return j;
      });
    });
  }

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'text') n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function field(label, input) { return el('label', {}, [label, input]); }
  function fmt(iso) { try { return new Date(iso).toLocaleString('vi-VN'); } catch (e) { return iso; } }

  var msg = el('p', { 'class': 'forum-msg', role: 'status', 'aria-live': 'polite', 'data-testid': 'msg' });
  function flash(t, err) { msg.textContent = t; msg.className = 'forum-msg' + (err ? ' error' : ''); }
  function onSubmit(form, fn) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var btn = form.querySelector('button[type=submit]'); if (btn) btn.disabled = true;
      Promise.resolve().then(fn).catch(function (e) { flash(e.message, true); })
        .then(function () { if (btn) btn.disabled = false; });
    });
  }

  function reload(note) {
    return api('GET', '/auth/me').then(function (r) {
      state.user = r.user;
      return api('GET', '/forums/' + KEY);
    }).then(function (f) {
      state.forum = f;
      return api('GET', '/forums/' + KEY + '/posts').then(function (p) {
        state.posts = p.posts; state.readError = null;
      }, function (e) { state.posts = []; state.readError = e.message; });
    }).then(function () { render(); if (note) flash(note); })
      .catch(function (e) { render(); flash('Không kết nối được máy chủ diễn đàn: ' + e.message, true); });
  }

  function authBlock() {
    if (state.user) {
      var out = el('button', { type: 'button', 'class': 'button secondary', 'data-testid': 'logout', text: 'Đăng xuất' });
      out.addEventListener('click', function () { api('POST', '/auth/logout').then(function () { return reload('Đã đăng xuất.'); }); });
      return el('div', { 'class': 'forum-auth', 'data-testid': 'auth' }, [
        el('p', {}, ['Đang đăng nhập: ', el('strong', { 'data-testid': 'user-name', text: state.user.name })]), out]);
    }
    var email = el('input', { type: 'email', required: '', autocomplete: 'email', 'data-testid': 'auth-email' });
    var pw = el('input', { type: 'password', required: '', minlength: '8', autocomplete: 'current-password', 'data-testid': 'auth-password' });
    var name = el('input', { maxlength: '60', autocomplete: 'nickname', 'data-testid': 'auth-name' });
    var mode = el('select', { 'data-testid': 'auth-mode' }, [el('option', { value: 'login', text: 'Đăng nhập' }), el('option', { value: 'register', text: 'Tạo tài khoản' })]);
    var f = el('form', { 'class': 'forum-form', 'data-testid': 'login-form' }, [
      el('h2', { text: 'Tài khoản CFP+ Forum' }), field('Chế độ', mode), field('Email', email),
      field('Mật khẩu (≥ 8 ký tự)', pw), field('Tên hiển thị (khi tạo tài khoản)', name),
      el('button', { type: 'submit', 'class': 'button primary', 'data-testid': 'auth-submit', text: 'Tiếp tục' })]);
    onSubmit(f, function () {
      var reg = mode.value === 'register';
      return api('POST', reg ? '/auth/register' : '/auth/login',
        reg ? { email: email.value, password: pw.value, name: name.value } : { email: email.value, password: pw.value })
        .then(function () { return reload(reg ? 'Đã tạo tài khoản và đăng nhập.' : 'Đăng nhập thành công.'); });
    });
    return f;
  }

  function memberBlock() {
    if (!state.user) return el('p', { 'class': 'section-copy', 'data-testid': 'login-hint', text: 'Đăng nhập để tham gia diễn đàn.' });
    var m = state.forum.membership;
    if (m && m.status === 'active') return el('p', { 'class': 'forum-meta', 'data-testid': 'member-status', text: 'Thành viên • ' + m.role });
    if (m && m.status === 'pending') return el('p', { 'class': 'forum-msg', 'data-testid': 'member-status', text: 'Yêu cầu tham gia đang chờ quản trị viên duyệt.' });
    var b = el('button', { type: 'button', 'class': 'button primary', 'data-testid': 'join', text: state.forum.join_policy === 'open' ? 'Tham gia diễn đàn' : 'Gửi yêu cầu tham gia' });
    b.addEventListener('click', function () {
      api('POST', '/forums/' + KEY + '/join').then(function (r) {
        return reload(r.status === 'active' ? 'Đã tham gia diễn đàn.' : 'Đã gửi yêu cầu, chờ duyệt.');
      }).catch(function (e) { flash(e.message, true); });
    });
    return b;
  }

  function isActive() { var m = state.forum && state.forum.membership; return !!(m && m.status === 'active'); }

  function composer() {
    if (!isActive()) return null;
    var t = el('input', { required: '', maxlength: '200', 'data-testid': 'post-title' });
    var b = el('textarea', { required: '', rows: '5', maxlength: '10000', 'data-testid': 'post-body' });
    var kids = [el('h2', { text: 'Đăng bài mới' }), field('Tiêu đề', t), field('Nội dung', b)];
    var h = null, cid = null;
    if (state.forum.post_fields.indexOf('hstdn') >= 0) {
      h = el('input', { required: '', maxlength: '200', 'data-testid': 'post-hstdn' });
      cid = el('input', { inputmode: 'numeric', pattern: '[0-9]*', maxlength: '32', 'data-testid': 'post-country' });
      kids.push(field('HSTDN (bắt buộc)', h), field('ID số Quốc Gia theo Registry (tuỳ chọn)', cid));
    }
    kids.push(el('button', { type: 'submit', 'class': 'button primary', 'data-testid': 'post-submit', text: 'Đăng bài' }));
    var f = el('form', { 'class': 'forum-form', 'data-testid': 'post-form' }, kids);
    onSubmit(f, function () {
      var body = { title: t.value, body: b.value };
      if (h) { body.hstdn = h.value; if (cid.value) body.country_id = cid.value; }
      return api('POST', '/forums/' + KEY + '/posts', body).then(function () { return reload('Đã đăng bài.'); });
    });
    return f;
  }

  function postView(p) {
    var tags = [];
    if (p.hstdn) tags.push(el('span', { 'class': 'forum-tag', 'data-testid': 'post-hstdn-view', text: 'HSTDN: ' + p.hstdn }));
    if (p.country_id) tags.push(el('span', { 'class': 'forum-tag', text: 'ID ' + p.country_id }));
    var form = null;
    if (isActive()) {
      var ta = el('textarea', { required: '', rows: '2', maxlength: '5000', 'aria-label': 'Bình luận', 'data-testid': 'comment-input' });
      form = el('form', { 'class': 'forum-form compact', 'data-testid': 'comment-form' }, [ta,
        el('button', { type: 'submit', 'class': 'button secondary', 'data-testid': 'comment-submit', text: 'Bình luận' })]);
      onSubmit(form, function () {
        return api('POST', '/forums/' + KEY + '/posts/' + p.id + '/comments', { body: ta.value }).then(function () { return reload('Đã bình luận.'); });
      });
    }
    return el('article', { 'class': 'chapter-card forum-post', 'data-testid': 'post', 'data-post-id': String(p.id) }, [
      el('h3', { 'data-testid': 'post-title-view', text: p.title }),
      el('p', { 'class': 'forum-meta', text: p.author.name + ' • ' + fmt(p.created_at) }),
      tags.length ? el('p', {}, tags) : null,
      el('p', { 'class': 'forum-body', 'data-testid': 'post-body-view', text: p.body }),
      el('h4', { text: 'Bình luận (' + p.comments.length + ')' }),
      el('ol', { 'class': 'forum-comments', 'data-testid': 'comments' }, p.comments.map(function (c) {
        return el('li', { 'data-testid': 'comment' }, [
          el('p', { 'class': 'forum-meta', text: c.author.name + ' • ' + fmt(c.created_at) }),
          el('p', { 'class': 'forum-body', 'data-testid': 'comment-body', text: c.body })]);
      })), form]);
  }

  function render() {
    var list;
    if (state.readError) list = el('p', { 'class': 'forum-msg error', 'data-testid': 'read-denied', text: state.readError });
    else if (!state.posts.length) list = el('p', { 'class': 'section-copy', 'data-testid': 'empty', text: 'Chưa có bài viết.' });
    var kids = [authBlock(), msg, state.forum ? memberBlock() : null, state.forum ? composer() : null,
      el('section', { 'class': 'section forum-list', 'data-testid': 'post-list' },
        [el('h2', { text: 'Bài viết (' + state.posts.length + ')' })].concat(list ? [list] : state.posts.map(postView)))];
    root.replaceChildren.apply(root, kids.filter(Boolean));
    root.setAttribute('data-ready', '1');
  }

  reload();
})();
