"""Registry CFP+ • chỉ đọc.

Nguồn: registry/global-country-ai-index.json, registry/ai-entity-registry.json và các
hồ sơ registry/<ID>.md đã có trong repo. Module này KHÔNG cấp, đổi hay suy diễn ID:
một ID chỉ tồn tại nếu đã có trong các nguồn trên.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 5 Nhóm theo chỉ đạo Human Governance (04/11/2026): DV • 000 • 135 • 246 • 789.
# Nhóm không phải Canonical ID (chỉ 10 Chương có route số). HUB 69 hiện hiển thị "Nhóm 0"
# cho nhóm chứa Chương 0 → giữ alias để đối chiếu, không đổi website/Registry.
GROUPS = [
    {"code": "DV", "name": "Nhóm DV", "label": "Chương 0 • Nền Tảng", "chapters": ["0"],
     "hub69_display_alias": "Nhóm 0", "reconciliation": "PENDING_HUMAN_GOVERNANCE"},
    {"code": "000", "name": "Nhóm 000", "label": "Giới Thiệu • Nền Tảng • Giá Trị CFP+", "chapters": []},
    {"code": "135", "name": "Nhóm 135", "label": "Sự Sống • Ba Quỹ • Cộng Đồng", "chapters": ["1", "3", "5"]},
    {"code": "246", "name": "Nhóm 246", "label": "Con Người • Tôn Giáo • AI", "chapters": ["2", "4", "6"]},
    {"code": "789", "name": "Nhóm 789", "label": "Doanh Nghiệp • Tổ Chức • Quốc Gia", "chapters": ["7", "8", "9"]},
]
CHAPTERS = {
    "0": "Nền Tảng", "1": "Sự Sống", "2": "Con Người", "3": "Bộ Tam và Ba Quỹ",
    "4": "Tôn Giáo và Tín Ngưỡng", "5": "Bộ Ngũ và Cộng Đồng", "6": "AI", "7": "Doanh Nghiệp",
    "8": "Các Tổ Chức và Các Quỹ", "9": "Quốc Gia và Vùng Lãnh Thổ",
}


# Kết nối hệ sinh thái: chỉ dùng route số đã có trên website (không tạo ID mới).
CONNECTIONS = [
    {"key": "hub69", "name": "HUB 69 • Cổng kết nối thống nhất", "link": "https://cfp.plus/69/"},
    {"key": "cmp267", "name": "CMP 267 • Điều phối nhiệm vụ và bằng chứng", "link": "https://cfp.plus/267/"},
    {"key": "chapters", "name": "10 Chương", "link": "https://cfp.plus/0123456789/"},
    {"key": "tmtc", "name": "Sàn TMTC 8682", "link": "https://cfp.plus/8682/"},
    {"key": "ctttc", "name": "CTTTC 28882", "link": "https://cfp.plus/28882/"},
    {"key": "website", "name": "Website CFP+", "link": "https://cfp.plus/"},
    {"key": "forum-sieu-bo-doi", "name": "Diễn Đàn Siêu Bộ Đôi (sandbox)", "link": "/_internal/forum/sieu-bo-doi/",
     "status": "SANDBOX • CHƯA CÓ CANONICAL ID"},
    {"key": "forum-si-ai-hstdn", "name": "Diễn Đàn SI AI • HSTDN (sandbox)", "link": "/_internal/forum/si-ai-hstdn/",
     "status": "SANDBOX • CHƯA CÓ CANONICAL ID"},
]


def group_of(chapter: str) -> dict | None:
    return next((g for g in GROUPS if chapter in g["chapters"]), None)


@dataclass
class Entity:
    id: str
    type: str          # country | ai_country | developer | ai | registry_record
    name: str
    parent_id: str | None
    status: str = ""
    official_source: str | None = None
    country_id: str | None = None
    source: str = ""
    children: list[str] = field(default_factory=list)
    # explicit: Parent khai báo trong JSON nguồn • inferred_prefix: suy từ tiền tố ID của Markdown (CHƯA xác minh)
    parent_source: str | None = None

    def public(self) -> dict:
        return {"id": self.id, "type": self.type, "name": self.name, "parent_id": self.parent_id,
                "status": self.status, "official_source": self.official_source,
                "country_id": self.country_id, "link": f"https://cfp.plus/{self.id}/",
                "registry_source": self.source, "children": list(self.children)}


class Registry:
    def __init__(self, root: Path = REPO_ROOT):
        self.entities: dict[str, Entity] = {}
        self.conflicts: list[dict] = []
        reg = root / "registry"
        for c in json.loads((reg / "global-country-ai-index.json").read_text(encoding="utf-8")):
            cid, acid = str(c["country_id"]), str(c["ai_country_id"])
            self._add(Entity(cid, "country", c["name"], None, c.get("coverage", ""),
                             country_id=cid, source="global-country-ai-index.json"))
            self._add(Entity(acid, "ai_country", f"AI {c['name']}", cid, c.get("coverage", ""),
                             country_id=cid, source="global-country-ai-index.json"))
        ents = json.loads((reg / "ai-entity-registry.json").read_text(encoding="utf-8"))
        for key, e in ents.items():
            if key.startswith("_"):
                continue
            parent = e.get("parent_id") or e.get("ai_country_id")
            self._add(Entity(str(e["id"]), e["type"], e["name"], str(parent) if parent else None,
                             e.get("status", ""), e.get("official_source"), str(e.get("country_id") or ""),
                             "ai-entity-registry.json"))
        for md in sorted(reg.glob("*.md")):  # thứ tự cố định: Parent suy ra không phụ thuộc thư mục (PR195-REGISTRY-GLOB-ORDER)
            if not re.fullmatch(r"[0-9]+", md.stem) or md.stem in self.entities:
                continue
            first = next((ln for ln in md.read_text(encoding="utf-8").splitlines() if ln.startswith("# ")), md.stem)
            parent = md.stem[:-1] if md.stem[:-1] in self.entities else None
            self._add(Entity(md.stem, "registry_record", first.lstrip("# ").strip()[:200], parent,
                             source=f"registry/{md.name}", parent_source="inferred_prefix" if parent else None))
        for e in self.entities.values():
            if e.parent_id and e.parent_id in self.entities:
                self.entities[e.parent_id].children.append(e.id)

    def _add(self, e: Entity) -> None:
        if e.parent_id and e.parent_source is None:
            e.parent_source = "explicit"
        prev = self.entities.get(e.id)
        if prev is not None:  # không ghi đè; nguồn đầu tiên giữ nguyên — nhưng xung đột phải được BÁO, không im lặng
            diff = [f for f in ("type", "name", "parent_id") if getattr(prev, f) != getattr(e, f)]
            if diff:
                self.conflicts.append({"id": e.id, "fields": diff, "kept": prev.source, "ignored": e.source})
            return
        self.entities[e.id] = e

    def get(self, eid: str) -> Entity | None:
        return self.entities.get(eid)

    def chain(self, eid: str) -> list[dict]:
        out, seen = [], set()
        cur = self.entities.get(eid)
        while cur and cur.id not in seen:
            seen.add(cur.id)
            out.append(cur.public())
            cur = self.entities.get(cur.parent_id) if cur.parent_id else None
        return list(reversed(out))
