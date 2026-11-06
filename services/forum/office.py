"""CFP+ • Văn Phòng SI AI (Link Mẫu) • Siêu Bộ Đôi • HSTDN • Kho nghiên cứu • Nhiệm vụ • Evidence • Review.

Gắn vào service diễn đàn hiện hữu (dùng chung tài khoản, phiên, rate limit, CSRF).
Dữ liệu nằm ở kho riêng (CFP_OFFICE_DB) — không đọc/ghi database của hai diễn đàn.
Định danh chỉ tham chiếu Registry (chỉ đọc); không có API nào tạo Canonical ID.
"""
from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text as sql_text
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text, UniqueConstraint,
                        and_, func, insert, or_, select, update)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from services.forum.registry import CHAPTERS, CONNECTIONS, GROUPS, Registry, group_of

# Danh tính người gọi cho RLS theo người dùng (003_office_rls.sql). Middleware của app đặt giá trị này
# cho mỗi request; mọi giao dịch Văn Phòng gửi nó vào Postgres bằng set_config('cfp.user_id', …, true).
ACTOR: ContextVar[int | None] = ContextVar("cfp_office_actor", default=None)

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
                      Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                implicit_returning=False)  # RLS 003: người ghi không nhất thiết được đọc lại
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
                UniqueConstraint("from_ref", "to_ref", "relation"),
                implicit_returning=False)  # RLS 003: người ghi không nhất thiết được đọc lại
audit_t = Table("audit_log", md,
                Column("id", Integer, primary_key=True),
                Column("actor_id", Integer),
                Column("action", String(40), nullable=False),
                Column("ref", String(64), nullable=False),
                Column("data", Text, nullable=False),
                Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()),
                implicit_returning=False)  # RLS 003: người ghi không nhất thiết được đọc lại

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
BOARD_BUCKETS = ("QUEUED", "RUNNING", "IN_REVIEW", "BLOCKED", "REVIEWED")
BOARD_OF_STATUS = {"QUEUED": "QUEUED", "ACKED": "RUNNING", "IN_PROGRESS": "RUNNING", "IN_REVIEW": "IN_REVIEW",
                   "CHANGES_REQUESTED": "BLOCKED", "ACCEPTED": "REVIEWED", "CLOSED": "REVIEWED"}
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


class AnswerCheckIn(BaseModel):
    """Bản nháp trả lời khách của một Agent (vd. Meta Business Agent) — chỉ kiểm tra, KHÔNG gửi (AUTO REPLY HOLD)."""
    draft: str = Field(min_length=1, max_length=8000)
    question: str | None = Field(default=None, max_length=4000)
    agent: str | None = Field(default=None, max_length=80)


class LessonIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    chapter: str = Field(pattern=CH)          # 10 Chương 0–9 (không tạo ID số mới)
    summary: str = Field(min_length=10, max_length=4000)


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


class CloseIn(BaseModel):
    note: str = Field(min_length=3, max_length=2000)


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class DiscussionIn(BaseModel):
    forum: Literal["sieu-bo-doi", "si-ai-hstdn"]
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    hstdn: str | None = Field(default=None, max_length=200)
    country_id: str | None = Field(default=None, max_length=32)


class LinkIn(BaseModel):
    from_ref: str = Field(max_length=64)
    to_ref: str = Field(max_length=64)
    relation: str = Field(min_length=2, max_length=40, pattern=r"^[a-z_]+$")


# ------------------------------------------------------------- router

def build_router(engine: Engine, registry: Registry, current_user, max_wip: int | None = None,
                 forums: dict | None = None, catalog=None) -> APIRouter:
    """forums: cầu nối tới hai Diễn Đàn (kho riêng) — {"keys", "can_read", "create_post"}; None → tắt thảo luận."""
    r = APIRouter(prefix="/api/office", tags=["office"])
    is_pg = engine.dialect.name == "postgresql"

    def _bind_actor(c: Connection) -> None:
        if is_pg:
            uid = ACTOR.get()
            c.execute(sql_text("select set_config('cfp.user_id', :u, true)"), {"u": "" if uid is None else str(uid)})

    @contextmanager
    def _begin():
        with engine.begin() as c:
            _bind_actor(c)
            yield c

    @contextmanager
    def _connect():
        with engine.connect() as c:
            _bind_actor(c)
            yield c

    def rls_enabled() -> bool:
        if not is_pg:
            return False
        with engine.connect() as c:
            return bool(c.execute(sql_text("select to_regprocedure('cfp_office.in_progress_count()') is not null")).scalar())

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
        if kind == "catalog":  # catalog:<ID> — trang ID số đã xuất bản (Link Mẫu); không cấp ID mới
            return catalog is not None and val in catalog.items
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

    def link(c: Connection, actor: int, a: str, b: str, rel: str) -> None:
        if c.execute(select(links_t.c.id).where(links_t.c.from_ref == a, links_t.c.to_ref == b,
                                                links_t.c.relation == rel)).first():
            return
        try:  # dưới RLS, một liên kết trùng có thể bị ẩn với người gọi → bỏ qua thay vì lỗi 500
            with c.begin_nested():
                c.execute(insert(links_t).values(from_ref=a, to_ref=b, relation=rel, created_by=actor))
        except IntegrityError:
            pass

    def is_maintainer(c: Connection, cid: str, uid: int) -> bool:
        return bool(c.execute(select(maintainers_t.c.user_id).where(
            maintainers_t.c.canonical_id == cid, maintainers_t.c.user_id == uid)).first())

    def conflict(msg: str):
        raise HTTPException(409, msg)

    # ---- quyền theo đối tượng (mặc định từ chối) • SEC-P0-195-01/02/04
    def principal(c: Connection, user: dict | None) -> dict | None:
        if not user:
            return None
        maint = set(c.execute(select(maintainers_t.c.canonical_id).where(maintainers_t.c.user_id == user["id"])).scalars())
        return {"id": user["id"], "roles": roles(c, user["id"]), "maintains": maint}

    def is_staff(p: dict | None) -> bool:
        # SEC-P0-195-06 (quyền tối thiểu): chỉ governance xem toàn bộ. Vai trò reviewer chỉ thấy
        # nhiệm vụ mình được chỉ định review (qua reviewer_id), không thấy nhiệm vụ/tài liệu khác.
        return bool(p and "governance" in p["roles"])

    def task_office(c: Connection, t) -> str | None:
        return c.execute(select(pairs_t.c.canonical_id).where(pairs_t.c.id == t["pair_id"])).scalar()

    def task_visible(c: Connection, p: dict | None, t, office_id: str | None = None) -> bool:
        if not p:
            return False
        if is_staff(p) or p["id"] in (t["assignee_id"], t["reviewer_id"], t["created_by"]):
            return True
        return (office_id or task_office(c, t)) in p["maintains"]

    def dataset_visible(c: Connection, p: dict | None, d) -> bool:
        if d["access"] == "public":
            return True
        if not p:
            return False
        if p["id"] == d["created_by"] or is_staff(p):
            return True
        # Tài liệu nội bộ dùng trong một nhiệm vụ: người xem được nhiệm vụ đó thì xem được tài liệu.
        for (task_ref,) in c.execute(select(links_t.c.from_ref).where(links_t.c.to_ref == f"dataset:{d['id']}",
                                                                      links_t.c.from_ref.like("task:%"))):
            t = c.execute(select(tasks_t).where(tasks_t.c.id == int(task_ref.split(":")[1]))).mappings().first()
            if t and task_visible(c, p, t):
                return True
        return False

    def ref_visible(c: Connection, p: dict | None, ref: str) -> bool:
        kind, _, val = ref.partition(":")
        if kind == "task" and val.isdigit():
            t = c.execute(select(tasks_t).where(tasks_t.c.id == int(val))).mappings().first()
            return bool(t) and task_visible(c, p, t)
        if kind == "dataset" and val.isdigit():
            d = c.execute(select(datasets_t).where(datasets_t.c.id == int(val))).mappings().first()
            return bool(d) and dataset_visible(c, p, d)
        if kind == "forum":  # forum:<key>:<post_id> — chỉ người đọc được diễn đàn đó mới thấy
            key = val.partition(":")[0]
            return bool(forums) and forums["can_read"](key, p and {"id": p["id"]})
        return True

    def can_link_from(c: Connection, p: dict, ref: str) -> bool:
        if "governance" in p["roles"]:
            return True
        kind, _, val = ref.partition(":")
        if kind == "office":
            return val in p["maintains"]
        if not val.isdigit():
            return False
        val = int(val)
        if kind == "task":
            t = c.execute(select(tasks_t).where(tasks_t.c.id == val)).mappings().first()
            return bool(t) and (p["id"] in (t["assignee_id"], t["created_by"]) or task_office(c, t) in p["maintains"])
        if kind in ("brand", "pair"):
            t, col = REF_TABLES[kind]
            cid = c.execute(select(t.c.canonical_id).where(col == val)).scalar()
            return cid in p["maintains"]
        if kind in ("enterprise", "topic", "dataset"):
            t, col = REF_TABLES[kind]
            return c.execute(select(t.c.created_by).where(col == val)).scalar() == p["id"]
        return False

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
        with _connect() as c:
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
        with _begin() as c:
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
        with _begin() as c:
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
        with _connect() as c:
            o = c.execute(select(offices_t).where(offices_t.c.canonical_id == cid)).mappings().first()
            if not o:
                raise HTTPException(404, "Không có Văn Phòng cho ID này.")
            p = principal(c, user)
            brand = c.execute(select(brand_t).where(brand_t.c.canonical_id == cid).order_by(brand_t.c.id)).mappings().all()
            pairs = c.execute(select(pairs_t).where(pairs_t.c.canonical_id == cid).order_by(pairs_t.c.id)).mappings().all()
            pair_ids = [p["id"] for p in pairs]
            tasks = c.execute(select(tasks_t).where(tasks_t.c.pair_id.in_(pair_ids)).order_by(tasks_t.c.id)).mappings().all() if pair_ids else []
            tasks = [t for t in tasks if task_visible(c, p, t, cid)]  # khách/người ngoài: không thấy nhiệm vụ
            tids = [t["id"] for t in tasks]
            ev = c.execute(select(evidence_t).where(evidence_t.c.task_id.in_(tids)).order_by(evidence_t.c.id)).mappings().all() if tids else []
            rv = c.execute(select(reviews_t).where(reviews_t.c.task_id.in_(tids)).order_by(reviews_t.c.id)).mappings().all() if tids else []
            hist = c.execute(select(task_events_t).where(task_events_t.c.task_id.in_(tids)).order_by(task_events_t.c.id)).mappings().all() if tids else []
            maint = c.execute(select(maintainers_t.c.user_id).where(maintainers_t.c.canonical_id == cid)).scalars().all()
            disc = {t["id"]: discussions_of(c, t["id"], user) for t in tasks}
        e = registry.get(cid)
        insider = bool(p and (cid in p["maintains"] or "governance" in p["roles"]))
        public_office = {k: v for k, v in _row(o).items() if k != "created_by"}
        return {
            "office": public_office, "registry_chain": registry.chain(cid), "taxonomy": {"group": group_of("6"), "chapter": {"id": "6", "name": CHAPTERS["6"]}},
            "maintainers": maint if insider else None, "can_edit": insider,
            "visibility": "insider" if insider else ("participant" if tasks else "public"),
            "brand": [{k: v for k, v in {**_row(b), "source_label": SOURCE_LABELS[b["source_type"]]}.items() if k != "created_by"}
                      for b in brand],
            "pairs": [_row(x) if insider else {"id": x["id"], "canonical_id": x["canonical_id"], "software": x["software"]}
                      for x in pairs],
            "tasks": [{**_row(t), "can_close": bool(p and t["status"] == "ACCEPTED" and p["id"] != t["assignee_id"]
                                                    and (is_staff(p) or p["id"] == t["created_by"])),
                       "evidence": [_row(x) for x in ev if x["task_id"] == t["id"]],
                       "reviews": [_row(x) for x in rv if x["task_id"] == t["id"]],
                       "history": [_row(x) for x in hist if x["task_id"] == t["id"]],
                       "discussions": disc.get(t["id"], [])} for t in tasks],
            "links": links_of(f"office:{cid}", user), "public_link": f"https://cfp.plus/{cid}/",
            "developer": registry.get(e.parent_id).public() if e and e.parent_id and registry.get(e.parent_id) else None,
        }

    # ---- thương hiệu • sản phẩm • dịch vụ của chính SI AI / nhà phát triển
    @r.post("/offices/{cid}/brand", status_code=201)
    def add_brand(cid: str, data: BrandIn, user=Depends(require_user)):
        with _begin() as c:
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
        with _begin() as c:
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
        with _begin() as c:
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
        with _begin() as c:
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
        with _connect() as c:
            d = c.execute(select(datasets_t).where(datasets_t.c.id == did)).mappings().first()
        if not d:
            raise HTTPException(404, "Không có tài liệu.")
        if d["access"] == "members" and not user:
            raise HTTPException(401, "Tài liệu này chỉ dành cho thành viên đã đăng nhập.")
        with _connect() as c:
            if not dataset_visible(c, principal(c, user), d):
                raise HTTPException(403, "Tài liệu nội bộ: chỉ người tạo, người duy trì Văn Phòng hoặc governance/reviewer.")
        return {**_row(d), "links": links_of(f"dataset:{did}", user)}

    @r.get("/enterprises/{eid}")
    def get_enterprise(eid: int, user=Depends(optional_user)):
        with _connect() as c:
            d = c.execute(select(enterprises_t).where(enterprises_t.c.id == eid)).mappings().first()
        if not d:
            raise HTTPException(404, "Không có doanh nghiệp.")
        return {**_row(d), "country": registry.get(d["country_id"]).public(), "links": links_of(f"enterprise:{eid}", user)}

    @r.get("/topics/{tid}")
    def get_topic(tid: int, user=Depends(optional_user)):
        with _connect() as c:
            d = c.execute(select(topics_t).where(topics_t.c.id == tid)).mappings().first()
        if not d:
            raise HTTPException(404, "Không có chủ đề.")
        return {**_row(d), "chapter_name": CHAPTERS[d["chapter"]], "group": group_of(d["chapter"]),
                "links": links_of(f"topic:{tid}", user)}

    # ---- Siêu Bộ Đôi + nhiệm vụ
    @r.post("/pairs", status_code=201)
    def add_pair(data: PairIn, user=Depends(require_user)):
        with _begin() as c:
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

    def same_task_request(c: Connection, prev, data: TaskIn, uid: int) -> bool:
        if not prev or prev["created_by"] != uid:
            return False
        original = c.execute(select(audit_t.c.data).where(
            audit_t.c.ref == f"task:{prev['id']}", audit_t.c.action == "task.create"
        ).order_by(audit_t.c.id)).scalar()
        return bool(original) and json.loads(original) == data.model_dump()

    @r.post("/tasks", status_code=201)
    def add_task(data: TaskIn, user=Depends(require_user)):
        with _begin() as c:
            # Kiểm tra quyền TRƯỚC khi tra idempotency_key (SEC-P0-195-02).
            p = c.execute(select(pairs_t).where(pairs_t.c.id == data.pair_id)).mappings().first()
            if not p:
                raise HTTPException(404, "Không có Siêu Bộ Đôi.")
            if not is_maintainer(c, p["canonical_id"], user["id"]) and "governance" not in roles(c, user["id"]):
                raise HTTPException(403, "Chỉ người duy trì Văn Phòng hoặc Governance được giao việc.")
            prev = c.execute(select(tasks_t).where(tasks_t.c.idempotency_key == data.idempotency_key)).mappings().first()
            if prev:  # chống tạo trùng khi chính người đó gửi lại; không lộ thông tin cho người khác
                if not same_task_request(c, prev, data, user["id"]):
                    conflict("idempotency_key không dùng được, hãy tạo khoá mới.")
                return {"id": prev["id"], "status": prev["status"], "duplicate": True}
            if data.reviewer_id == p["lead_user_id"]:
                raise HTTPException(422, "Reviewer phải độc lập với người thực thi.")
            if not roles(c, data.reviewer_id) & {"reviewer", "governance"}:
                raise HTTPException(422, "Reviewer phải có vai trò reviewer hoặc governance.")
            pr = principal(c, user)
            for ref in data.refs:
                if not ref_exists(c, ref) or not ref_visible(c, pr, ref):
                    raise HTTPException(422, f"Liên kết không tồn tại: {ref}")
            try:
                with c.begin_nested():
                    tid = c.execute(insert(tasks_t).values(
                        pair_id=p["id"], title=_clean(data.title), description=data.description,
                        acceptance=data.acceptance, assignee_id=p["lead_user_id"], reviewer_id=data.reviewer_id,
                        status="QUEUED", idempotency_key=data.idempotency_key, created_by=user["id"])
                        .returning(tasks_t.c.id)).scalar_one()
            except IntegrityError:
                # Hai request cùng khoá chạy đồng thời: request thua nhận kết quả như gửi lại, không lỗi 500.
                prev = c.execute(select(tasks_t).where(tasks_t.c.idempotency_key == data.idempotency_key)).mappings().first()
                if same_task_request(c, prev, data, user["id"]):
                    return {"id": prev["id"], "status": prev["status"], "duplicate": True}
                conflict("idempotency_key không dùng được, hãy tạo khoá mới.")
            c.execute(insert(task_events_t).values(task_id=tid, actor_id=user["id"], from_status=None, to_status="QUEUED"))
            link(c, user["id"], f"task:{tid}", f"pair:{p['id']}", "assigned_to")
            for ref in data.refs:
                link(c, user["id"], f"task:{tid}", ref, "uses")
            audit(c, user["id"], "task.create", f"task:{tid}", data.model_dump())
        return {"id": tid, "status": "QUEUED"}

    def load_task(c: Connection, tid: int, lock: bool = True) -> dict:
        # RLS 003: FOR UPDATE còn đòi policy UPDATE → chỉ khoá khi người gọi được cập nhật (người thực thi/reviewer).
        q = select(tasks_t).where(tasks_t.c.id == tid)
        t = c.execute(q.with_for_update() if lock else q).mappings().first()
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
        with _begin() as c:
            t = load_task(c, tid)
            if user["id"] != t["assignee_id"]:
                raise HTTPException(403, "Chỉ người thực thi của Siêu Bộ Đôi được thao tác bước này.")
            if t["status"] not in src:
                conflict(f"Không thể '{action}' khi nhiệm vụ đang {t['status']}.")
            if action == "start":
                if rls_enabled():  # 003: RLS thu hẹp theo người dùng → đếm toàn cục qua hàm SECURITY DEFINER
                    running = c.execute(sql_text("select cfp_office.in_progress_count()")).scalar_one()
                else:
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
        with _begin() as c:
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
        with _begin() as c:
            t = load_task(c, tid)
            if user["id"] != t["reviewer_id"]:
                raise HTTPException(403, "Chỉ reviewer được chỉ định mới nghiệm thu.")
            if t["status"] != "IN_REVIEW":
                conflict(f"Nhiệm vụ đang {t['status']}, chưa sẵn sàng nghiệm thu.")
            c.execute(insert(reviews_t).values(task_id=tid, reviewer_id=user["id"], decision=data.decision, notes=data.notes))
            move(c, t, user["id"], "ACCEPTED" if data.decision == "ACCEPT" else "CHANGES_REQUESTED", data.notes)
        return {"id": tid, "status": "ACCEPTED" if data.decision == "ACCEPT" else "CHANGES_REQUESTED"}

    @r.post("/tasks/{tid}/close")
    def close(tid: int, data: CloseIn, user=Depends(require_user)):
        """Closure sau Independent Review: governance hoặc người giao việc, không phải người thực thi."""
        with _begin() as c:
            t = load_task(c, tid, lock=False)  # move() cập nhật có điều kiện trạng thái
            p = principal(c, user)
            if not task_visible(c, p, t):
                raise HTTPException(404, "Không có nhiệm vụ.")
            if user["id"] == t["assignee_id"] or not (is_staff(p) or user["id"] == t["created_by"]):
                raise HTTPException(403, "Closure: Governance hoặc người giao việc (không phải người thực thi).")
            if t["status"] != "ACCEPTED":
                conflict(f"Chỉ đóng nhiệm vụ đã ACCEPTED (hiện {t['status']}).")
            accepted = c.execute(select(func.count()).select_from(reviews_t).where(
                reviews_t.c.task_id == tid, reviews_t.c.reviewer_id == t["reviewer_id"],
                reviews_t.c.decision == "ACCEPT")).scalar_one()
            if not accepted:
                conflict("Thiếu Review ACCEPT của reviewer được chỉ định.")
            move(c, t, user["id"], "CLOSED", data.note)
        return {"id": tid, "status": "CLOSED"}

    @r.post("/tasks/{tid}/lessons", status_code=201)
    def add_lesson(tid: int, data: LessonIn, user=Depends(require_user)):
        """Vòng khép kín: sau nghiệm thu + Closure, người tham gia ghi tri thức/bài học (chủ đề nghiên cứu theo Chương)
        liên kết với nhiệm vụ; nhiệm vụ tiếp theo tham chiếu task:<id> + topic:<bài học>."""
        with _begin() as c:
            t = load_task(c, tid, lock=False)
            p = principal(c, user)
            if not task_visible(c, p, t):
                raise HTTPException(404, "Không có nhiệm vụ.")
            if t["status"] != "CLOSED":
                conflict(f"Bài học ghi sau khi nghiệm thu và đóng nhiệm vụ (hiện {t['status']}).")
            try:
                with c.begin_nested():
                    lid = c.execute(insert(topics_t).values(
                        title=_clean(data.title), title_key=_key(data.title), chapter=data.chapter, field="lesson",
                        summary=data.summary, created_by=user["id"]).returning(topics_t.c.id)).scalar_one()
            except IntegrityError:
                conflict("Bài học/chủ đề này đã có trong cùng Chương.")
            link(c, user["id"], f"task:{tid}", f"topic:{lid}", "lesson")
            audit(c, user["id"], "task.lesson", f"task:{tid}", {"topic_id": lid, "chapter": data.chapter})
        return {"task_id": tid, "topic_id": lid, "ref": f"topic:{lid}"}

    from services.forum.agents import load_agents, public_view, run_tests
    agents = load_agents()

    def agent_cfg(slug: str) -> dict:
        if slug not in agents:
            raise HTTPException(404, "Chưa có cấu hình Agent này.")
        return agents[slug]

    @r.get("/agents")
    def agents_list():
        """Agent bên ngoài đang ĐÀO TẠO trong sandbox (không phải danh sách đã nghiệm thu)."""
        return {"agents": [{k: a[k] for k in ("slug", "name", "developer", "canonical_id", "stage", "flags")}
                           for a in agents.values()]}

    @r.get("/agents/{slug}")
    def agent_detail(slug: str):
        return public_view(agent_cfg(slug), catalog)

    @r.post("/agents/{slug}/test-runs", status_code=201)
    def agent_test_run(slug: str, user=Depends(require_user)):
        """Chạy bộ tình huống tư vấn qua Siêu Phần Mềm giám sát; kết quả dùng làm Evidence (test_report)."""
        run = run_tests(agent_cfg(slug), catalog)
        with _begin() as c:
            audit(c, user["id"], "agent.test_run", f"agent:{slug}",
                  {"sha": run["sha"], "passed": run["passed"], "failed": run["failed"], "config": run["config_version"]})
        return run

    @r.get("/agents/{slug}/test-runs/{sha}")
    def agent_test_run_get(slug: str, sha: str):
        """Evidence URL: tính lại từ nguồn hiện hành; khác sha → 409 (Evidence đã cũ, cần chạy lại)."""
        run = run_tests(agent_cfg(slug), catalog)
        if run["sha"] != sha:
            raise HTTPException(409, f"Kết quả {sha} không còn khớp nguồn/cấu hình hiện hành (hiện {run['sha']}) — chạy lại.")
        return run

    @r.post("/answer-check")
    def answer_check(data: AnswerCheckIn, user=Depends(require_user)):
        """Siêu Phần Mềm giám sát: kiểm tra nguồn/ID, tuyên bố chưa kiểm chứng, cam kết, dữ liệu nhạy cảm.
        Luôn auto_reply=HOLD. Audit chỉ lưu verdict + mã lỗi + sha256 (không lưu nội dung có thể chứa dữ liệu khách)."""
        from services.forum.answer_guard import check_answer
        res = check_answer(data.draft, catalog, data.question)
        with _begin() as c:
            audit(c, user["id"], "answer.check", f"agent:{_clean(data.agent or 'unspecified')}",
                  {"verdict": res["verdict"], "codes": sorted({f["code"] for f in res["findings"]}),
                   "draft_sha256": res["draft_sha256"], "citations": [x["id"] for x in res["citations"]]})
        return res

    @r.get("/tasks/{tid}/loop")
    def task_loop(tid: int, user=Depends(require_user)):
        """Vòng khép kín của MỘT nhiệm vụ, chỉ từ dữ liệu thật: HUB 69 → CMP 267 → Văn Phòng → Diễn Đàn →
        Siêu Bộ Đôi thực thi → Evidence → Review độc lập → nghiệm thu → Closure → bài học → nhiệm vụ tiếp theo."""
        with _connect() as c:
            t = c.execute(select(tasks_t).where(tasks_t.c.id == tid)).mappings().first()
            p = principal(c, user)
            if not t or not task_visible(c, p, t):
                raise HTTPException(404, "Không có nhiệm vụ.")
            pair = c.execute(select(pairs_t).where(pairs_t.c.id == t["pair_id"])).mappings().first()
            ev = c.execute(select(task_events_t.c.to_status).where(task_events_t.c.task_id == tid)).scalars().all()
            n_ev = c.execute(select(func.count()).select_from(evidence_t).where(evidence_t.c.task_id == tid)).scalar_one()
            rv = c.execute(select(reviews_t).where(reviews_t.c.task_id == tid).order_by(reviews_t.c.id)).mappings().all()
            lessons = c.execute(select(links_t.c.to_ref).where(links_t.c.from_ref == f"task:{tid}",
                                                              links_t.c.relation == "lesson")).scalars().all()
            nxt = c.execute(select(links_t.c.from_ref).where(links_t.c.to_ref == f"task:{tid}",
                                                            links_t.c.from_ref.like("task:%"))).scalars().all()
            nxt = [r_ for r_ in nxt if ref_visible(c, p, r_)]
            disc = discussions_of(c, tid, user)
        last = rv[-1] if rv else None
        independent = bool(last and last["decision"] == "ACCEPT" and last["reviewer_id"] == t["reviewer_id"]
                           and last["reviewer_id"] != t["assignee_id"])
        office = pair["canonical_id"] if pair else None
        stages = [
            ("hub69", "HUB 69", True, {"url": "/69/"}),
            ("cmp267", "CMP 267 • điều phối", True, {"url": "/267/"}),
            ("office", "Văn Phòng SI AI", bool(office), {"canonical_id": office, "url": f"/_internal/office/{office}/"}),
            ("discussion", "Thảo luận Diễn Đàn", bool(disc), {"posts": disc}),
            ("pair", "Siêu Bộ Đôi (SI AI + Siêu Phần Mềm)", bool(pair),
             {"pair_id": t["pair_id"], "software": pair["software"] if pair else None}),
            ("execution", "Nhận việc (ACK) → thực thi", "ACKED" in ev and "IN_PROGRESS" in ev,
             {"owner_id": t["assignee_id"]}),
            ("evidence", "Evidence", n_ev > 0, {"count": n_ev}),
            ("review", "Review độc lập (SecuritySI/ReviewSI)", independent,
             {"reviewer_id": t["reviewer_id"], "decision": last["decision"] if last else None}),
            ("acceptance", "Nghiệm thu", t["status"] in ("ACCEPTED", "CLOSED"), {"status": t["status"]}),
            ("closure", "Closure", t["status"] == "CLOSED", {}),
            ("lesson", "Tri thức • bài học", bool(lessons), {"refs": lessons}),
            ("next", "Quay lại Văn Phòng • nhiệm vụ tiếp theo", bool(nxt), {"refs": nxt}),
        ]
        out = [{"key": k, "label": lb, "done": d, **({"detail": det} if det else {})} for k, lb, d, det in stages]
        return {"task_id": tid, "status": t["status"], "owner_id": t["assignee_id"], "reviewer_id": t["reviewer_id"],
                "stages": out, "closed_loop": all(x["done"] for x in out),
                "next_stage": next((x["key"] for x in out if not x["done"]), None)}

    def discussions_of(c: Connection, tid: int, user: dict | None) -> list[dict]:
        if not forums:
            return []
        rows = c.execute(select(links_t.c.to_ref).where(links_t.c.from_ref == f"task:{tid}",
                                                        links_t.c.relation == "discussion").order_by(links_t.c.id)).scalars().all()
        out = []
        for ref in rows:
            _, key, pid = ref.split(":", 2)
            if forums["can_read"](key, user):
                out.append({"forum": key, "post_id": int(pid), "ref": ref, "url": f"/_internal/forum/{key}/#post-{pid}"})
        return out

    @r.post("/tasks/{tid}/discussions", status_code=201)
    def open_discussion(tid: int, data: DiscussionIn, user=Depends(require_user)):
        """Mở thảo luận ở đúng Diễn Đàn cho nhiệm vụ: bài tạo theo quy tắc của diễn đàn đó + liên kết hai chiều."""
        if not forums or data.forum not in forums["keys"]:
            raise HTTPException(404, "Không có diễn đàn này.")
        with _connect() as c:
            t = load_task(c, tid, lock=False)
            if not task_visible(c, principal(c, user), t):
                raise HTTPException(404, "Không có nhiệm vụ.")
            if t["status"] == "CLOSED":
                conflict("Nhiệm vụ đã đóng.")
        # Diễn đàn tự kiểm: thành viên active của ĐÚNG diễn đàn, trường HSTDN… (kho riêng, không dùng chung giao dịch)
        post = forums["create_post"](data.forum, data.model_dump(exclude={"forum"}), user)
        ref = f"forum:{data.forum}:{post['id']}"
        with _begin() as c:
            link(c, user["id"], f"task:{tid}", ref, "discussion")
            audit(c, user["id"], "task.discussion", f"task:{tid}", {"forum": data.forum, "post_id": post["id"]})
        return {"task_id": tid, "forum": data.forum, "post_id": post["id"], "ref": ref,
                "url": f"/_internal/forum/{data.forum}/#post-{post['id']}"}

    @r.get("/forum-links")
    def forum_links(forum: str, user=Depends(optional_user)):
        """Liên kết ngược bài diễn đàn → nhiệm vụ; chỉ trả nhiệm vụ người xem được phép thấy."""
        if not forums or forum not in forums["keys"] or not forums["can_read"](forum, user):
            return {"links": []}
        with _connect() as c:
            p = principal(c, user)
            rows = c.execute(select(links_t.c.from_ref, links_t.c.to_ref).where(
                links_t.c.relation == "discussion", links_t.c.to_ref.like(f"forum:{forum}:%"))).all()
            out = []
            for fr, to in rows:
                if not fr.startswith("task:"):
                    continue
                t = c.execute(select(tasks_t).where(tasks_t.c.id == int(fr[5:]))).mappings().first()
                if t and task_visible(c, p, t):
                    out.append({"post_id": int(to.rsplit(":", 1)[1]), "task_id": t["id"], "office_id": task_office(c, t)})
        return {"links": out}

    @r.post("/tasks/{tid}/comments", status_code=201)
    def comment(tid: int, data: CommentIn, user=Depends(require_user)):
        """Trao đổi trong nhiệm vụ: ghi vào task_events (to_status=COMMENT), không đổi trạng thái."""
        body = data.body.strip()
        if not body:
            raise HTTPException(422, "Nội dung trao đổi trống.")
        with _begin() as c:
            t = load_task(c, tid, lock=False)
            if not task_visible(c, principal(c, user), t):
                raise HTTPException(404, "Không có nhiệm vụ.")  # không lộ sự tồn tại cho người ngoài
            c.execute(insert(task_events_t).values(task_id=tid, actor_id=user["id"], from_status=t["status"],
                                                   to_status="COMMENT", note=body))
            audit(c, user["id"], "task.comment", f"task:{tid}", {"status": t["status"], "length": len(body)})
        return {"id": tid, "ok": True}

    # ---- liên kết hai chiều + tìm kiếm + lịch sử
    def links_of(ref: str, user: dict | None) -> dict:
        with _connect() as c:
            p = principal(c, user)
            if not ref_visible(c, p, ref):
                return {"outgoing": [], "incoming": []}
            out = c.execute(select(links_t.c.to_ref, links_t.c.relation).where(links_t.c.from_ref == ref)).all()
            inc = c.execute(select(links_t.c.from_ref, links_t.c.relation).where(links_t.c.to_ref == ref)).all()
            return {"outgoing": [resolved({"ref": a, "relation": b}) for a, b in out if ref_visible(c, p, a)],
                    "incoming": [resolved({"ref": a, "relation": b}) for a, b in inc if ref_visible(c, p, a)]}

    def resolved(x: dict) -> dict:
        """Tham chiếu tới bản gốc: gắn tiêu đề/version/URL HIỆN HÀNH lúc đọc (link không lưu bản sao)."""
        cur = catalog.resolve(x["ref"]) if catalog is not None else None
        return {**x, "source": cur} if cur else x

    @r.post("/links", status_code=201)
    def add_link(data: LinkIn, user=Depends(require_user)):
        if data.from_ref == data.to_ref:
            raise HTTPException(422, "Không liên kết một mục với chính nó.")
        with _begin() as c:
            pr = principal(c, user)
            for ref in (data.from_ref, data.to_ref):
                if not ref_exists(c, ref) or not ref_visible(c, pr, ref):
                    raise HTTPException(422, f"Không tồn tại: {ref}")
            if not can_link_from(c, pr, data.from_ref):
                raise HTTPException(403, "Chỉ chủ sở hữu/người duy trì mục nguồn hoặc governance được tạo liên kết.")
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
        with _connect() as c:
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
            pr = principal(c, user)
            for row in c.execute(select(datasets_t).where(cond)).mappings():
                if dataset_visible(c, pr, row):
                    res.append({"ref": f"dataset:{row['id']}", "title": row["title"], "chapter": row["chapter"]})
        for e in registry.entities.values():
            if q.casefold() in e.name.casefold() and chapter in (None, "6", "9"):
                res.append({"ref": f"registry:{e.id}", "title": e.name, "chapter": "9" if e.type == "country" else "6"})
        return {"results": res[:100]}

    @r.get("/board")
    def board(user=Depends(optional_user)):
        """Bảng điều phối theo quyền người xem: RUNNING / IN_REVIEW / BLOCKED / REVIEWED.

        REVIEWED chỉ được tính khi có execution evidence (≥1 Evidence) VÀ Review ACCEPT của đúng
        reviewer độc lập (≠ người thực thi); thiếu một trong hai → BLOCKED kèm lý do. Khách: rỗng.
        """
        with _connect() as c:
            p = principal(c, user)
            if not p:
                return {"viewer": "guest", "counts": {b: 0 for b in BOARD_BUCKETS}, "tasks": []}
            rows = c.execute(select(tasks_t, pairs_t.c.canonical_id).join(pairs_t, pairs_t.c.id == tasks_t.c.pair_id)
                             .order_by(tasks_t.c.id)).mappings().all()
            rows = [t for t in rows if task_visible(c, p, t, t["canonical_id"])]
            tids = [t["id"] for t in rows]
            ev = dict(c.execute(select(evidence_t.c.task_id, func.count()).where(evidence_t.c.task_id.in_(tids))
                                .group_by(evidence_t.c.task_id)).all()) if tids else {}
            rv = c.execute(select(reviews_t).where(reviews_t.c.task_id.in_(tids))
                           .order_by(reviews_t.c.id)).mappings().all() if tids else []
        last_review = {x["task_id"]: x for x in rv}
        out = []
        for t in rows:
            n_ev, lr = ev.get(t["id"], 0), last_review.get(t["id"])
            bucket, reason = BOARD_OF_STATUS[t["status"]], None
            if t["status"] == "CHANGES_REQUESTED":
                reason = "Reviewer yêu cầu chỉnh sửa"
            if bucket == "REVIEWED":
                independent = bool(lr and lr["decision"] == "ACCEPT" and lr["reviewer_id"] == t["reviewer_id"]
                                   and lr["reviewer_id"] != t["assignee_id"])
                if not n_ev or not independent:
                    bucket, reason = "BLOCKED", ("Thiếu execution evidence" if not n_ev else "Thiếu Review độc lập hợp lệ")
            out.append({"id": t["id"], "title": t["title"], "office_id": t["canonical_id"], "status": t["status"],
                        "bucket": bucket, "reason": reason, "evidence": n_ev,
                        "review": {"decision": lr["decision"], "at": (lr["at"].isoformat() if hasattr(lr["at"], "isoformat") else lr["at"])} if lr else None,
                        "updated_at": _row({"u": t["updated_at"]})["u"],
                        "url": f"/_internal/office/{t['canonical_id']}/#task:{t['id']}"})
        counts = {b: sum(1 for x in out if x["bucket"] == b) for b in BOARD_BUCKETS}
        return {"viewer": "governance" if is_staff(p) else "participant", "counts": counts, "tasks": out}

    @r.get("/audit")
    def audit_log(ref: str, user=Depends(require_user)):
        with _connect() as c:
            pr = principal(c, user)
            kind, _, val = ref.partition(":")
            allowed = is_staff(pr) or (kind == "task" and val.isdigit() and ref_visible(c, pr, ref))
            if not allowed:
                raise HTTPException(403, "Nhật ký kiểm toán: governance, hoặc người tham gia/maintainer của đúng nhiệm vụ.")
            rows = c.execute(select(audit_t).where(audit_t.c.ref == ref).order_by(audit_t.c.id)).mappings().all()
        return {"events": [_row(x) for x in rows]}

    return r


def _row(m) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(m).items()
            if not k.endswith("_key")}
