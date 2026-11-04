"""CFP+ • Văn Phòng SI AI (Link Mẫu) • Siêu Bộ Đôi • HSTDN • Kho nghiên cứu • Nhiệm vụ • Evidence • Review.

Gắn vào service diễn đàn hiện hữu (dùng chung tài khoản, phiên, rate limit, CSRF).
Dữ liệu nằm ở kho riêng (CFP_OFFICE_DB) — không đọc/ghi database của hai diễn đàn.
Định danh chỉ tham chiếu Registry (chỉ đọc); không có API nào tạo Canonical ID.
"""
from __future__ import annotations

import json
import os
import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text, UniqueConstraint,
                        and_, func, insert, or_, select, update)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from services.forum.registry import CHAPTERS, CONNECTIONS, GROUPS, Registry, group_of

md = MetaData()
roles_t = Table("office_roles", md,
                Column("user_id", Integer, primary_key=True),
                Column("role", String(16), primary_key=True))  # governance | reviewer
offices_t = Table("offices", md,
                  Column("canonical_id", String(32), primary_key=True),   # ID đã có trong Registry
                  Column("display_name", String(120), nullable=False),
                  Column("platform", String(120), nullable=False),
                  Column("specialties", Text, nullable=False, default=""),
                  Column("capabilities", Text, nullable=False, default=""),
                  Column("limits", Text, nullable=False, default=""),
                  Column("verification", String(40), nullable=False),
                  Column("created_by", Integer, nullable=False),
                  Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
maintainers_t = Table("office_maintainers", md,
                      Column("canonical_id", String(32), ForeignKey("offices.canonical_id"), primary_key=True),
                      Column("user_id", Integer, primary_key=True))
brand_t = Table("brand_items", md,
                Column("id", Integer, primary_key=True),
                Column("canonical_id", String(32), ForeignKey("offices.canonical_id"), nullable=False),
                Column("kind", String(16), nullable=False),
                Column("name", String(160), nullable=False),
                Column("name_key", String(160), nullable=False),
                Column("description", Text, nullable=False, default=""),
                Column("url", String(1000), nullable=False),
                Column("source_type", String(24), nullable=False),
                Column("source_url", String(1000), nullable=False),
                Column("authorization_url", String(1000)),
                Column("created_by", Integer, nullable=False),
                Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                UniqueConstraint("canonical_id", "kind", "name_key"))
enterprises_t = Table("enterprises", md,
                      Column("id", Integer, primary_key=True),
                      Column("name", String(200), nullable=False),
                      Column("name_key", String(200), nullable=False),
                      Column("country_id", String(32), nullable=False),     # ID quốc gia đã có trong Registry
                      Column("chapter", String(1), nullable=False),
                      Column("official_url", String(1000), nullable=False),
                      Column("source_url", String(1000), nullable=False),
                      Column("products", Text, nullable=False, default=""),
                      Column("capacity", Text, nullable=False, default=""),
                      Column("needs", Text, nullable=False, default=""),       # hợp tác • thương mại • đầu tư
                      Column("status", String(24), nullable=False, default="PROVISIONAL"),
                      Column("created_by", Integer, nullable=False),
                      Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                      UniqueConstraint("name_key", "country_id"))
topics_t = Table("research_topics", md,
                 Column("id", Integer, primary_key=True),
                 Column("title", String(200), nullable=False),
                 Column("title_key", String(200), nullable=False),
                 Column("chapter", String(1), nullable=False),
                 Column("field", String(120), nullable=False, default=""),
                 Column("summary", Text, nullable=False, default=""),
                 Column("created_by", Integer, nullable=False),
                 Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                 UniqueConstraint("title_key", "chapter"))
datasets_t = Table("datasets", md,
                   Column("id", Integer, primary_key=True),
                   Column("title", String(200), nullable=False),
                   Column("kind", String(16), nullable=False),
                   Column("url", String(1000), nullable=False),
                   Column("author", String(200), nullable=False),
                   Column("version", String(64), nullable=False),
                   Column("source_url", String(1000), nullable=False),
                   Column("access", String(8), nullable=False),           # public | members
                   Column("chapter", String(1), nullable=False),
                   Column("topic_id", Integer, ForeignKey("research_topics.id")),
                   Column("created_by", Integer, nullable=False),
                   Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                   UniqueConstraint("url", "version"))
pairs_t = Table("super_pairs", md,
                Column("id", Integer, primary_key=True),
                Column("canonical_id", String(32), ForeignKey("offices.canonical_id"), nullable=False),
                Column("software", String(160), nullable=False),
                Column("software_key", String(160), nullable=False),
                Column("lead_user_id", Integer, nullable=False),
                Column("created_by", Integer, nullable=False),
                Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                UniqueConstraint("canonical_id", "software_key"))
tasks_t = Table("tasks", md,
                Column("id", Integer, primary_key=True),
                Column("pair_id", Integer, ForeignKey("super_pairs.id"), nullable=False),
                Column("title", String(200), nullable=False),
                Column("description", Text, nullable=False, default=""),
                Column("acceptance", Text, nullable=False),
                Column("assignee_id", Integer, nullable=False),
                Column("reviewer_id", Integer, nullable=False),
                Column("status", String(24), nullable=False),
                Column("idempotency_key", String(80), unique=True, nullable=False),
                Column("created_by", Integer, nullable=False),
                Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
task_events_t = Table("task_events", md,
                      Column("id", Integer, primary_key=True),
                      Column("task_id", Integer, ForeignKey("tasks.id"), nullable=False),
                      Column("actor_id", Integer, nullable=False),
                      Column("from_status", String(24)),
                      Column("to_status", String(24), nullable=False),
                      Column("note", Text, nullable=False, default=""),
                      Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()))
evidence_t = Table("evidence", md,
                   Column("id", Integer, primary_key=True),
                   Column("task_id", Integer, ForeignKey("tasks.id"), nullable=False),
                   Column("kind", String(16), nullable=False),
                   Column("url", String(1000), nullable=False),
                   Column("sha", String(80)),
                   Column("description", Text, nullable=False),
                   Column("submitted_by", Integer, nullable=False),
                   Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                   UniqueConstraint("task_id", "url"))
reviews_t = Table("reviews", md,
                  Column("id", Integer, primary_key=True),
                  Column("task_id", Integer, ForeignKey("tasks.id"), nullable=False),
                  Column("reviewer_id", Integer, nullable=False),
                  Column("decision", String(24), nullable=False),
                  Column("notes", Text, nullable=False),
                  Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()))
links_t = Table("links", md,
                Column("id", Integer, primary_key=True),
                Column("from_ref", String(64), nullable=False),
                Column("to_ref", String(64), nullable=False),
                Column("relation", String(40), nullable=False),
                Column("created_by", Integer, nullable=False),
                Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                UniqueConstraint("from_ref", "to_ref", "relation"))
audit_t = Table("audit_log", md,
                Column("id", Integer, primary_key=True),
                Column("actor_id", Integer),
                Column("action", String(40), nullable=False),
                Column("ref", String(64), nullable=False),
                Column("data", Text, nullable=False),
                Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()))

REF_TABLES = {"office": (offices_t, offices_t.c.canonical_id), "brand": (brand_t, brand_t.c.id),
              "enterprise": (enterprises_t, enterprises_t.c.id), "topic": (topics_t, topics_t.c.id),
              "dataset": (datasets_t, datasets_t.c.id), "pair": (pairs_t, pairs_t.c.id),
              "task": (tasks_t, tasks_t.c.id)}
SOURCE_LABELS = {"CFP_PUBLIC_SOURCE": "Hồ sơ CFP+ tổng hợp từ nguồn công khai",
                 "BRAND_CONFIRMED": "Nội dung đã được thương hiệu xác nhận",
                 "AUTHORIZED_PROMOTION": "Quảng bá chính thức được ủy quyền"}
# Máy trạng thái nhiệm vụ: hành động → (trạng thái nguồn, trạng thái đích, ai được làm)
TRANSITIONS = {
    "ack": ({"QUEUED"}, "ACKED", "assignee"),
    "start": ({"ACKED", "CHANGES_REQUESTED"}, "IN_PROGRESS", "assignee"),
    "submit": ({"IN_PROGRESS"}, "IN_REVIEW", "assignee"),
}
HTTPS = r"^https://[^\s]{3,990}$"
CH = r"^[0-9]$"


def _key(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().casefold()


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ------------------------------------------------------------- input models

class OfficeIn(BaseModel):
    canonical_id: str = Field(pattern=r"^[0-9]{1,32}$")
    platform: str = Field(min_length=2, max_length=120)
    specialties: str = Field(default="", max_length=2000)
    capabilities: str = Field(default="", max_length=4000)
    limits: str = Field(default="", max_length=4000)


class BrandIn(BaseModel):
    kind: Literal["product", "api", "software", "app", "service", "technology", "training", "research", "program"]
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    url: str = Field(pattern=HTTPS)
    source_url: str = Field(pattern=HTTPS)
    source_type: Literal["CFP_PUBLIC_SOURCE", "BRAND_CONFIRMED", "AUTHORIZED_PROMOTION"] = "CFP_PUBLIC_SOURCE"
    authorization_url: str | None = Field(default=None, pattern=HTTPS)


class EnterpriseIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    country_id: str = Field(pattern=r"^[0-9]{1,32}$")
    chapter: str = Field(default="7", pattern=CH)
    official_url: str = Field(pattern=HTTPS)
    source_url: str = Field(pattern=HTTPS)
    products: str = Field(default="", max_length=4000)
    capacity: str = Field(default="", max_length=4000)
    needs: str = Field(default="", max_length=4000)


class TopicIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    chapter: str = Field(pattern=CH)
    field: str = Field(default="", max_length=120)
    summary: str = Field(default="", max_length=4000)


class DatasetIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    kind: Literal["document", "curriculum", "dataset", "project"]
    url: str = Field(pattern=HTTPS)
    author: str = Field(min_length=2, max_length=200)
    version: str = Field(min_length=1, max_length=64)
    source_url: str = Field(pattern=HTTPS)
    access: Literal["public", "members"] = "public"
    chapter: str = Field(pattern=CH)
    topic_id: int | None = None


class PairIn(BaseModel):
    canonical_id: str = Field(pattern=r"^[0-9]{1,32}$")
    software: str = Field(min_length=2, max_length=160)
    lead_user_id: int


class TaskIn(BaseModel):
    pair_id: int
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=8000)
    acceptance: str = Field(min_length=3, max_length=4000)
    reviewer_id: int
    idempotency_key: str = Field(min_length=8, max_length=80, pattern=r"^[A-Za-z0-9._:-]+$")
    refs: list[str] = Field(default_factory=list, max_length=20)


class EvidenceIn(BaseModel):
    kind: Literal["url", "commit", "test_report", "pull_request", "document"]
    url: str = Field(pattern=HTTPS)
    sha: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{7,64}$")
    description: str = Field(min_length=3, max_length=4000)


class ReviewIn(BaseModel):
    decision: Literal["ACCEPT", "CHANGES_REQUESTED"]
    notes: str = Field(min_length=3, max_length=4000)


class TransitionIn(BaseModel):
    note: str = Field(default="", max_length=2000)


class LinkIn(BaseModel):
    from_ref: str = Field(max_length=64)
    to_ref: str = Field(max_length=64)
    relation: str = Field(min_length=2, max_length=40, pattern=r"^[a-z_]+$")


# ------------------------------------------------------------- router

def build_router(engine: Engine, registry: Registry, current_user, max_wip: int | None = None) -> APIRouter:
    r = APIRouter(prefix="/api/office", tags=["office"])
    wip_limit = max_wip if max_wip is not None else int(os.environ.get("CFP_OFFICE_MAX_WIP", "5"))

    def require_user(request: Request) -> dict:
        u = current_user(request)
        if not u:
            raise HTTPException(401, "Vui lòng đăng nhập.")
        return u

    def optional_user(request: Request) -> dict | None:
        return current_user(request)

    def roles(c: Connection, uid: int) -> set[str]:
        return set(c.execute(select(roles_t.c.role).where(roles_t.c.user_id == uid)).scalars())

    def audit(c: Connection, actor: int | None, action: str, ref: str, data: dict) -> None:
        c.execute(insert(audit_t).values(actor_id=actor, action=action, ref=ref,
                                         data=json.dumps(data, ensure_ascii=False, default=str)))

    def ref_exists(c: Connection, ref: str) -> bool:
        kind, _, val = ref.partition(":")
        if kind == "registry":
            return registry.get(val) is not None
        if kind not in REF_TABLES or not val:
            return False
        t, col = REF_TABLES[kind]
        if kind != "office":
            if not val.isdigit():
                return False
            val = int(val)
        return c.execute(select(col).where(col == val)).first() is not None

    def can_read_ref(c: Connection, ref: str, user: dict | None) -> bool:
        kind, _, value = ref.partition(":")
        if kind not in {"office", "pair", "task", "dataset"}:
            return True
        if kind != "office" and (not value.isascii() or not value.isdigit() or len(value) > 9):
            return False
        uid = user["id"] if user else None
        if uid is not None and "governance" in roles(c, uid):
            return True
        if kind == "dataset":
            d = c.execute(select(datasets_t).where(datasets_t.c.id == value)).mappings().first()
            return bool(d and (d["access"] == "public" or uid == d["created_by"]))
        if uid is None:
            return False
        if kind == "office":
            return is_maintainer(c, value, uid) or bool(c.execute(
                select(tasks_t.c.id).join(pairs_t, tasks_t.c.pair_id == pairs_t.c.id).where(
                    pairs_t.c.canonical_id == value,
                    or_(tasks_t.c.assignee_id == uid, tasks_t.c.reviewer_id == uid)
                )).first())
        if kind == "pair":
            p = c.execute(select(pairs_t).where(pairs_t.c.id == value)).mappings().first()
            return bool(p and (p["lead_user_id"] == uid or is_maintainer(c, p["canonical_id"], uid)))
        t = c.execute(select(tasks_t).where(tasks_t.c.id == value)).mappings().first()
        if not t:
            return False
        p = c.execute(select(pairs_t).where(pairs_t.c.id == t["pair_id"])).mappings().first()
        return uid in {t["assignee_id"], t["reviewer_id"]} or bool(p and is_maintainer(c, p["canonical_id"], uid))

    def link(c: Connection, actor: int, a: str, b: str, rel: str) -> None:
        if c.execute(select(links_t.c.id).where(links_t.c.from_ref == a, links_t.c.to_ref == b,
                                                links_t.c.relation == rel)).first():
            return
        c.execute(insert(links_t).values(from_ref=a, to_ref=b, relation=rel, created_by=actor))

    def is_maintainer(c: Connection, cid: str, uid: int) -> bool:
        return bool(c.execute(select(maintainers_t.c.user_id).where(
            maintainers_t.c.canonical_id == cid, maintainers_t.c.user_id == uid)).first())

    def conflict(msg: str):
        raise HTTPException(409, msg)

    # ---- taxonomy + registry (chỉ đọc)
    @r.get("/taxonomy")
    def taxonomy():
        return {"groups": GROUPS, "chapters": [{"id": k, "name": v, "group": group_of(k)["code"] if group_of(k) else None,
                                                "link": f"https://cfp.plus/{k}/"} for k, v in CHAPTERS.items()],
                "hub": {"id": "69", "link": "https://cfp.plus/69/"}, "cmp": {"id": "267", "link": "https://cfp.plus/267/"},
                "connections": CONNECTIONS}

    @r.get("/registry/{eid}")
    def registry_entity(eid: str):
        e = registry.get(eid)
        if not e:
            raise HTTPException(404, "ID không có trong Registry. API không cấp ID mới.")
        with engine.connect() as c:
            office = c.execute(select(offices_t.c.canonical_id).where(offices_t.c.canonical_id == eid)).first()
        return {"entity": e.public(), "chain": registry.chain(eid),
                "children": [registry.get(x).public() for x in e.children], "office": bool(office)}

    # ---- văn phòng SI AI
    @r.post("/offices", status_code=201)
    def create_office(data: OfficeIn, user=Depends(require_user)):
        e = registry.get(data.canonical_id)
        if not e:
            raise HTTPException(422, "canonical_id không có trong Registry. Không tự cấp ID.")
        if e.type not in {"ai", "registry_record"}:
            raise HTTPException(422, f"ID {e.id} là '{e.type}', không phải SI AI.")
        with engine.begin() as c:
            if "governance" not in roles(c, user["id"]):
                raise HTTPException(403, "Chỉ Human Governance được mở Văn Phòng (xác minh định danh trước khi ghi).")
            if c.execute(select(offices_t.c.canonical_id).where(offices_t.c.canonical_id == e.id)).first():
                conflict("Văn Phòng cho ID này đã tồn tại.")
            c.execute(insert(offices_t).values(canonical_id=e.id, display_name=e.name, platform=_clean(data.platform),
                                               specialties=data.specialties, capabilities=data.capabilities,
                                               limits=data.limits, verification="REGISTRY_LINKED_UNVERIFIED",
                                               created_by=user["id"]))
            c.execute(insert(maintainers_t).values(canonical_id=e.id, user_id=user["id"]))
            link(c, user["id"], f"office:{e.id}", f"registry:{e.id}", "profile_of")
            audit(c, user["id"], "office.create", f"office:{e.id}", data.model_dump())
        return office_view(e.id, user)

    @r.post("/offices/{cid}/maintainers/{uid}", status_code=201)
    def add_maintainer(cid: str, uid: int, user=Depends(require_user)):
        with engine.begin() as c:
            if "governance" not in roles(c, user["id"]):
                raise HTTPException(403, "Chỉ Human Governance cấp quyền Văn Phòng.")
            if not ref_exists(c, f"office:{cid}"):
                raise HTTPException(404, "Không có Văn Phòng.")
            if not is_maintainer(c, cid, uid):
                c.execute(insert(maintainers_t).values(canonical_id=cid, user_id=uid))
                audit(c, user["id"], "office.maintainer_add", f"office:{cid}", {"user_id": uid})
        return {"ok": True}

    @r.get("/offices/{cid}")
    def office_view(cid: str, user=Depends(optional_user)):
        with engine.connect() as c:
            o = c.execute(select(offices_t).where(offices_t.c.canonical_id == cid)).mappings().first()
            if not o:
                raise HTTPException(404, "Không có Văn Phòng cho ID này.")
            member = bool(user and (is_maintainer(c, cid, user["id"]) or "governance" in roles(c, user["id"])))
            assigned = bool(user and c.execute(select(tasks_t.c.id).join(pairs_t, tasks_t.c.pair_id == pairs_t.c.id).where(
                pairs_t.c.canonical_id == cid,
                or_(tasks_t.c.assignee_id == user["id"], tasks_t.c.reviewer_id == user["id"])
            )).first())
            if not member and not assigned:
                raise HTTPException(401 if not user else 403, "Văn Phòng yêu cầu quyền truy cập.")
            brand = c.execute(select(brand_t).where(brand_t.c.canonical_id == cid).order_by(brand_t.c.id)).mappings().all()
            pairs = c.execute(select(pairs_t).where(pairs_t.c.canonical_id == cid).order_by(pairs_t.c.id)).mappings().all()
            pair_ids = [p["id"] for p in pairs]
            tasks = c.execute(select(tasks_t).where(tasks_t.c.pair_id.in_(pair_ids)).order_by(tasks_t.c.id)).mappings().all() if pair_ids else []
            if not member:
                tasks = [t for t in tasks if user["id"] in {t["assignee_id"], t["reviewer_id"]}]
                pairs = [p for p in pairs if p["id"] in {t["pair_id"] for t in tasks}]
            tids = [t["id"] for t in tasks]
            ev = c.execute(select(evidence_t).where(evidence_t.c.task_id.in_(tids)).order_by(evidence_t.c.id)).mappings().all() if tids else []
            rv = c.execute(select(reviews_t).where(reviews_t.c.task_id.in_(tids)).order_by(reviews_t.c.id)).mappings().all() if tids else []
            hist = c.execute(select(task_events_t).where(task_events_t.c.task_id.in_(tids)).order_by(task_events_t.c.id)).mappings().all() if tids else []
            maint = c.execute(select(maintainers_t.c.user_id).where(maintainers_t.c.canonical_id == cid)).scalars().all()
        e = registry.get(cid)
        return {
            "office": _row(o), "registry_chain": registry.chain(cid), "taxonomy": {"group": group_of("6"), "chapter": {"id": "6", "name": CHAPTERS["6"]}},
            "maintainers": maint if member else [], "can_edit": bool(user and user["id"] in maint),
            "brand": [{**_row(b), "source_label": SOURCE_LABELS[b["source_type"]]} for b in brand],
            "pairs": [_row(p) for p in pairs],
            "tasks": [{**_row(t), "evidence": [_row(x) for x in ev if x["task_id"] == t["id"]],
                       "reviews": [_row(x) for x in rv if x["task_id"] == t["id"]],
                       "history": [_row(x) for x in hist if x["task_id"] == t["id"]]} for t in tasks],
            "links": links_of(f"office:{cid}", user), "public_link": f"https://cfp.plus/{cid}/",
            "developer": registry.get(e.parent_id).public() if e and e.parent_id and registry.get(e.parent_id) else None,
        }

    # ---- thương hiệu • sản phẩm • dịch vụ của chính SI AI / nhà phát triển
    @r.post("/offices/{cid}/brand", status_code=201)
    def add_brand(cid: str, data: BrandIn, user=Depends(require_user)):
        with engine.begin() as c:
            if not ref_exists(c, f"office:{cid}"):
                raise HTTPException(404, "Không có Văn Phòng.")
            rs = roles(c, user["id"])
            if not is_maintainer(c, cid, user["id"]) and "governance" not in rs:
                raise HTTPException(403, "Chỉ người duy trì Văn Phòng được thêm thương hiệu/sản phẩm.")
            if data.source_type != "CFP_PUBLIC_SOURCE":
                if "governance" not in rs:
                    raise HTTPException(403, "Chỉ Human Governance được gắn nhãn đã xác nhận/ủy quyền.")
                if not data.authorization_url:
                    raise HTTPException(422, "Nội dung xác nhận/ủy quyền phải có authorization_url làm bằng chứng.")
            try:
                with c.begin_nested():
                    bid = c.execute(insert(brand_t).values(canonical_id=cid, kind=data.kind, name=_clean(data.name),
                                                           name_key=_key(data.name), description=data.description,
                                                           url=data.url, source_type=data.source_type,
                                                           source_url=data.source_url, authorization_url=data.authorization_url,
                                                           created_by=user["id"]).returning(brand_t.c.id)).scalar_one()
            except IntegrityError:
                conflict("Mục thương hiệu này đã có (trùng tên + loại).")
            link(c, user["id"], f"brand:{bid}", f"office:{cid}", "offered_by")
            audit(c, user["id"], "brand.create", f"brand:{bid}", data.model_dump())
        return {"id": bid, "source_label": SOURCE_LABELS[data.source_type]}

    # ---- HSTDN • doanh nghiệp • giao thương
    @r.post("/enterprises", status_code=201)
    def add_enterprise(data: EnterpriseIn, user=Depends(require_user)):
        country = registry.get(data.country_id)
        if not country or country.type != "country":
            raise HTTPException(422, "country_id phải là Country ID đã có trong Registry.")
        with engine.begin() as c:
            try:
                with c.begin_nested():
                    eid = c.execute(insert(enterprises_t).values(
                        name=_clean(data.name), name_key=_key(data.name), country_id=data.country_id,
                        chapter=data.chapter, official_url=data.official_url, source_url=data.source_url,
                        products=data.products, capacity=data.capacity, needs=data.needs, created_by=user["id"])
                        .returning(enterprises_t.c.id)).scalar_one()
            except IntegrityError:
                conflict("Doanh nghiệp này đã có trong cùng quốc gia.")
            link(c, user["id"], f"enterprise:{eid}", f"registry:{data.country_id}", "located_in")
            audit(c, user["id"], "enterprise.create", f"enterprise:{eid}", data.model_dump())
        return {"id": eid, "status": "PROVISIONAL"}

    # ---- kho nghiên cứu
    @r.post("/topics", status_code=201)
    def add_topic(data: TopicIn, user=Depends(require_user)):
        with engine.begin() as c:
            try:
                with c.begin_nested():
                    tid = c.execute(insert(topics_t).values(title=_clean(data.title), title_key=_key(data.title),
                                                            chapter=data.chapter, field=data.field, summary=data.summary,
                                                            created_by=user["id"]).returning(topics_t.c.id)).scalar_one()
            except IntegrityError:
                conflict("Chủ đề này đã có trong cùng Chương.")
            audit(c, user["id"], "topic.create", f"topic:{tid}", data.model_dump())
        return {"id": tid}

    @r.post("/datasets", status_code=201)
    def add_dataset(data: DatasetIn, user=Depends(require_user)):
        with engine.begin() as c:
            if data.topic_id is not None and not ref_exists(c, f"topic:{data.topic_id}"):
                raise HTTPException(422, "topic_id không tồn tại.")
            try:
                with c.begin_nested():
                    did = c.execute(insert(datasets_t).values(**data.model_dump(), created_by=user["id"])
                                    .returning(datasets_t.c.id)).scalar_one()
            except IntegrityError:
                conflict("Tài liệu này (URL + phiên bản) đã có.")
            if data.topic_id is not None:
                link(c, user["id"], f"dataset:{did}", f"topic:{data.topic_id}", "supports")
            audit(c, user["id"], "dataset.create", f"dataset:{did}", data.model_dump())
        return {"id": did}

    @r.get("/datasets/{did}")
    def get_dataset(did: int, user=Depends(optional_user)):
        with engine.connect() as c:
            d = c.execute(select(datasets_t).where(datasets_t.c.id == did)).mappings().first()
        if not d:
            raise HTTPException(404, "Không có tài liệu.")
        with engine.connect() as c:
            if not can_read_ref(c, f"dataset:{did}", user):
                raise HTTPException(404, "Không có tài liệu.")
        return {**_row(d), "links": links_of(f"dataset:{did}", user)}

    @r.get("/enterprises/{eid}")
    def get_enterprise(eid: int, user=Depends(optional_user)):
        with engine.connect() as c:
            d = c.execute(select(enterprises_t).where(enterprises_t.c.id == eid)).mappings().first()
        if not d:
            raise HTTPException(404, "Không có doanh nghiệp.")
        return {**_row(d), "country": registry.get(d["country_id"]).public(), "links": links_of(f"enterprise:{eid}", user)}

    @r.get("/topics/{tid}")
    def get_topic(tid: int, user=Depends(optional_user)):
        with engine.connect() as c:
            d = c.execute(select(topics_t).where(topics_t.c.id == tid)).mappings().first()
        if not d:
            raise HTTPException(404, "Không có chủ đề.")
        return {**_row(d), "chapter_name": CHAPTERS[d["chapter"]], "group": group_of(d["chapter"]),
                "links": links_of(f"topic:{tid}", user)}

    # ---- Siêu Bộ Đôi + nhiệm vụ
    @r.post("/pairs", status_code=201)
    def add_pair(data: PairIn, user=Depends(require_user)):
        with engine.begin() as c:
            if not ref_exists(c, f"office:{data.canonical_id}"):
                raise HTTPException(404, "Không có Văn Phòng cho SI AI này.")
            if not is_maintainer(c, data.canonical_id, user["id"]) and "governance" not in roles(c, user["id"]):
                raise HTTPException(403, "Chỉ người duy trì Văn Phòng được lập Siêu Bộ Đôi.")
            try:
                with c.begin_nested():
                    pid = c.execute(insert(pairs_t).values(canonical_id=data.canonical_id, software=_clean(data.software),
                                                           software_key=_key(data.software), lead_user_id=data.lead_user_id,
                                                           created_by=user["id"]).returning(pairs_t.c.id)).scalar_one()
            except IntegrityError:
                conflict("Siêu Bộ Đôi này đã tồn tại.")
            link(c, user["id"], f"pair:{pid}", f"office:{data.canonical_id}", "works_in")
            audit(c, user["id"], "pair.create", f"pair:{pid}", data.model_dump())
        return {"id": pid}

    @r.post("/tasks", status_code=201)
    def add_task(data: TaskIn, user=Depends(require_user)):
        with engine.begin() as c:
            p = c.execute(select(pairs_t).where(pairs_t.c.id == data.pair_id)).mappings().first()
            if not p:
                raise HTTPException(404, "Không có Siêu Bộ Đôi.")
            if not is_maintainer(c, p["canonical_id"], user["id"]) and "governance" not in roles(c, user["id"]):
                raise HTTPException(403, "Chỉ người duy trì Văn Phòng hoặc Governance được giao việc.")
            prev = c.execute(select(tasks_t).where(tasks_t.c.idempotency_key == data.idempotency_key)).mappings().first()
            if prev:
                # Authorization must precede receipt lookup; replay must match the entire original request.
                original = c.execute(select(audit_t.c.data).where(
                    audit_t.c.ref == f"task:{prev['id']}", audit_t.c.action == "task.create"
                ).order_by(audit_t.c.id)).scalar()
                if prev["created_by"] != user["id"] or not original or json.loads(original) != data.model_dump():
                    conflict("idempotency_key đã dùng cho nhiệm vụ khác.")
                return {"id": prev["id"], "status": prev["status"], "duplicate": True}
            if data.reviewer_id == p["lead_user_id"]:
                raise HTTPException(422, "Reviewer phải độc lập với người thực thi.")
            if not roles(c, data.reviewer_id) & {"reviewer", "governance"}:
                raise HTTPException(422, "Reviewer phải có vai trò reviewer hoặc governance.")
            for ref in data.refs:
                if not ref_exists(c, ref):
                    raise HTTPException(422, f"Liên kết không tồn tại: {ref}")
            tid = c.execute(insert(tasks_t).values(pair_id=p["id"], title=_clean(data.title), description=data.description,
                                                   acceptance=data.acceptance, assignee_id=p["lead_user_id"],
                                                   reviewer_id=data.reviewer_id, status="QUEUED",
                                                   idempotency_key=data.idempotency_key, created_by=user["id"])
                            .returning(tasks_t.c.id)).scalar_one()
            c.execute(insert(task_events_t).values(task_id=tid, actor_id=user["id"], from_status=None, to_status="QUEUED"))
            link(c, user["id"], f"task:{tid}", f"pair:{p['id']}", "assigned_to")
            for ref in data.refs:
                link(c, user["id"], f"task:{tid}", ref, "uses")
            audit(c, user["id"], "task.create", f"task:{tid}", data.model_dump())
        return {"id": tid, "status": "QUEUED"}

    def load_task(c: Connection, tid: int) -> dict:
        t = c.execute(select(tasks_t).where(tasks_t.c.id == tid).with_for_update()).mappings().first()
        if not t:
            raise HTTPException(404, "Không có nhiệm vụ.")
        return dict(t)

    def move(c: Connection, t: dict, actor: int, to: str, note: str) -> None:
        n = c.execute(update(tasks_t).where(tasks_t.c.id == t["id"], tasks_t.c.status == t["status"])
                      .values(status=to, updated_at=func.now())).rowcount
        if n != 1:
            conflict("Trạng thái nhiệm vụ vừa thay đổi, hãy tải lại.")
        c.execute(insert(task_events_t).values(task_id=t["id"], actor_id=actor, from_status=t["status"], to_status=to, note=note))
        audit(c, actor, f"task.{to.lower()}", f"task:{t['id']}", {"from": t["status"], "to": to, "note": note})

    @r.post("/tasks/{tid}/ack")
    def ack(tid: int, data: TransitionIn, user=Depends(require_user)):
        return transition(tid, "ack", data, user)

    @r.post("/tasks/{tid}/start")
    def start(tid: int, data: TransitionIn, user=Depends(require_user)):
        return transition(tid, "start", data, user)

    @r.post("/tasks/{tid}/submit")
    def submit(tid: int, data: TransitionIn, user=Depends(require_user)):
        return transition(tid, "submit", data, user)

    def transition(tid: int, action: str, data: TransitionIn, user: dict):
        src, dst, who = TRANSITIONS[action]
        with engine.begin() as c:
            t = load_task(c, tid)
            if user["id"] != t["assignee_id"]:
                raise HTTPException(403, "Chỉ người thực thi của Siêu Bộ Đôi được thao tác bước này.")
            if t["status"] not in src:
                conflict(f"Không thể '{action}' khi nhiệm vụ đang {t['status']}.")
            if action == "start":
                running = c.execute(select(func.count()).select_from(tasks_t).where(tasks_t.c.status == "IN_PROGRESS")).scalar_one()
                if running >= wip_limit:
                    conflict(f"Đã đủ {wip_limit} nhiệm vụ đang thực thi song song (giới hạn P0).")
            if action == "submit":
                n = c.execute(select(func.count()).select_from(evidence_t).where(evidence_t.c.task_id == tid)).scalar_one()
                if not n:
                    raise HTTPException(422, "Cần ít nhất một Evidence trước khi chuyển Review.")
            move(c, t, user["id"], dst, data.note)
        return {"id": tid, "status": dst}

    @r.post("/tasks/{tid}/evidence", status_code=201)
    def add_evidence(tid: int, data: EvidenceIn, user=Depends(require_user)):
        with engine.begin() as c:
            t = load_task(c, tid)
            if user["id"] != t["assignee_id"]:
                raise HTTPException(403, "Chỉ người thực thi được nộp Evidence.")
            if t["status"] not in {"ACKED", "IN_PROGRESS"}:
                conflict(f"Không nộp Evidence khi nhiệm vụ đang {t['status']}.")
            try:
                with c.begin_nested():
                    eid = c.execute(insert(evidence_t).values(task_id=tid, kind=data.kind, url=data.url, sha=data.sha,
                                                              description=data.description, submitted_by=user["id"])
                                    .returning(evidence_t.c.id)).scalar_one()
            except IntegrityError:
                conflict("Evidence này đã được nộp.")
            audit(c, user["id"], "evidence.create", f"task:{tid}", data.model_dump())
        return {"id": eid}

    @r.post("/tasks/{tid}/review", status_code=201)
    def review(tid: int, data: ReviewIn, user=Depends(require_user)):
        with engine.begin() as c:
            t = load_task(c, tid)
            if user["id"] != t["reviewer_id"]:
                raise HTTPException(403, "Chỉ reviewer được chỉ định mới nghiệm thu.")
            if t["status"] != "IN_REVIEW":
                conflict(f"Nhiệm vụ đang {t['status']}, chưa sẵn sàng nghiệm thu.")
            c.execute(insert(reviews_t).values(task_id=tid, reviewer_id=user["id"], decision=data.decision, notes=data.notes))
            move(c, t, user["id"], "ACCEPTED" if data.decision == "ACCEPT" else "CHANGES_REQUESTED", data.notes)
        return {"id": tid, "status": "ACCEPTED" if data.decision == "ACCEPT" else "CHANGES_REQUESTED"}

    # ---- liên kết hai chiều + tìm kiếm + lịch sử
    def links_of(ref: str, user: dict | None = None) -> dict:
        with engine.connect() as c:
            if not can_read_ref(c, ref, user):
                raise HTTPException(404, "Không có liên kết.")
            out = c.execute(select(links_t.c.to_ref, links_t.c.relation).where(links_t.c.from_ref == ref)).all()
            inc = c.execute(select(links_t.c.from_ref, links_t.c.relation).where(links_t.c.to_ref == ref)).all()
            return {"outgoing": [{"ref": a, "relation": b} for a, b in out if can_read_ref(c, a, user)],
                    "incoming": [{"ref": a, "relation": b} for a, b in inc if can_read_ref(c, a, user)]}

    @r.post("/links", status_code=201)
    def add_link(data: LinkIn, user=Depends(require_user)):
        if data.from_ref == data.to_ref:
            raise HTTPException(422, "Không liên kết một mục với chính nó.")
        with engine.begin() as c:
            for ref in (data.from_ref, data.to_ref):
                if not ref_exists(c, ref):
                    raise HTTPException(422, f"Không tồn tại: {ref}")
            if not all(can_read_ref(c, ref, user) for ref in (data.from_ref, data.to_ref)):
                raise HTTPException(403, "Không có quyền liên kết các mục này.")
            link(c, user["id"], data.from_ref, data.to_ref, data.relation)
            audit(c, user["id"], "link.create", data.from_ref, data.model_dump())
        return {"ok": True}

    @r.get("/links")
    def get_links(ref: str, user=Depends(optional_user)):
        return links_of(ref, user)

    @r.get("/search")
    def search(q: str = "", chapter: str | None = None, user=Depends(optional_user)):
        q = q.strip()
        if len(q) < 2:
            raise HTTPException(422, "Từ khoá cần ít nhất 2 ký tự.")
        if chapter is not None and not re.fullmatch(CH, chapter):
            raise HTTPException(422, "Chương phải từ 0 đến 9.")
        like = f"%{q.casefold()}%"
        res = []
        with engine.connect() as c:
            for row in c.execute(select(offices_t.c.canonical_id, offices_t.c.display_name)
                                 .where(func.lower(offices_t.c.display_name).like(like))):
                if chapter in (None, "6"):
                    res.append({"ref": f"office:{row[0]}", "title": row[1], "chapter": "6"})
            for row in c.execute(select(brand_t.c.id, brand_t.c.name).where(brand_t.c.name_key.like(like))):
                if chapter in (None, "6"):
                    res.append({"ref": f"brand:{row[0]}", "title": row[1], "chapter": "6"})
            for t, title, key in ((enterprises_t, enterprises_t.c.name, enterprises_t.c.name_key),
                                  (topics_t, topics_t.c.title, topics_t.c.title_key)):
                cond = key.like(like)
                if chapter is not None:
                    cond = and_(cond, t.c.chapter == chapter)
                kind = "enterprise" if t is enterprises_t else "topic"
                for row in c.execute(select(t.c.id, title, t.c.chapter).where(cond)):
                    res.append({"ref": f"{kind}:{row[0]}", "title": row[1], "chapter": row[2]})
            cond = func.lower(datasets_t.c.title).like(like)
            if chapter is not None:
                cond = and_(cond, datasets_t.c.chapter == chapter)
            if not user or "governance" not in roles(c, user["id"]):
                cond = and_(cond, or_(datasets_t.c.access == "public", datasets_t.c.created_by == user["id"]) if user else datasets_t.c.access == "public")
            for row in c.execute(select(datasets_t.c.id, datasets_t.c.title, datasets_t.c.chapter).where(cond)):
                res.append({"ref": f"dataset:{row[0]}", "title": row[1], "chapter": row[2]})
        for e in registry.entities.values():
            if q.casefold() in e.name.casefold() and chapter in (None, "6", "9"):
                res.append({"ref": f"registry:{e.id}", "title": e.name, "chapter": "9" if e.type == "country" else "6"})
        return {"results": res[:100]}

    @r.get("/audit")
    def audit_log(ref: str, user=Depends(require_user)):
        with engine.connect() as c:
            if not roles(c, user["id"]) & {"governance", "reviewer"}:
                raise HTTPException(403, "Chỉ governance/reviewer xem nhật ký kiểm toán.")
            if not can_read_ref(c, ref, user):
                raise HTTPException(403, "Không có quyền đọc nhật ký của mục này.")
            rows = c.execute(select(audit_t).where(or_(audit_t.c.ref == ref)).order_by(audit_t.c.id)).mappings().all()
        return {"events": [_row(x) for x in rows]}

    return r


def _row(m) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(m).items()
            if not k.endswith("_key")}
