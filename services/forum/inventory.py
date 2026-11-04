"""Sinh hợp đồng OpenAPI + bảng kiểm kê API theo module (existing vs missing) từ chính code.

  python -m services.forum.inventory --write     # cập nhật openapi.json + API_INVENTORY.md
  python -m services.forum.inventory --check     # CI: thất bại nếu tệp lệch với code
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from fastapi.routing import APIRoute

HERE = Path(__file__).parent
OPENAPI_PATH = HERE / "openapi.json"
INVENTORY_PATH = HERE / "API_INVENTORY.md"

# Ranh giới quyền ngoài mức đăng nhập (kiểm tra trong thân handler; có test riêng trong tests/forum).
ROLE_RULES = {
    ("GET", "/api/forums/{key}/posts"): "Siêu Bộ Đôi: công khai • SI AI • HSTDN: thành viên đã duyệt",
    ("POST", "/api/forums/{key}/posts"): "thành viên active của đúng diễn đàn",
    ("POST", "/api/forums/{key}/posts/{post_id}/comments"): "thành viên active của đúng diễn đàn",
    ("GET", "/api/forums/{key}/members"): "admin của đúng diễn đàn",
    ("POST", "/api/forums/{key}/members/{member_id}/approve"): "admin của đúng diễn đàn",
    ("POST", "/api/office/offices"): "governance • ID phải có trong Registry (type ai)",
    ("POST", "/api/office/offices/{cid}/maintainers/{uid}"): "governance",
    ("POST", "/api/office/offices/{cid}/brand"): "maintainer/governance • nhãn xác nhận/ủy quyền: chỉ governance",
    ("POST", "/api/office/pairs"): "maintainer/governance",
    ("POST", "/api/office/tasks"): "maintainer/governance • reviewer độc lập có vai trò",
    ("POST", "/api/office/tasks/{tid}/ack"): "người thực thi",
    ("POST", "/api/office/tasks/{tid}/start"): "người thực thi • tối đa 5 việc song song",
    ("POST", "/api/office/tasks/{tid}/submit"): "người thực thi • cần ≥1 Evidence",
    ("POST", "/api/office/tasks/{tid}/evidence"): "người thực thi",
    ("POST", "/api/office/tasks/{tid}/close"): "governance hoặc người giao việc • không phải người thực thi • cần ACCEPTED",
    ("POST", "/api/office/tasks/{tid}/discussions"): "người xem được nhiệm vụ • thành viên active của ĐÚNG diễn đàn (diễn đàn tự kiểm)",
    ("GET", "/api/office/forum-links"): "chỉ nhiệm vụ người xem được phép thấy • diễn đàn người xem đọc được",
    ("POST", "/api/office/tasks/{tid}/comments"): "người tham gia / maintainer / governance của đúng nhiệm vụ",
    ("POST", "/api/office/tasks/{tid}/review"): "reviewer được chỉ định",
    ("GET", "/api/worker/status"): "công khai, chỉ số tổng hợp (không có nội dung lỗi/kết quả chi tiết)",
    ("GET", "/api/office/audit"): "governance • hoặc người tham gia/maintainer của đúng nhiệm vụ",
    ("GET", "/api/office/datasets/{did}"): "access=members → người tạo / governance / người xem được nhiệm vụ dùng tài liệu",
    ("GET", "/api/office/offices/{cid}"): "khách: hồ sơ công khai • nhiệm vụ/evidence/review: người tham gia (assignee/reviewer/người tạo), maintainer, governance",
    ("GET", "/api/office/links"): "ẩn liên kết tới nhiệm vụ/tài liệu không được xem",
    ("POST", "/api/office/links"): "chủ sở hữu mục nguồn / maintainer / governance • đích phải được xem",
    ("GET", "/api/office/search"): "tài liệu nội bộ chỉ hiện với người được xem",
}


def _store(path: str) -> str:
    if path.startswith("/api/auth"):
        return "auth (cfp_forum_auth)"
    if path.startswith("/api/forums"):
        return "diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn)"
    if path in ("/api/office/tasks/{tid}/discussions", "/api/office/forum-links"):
        return "cfp_office (liên kết) + diễn đàn tương ứng (bài, qua đúng quy tắc diễn đàn)"
    if path.startswith("/api/office"):
        return "cfp_office"
    if path.startswith("/api/worker"):
        return "cfp_worker (chỉ đọc)"
    if path.startswith(("/api/hub", "/api/directory", "/api/modules")):
        return "Registry (tệp, chỉ đọc) + cfp_office (đọc)"
    return "tất cả (chỉ đọc trạng thái)"


def _auth(route: APIRoute) -> str:
    names = {d.call.__name__ for d in route.dependant.dependencies if getattr(d, "call", None)}
    if "require_user" in names:
        return "đăng nhập"
    if names & {"current_user", "optional_user"}:
        return "công khai (+phiên nếu có)"
    return "công khai"


def iter_api_routes(routes):
    """Duyệt mọi APIRoute, kể cả trong router con (FastAPI ≥0.16x bọc bằng _IncludedRouter)."""
    for r in routes:
        if isinstance(r, APIRoute):
            yield r
        elif getattr(r, "original_router", None) is not None:
            yield from iter_api_routes(r.original_router.routes)
        elif getattr(r, "routes", None):
            yield from iter_api_routes(r.routes)


def build_app():
    from services.forum.app import Stores, create_app
    d = Path(tempfile.mkdtemp())
    st = Stores(f"sqlite:///{d/'a.db'}", {"sieu-bo-doi": f"sqlite:///{d/'s.db'}",
                                          "si-ai-hstdn": f"sqlite:///{d/'h.db'}"}, f"sqlite:///{d/'o.db'}")
    return create_app(st)


def inventory_rows(app) -> list[dict]:
    rows = []
    for r in iter_api_routes(app.routes):
        if not r.include_in_schema:
            continue
        for m in sorted(r.methods - {"HEAD", "OPTIONS"}):
            rows.append({"module": (r.tags or ["?"])[0], "method": m, "path": r.path, "auth": _auth(r),
                         "role": ROLE_RULES.get((m, r.path), ""), "store": _store(r.path),
                         "csrf": "header X-CFP-Forum + Origin" if m != "GET" else ""})
    return sorted(rows, key=lambda x: (x["module"], x["path"], x["method"]))


def render_markdown(app) -> str:
    from services.forum.hub import MODULES
    lines = ["# CFP+ Backend API • Kiểm kê theo module", "",
             "Sinh tự động bởi `python -m services.forum.inventory --write` • CI kiểm tra khớp code.",
             "**SANDBOX • NOT DEPLOYED.** Hợp đồng đầy đủ: `services/forum/openapi.json` (OpenAPI 3).", "",
             "## Module (đã có / còn thiếu)", "", "| Module | Trạng thái | Phạm vi | Ghi chú |", "|---|---|---|---|"]
    for mo in MODULES:
        lines.append(f"| {mo['name']} | **{mo['status']}** | `{mo.get('prefix', '—')}` | {mo.get('note', '')} |")
    lines += ["", "## Endpoint", "", "| Module | Method | Path | Xác thực | Quyền thêm | CSRF | Kho dữ liệu |",
              "|---|---|---|---|---|---|---|"]
    for r in inventory_rows(app):
        lines.append(f"| {r['module']} | {r['method']} | `{r['path']}` | {r['auth']} | {r['role']} | {r['csrf']} | {r['store']} |")
    lines += ["", "Ranh giới dữ liệu: mỗi kho là một schema + role riêng (#193 + 002_office.sql); "
              "role của kho này không có USAGE trên schema kho khác; `anon`/`authenticated` không có quyền.",
              "", "RLS theo người dùng (003_office_rls.sql, **chưa áp Supabase**): backend đặt `cfp.user_id` mỗi giao dịch; "
              "Postgres tự tính governance/maintainer/người tham gia và ẩn hoặc chặn ghi dữ liệu của người khác "
              "(nhiệm vụ, evidence, review, lịch sử, tài liệu nội bộ, liên kết, audit). Thiếu danh tính → fail-closed.", ""]
    return "\n".join(lines)


def openapi_text(app) -> str:
    return json.dumps(app.openapi(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    app = build_app()
    want = {OPENAPI_PATH: openapi_text(app), INVENTORY_PATH: render_markdown(app)}
    if a.write:
        for p, t in want.items():
            p.write_text(t, encoding="utf-8")
        print("written:", ", ".join(str(p) for p in want))
        return 0
    bad = [str(p) for p, t in want.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
    if bad:
        print("LỆCH với code, chạy --write:", ", ".join(bad))
        return 1
    print("openapi.json + API_INVENTORY.md khớp code")
    return 0


if __name__ == "__main__":
    sys.exit(main())
