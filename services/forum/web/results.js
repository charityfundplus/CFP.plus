(function () {
  'use strict';

  const results = document.getElementById('results');
  const filter = document.getElementById('lane');
  const count = document.getElementById('result-count');
  let office = [];
  let github = [];

  async function get(path) {
    const response = await fetch(path, {cache: 'no-store', credentials: 'same-origin'});
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  }

  function node(tag, text) {
    const element = document.createElement(tag);
    element.textContent = text;
    return element;
  }

  function link(label, value) {
    try {
      const url = new URL(value);
      if (url.protocol !== 'https:' || url.username || url.password) return null;
      const a = node('a', label);
      a.href = url.href;
      return a;
    } catch {
      return null;
    }
  }

  function utc(value) {
    if (!value) return 'Chưa có';
    const input = /(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : value + 'Z';
    const date = new Date(input);
    return Number.isNaN(date.getTime()) ? 'Chưa có' : date.toISOString().replace('T', ' ').replace(/\.\d+Z$/, ' UTC');
  }

  function render() {
    const rows = [...office, ...github]
      .filter(row => !filter.value || row.lane === filter.value)
      .sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
    count.textContent = rows.length ? rows.length + ' nhiệm vụ' : 'Chưa có nhiệm vụ trong mục này.';
    results.replaceChildren();
    for (const row of rows) {
      const card = node('article', '');
      card.className = 'chapter-card';
      card.style.overflowWrap = 'anywhere';
      card.append(node('small', row.lane + ' · ' + (row.workspace ? 'Văn Phòng' : 'GitHub')));
      card.append(node('h2', row.title));
      card.append(node('p', 'Owner · ' + (row.owner || 'Chưa xác nhận')));
      card.append(node('p', 'Trạng thái · ' + row.status + (row.stale ? ' · dữ liệu cũ' : '')));
      card.append(node('p', 'Cập nhật · ' + utc(row.updated_at)));
      card.append(node('p', 'Blocker · ' + (row.blocker || 'Chưa ghi nhận')));
      const evidence = node('div', '');
      const urls = row.evidence_urls.map((url, i) => link('Evidence URL ' + (i + 1), url)).filter(Boolean);
      if (urls.length) {
        const list = node('ul', '');
        for (const a of urls) {
          const item = node('li', '');
          item.append(a);
          list.append(item);
        }
        evidence.append(list);
      } else {
        evidence.textContent = 'Evidence URL · Chưa có';
      }
      card.append(evidence);
      let source = link('Mở nguồn GitHub', row.url);
      if (row.workspace && /^\/_internal\/office\/\d+\/#task:\d+$/.test(row.url)) {
        source = node('a', 'Mở nhiệm vụ trong Link Mẫu');
        source.href = row.url;
      }
      if (source) card.append(source);
      results.append(card);
    }
  }

  async function refresh() {
    const sync = document.getElementById('sync-status');
    try {
      const data = await get('/api/hub/69/github-results');
      github = data.rows;
      sync.textContent = data.state === 'disabled' ? 'Đồng bộ GitHub đang tắt trong môi trường này.' :
        'GitHub · ' + utc(data.checked_at) + (data.errors.length ? ' · Không tải được ' + data.errors.join(', ') : ' · Đã kiểm tra nguồn.');
    } catch {
      github = github.map(row => ({...row, stale: true}));
      sync.textContent = 'Không tải được kết quả GitHub.';
    }
    render();
  }

  filter.addEventListener('change', render);
  get('/api/office/board').then(data => {
    office = data.tasks.map(row => ({...row, lane: 'Siêu Bộ Đôi', workspace: true,
      status: row.bucket === 'BLOCKED' ? 'BLOCKED · ' + row.status : row.status, blocker: row.reason}));
    document.getElementById('office-status').textContent = data.viewer === 'guest' ?
      'Đăng nhập vào Văn Phòng để xem nhiệm vụ theo quyền của bạn.' : 'Văn Phòng · nhiệm vụ theo quyền người xem.';
    render();
  }).catch(() => {
    document.getElementById('office-status').textContent = 'Không tải được nhiệm vụ Văn Phòng.';
  });
  refresh();
  window.setInterval(refresh, 300000);
})();
