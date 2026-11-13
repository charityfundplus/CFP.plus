/* CFP+ Văn Phòng Agent (sandbox) • dữ liệu từ API; mọi nội dung hiển thị dạng text. Không gửi trả lời cho khách. */
(function () {
  'use strict';
  var root = document.querySelector('[data-agent-root]');
  if (!root) return;
  var slug = (location.pathname.match(/\/_internal\/agent\/([a-z0-9-]+)\//) || [])[1] || 'meta-business-agent';
  var H = { Accept: 'application/json', 'Content-Type': 'application/json', 'X-CFP-Forum': '1' };
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function api(method, p, body) {
    return fetch(p, { method: method, headers: H, credentials: 'same-origin', body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error((j.detail || 'Lỗi') + ' (' + r.status + ')'); return j; }); });
  }
  function section(title, kids, tid) { return el('section', { class: 'section', 'data-testid': tid }, [el('h2', { text: title })].concat(kids)); }
  function render(a) {
    root.textContent = '';
    document.querySelector('[data-testid=agent-title]').textContent = 'Văn Phòng Siêu Bộ Đôi • ' + a.name;
    root.appendChild(section('Trạng thái', [
      el('p', { 'data-testid': 'agent-id-status', text: 'ID: ' + (a.canonical_id || 'chưa cấp') + ' • ' + a.id_status }),
      el('p', { text: 'Nhà phát triển: ' + a.developer + ' • tham chiếu ' + a.developer_ref + ' (' + (a.developer_ref_status || '?') + ')' }),
      el('p', { text: a.pair }),
      el('ol', { 'data-testid': 'agent-pipeline' }, a.pipeline.map(function (s) { return el('li', { text: s + (s === a.stage ? '  ← hiện tại' : '') }); })),
      el('p', { text: 'auto_reply=' + a.flags.auto_reply + ' • production=' + a.flags.production + ' • đã công bố: ' + (a.flags.published ? 'có' : 'chưa') + ' • kết nối API nhà phát triển: ' + (a.flags.meta_api_connected ? 'có' : 'chưa') }),
      el('small', { text: 'Cấu hình ' + a.config_source + ' • ' + a.config_version })
    ], 'agent-status'));
    var k = a.knowledge;
    root.appendChild(section('Kho tri thức (Knowledge) • ' + k.approved + ' nguồn duyệt • ' + k.verifying + ' đang xác minh • ' + k.excluded + ' loại', [
      el('p', { text: k.rule }),
      el('ul', { 'data-testid': 'agent-knowledge' }, k.sources.map(function (s) {
        var label = { approved_source: '✓ nguồn duyệt', verifying: '⚠️ đang xác minh (Parent HOLD)', excluded_hold: '⛔ loại (ID HOLD)', missing: '⛔ chưa xuất bản' }[s.status] || s.status;
        return el('li', {}, [s.url ? el('a', { href: s.url, rel: 'noopener', text: s.id + ' • ' + s.title }) : el('span', { text: s.id }), el('small', { text: '  ' + label + (s.version ? ' • ' + s.version : '') })]);
      }))
    ], 'agent-knowledge-section'));
    root.appendChild(section('Hướng dẫn Agent', [el('ul', {}, a.instructions.map(function (t) { return el('li', { text: t }); }))], 'agent-instructions'));
    var runOut = el('pre', { class: 'agent-out', 'data-testid': 'agent-run-out', text: 'Bộ kiểm thử hiện hành: ' + a.tests.passed + '/' + a.tests.total + ' PASS • sha ' + a.tests.sha });
    var runBtn = el('button', { type: 'button', 'data-testid': 'agent-run', text: 'Chạy bộ tình huống tư vấn (ghi audit)' });
    runBtn.addEventListener('click', function () {
      runOut.textContent = 'Đang chạy…';
      api('POST', '/api/office/agents/' + slug + '/test-runs').then(function (r) {
        runOut.textContent = r.passed + '/' + r.total + ' PASS • ' + r.failed + ' FAIL • sha ' + r.sha + '\nEvidence URL: ' + location.origin + '/api/office/agents/' + slug + '/test-runs/' + r.sha + '\n' +
          r.results.map(function (x) { return (x.pass ? '✓ ' : '✗ ') + x.name + ' → ' + x.got + ' [' + x.codes.join(', ') + ']'; }).join('\n');
      }).catch(function (e) { runOut.textContent = e.message + ' — cần đăng nhập.'; });
    });
    root.appendChild(section('Kiểm thử • Evidence', [runBtn, runOut, el('p', { text: a.human_review })], 'agent-tests'));
    var q = el('input', { id: 'agent-q', 'data-testid': 'agent-q', placeholder: 'Câu hỏi của khách (không nhập dữ liệu thật)' });
    var d = el('textarea', { id: 'agent-draft', 'data-testid': 'agent-draft', rows: '4', placeholder: 'Bản nháp trả lời của Agent' });
    var out = el('pre', { class: 'agent-out', 'data-testid': 'agent-check-out' });
    var btn = el('button', { type: 'button', 'data-testid': 'agent-check', text: 'Kiểm tra bản nháp (không gửi)' });
    btn.addEventListener('click', function () {
      out.textContent = 'Đang kiểm tra…';
      api('POST', '/api/office/answer-check', { draft: d.value, question: q.value || null, agent: a.name }).then(function (r) {
        out.textContent = 'Kết luận: ' + r.verdict + ' • auto_reply=' + r.auto_reply + '\n' + r.findings.map(function (f) { return '[' + f.level + '] ' + f.code + ' — ' + f.message; }).join('\n') +
          (r.citations.length ? '\nNguồn: ' + r.citations.map(function (c) { return c.url; }).join(' ') : '');
      }).catch(function (e) { out.textContent = e.message + ' — cần đăng nhập.'; });
    });
    root.appendChild(section('Giám sát câu trả lời (Human Review trước khi gửi)', [el('div', { class: 'agent-form' }, [
      el('label', { for: 'agent-q', text: 'Câu hỏi' }), q, el('label', { for: 'agent-draft', text: 'Bản nháp' }), d]), btn, out
    ], 'agent-check-section'));
  }
  api('GET', '/api/office/agents/' + slug).then(render).catch(function (e) { root.textContent = e.message; });
})();
