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

# 5 Nhóm theo HUB 69 hiện hành (https://cfp.plus/69). Mã nhóm giữ nguyên như website.
GROUPS = [
    {"code": "000", "name": "Nhóm 000", "label": "Giới Thiệu • Nền Tảng • Giá Trị CFP+", "chapters": []},
    {"code": "0", "name": "Nhóm 0", "label": "Chương 0 • Nền Tảng", "chapters": ["0"]},
    {"code": "135", "name": "Nhóm 135", "label": "Sự Sống • Ba Quỹ • Cộng Đồng", "chapters": ["1", "3", "5"]},
    {"code": "246", "name": "Nhóm 246", "label": "Con Người • Tôn Giáo • AI", "chapters": ["2", "4", "6"]},
    {"code": "789", "name": "Nhóm 789", "label": "Doanh Nghiệp • Tổ Chức • Quốc Gia", "chapters": ["7", "8", "9"]},
]
CHAPTERS = {
    "0": "Nền Tảng", "1": "Sự Sống", "2": "Con Người", "3": "Bộ Tam và Ba Quỹ",
    "4": "Tôn Giáo và Tín Ngưỡng", "5": "Bộ Ngũ và Cộng Đồng", "6": "AI", "7": "Doanh Nghiệp",
    "8": "Các Tổ Chức và Các Quỹ", "9": "Quốc Gia và Vùng Lãnh Thổ",
}


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

    def public(self) -> dict:
        return {"id": self.id, "type": self.type, "name": self.name, "parent_id": self.parent_id,
                "status": self.status, "official_source": self.official_source,
                "country_id": self.country_id, "link": f"https://cfp.plus/{self.id}/",
                "registry_source": self.source, "children": list(self.children)}


class Registry:
    def __init__(self, root: Path = REPO_ROOT):
        self.entities: dict[str, Entity] = {}
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
        for md in reg.glob("*.md"):
            if not re.fullmatch(r"[0-9]+", md.stem) or md.stem in self.entities:
                continue
            first = next((ln for ln in md.read_text(encoding="utf-8").splitlines() if ln.startswith("# ")), md.stem)
            parent = md.stem[:-1] if md.stem[:-1] in self.entities else None
            self._add(Entity(md.stem, "registry_record", first.lstrip("# ").strip()[:200], parent,
                             source=f"registry/{md.name}"))
        for e in self.entities.values():
            if e.parent_id and e.parent_id in self.entities:
                self.entities[e.parent_id].children.append(e.id)

    def _add(self, e: Entity) -> None:
        if e.id in self.entities:  # không ghi đè; nguồn đầu tiên thắng
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
