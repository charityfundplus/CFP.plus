"""CFP+ • HUB 69 • AI Directory • Danh mục module — API chỉ đọc cho Website / App.

Dùng chung backend FastAPI hiện hữu (PR #195); không tạo backend thứ hai.
Registry chỉ đọc: không cấp, đổi hay suy diễn Canonical ID / Parent.
"""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from services.forum.registry import CHAPTERS, CONNECTIONS, GROUPS, Registry, group_of

# Trạng thái từng module theo phạm vi kiến trúc 04/11/2026. "implemented" chỉ dùng khi có code + test
# trong repo này; không đồng nghĩa đã triển khai HTTPS/production.
MODULES = [
    {"key": "auth", "name": "Tài khoản • phiên đăng nhập", "status": "implemented", "prefix": "/api/auth"},
    {"key": "forum-sieu-bo-doi", "name": "Diễn Đàn Siêu Bộ Đôi", "status": "implemented", "prefix": "/api/forums/sieu-bo-doi"},
    {"key": "forum-si-ai-hstdn", "name": "Diễn Đàn SI AI • HSTDN", "status": "implemented", "prefix": "/api/forums/si-ai-hstdn"},
    {"key": "office", "name": "Văn Phòng SI AI • Siêu Bộ Đôi • CMP 267 (task/evidence/review)", "status": "implemented", "prefix": "/api/office"},
    {"key": "hstdn", "name": "HSTDN • hồ sơ doanh nghiệp", "status": "implemented", "prefix": "/api/office/enterprises"},
    {"key": "research", "name": "Nghiên cứu • kho dữ liệu • giáo trình", "status": "implemented", "prefix": "/api/office/topics, /api/office/datasets"},
    {"key": "hub69", "name": "HUB 69 • tổng hợp chỉ đọc", "status": "implemented", "prefix": "/api/hub"},
    {"key": "directory", "name": "AI Directory • Registry chỉ đọc", "status": "implemented", "prefix": "/api/directory"},
    {"key": "worker", "name": "Worker P0 • hàng đợi + lịch chạy (heartbeat, retry, dead-letter, kill switch)",
     "status": "partial", "prefix": "/api/worker/status",
     "note": "SANDBOX: 1 việc chỉ đọc (registry_integrity). Chưa có runtime cố định → không phải 24/24."},
    {"key": "website", "name": "Website • nội dung động và form", "status": "missing",
     "note": "Website hiện là nginx tĩnh; chưa có API nội dung/form."},
    {"key": "app", "name": "App • API dùng chung", "status": "partial",
     "note": "App dùng được các API trên; chưa có client/App riêng trong repo."},
    {"key": "tmtc", "name": "Sàn TMTC 8682 • danh mục sản phẩm (sandbox, không thanh toán)", "status": "missing",
     "note": "Chưa có API danh mục; thanh toán không thuộc phạm vi."},
    {"key": "ctttc", "name": "CTTTC 28882 • đọc/tìm kiếm/nguồn chứng cứ", "status": "missing",
     "note": "Có schema + validator v0.6.6 trong repo; chưa có API."},
]


def build_hub_router(registry: Registry, stores, forums_cfg: dict) -> APIRouter:
    r = APIRouter()

    def counts() -> dict:
        c = Counter(e.type for e in registry.entities.values())
        return {"total": len(registry.entities), **dict(sorted(c.items()))}

    @r.get("/api/hub/69", tags=["hub69"])
    def hub69():
        offices = []
        if stores.office is not None:
            from services.forum.office import offices_t
            with stores.office.connect() as c:
                offices = [{"canonical_id": o.canonical_id, "name": o.display_name, "verification": o.verification,
                            "link": f"/_internal/office/{o.canonical_id}/"}
                           for o in c.execute(select(offices_t.c.canonical_id, offices_t.c.display_name,
                                                     offices_t.c.verification).order_by(offices_t.c.canonical_id))]
        return {
            "hub": {"id": "69", "link": "https://cfp.plus/69/", "role": "Cổng kết nối thống nhất"},
            "cmp": {"id": "267", "link": "https://cfp.plus/267/", "role": "Điều phối nhiệm vụ và bằng chứng"},
            "groups": GROUPS,
            "chapters": [{"id": k, "name": v, "group": (group_of(k) or {}).get("code"), "link": f"https://cfp.plus/{k}/"}
                         for k, v in CHAPTERS.items()],
            "connections": CONNECTIONS,
            "forums": [{"key": k, "title": c.title, "public_read": c.public_read, "join_policy": c.join_policy,
                        "link": f"/_internal/forum/{k}/"} for k, c in forums_cfg.items()],
            "offices": offices,
            "registry": counts(),
            "modules": MODULES,
            "status": "SANDBOX • NOT DEPLOYED",
        }

    @r.get("/api/modules", tags=["hub69"])
    def modules():
        return {"modules": MODULES}

    @r.get("/api/directory/countries", tags=["directory"])
    def countries():
        out = []
        for e in registry.entities.values():
            if e.type != "country":
                continue
            ai_country = next((registry.get(x) for x in e.children if registry.get(x).type == "ai_country"), None)
            devs = [registry.get(x) for x in (ai_country.children if ai_country else [])]
            out.append({"country_id": e.id, "name": e.name, "coverage": e.status,
                        "ai_country_id": ai_country.id if ai_country else None,
                        "developers": sum(1 for d in devs if d.type == "developer"),
                        "link": f"https://cfp.plus/{e.id}/"})
        return {"countries": out, "source": "registry/global-country-ai-index.json", "read_only": True}

    @r.get("/api/directory/{eid}", tags=["directory"])
    def entity(eid: str):
        e = registry.get(eid)
        if not e:
            raise HTTPException(404, "ID không có trong Registry. API không cấp ID mới.")
        return {"entity": e.public(), "chain": registry.chain(eid),
                "children": [registry.get(x).public() for x in e.children], "read_only": True}

    return r
