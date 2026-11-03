(function () {
  'use strict';
  if (window.HUB69_CONFIG?.mode !== 'app') return;
  let epoch = 0;
  const nativePlatform = () => !!window.Capacitor?.isNativePlatform?.();
  const backendPermitted = () => !nativePlatform() || (location.protocol === 'https:' && location.origin === window.HUB69_CONFIG?.approvedStagingOrigin);
  function publish(phase, data, message) {
    window.dispatchEvent(new CustomEvent('cfp-registry', {detail: {phase, data, message}}));
  }
  async function readRegistry() {
    const run = ++epoch;
    if (!backendPermitted()) {
      publish('blocked', null, 'Gói native review chưa cấu hình HTTPS staging được phê duyệt.');
      return;
    }
    publish('loading', null, 'Đang đọc Registry qua phiên backend hiện hữu…');
    try {
      const response = await fetch('/api/app/registry', {credentials: 'same-origin', cache: 'no-store'});
      if (!response.ok) throw new Error(response.status === 401 ? 'Đăng nhập tại mục Vận hành để đọc Registry qua API.' : 'Không xác minh được Registry. Không dùng dữ liệu từ lần đọc cũ.');
      const data = await response.json();
      if (data.registryBlobSHA !== '1f18068d66379ce90bb079dc56c77b4c4d66dcdf' || !Array.isArray(data.records) || data.records.length !== 26 || new Set(data.records.map(r => r.id)).size !== 26) throw new Error('Nguồn Registry không khớp phiên bản đã kiểm tra.');
      if (run === epoch) publish('ready', data, 'Registry API · 26 bản ghi nguồn · không tự nâng quyền hoặc trạng thái VERIFIED');
    } catch (error) {
      if (run === epoch) publish('blocked', null, error.message || 'Mất kết nối Registry.');
    }
  }
  window.addEventListener('DOMContentLoaded', () => {
    const frame = document.getElementById('operations-frame');
    if (backendPermitted() && /^https?:$/.test(location.protocol)) {
      frame.src = '/#operations';
      document.getElementById('operations-runtime-note').textContent = 'Dùng cùng phiên, API và SQLite với Website SpaceX; không sao chép dữ liệu sang kho App.';
    } else {
      frame.hidden = true;
      document.getElementById('operations-runtime-note').textContent = 'Gói native chưa có endpoint HTTPS được duyệt. Chưa thể đăng nhập, đọc hoặc ghi backend từ thiết bị.';
    }
    document.querySelector('.mobile-tabs').hidden = false;
    document.querySelectorAll('[data-website-preview]').forEach(link => {link.hidden = !backendPermitted() || !/^https?:$/.test(location.protocol);});
    readRegistry();
  });
  window.addEventListener('message', event => {
    const frame = document.getElementById('operations-frame');
    if (event.origin === location.origin && event.source === frame?.contentWindow && event.data?.type === 'cfp-session-changed') readRegistry();
  });
  document.addEventListener('click', event => {if (event.target.closest('[data-app-retry]')) readRegistry();});
  window.addEventListener('online', readRegistry);
  window.addEventListener('offline', () => {++epoch; publish('blocked', null, 'Mất kết nối · không hiển thị Registry từ lần đọc cũ.');});
  window.addEventListener('focus', readRegistry);
})();
