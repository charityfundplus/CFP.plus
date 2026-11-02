'use strict';
// This panel uses same-origin authenticated local APIs. Offline fixtures above
// remain separately labelled; a failed heartbeat never becomes an online claim.
(() => {
  const $ = selector => document.querySelector(selector);
  const groups = {V: [], '0': [0], '135': [1, 3, 5], '246': [2, 4, 6], '789': [7, 8, 9]};
  const chapterNames = ['Nền Tảng', 'Sự Sống', 'Con Người', 'Ba Quỹ', 'Tôn Giáo', 'Cộng Đồng', 'Siêu Trí Tuệ & Công Nghệ', 'Doanh Nghiệp / HSTDN', 'Tổ Chức', 'Quốc Gia'];
  let state = null;
  let ready = false;
  let busy = false;
  let lastBackup = '';
  const text = (tag, value, className) => {
    const node = document.createElement(tag);
    node.textContent = value;
    if (className) node.className = className;
    return node;
  };
  function controls() {
    const role = state?.user?.role;
    $('#ops-write button').disabled = busy || !ready || !['editor', 'admin'].includes(role);
    $('#ops-sync').disabled = busy || !ready || !['editor', 'admin'].includes(role);
    $('#ops-backup').disabled = busy || !ready || role !== 'admin';
    $('#ops-restore button').disabled = busy || !ready || role !== 'admin';
    $('#ops-logout').disabled = busy || !ready;
    $('#ops-login button').disabled = busy;
  }
  function connection(label, connected = false) {
    ready = connected;
    $('#ops-connection').textContent = label;
    $('#ops-connection').dataset.connected = String(connected);
    controls();
  }
  async function api(path, body) {
    let response;
    try {
      response = await fetch('/api/' + path, {
        method: body === undefined ? 'GET' : 'POST',
        credentials: 'same-origin', cache: 'no-store',
        headers: {'Content-Type': 'application/json'},
        ...(body === undefined ? {} : {body: JSON.stringify(body)})
      });
    } catch (error) {
      connection('MẤT KẾT NỐI · dữ liệu hiển thị có thể đã cũ; chưa xác nhận thao tác');
      throw new Error('Không liên lạc được API. Kết nối lại rồi tải trạng thái để xác minh.');
    }
    let value;
    try { value = await response.json(); }
    catch { connection('API KHÔNG KHẢ DỤNG · chưa xác minh kết nối'); throw new Error('Chưa có API vận hành tương thích.'); }
    if (response.status === 401) {
      state = null; ready = false; render();
      connection('CHƯA ĐĂNG NHẬP · cần tài khoản sandbox được cấp');
    }
    if (!response.ok) throw new Error(value.error || 'HTTP ' + response.status);
    return value;
  }
  function renderRows() {
    const query = $('#ops-search').value.trim().toLowerCase();
    const rows = (state?.records || []).filter(row => [row.key, row.title, row.content, row.chapter].join(' ').toLowerCase().includes(query));
    $('#ops-records').replaceChildren(...rows.map(row => {
      const card = text('article', '');
      card.append(text('h3', row.title), text('p', 'Mã vận hành: ' + row.key), text('p', 'Nhóm ' + row.group + ' · Chương ' + row.chapter + ' · phiên bản ' + row.version), text('p', row.content || ''), text('code', row.content_hash || ''));
      return card;
    }));
    $('#ops-count').textContent = state ? rows.length + ' bản ghi cục bộ · không phải dữ liệu SpaceX chính thức' : 'Chưa tải dữ liệu được xác thực';
  }
  function render() {
    $('#ops-account').textContent = state ? state.user.id + ' · ' + state.user.role + ' · workspace ' + state.user.workspace : 'Chưa có phiên xác thực';
    $('#ops-login').hidden = !!state;
    $('#ops-queue').textContent = state ? JSON.stringify(state.queue, null, 2) : 'Chưa tải hàng đợi';
    $('#ops-replica').textContent = state ? JSON.stringify(state.replica, null, 2) : 'Chưa kiểm tra kho đích';
    $('#ops-audit').textContent = state ? JSON.stringify(state.audit, null, 2) : 'Chưa tải audit';
    const pending = (state?.queue || []).filter(item => item.status === 'PENDING').length;
    const conflicts = (state?.queue || []).filter(item => item.status === 'CONFLICT').length;
    $('#ops-sync-summary').textContent = state ? pending + ' đang chờ · ' + conflicts + ' xung đột · phạm vi hai tệp SQLite cục bộ' : 'Chưa tải hàng đợi';
    $('#ops-integrity').textContent = !state ? 'Chưa kiểm tra toàn vẹn' : state.replica?.digest === state.digest && !pending && !conflicts ? 'Nguồn và đích cục bộ khớp digest · audit ' + (state.audit_valid ? 'hợp lệ' : 'chưa xác minh') : 'Nguồn và đích chưa khớp hoặc chưa truy cập được · cần kiểm tra hàng đợi';
    const connectors = state?.connectors || ['Notion', 'GitHub', 'Google Drive', 'Canva', 'Cloud', 'Supabase', 'HubSpot'].map(name => ({name, status: 'BLOCKED', reason: 'Chưa kiểm thử kết nối được cấp quyền'}));
    $('#ops-connectors').replaceChildren(...connectors.map(c => {
      const item = text('article', ''); item.append(text('h3', c.name), text('p', c.status, 'badge'), text('p', c.reason || '')); return item;
    }));
    renderRows(); controls();
  }
  async function refresh() {
    state = await api('state'); render();
    connection('API CỤC BỘ ĐÃ XÁC MINH · ' + new Date().toLocaleTimeString('vi-VN') + ' · không chứng minh kết nối kho ngoài', true);
  }
  async function action(fn) {
    if (busy) return;
    busy = true; controls();
    try { await fn(); }
    catch (error) { $('#ops-message').textContent = error.message; }
    finally { busy = false; controls(); }
  }
  const navigation = [];
  for (const group of ['V', '0', '135', '246', '789']) {
    const chapters = groups[group];
    const card = text('article', ''); card.append(text('h3', 'Nhóm ' + group));
    if (group === 'V') card.append(text('p', 'Cổng công khai · giữ nguyên định danh hiện hữu'));
    for (const chapter of chapters) {
      const a = text('a', 'Chương ' + chapter + ' · ' + chapterNames[chapter]);
      a.href = 'https://cfp.plus/' + chapter; card.append(a, document.createElement('br'));
    }
    navigation.push(card);
  }
  $('#ops-navigation').replaceChildren(...navigation);
  function selectChapter() {
    const selected = $('#ops-group').value;
    $('#ops-chapter').replaceChildren(...groups[selected].map(chapter => {
      const option = text('option', 'Chương ' + chapter); option.value = chapter; return option;
    }));
  }
  $('#ops-group').onchange = selectChapter;
  selectChapter();
  $('#ops-search').oninput = renderRows;
  $('#ops-refresh').onclick = () => action(refresh);
  $('#ops-login').onsubmit = event => {
    event.preventDefault();
    const form = event.currentTarget;
    const credentials = {id: form.elements.id.value, password: form.elements.password.value};
    form.elements.password.value = '';
    action(async () => { await api('session', credentials); await refresh(); $('#ops-message').textContent = 'Đã mở phiên sandbox cục bộ.'; });
  };
  $('#ops-logout').onclick = () => action(async () => {
    await api('logout', {}); state = null; ready = false; render(); connection('ĐÃ ĐĂNG XUẤT');
    $('#ops-message').textContent = 'Phiên đã bị thu hồi.';
  });
  $('#ops-write').onsubmit = event => {
    event.preventDefault();
    const form = event.currentTarget;
    // Retain the same key if transport fails; retries must not duplicate a write.
    const payload = {title: form.elements.title.value, group: form.elements.group.value, chapter: Number(form.elements.chapter.value), content: form.elements.content.value};
    const serial = JSON.stringify(payload);
    if (form.dataset.payload !== serial) {form.dataset.payload = serial; form.dataset.requestKey = crypto.randomUUID();}
    action(async () => {
      const receipt = await api('records', {...payload, idempotency_key: form.dataset.requestKey});
      $('#ops-message').textContent = 'Đã lưu vào SQLite cục bộ: ' + JSON.stringify(receipt);
      await refresh();
    });
  };
  $('#ops-sync').onclick = () => action(async () => {
    try {
      const receipt = await api('sync', {});
      $('#ops-message').textContent = 'Kết quả đồng bộ SQLite cục bộ: ' + JSON.stringify(receipt);
    } finally { await refresh(); }
  });
  $('#ops-backup').onclick = () => action(async () => {
    const receipt = await api('backup', {}); lastBackup = receipt.backup_id;
    $('#ops-backup-id').value = lastBackup || '';
    $('#ops-message').textContent = 'Biên nhận sao lưu: ' + JSON.stringify(receipt);
    await refresh();
  });
  $('#ops-restore').onsubmit = event => {
    event.preventDefault();
    action(async () => {
      const receipt = await api('restore', {backup_id: $('#ops-backup-id').value});
      $('#ops-message').textContent = 'Đã kiểm chứng phục hồi vào bản sao riêng, không ghi đè kho đang chạy: ' + JSON.stringify(receipt);
      await refresh();
    });
  };
  render();
  action(refresh);
  // Heartbeat only; never automatically replay writes or claim 24/7 supervision.
  setInterval(() => {if (state && !busy) action(refresh);}, 15000);
})();
