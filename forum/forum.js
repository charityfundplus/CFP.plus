/*
 * CFP+ Forum Engine • P0
 *
 * Một engine dùng chung cho nhiều diễn đàn; mỗi diễn đàn có namespace lưu trữ
 * riêng (cfp.forum.v1.<forumKey>) nên dữ liệu không bao giờ trộn lẫn.
 *
 * P0: lưu trữ trong localStorage của trình duyệt (site hiện là nginx tĩnh,
 * chưa có backend). Lớp `LocalStore` có thể thay bằng adapter API sau này mà
 * không đổi giao diện.
 */
(function (global) {
  'use strict';

  var SESSION_KEY = 'cfp.forum.v1.session';
  var DATA_PREFIX = 'cfp.forum.v1.';

  function LocalStore(forumKey, storage) {
    if (!/^[a-z0-9-]+$/.test(forumKey)) throw new Error('forumKey không hợp lệ');
    this.key = DATA_PREFIX + forumKey;
    this.storage = storage || global.localStorage;
  }
  LocalStore.prototype.load = function () {
    try {
      var raw = this.storage.getItem(this.key);
      var data = raw ? JSON.parse(raw) : null;
      if (data && Array.isArray(data.posts)) return data;
    } catch (e) { /* dữ liệu hỏng → không ghi đè, chỉ trả rỗng */ }
    return { version: 1, posts: [] };
  };
  LocalStore.prototype.save = function (data) {
    this.storage.setItem(this.key, JSON.stringify(data));
  };

  function uid() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }

  function clean(s, max) {
    return String(s == null ? '' : s).replace(/\r\n/g, '\n').trim().slice(0, max);
  }

  function Forum(forumKey, opts) {
    opts = opts || {};
    this.forumKey = forumKey;
    this.storage = opts.storage || global.localStorage;
    this.store = opts.store || new LocalStore(forumKey, this.storage);
  }

  Forum.prototype.currentUser = function () {
    try {
      var u = JSON.parse(this.storage.getItem(SESSION_KEY) || 'null');
      return u && u.name ? u : null;
    } catch (e) { return null; }
  };

  Forum.prototype.login = function (name, email) {
    name = clean(name, 60);
    email = clean(email, 120).toLowerCase();
    if (name.length < 2) throw new Error('Tên hiển thị cần ít nhất 2 ký tự.');
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error('Email không hợp lệ.');
    var user = { id: email || ('u-' + uid()), name: name, email: email, at: new Date().toISOString() };
    this.storage.setItem(SESSION_KEY, JSON.stringify(user));
    return user;
  };

  Forum.prototype.logout = function () { this.storage.removeItem(SESSION_KEY); };

  Forum.prototype.requireUser = function () {
    var u = this.currentUser();
    if (!u) throw new Error('Vui lòng đăng nhập trước.');
    return u;
  };

  Forum.prototype.listPosts = function () {
    return this.store.load().posts.slice().sort(function (a, b) {
      return a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0;
    });
  };

  Forum.prototype.createPost = function (title, body) {
    var u = this.requireUser();
    title = clean(title, 200);
    body = clean(body, 10000);
    if (!title) throw new Error('Tiêu đề không được để trống.');
    if (!body) throw new Error('Nội dung không được để trống.');
    var data = this.store.load();
    var post = {
      id: uid(), forum: this.forumKey, title: title, body: body,
      author: { id: u.id, name: u.name }, createdAt: new Date().toISOString(), comments: []
    };
    data.posts.push(post);
    this.store.save(data);
    return post;
  };

  Forum.prototype.addComment = function (postId, body) {
    var u = this.requireUser();
    body = clean(body, 5000);
    if (!body) throw new Error('Bình luận không được để trống.');
    var data = this.store.load();
    var post = data.posts.filter(function (p) { return p.id === postId; })[0];
    if (!post) throw new Error('Không tìm thấy bài viết.');
    var c = { id: uid(), body: body, author: { id: u.id, name: u.name }, createdAt: new Date().toISOString() };
    post.comments.push(c);
    this.store.save(data);
    return c;
  };

  /* ---------- UI ---------- */

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'text') n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }

  function fmt(iso) {
    try { return new Date(iso).toLocaleString('vi-VN'); } catch (e) { return iso; }
  }

  function mount(root, forum) {
    var msg = el('p', { 'class': 'forum-msg', role: 'status', 'aria-live': 'polite', 'data-testid': 'msg' });

    function flash(text, isErr) {
      msg.textContent = text;
      msg.className = 'forum-msg' + (isErr ? ' error' : '');
    }
    function guard(fn) {
      return function (ev) {
        if (ev) ev.preventDefault();
        try { fn(ev); } catch (e) { flash(e.message, true); }
      };
    }

    function renderAuth() {
      var u = forum.currentUser();
      if (u) {
        var out = el('button', { type: 'button', 'class': 'button secondary', 'data-testid': 'logout', text: 'Đăng xuất' });
        out.addEventListener('click', guard(function () { forum.logout(); flash('Đã đăng xuất.'); render(); }));
        return el('div', { 'class': 'forum-auth', 'data-testid': 'auth' }, [
          el('p', {}, [document.createTextNode('Đang đăng nhập: '), el('strong', { 'data-testid': 'user-name', text: u.name })]), out
        ]);
      }
      var name = el('input', { name: 'name', required: '', minlength: '2', maxlength: '60', autocomplete: 'nickname', 'data-testid': 'login-name' });
      var email = el('input', { name: 'email', type: 'email', maxlength: '120', autocomplete: 'email', 'data-testid': 'login-email' });
      var f = el('form', { 'class': 'forum-form', 'data-testid': 'login-form' }, [
        el('h2', { text: 'Đăng nhập' }),
        el('label', {}, [document.createTextNode('Tên hiển thị'), name]),
        el('label', {}, [document.createTextNode('Email (tuỳ chọn)'), email]),
        el('button', { type: 'submit', 'class': 'button primary', 'data-testid': 'login-submit', text: 'Đăng nhập' })
      ]);
      f.addEventListener('submit', guard(function () { forum.login(name.value, email.value); flash('Đăng nhập thành công.'); render(); }));
      return f;
    }

    function renderComposer() {
      if (!forum.currentUser()) return el('p', { 'class': 'section-copy', 'data-testid': 'login-hint', text: 'Đăng nhập để đăng bài và bình luận.' });
      var t = el('input', { name: 'title', required: '', maxlength: '200', 'data-testid': 'post-title' });
      var b = el('textarea', { name: 'body', required: '', rows: '5', maxlength: '10000', 'data-testid': 'post-body' });
      var f = el('form', { 'class': 'forum-form', 'data-testid': 'post-form' }, [
        el('h2', { text: 'Đăng bài mới' }),
        el('label', {}, [document.createTextNode('Tiêu đề'), t]),
        el('label', {}, [document.createTextNode('Nội dung'), b]),
        el('button', { type: 'submit', 'class': 'button primary', 'data-testid': 'post-submit', text: 'Đăng bài' })
      ]);
      f.addEventListener('submit', guard(function () { forum.createPost(t.value, b.value); flash('Đã đăng bài.'); render(); }));
      return f;
    }

    function renderPost(p) {
      var list = el('ol', { 'class': 'forum-comments', 'data-testid': 'comments' }, p.comments.map(function (c) {
        return el('li', { 'data-testid': 'comment' }, [
          el('p', { 'class': 'forum-meta', text: c.author.name + ' • ' + fmt(c.createdAt) }),
          el('p', { 'class': 'forum-body', 'data-testid': 'comment-body', text: c.body })
        ]);
      }));
      var form = null;
      if (forum.currentUser()) {
        var ta = el('textarea', { name: 'comment', required: '', rows: '2', maxlength: '5000', 'aria-label': 'Bình luận', 'data-testid': 'comment-input' });
        form = el('form', { 'class': 'forum-form compact', 'data-testid': 'comment-form' }, [
          ta, el('button', { type: 'submit', 'class': 'button secondary', 'data-testid': 'comment-submit', text: 'Bình luận' })
        ]);
        form.addEventListener('submit', guard(function () { forum.addComment(p.id, ta.value); flash('Đã bình luận.'); render(); }));
      }
      return el('article', { 'class': 'chapter-card forum-post', 'data-testid': 'post', 'data-post-id': p.id }, [
        el('h3', { 'data-testid': 'post-title-view', text: p.title }),
        el('p', { 'class': 'forum-meta', text: p.author.name + ' • ' + fmt(p.createdAt) }),
        el('p', { 'class': 'forum-body', 'data-testid': 'post-body-view', text: p.body }),
        el('h4', { text: 'Bình luận (' + p.comments.length + ')' }),
        list, form
      ]);
    }

    function render() {
      var posts = forum.listPosts();
      root.replaceChildren(
        renderAuth(), msg, renderComposer(),
        el('section', { 'class': 'section forum-list', 'data-testid': 'post-list' }, [
          el('h2', { text: 'Bài viết (' + posts.length + ')' })
        ].concat(posts.length ? posts.map(renderPost) : [el('p', { 'class': 'section-copy', 'data-testid': 'empty', text: 'Chưa có bài viết.' })]))
      );
    }

    render();
    return { render: render };
  }

  global.CFPForum = { Forum: Forum, LocalStore: LocalStore, mount: mount, SESSION_KEY: SESSION_KEY, DATA_PREFIX: DATA_PREFIX };

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function () {
      var root = document.querySelector('[data-forum]');
      if (root) mount(root, new Forum(root.getAttribute('data-forum')));
    });
  }
})(typeof window !== 'undefined' ? window : globalThis);
