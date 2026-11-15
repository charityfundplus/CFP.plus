import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {fiveStoreStatus} from '../core/store-status.mjs';
const esc=v=>String(v??'UNKNOWN').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const link=(url,label)=>url?`<a href="${esc(url)}">${esc(label)}</a>`:'UNKNOWN — chờ đích công khai được duyệt';
export function renderStoreTable(){
 const state=fiveStoreStatus();
 return `<!-- five-store-status:start -->
<section class="section panel" id="five-store-status" aria-labelledby="five-store-heading">
<h2 id="five-store-heading">Trạng thái 5 kho • Evidence</h2>
<p>HOLD ACTIVATION • PRODUCTION NO-GO. Bảng theo kế hoạch đồng bộ Notion, GitHub, Google, MCP, CMP; Website là nơi hiển thị.</p>
<p>Chưa có bằng chứng đồng bộ phiên bản hiện tại. UNKNOWN nghĩa là chưa xác minh; link tham chiếu không cấp quyền truy cập. Thời điểm chưa kiểm tra giữ UNKNOWN.</p>
<div class="store-table-scroll" role="region" aria-label="Bảng trạng thái 5 kho, cuộn ngang để đọc" tabindex="0"><table class="store-table"><caption>Danh mục chuẩn bị • chưa kết nối adapter vận hành</caption><thead><tr>${['Kho','Link','Owner','Quyền truy cập / phạm vi','Kiểm tra (UTC)','Evidence','Đồng bộ'].map(s=>`<th scope="col">${s}</th>`).join('')}</tr></thead><tbody>
${state.stores.map(s=>`<tr><th scope="row">${esc(s.name)}</th><td>${link(s.url,s.name)}</td><td>${esc(s.owner)}</td><td>${esc(s.access)}${s.scope?'<br>'+esc(s.scope):''}</td><td>${esc(s.checkedAt)}</td><td>${s.evidence?link(s.evidence,'Source only • '+state.sourceRevision.slice(0,8)):'MISSING — chưa có receipt đối chiếu và đọc lại'}</td><td><strong>${s.syncStatus}</strong></td></tr>`).join('\n')}
</tbody></table></div><p><a href="/69/store-status.json">Dữ liệu trạng thái</a> • Receipt đồng bộ cần đúng target, owner/scope đã xác minh, revision, SHA256 nguồn và nội dung đọc lại, thời điểm và kết luận review.</p></section>
<!-- five-store-status:end -->`;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const root=new URL('../../../',import.meta.url),page=new URL('69/index.html',root);
 let html=readFileSync(page,'utf8');const section=renderStoreTable();
 html=html.includes('<!-- five-store-status:start -->')?html.replace(/<!-- five-store-status:start -->[\s\S]*?<!-- five-store-status:end -->/,section):html.replace('</main>',section+'\n</main>');
 writeFileSync(page,html);writeFileSync(new URL('69/store-status.json',root),JSON.stringify(fiveStoreStatus(),null,2)+'\n');
}
