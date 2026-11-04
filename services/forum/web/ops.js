/* CFP+ Bảng điều phối • P0 — chỉ đọc qua API thật; nội dung luôn hiển thị dạng text. */
(function () {
  'use strict';
  var root = document.querySelector('[data-ops-root]');
  if (!root) return;
  function get(path) {
    return fetch(path, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
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
  function badge(state, testid) { return el('strong', { 'data-testid': testid, 'data-state': state, text: state }); }
  function fail(e) { return el('p', { role: 'alert', text: 'Không tải được: ' + e.message }); }

  var LABEL = { RUNNING: 'RUNNING • đang làm', IN_REVIEW: 'IN REVIEW • chờ review độc lập', BLOCKED: 'BLOCKED • bị chặn',
                REVIEWED: 'REVIEWED • đã review (có Evidence)', QUEUED: 'QUEUED • đã giao, chưa ACK' };

  Promise.all([
    get('/api/health').catch(function (e) { return { _err: e }; }),
    get('/api/worker/status').catch(function (e) { return { _err: e }; }),
    get('/api/office/board').catch(function (e) { return { _err: e }; }),
    get('/api/auth/me').catch(function () { return { user: null }; })
  ]).then(function (res) {
    var h = res[0], w = res[1], b = res[2], me = res[3].user;
    root.textContent = '';
    root.appendChild(el('p', { 'data-testid': 'ops-viewer', text: me ? ('Đang xem với quyền: ' + me.name + ' (' + (b.viewer || '—') + ')') : 'Khách: chỉ thấy trạng thái dịch vụ. Đăng nhập ở Diễn Đàn/Văn Phòng để xem nhiệm vụ của bạn.' }));

    // ONLINE: chỉ khi /api/health trả về ok từ chính server này
    var svc = [];
    if (h._err) svc.push(el('li', {}, [badge('OFFLINE', 'svc-state'), ' API: ' + h._err.message]));
    else {
      svc.push(el('li', {}, [badge(h.status === 'ok' ? 'ONLINE' : 'DEGRADED', 'svc-state'), ' API • build ' + (h.build || 'local')]));
      if (h.storage && h.storage !== 'configured') svc.push(el('li', { 'data-testid': 'svc-storage' }, [badge('EPHEMERAL', 'svc-storage-state'), ' ' + h.storage]));
      Object.keys(h.forums || {}).forEach(function (k) { svc.push(el('li', {}, [badge('ONLINE', 'svc-forum'), ' Diễn Đàn ' + k + ' • ' + h.forums[k].db])); });
      svc.push(el('li', {}, [badge(h.office ? 'ONLINE' : 'NOT CONFIGURED', 'svc-office'), ' Văn Phòng SI AI' + (h.office ? ' • ' + h.office.db : '')]));
      svc.push(el('li', {}, [badge('READ-ONLY', 'svc-registry'), ' Registry • ' + h.registry.entities + ' thực thể']));
    }
    root.appendChild(section('ONLINE • Dịch vụ', 'ops-online', [el('ul', {}, svc)]));

    // SCHEDULED: chỉ dựa trên heartbeat + lần chạy xong thật trong cfp_worker
    var sch = [];
    if (w._err) sch.push(el('p', { role: 'alert', text: 'Worker: ' + w._err.message }));
    else if (!w.configured) sch.push(el('p', {}, [badge('NOT RUNNING', 'worker-state'), ' ' + w.note]));
    else {
      sch.push(el('p', {}, [badge(w.paused ? 'PAUSED' : (w.alive ? 'ALIVE' : 'STALE'), 'worker-state'),
        ' heartbeat: ' + (w.heartbeats.length ? w.heartbeats[0].age_seconds + ' giây trước' : 'chưa có') + ' • cảnh báo 24h: ' + w.alerts_24h]));
      sch.push(el('ul', {}, (w.schedule || []).map(function (s) {
        return el('li', { 'data-testid': 'sched-item' }, [badge(s.overdue ? 'OVERDUE' : 'SCHEDULED', 'sched-state'),
          ' ' + s.kind + ' • mỗi ' + s.every_seconds + ' giây • lần xong gần nhất: ' + (s.last_done_at || 'chưa có')]);
      })));
      sch.push(el('p', { text: w.note }));
    }
    root.appendChild(section('SCHEDULED • Việc định kỳ (worker)', 'ops-scheduled', sch));

    if (b._err) { root.appendChild(fail(b._err)); return; }
    ['RUNNING', 'IN_REVIEW', 'BLOCKED', 'REVIEWED', 'QUEUED'].forEach(function (k) {
      var items = b.tasks.filter(function (t) { return t.bucket === k; });
      root.appendChild(section(LABEL[k] + ' (' + b.counts[k] + ')', 'ops-' + k.toLowerCase(), [
        items.length ? el('ul', {}, items.map(function (t) {
          return el('li', { 'data-testid': 'ops-task', 'data-task': String(t.id) }, [
            el('a', { href: t.url, text: '#' + t.id + ' ' + t.title }),
            ' • ' + t.status + ' • Evidence: ' + t.evidence + (t.review ? ' • Review: ' + t.review.decision : '') + (t.reason ? ' • ' + t.reason : '')]);
        })) : el('p', { text: '—' })]));
    });
  });
})();
