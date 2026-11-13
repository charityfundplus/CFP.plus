"""Ghép canva.html + canva.css + canva.js thành MỘT tệp để dán vào Canva Code (không cần tải tài nguyên ngoài).

  python -m services.forum.web.build_canva            # ghi services/forum/web/canva-code.html
  python -m services.forum.web.build_canva --check    # CI: tệp đã ghép phải khớp nguồn
Địa chỉ backend mặc định trong tệp = Render sandbox; người dùng đổi được ở mục Tài khoản.
"""
import sys
from pathlib import Path

WEB = Path(__file__).parent
OUT = WEB / "canva-code.html"
BASE = "https://cfp-forum-office-sandbox-p0.onrender.com"


def build() -> str:
    html = (WEB / "canva.html").read_text(encoding="utf-8")
    css = (WEB / "canva.css").read_text(encoding="utf-8")
    js = (WEB / "canva.js").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="/canva/canva.css">', "<style>\n" + css + "</style>")
    html = html.replace('<script src="/canva/canva.js"></script>',
                        f'<script>window.CFP_CANVA_BASE = "{BASE}";</script>\n<script>\n' + js + "</script>")
    assert "/canva/canva" not in html
    return "<!-- TỆP SINH TỰ ĐỘNG từ canva.html/css/js — dán nguyên văn vào Canva Code. SANDBOX. -->\n" + html


if __name__ == "__main__":
    out = build()
    if "--check" in sys.argv:
        sys.exit(0 if OUT.read_text(encoding="utf-8") == out else "canva-code.html cũ: chạy build_canva")
    OUT.write_text(out, encoding="utf-8")
    print(OUT, len(out), "bytes")
