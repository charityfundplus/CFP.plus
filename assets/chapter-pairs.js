// Read-only Gateway projection. Rendering never grants scopes or changes lineage.
(async () => {
  const chapter = location.pathname.split('/').filter(Boolean)[0];
  if (!/^[0-9]$/.test(chapter || '')) return;
  const panel = document.createElement('section');
  panel.id = 'chapter-pair'; panel.className = 'section panel';
  document.querySelector('main').append(panel);
  const element = (tag, text, parent = panel) => {
    const node = document.createElement(tag); node.textContent = text; parent.append(node); return node;
  };
  try {
    const response = await fetch('/assets/chapter-projection.json', {cache: 'no-store'});
    if (!response.ok) throw Error('Projection unavailable');
    const data = await response.json();
    const view = data.chapters.find(c => c.chapter === chapter);
    if (data.authority !== 'READ_ONLY_MIRROR' || !view || view.entities.length !== 2 ||
        new Set(view.entities.map(e => e.entity_type)).size !== 2) throw Error('Projection mismatch');
    panel.dataset.sourceCommit = data.source_commit;
    element('h2', `${chapter} • ${view.display_name} • AI + Phần Mềm`);
    const canonical = element('a', view.canonical_url); canonical.href = view.canonical_url;
    element('p', 'Hồ sơ kỹ thuật • Chưa xác nhận AI đã được tạo hoặc kết nối vận hành.');
    for (const record of view.entities) {
      const article = element('article', ''); article.dataset.entityType = record.entity_type;
      article.id = record.entity_key;
      element('h3', record.display_name, article);
      element('p', `Status: ${record.status}`, article);
      element('p', `Permissions: ${record.permissions.length ? 'REVIEW REQUIRED' : 'Không có quyền được cấp'}`, article);
      element('p', `Evidence: ${record.evidence.join(' • ') || 'Chưa có'}`, article);
      element('p', `Readback: ${record.readback.length ? 'REVIEW REQUIRED' : 'Chưa có Readback vận hành'}`, article);
    }
    element('h3', 'Cây trực tiếp');
    element('p', 'Chưa có hồ sơ descendant được xác minh. Không suy diễn Parent từ tiền tố số.');
    element('h3', 'Các cặp liên quan • Placement chờ Human Review');
    const refs = element('ul', '');
    for (const key of new Set(view.pair_references)) {
      const profile = data.profiles[key]; const item = element('li', '', refs);
      item.dataset.identityReference = key;
      const label = profile.full_name || 'Chưa có tên đầy đủ';
      if (profile.did) {const link = element('a', `${profile.did} • ${label}`, item); link.href = `/${profile.did}`;}
      else element('span', `${label} • DID PENDING`, item);
    }
    element('h3', 'Soi chiếu 10 Chương');
    const list = element('ul', '');
    for (const relation of view.relationships) {
      const item = element('li', '', list); item.dataset.chapter = relation.chapter;
      const link = element('a', `${relation.chapter} • ${relation.relationship}`, item); link.href = `/${relation.chapter}`;
      element('span', ` • ${relation.review_status} • Không cấp quyền`, item);
    }
    element('p', '691141 • CONFLICT FOUND / HUMAN REVIEW');
    element('p', `Nguồn Gateway: ${data.source_commit} • Bản hiển thị chỉ đọc • Chưa kết nối Backend trực tiếp.`);
  } catch (error) {
    element('h2', 'Chapter Pair • REVIEW REQUIRED');
    element('p', 'Không đọc được projection. Không suy diễn căn tính, quyền hoặc trạng thái.');
    panel.dataset.error = 'PROJECTION_UNAVAILABLE';
  }
})();
