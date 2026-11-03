'use strict';
const data = window.PILOT_DATA;
const records = document.querySelector('#records');
function render() {
  records.replaceChildren();
  const query = document.querySelector('#search').value.toLowerCase();
  const rows = (data?.records || []).filter(r => (r.name + r.id).toLowerCase().includes(query));
  rows.forEach(r => {
    const card = document.createElement('article');
    const title = document.createElement('h3'); title.textContent = r.name;
    const body = document.createElement('p'); body.textContent = `ID ${r.id} → Parent ${r.parent_id}`;
    const status = document.createElement('span'); status.className = 'badge'; status.textContent = r.status;
    card.append(title, body, status); records.append(card);
  });
  document.querySelector('#count').textContent = `${rows.length} bản ghi · OFFLINE FIXTURE`;
}
document.querySelector('#search').addEventListener('input', render);
document.querySelector('#reverse').addEventListener('click', () => {
  document.querySelector('#feedback').textContent = 'WRITEBACK BLOCKED · UI không có đường ghi về CFP+. Xem test log để kiểm chứng adapter.';
});
document.querySelector('#audit').textContent = data ? JSON.stringify({digest:data.digest,audit:data.audit},null,2) : 'Chưa có snapshot. Chạy python3 pilot.py --enable';
render();

// Session-only demonstrations: no storage, fetch, or authenticated ACK.
document.querySelector('#demo-discussion').addEventListener('submit', event => {
  event.preventDefault();
  const input = document.querySelector('#demo-message');
  const text = input.value.trim();
  if (!text) return;
  const note = document.createElement('p');
  note.textContent = 'DEMO · ' + text;
  document.querySelector('#demo-notes').append(note);
  input.value = '';
});
for (const action of ['ack', 'decline']) {
  document.querySelector('#demo-' + action).addEventListener('click', () => {
    document.querySelector('#demo-task-status').textContent = 'DEMO · ' + action.toUpperCase() + ' · không gửi lên GitHub';
  });
}
