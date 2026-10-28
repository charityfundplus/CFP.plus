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
