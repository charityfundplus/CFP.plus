(function () {
  'use strict';
  if (window.HUB69_CONFIG?.mode !== 'app') return;
  const $ = id => document.getElementById(id);
  let current = null, epoch = 0, busy = false;
  function element(tag, value) {const n = document.createElement(tag); n.textContent = value; return n;}
  async function request(path, body) {
    if (window.Capacitor?.isNativePlatform?.() && !(location.protocol === 'https:' && location.origin === window.HUB69_CONFIG?.approvedStagingOrigin)) throw new Error('Chưa cấu hình HTTPS staging được phê duyệt cho gói native.');
    const r = await fetch('/api/' + path, {method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store', headers: {'Content-Type': 'application/json'}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    const value = await r.json();
    if (!r.ok) {
      if (r.status === 401) clear('Phiên đã hết hạn hoặc bị thu hồi.');
      throw new Error(value.error || 'Không xác minh được phiên backend.');
    }
    return value;
  }
  function clear(message) {
    current = null;
    for (const id of ['forum-tasks', 'forum-posts', 'forum-evidence', 'forum-notifications']) $(id).replaceChildren();
    $('forum-audit').textContent = '';
    for (const select of document.querySelectorAll('[data-forum-task]')) select.replaceChildren();
    $('forum-status').textContent = message;
    for (const button of document.querySelectorAll('#view-forum form button')) button.disabled = true;
  }
  function selectTasks(tasks) {
    for (const select of document.querySelectorAll('[data-forum-task]')) {
      const previous = select.value;
      select.replaceChildren(...tasks.map(task => {const option = element('option', task.title + ' · ' + task.key); option.value = task.key; return option;}));
      if (tasks.some(t => t.key === previous)) select.value = previous;
    }
  }
  async function read() {
    if (location.hash !== '#forum') return;
    const run = ++epoch;
    try {
      const [data, state] = await Promise.all([request('forum/state'), request('state')]);
      if (run !== epoch) return;
      current = {data, user: state.user};
      $('forum-status').textContent = 'Đã đọc Diễn đàn qua API · ' + state.user.id + ' · ' + state.user.role;
      const canWrite = ['editor', 'admin'].includes(state.user.role);
      for (const button of document.querySelectorAll('#view-forum form button')) button.disabled = !canWrite;
      selectTasks(data.tasks);
      $('forum-tasks').replaceChildren(...data.tasks.map(task => {
        const card = element('article', ''); card.className = 'panel';
        card.append(element('h2', task.title), element('p', task.content), element('p', task.key), element('p', task.author + ' → ' + task.recipient + ' · ' + task.status));
        if (canWrite && task.recipient === state.user.id && task.status === 'QUEUED') {
          const ack = element('button', 'Tiếp nhận nhiệm vụ'); ack.className = 'btn';
          ack.onclick = () => action(async () => {await request('forum/ack', {task_key: task.key}); $('forum-message').textContent = 'Đã tiếp nhận bằng đúng tài khoản được giao.';});
          card.append(ack);
        }
        return card;
      }));
      $('forum-posts').replaceChildren(...data.posts.map(post => {const n = element('article', '');n.className='panel';n.append(element('strong', post.author + ' · ' + post.task_key), element('p', post.content));return n;}));
      $('forum-evidence').replaceChildren(...data.evidence.map(item => {
        const card = element('article', ''); card.className = 'panel';
        card.append(element('strong', item.name), element('p', 'Nhiệm vụ: ' + item.task_key), element('code', item.sha256));
        const verify = element('button', 'Đọc lại và kiểm tra Evidence'); verify.className = 'btn';
        verify.onclick = () => action(async () => {
          const saved = await request('forum/evidence/' + encodeURIComponent(item.key));
          const bytes = Uint8Array.from(atob(saved.content_base64), c => c.charCodeAt(0));
          const actual = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
          if (actual !== saved.sha256 || saved.task_key !== item.task_key) throw new Error('Evidence không khớp mã nhiệm vụ hoặc SHA256.');
          $('forum-message').textContent = 'Evidence PASS · ' + saved.task_key + ' · SHA256 ' + actual;
        });
        card.append(verify);return card;
      }));
      $('forum-notifications').replaceChildren(...data.notifications.map(n => element('p', 'Nhiệm vụ được giao: ' + n.task_key + ' · ' + n.status)));
      $('forum-audit').textContent = JSON.stringify(state.audit.filter(e => e.action.startsWith('forum.')), null, 2);
    } catch (error) {if (run === epoch) clear('Chưa đọc được Diễn đàn. Đăng nhập tại Vận hành và thử lại. ' + error.message);}
  }
  async function action(fn) {
    if (busy) return;
    busy = true;
    try {await fn();await read();}
    catch (error) {$('forum-message').textContent = error.message;}
    finally {busy = false;}
  }
  function key(form, payload) {
    const serial = JSON.stringify(payload);
    if (form.dataset.payload !== serial) {form.dataset.payload = serial;form.dataset.key = crypto.randomUUID();}
    return form.dataset.key;
  }
  window.addEventListener('DOMContentLoaded', () => {
    $('forum-refresh').onclick = read;
    $('forum-create').onsubmit = event => {
      event.preventDefault(); const form = event.currentTarget;
      const payload = Object.fromEntries(new FormData(form));
      action(async () => {await request('forum/tasks', {...payload, idempotency_key: key(form, payload)});$('forum-message').textContent = 'Đã tạo nhiệm vụ và lưu bền vững.';});
    };
    $('forum-reply').onsubmit = event => {
      event.preventDefault();const form = event.currentTarget,payload = Object.fromEntries(new FormData(form));
      action(async () => {await request('forum/posts', {...payload, idempotency_key: key(form, payload)});$('forum-message').textContent = 'Đã lưu phản hồi.';});
    };
    $('forum-upload').onsubmit = event => {
      event.preventDefault();const form = event.currentTarget;
      action(async () => {
        const file = form.elements.file.files[0];
        if (!file || file.size > 32768) throw new Error('Chọn Evidence văn bản UTF-8 tối đa 32 KiB.');
        const bytes = new Uint8Array(await file.arrayBuffer());
        const payload = {task_key: form.elements.task_key.value, name: file.name, content_base64: btoa(Array.from(bytes, b => String.fromCharCode(b)).join(''))};
        await request('forum/evidence', {...payload, idempotency_key: key(form, payload)});
        $('forum-message').textContent = 'Đã lưu Evidence; hãy đọc lại để kiểm tra SHA256 và mã nhiệm vụ.';
      });
    };
    read();
  });
  window.addEventListener('hashchange', read);
  window.addEventListener('offline', () => {++epoch;clear('Mất kết nối · chưa xác minh được Diễn đàn.');});
  window.addEventListener('online', read);
  window.addEventListener('message', event => {const frame=$('operations-frame');if(event.origin===location.origin&&event.source===frame?.contentWindow&&event.data?.type==='cfp-session-changed')read();});
})();
