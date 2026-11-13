/* CFP+ Diễn Đàn + Văn Phòng cho Canva (Canva Code / trang Canva / iframe). SANDBOX.
 * - Chỉ gọi API PR #195. Không có khóa bí mật trong mã: đăng nhập bằng email/mật khẩu của chính người dùng.
 * - Khác nguồn (nhúng): token Bearer giữ trong bộ nhớ trang (sessionStorage nếu trình duyệt cho phép),
 *   credentials: "omit". Cùng nguồn (/canva/ trên backend): dùng cookie phiên như trang gốc.
 * - Mọi nội dung người dùng hiển thị bằng textContent (không chèn HTML thô).
 * - Mọi quyền được kiểm ở máy chủ; nút chỉ là gợi ý giao diện.
 */
(function () {
  "use strict";
  var DEFAULT_BASE = "https://cfp-forum-office-sandbox-p0.onrender.com";
  var FORUM = "sieu-bo-doi";
  var S = { base: "", token: null, user: null };

  function store(k, v) { try { if (v === undefined) return window.sessionStorage.getItem(k); if (v === null) window.sessionStorage.removeItem(k); else window.sessionStorage.setItem(k, v); } catch (e) { return null; } return null; }
  function $(id) { return document.getElementById(id); }
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === "text") n.textContent = attrs[k]; else if (k === "class") n.className = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  // Văn bản người dùng: **đậm** → <strong> (tạo node, không chèn HTML thô); bỏ dòng đánh dấu kỹ thuật <!-- … -->.
  function rich(text) {
    var box = el("div", { class: "msg" });
    String(text || "").split("\n").filter(function (ln) { return !/^\s*<!--.*-->\s*$/.test(ln); }).forEach(function (ln, i) {
      if (i) box.appendChild(document.createElement("br"));
      ln.split(/\*\*(.+?)\*\*/).forEach(function (part, j) {
        if (!part) return;
        box.appendChild(j % 2 ? el("strong", { text: part }) : document.createTextNode(part.replace(/^_(.*)_$/, "$1")));
      });
    });
    return box;
  }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); return n; }
  var toastTimer;
  function toast(msg, bad) { var t = $("toast"); t.textContent = msg; t.style.display = "block"; t.style.background = bad ? "var(--bad)" : ""; clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.style.display = "none"; }, 4500); }
  function sameOrigin() { try { return new URL(S.base).origin === window.location.origin; } catch (e) { return false; } }
  function fmt(iso) { try { return new Date(iso).toLocaleString("vi-VN"); } catch (e) { return iso || ""; } }

  function api(method, path, body) {
    var h = { "Accept": "application/json" };
    if (method !== "GET") { h["X-CFP-Forum"] = "1"; h["Content-Type"] = "application/json"; }
    if (S.token) h["Authorization"] = "Bearer " + S.token;
    if (/^\/api\/auth\/(login|register)$/.test(path)) h["X-CFP-Token"] = "1";
    return fetch(S.base + path, { method: method, headers: h, body: body === undefined ? undefined : JSON.stringify(body),
                                  credentials: sameOrigin() ? "same-origin" : "omit", mode: "cors" })
      .then(function (r) {
        return r.text().then(function (t) {
          var j = null; try { j = t ? JSON.parse(t) : null; } catch (e) { j = { detail: t.slice(0, 200) }; }
          if (!r.ok) { var e = new Error((j && j.detail) ? (typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail)) : ("HTTP " + r.status)); e.status = r.status; throw e; }
          return j;
        });
      });
  }
  function fail(e) { toast((e.status ? "Lỗi " + e.status + ": " : "Không kết nối được: ") + e.message, true); if (e.status === 401) setUser(null); }

  // ------------------------------------------------------------- tài khoản
  function setUser(u, token) {
    S.user = u;
    if (token !== undefined) { S.token = token; store("cfp.token", token); }
    if (!u) { S.token = null; store("cfp.token", null); }
    $("who").textContent = u ? ("Đang đăng nhập: " + u.name + " (#" + u.id + ")") : "Chưa đăng nhập • mở mục Tài khoản";
  }
  function auth(kind) {
    var body = { email: $("u-email").value.trim(), password: $("u-pass").value };
    if (kind === "register") body.name = $("u-name").value.trim() || body.email.split("@")[0];
    api("POST", "/api/auth/" + kind, body).then(function (u) {
      setUser({ id: u.id, name: u.name, email: u.email }, u.token || null);
      $("u-pass").value = "";
      return ensureMember();
    }).then(function () { toast("Đã đăng nhập."); show("forum"); }).catch(fail);
  }
  function logout() { api("POST", "/api/auth/logout").catch(function () { return null; }).then(function () { setUser(null); toast("Đã đăng xuất."); }); }
  function refreshMe() { return api("GET", "/api/auth/me").then(function (r) { setUser(r.user || null); }).catch(function () { setUser(null); }); }

  // ------------------------------------------------------------- chẩn đoán kết nối (ghi đúng lỗi)
  function diag() {
    var out = [];
    out.push("Trang: " + window.location.origin + (window.self !== window.top ? " (trong iframe)" : ""));
    out.push("Backend: " + S.base);
    var st = "không"; try { window.sessionStorage.setItem("cfp.t", "1"); window.sessionStorage.removeItem("cfp.t"); st = "có"; } catch (e) { st = "bị chặn (" + e.name + ")"; }
    out.push("sessionStorage: " + st);
    $("diag").textContent = out.join("\n") + "\nĐang gọi /api/health …";
    var t0 = Date.now();
    return api("GET", "/api/health").then(function (h) {
      out.push("Kết nối: OK " + (Date.now() - t0) + " ms • build " + (h.build || "?").slice(0, 7));
      out.push("Lưu trữ: " + h.storage);
      $("diag").textContent = out.join("\n");
    }).catch(function (e) {
      out.push("Kết nối: LỖI • " + e.name + ": " + e.message);
      out.push(e.status ? "Máy chủ trả lời nhưng từ chối." : "Trình duyệt chặn trước khi có phản hồi: CSP connect-src của Canva, CORS (nguồn này chưa có trong CFP_EMBED_ORIGINS) hoặc mạng.");
      $("diag").textContent = out.join("\n");
    });
  }

  // ------------------------------------------------------------- Diễn Đàn
  function loadPosts() {
    return api("GET", "/api/forums/" + FORUM + "/posts").then(function (r) {
      var box = clear($("posts"));
      if (!r.posts.length) box.appendChild(el("p", { class: "meta", text: "Chưa có bài viết." }));
      r.posts.slice().reverse().forEach(function (p) {
        var comments = el("div");
        (p.comments || []).forEach(function (c) {
          comments.appendChild(el("div", { class: "comment" }, [rich(c.body),
            el("div", { class: "meta", text: c.author.name + " • " + fmt(c.created_at) })]));
        });
        var ta = el("textarea", { maxlength: "5000", "aria-label": "Phản hồi bài " + p.id });
        var btn = el("button", { text: "Phản hồi" });
        btn.addEventListener("click", function () {
          if (!ta.value.trim()) return;
          btn.disabled = true;
          api("POST", "/api/forums/" + FORUM + "/posts/" + p.id + "/comments", { body: ta.value.trim() })
            .then(function () { toast("Đã gửi phản hồi."); return loadPosts(); }).catch(fail).then(function () { btn.disabled = false; });
        });
        box.appendChild(el("article", { class: "card", id: "post-" + p.id }, [
          el("h3", { text: p.title }), el("div", { class: "meta", text: p.author.name + " • " + fmt(p.created_at) + " • #" + p.id }),
          rich(p.body), comments, ta, el("div", { class: "row" }, [btn])]));
      });
    }).catch(fail);
  }
  function ensureMember() {  // tham gia Diễn Đàn Siêu Bộ Đôi (mở) một lần, chỉ khi chưa là thành viên
    return api("GET", "/api/forums/" + FORUM).then(function (f) {
      return f.membership ? f.membership : api("POST", "/api/forums/" + FORUM + "/join");
    });
  }
  function sendPost(title, body) {
    return ensureMember().then(function () { return api("POST", "/api/forums/" + FORUM + "/posts", { title: title, body: body }); });
  }

  // ------------------------------------------------------------- Nhiệm vụ (Văn Phòng #195)
  var STATUS_VI = { QUEUED: "Chờ nhận", ACKED: "Đã nhận", IN_PROGRESS: "Đang làm", IN_REVIEW: "Chờ review",
                    CHANGES_REQUESTED: "Cần sửa", ACCEPTED: "Đạt (chờ đóng)", CLOSED: "Đã đóng" };
  function loadBoard() {
    return api("GET", "/api/office/board").then(function (b) {
      var c = b.counts || {};
      $("board-counts").textContent = "Chờ: " + (c.QUEUED || 0) + " • Đang chạy: " + (c.RUNNING || 0) + " • Chờ review: " + (c.IN_REVIEW || 0) +
        " • Đã review: " + (c.REVIEWED || 0) + " • Bị chặn: " + (c.BLOCKED || 0) + (b.viewer === "guest" ? " (khách: đăng nhập để xem nhiệm vụ của bạn)" : "");
      var box = clear($("board"));
      if (!b.tasks.length) box.appendChild(el("p", { class: "meta", text: "Không có nhiệm vụ bạn được xem." }));
      b.tasks.forEach(function (t) {
        var btn = el("button", { text: "Mở" });
        btn.addEventListener("click", function () { openTask(t.id); });
        box.appendChild(el("div", { class: "card", id: "task-" + t.id }, [
          el("h3", { text: t.title }),
          el("div", { class: "meta" }, [el("span", { class: "chip", text: STATUS_VI[t.status] || t.status }),
            " Văn Phòng " + t.office_id + " • Evidence: " + t.evidence + (t.reason ? " • " + t.reason : "")]),
          el("div", { class: "row" }, [btn])]));
      });
    }).catch(fail);
  }
  function openTask(id) {
    return api("GET", "/api/office/tasks/" + id + "/loop").then(function (lp) {
      var box = clear($("task-detail"));
      var me = S.user ? S.user.id : -1;
      var list = el("ul", { class: "stages" });
      lp.stages.forEach(function (s) { list.appendChild(el("li", { class: s.done ? "s-ok" : "meta", text: (s.done ? "✓ " : "○ ") + s.label })); });
      var acts = el("div", { class: "row" });
      function act(label, path, body, primary) {
        var b = el("button", { text: label, class: primary ? "primary" : "" });
        b.addEventListener("click", function () { b.disabled = true; api("POST", "/api/office/tasks/" + id + "/" + path, typeof body === "function" ? body() : body)
          .then(function () { toast("Đã cập nhật."); return Promise.all([openTask(id), loadBoard()]); }).catch(fail).then(function () { b.disabled = false; }); });
        acts.appendChild(b);
      }
      var extra = el("div");
      if (me === lp.owner_id) {
        if (lp.status === "QUEUED") act("Nhận việc (ACK)", "ack", { note: "ACK từ Canva" }, true);
        if (lp.status === "ACKED" || lp.status === "CHANGES_REQUESTED") act("Bắt đầu", "start", {}, true);
        if (lp.status === "IN_PROGRESS") {
          var url = el("input", { inputmode: "url", placeholder: "https://… (bằng chứng)", "aria-label": "URL Evidence" });
          var desc = el("input", { placeholder: "Mô tả bằng chứng", "aria-label": "Mô tả Evidence" });
          var eb = el("button", { text: "Nộp Evidence" });
          eb.addEventListener("click", function () {
            api("POST", "/api/office/tasks/" + id + "/evidence", { kind: "url", url: url.value.trim(), description: desc.value.trim() })
              .then(function () { toast("Đã nộp Evidence."); return openTask(id); }).catch(fail);
          });
          extra.appendChild(el("div", { class: "card" }, [el("label", { text: "Evidence" }), url, desc, el("div", { class: "row" }, [eb])]));
          act("Gửi review", "submit", { note: "Gửi từ Canva" }, true);
        }
      }
      if (me === lp.reviewer_id && lp.status === "IN_REVIEW") {
        var notes = el("textarea", { placeholder: "Nhận xét review (bắt buộc)", "aria-label": "Nhận xét review" });
        extra.appendChild(el("div", { class: "card" }, [el("label", { text: "Review độc lập" }), notes]));
        act("Đạt (ACCEPT)", "review", function () { return { decision: "ACCEPT", notes: notes.value.trim() }; }, true);
        act("Yêu cầu sửa", "review", function () { return { decision: "CHANGES_REQUESTED", notes: notes.value.trim() }; });
      }
      var role = me === lp.owner_id ? "Bạn là người thực thi" : (me === lp.reviewer_id ? "Bạn là reviewer" : "Bạn đang xem");
      box.appendChild(el("div", { class: "card" }, [el("h3", { text: "Nhiệm vụ #" + id + " • " + (STATUS_VI[lp.status] || lp.status) }),
        el("div", { class: "meta", text: role + " • người thực thi #" + lp.owner_id + " • reviewer #" + lp.reviewer_id }), list, extra, acts]));
      box.scrollIntoView({ behavior: "smooth" });
    }).catch(fail);
  }

  // ------------------------------------------------------------- Giao việc (theo mẫu HUB 69, bộ điều phối đọc)
  function assign() {
    var title = $("a-title").value.trim();
    if (title.length < 3) { toast("Nhập tên nhiệm vụ (≥ 3 ký tự).", true); return; }
    var body = ["**SI AI / Siêu Bộ Đôi:** " + (S.user ? S.user.name : "Thành viên"),
      "**Nhiệm vụ:** " + title, "**Năng lực:** " + $("a-cap").value, "**Assignee:** auto", "**Reviewer:** auto",
      "**Priority:** " + $("a-pri").value, "**Tiêu chí nghiệm thu:** " + ($("a-acc").value.trim() || "Evidence + review độc lập"),
      "**Trạng thái:** OPEN"].join("\n");
    sendPost("[NHIỆM VỤ] " + title, body).then(function () { toast("Đã đăng nhiệm vụ. Bộ điều phối sẽ nhận ở lượt chạy kế tiếp."); $("a-title").value = ""; show("forum"); }).catch(fail);
  }

  // ------------------------------------------------------------- điều hướng
  function show(tab) {
    ["forum", "tasks", "assign", "account"].forEach(function (t) {
      $("tab-" + t).classList.toggle("hidden", t !== tab);
      document.querySelector('nav [data-tab="' + t + '"]').setAttribute("aria-pressed", String(t === tab));
    });
    if (tab === "forum") loadPosts();
    if (tab === "tasks") loadBoard();
    if (tab === "account") diag();
  }

  function init() {
    var qs = new URLSearchParams(window.location.search);
    var cfg = qs.get("api") || store("cfp.base") || window.CFP_CANVA_BASE;
    S.base = (cfg || (window.location.pathname.indexOf("/canva/") === 0 ? window.location.origin : DEFAULT_BASE)).replace(/\/+$/, "");
    S.token = store("cfp.token");
    $("cfg-base").value = S.base;
    document.querySelectorAll("nav [data-tab]").forEach(function (b) { b.addEventListener("click", function () { show(b.getAttribute("data-tab")); }); });
    $("u-login").addEventListener("click", function () { auth("login"); });
    $("u-register").addEventListener("click", function () { auth("register"); });
    $("u-logout").addEventListener("click", logout);
    $("cfg-save").addEventListener("click", function () { S.base = $("cfg-base").value.trim().replace(/\/+$/, ""); store("cfp.base", S.base); diag(); });
    $("p-send").addEventListener("click", function () {
      var t = $("p-title").value.trim(), b = $("p-body").value.trim();
      if (!t || !b) { toast("Nhập tiêu đề và nội dung.", true); return; }
      sendPost(t, b).then(function () { $("p-title").value = ""; $("p-body").value = ""; toast("Đã đăng."); return loadPosts(); }).catch(fail);
    });
    $("f-reload").addEventListener("click", loadPosts);
    $("t-reload").addEventListener("click", loadBoard);
    $("a-send").addEventListener("click", assign);
    refreshMe().then(function () { show(S.user ? "forum" : "account"); if (!S.user) loadPosts(); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
