"""Render editorial review pages from the shared standard; no Registry writes."""
import html
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def render(key, record, standard):
    esc = html.escape
    canonical = '' if key == 'V' else '<link rel="canonical" href="https://cfp.plus/'+key+'">'
    sections = ''.join('<section><h2>'+esc(s['title'])+'</h2>'+''.join('<p>'+esc(p)+'</p>' for p in s['paragraphs'])+'</section>' for s in record['sections'])
    chapters = ' '.join('<a href="/'+str(i)+'">'+str(i)+' • '+esc(name)+'</a>' for i,name in enumerate(standard['chapter_names']))
    groups = ' '.join('<a href="/'+g+'">'+g+'</a>' for g in ['V','000','135','246','789'])
    priorities = ' '.join('<a href="/'+did+'">'+did+' • '+esc(p['name'])+'</a>' for did,p in standard['pages'].items())
    return '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+key+' • '+esc(record['name'])+' • CFP+</title>'+canonical+'<link rel="stylesheet" href="/styles.css"><style>main{max-width:1000px;margin:auto;padding:20px}nav a{display:inline-block;margin:6px}section{margin:24px 0}</style></head><body><main><a href="/69">HUB 69</a><h1>'+key+' • '+esc(record['name'])+'</h1><p>'+esc(record['purpose'])+'</p>'+sections+'<section><h2>Quyền riêng tư và quyền hạn</h2><p>'+esc(record['privacy'])+'</p><p>THƯỢNG TÔN PHÁP LUẬT • TUÂN THỦ PHÁP LUẬT. Capability ≠ Authority. Parent/Child: chỉ ghi từ Registry Evidence, không suy từ chữ số. Quản lý SI 🤖 AI 🤖 và Siêu Phần Mềm: chưa xác minh trong trang biên tập này; không tuyên bố ACTIVE hoặc quyền thực thi.</p></section><section><h2>Điều hướng CFP+</h2><nav aria-label="5 Nhóm">'+groups+'</nav><nav aria-label="10 Chương">'+chapters+'</nav><nav aria-label="Trang trọng tâm">'+priorities+'</nav><p>Liên kết điều hướng không xác nhận quan hệ Canonical hoặc quyền truy cập chéo.</p></section><section><h2>Evidence • Trạng thái</h2><p>'+esc(record['source'])+'</p><p>'+esc(record['content_status'])+' • Publication: REVIEW CANDIDATE • Updated: '+esc(standard['updated'])+' • Canonical Lock: NO.</p><p>Nội dung biên tập chờ Human Review; không thay Registry, không xác nhận publication production hoặc operational PASS.</p>'+('<p>V là informational working view, không phải Canonical Numeric ID; không tự cấp DID cho V.</p>' if key=='V' else '')+'</section></main></body></html>\n'

def main():
    standard=json.loads((ROOT/'content/site-standard.json').read_text())
    for key, record in standard['foundations'].items():
        target=ROOT/key/'index.html'
        target.parent.mkdir(exist_ok=True)
        target.write_text(render(key,record,standard))

if __name__ == '__main__':
    main()
