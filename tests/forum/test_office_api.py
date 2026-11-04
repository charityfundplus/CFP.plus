"""Văn Phòng SI AI • unit + integration trên database thật.

Chế độ Postgres (giống Supabase: schemas_up.sql của #193 + 002_office.sql):
  CFP_FORUM_TEST_AUTH_DB, CFP_FORUM_TEST_DB_SIEU_BO_DOI, CFP_FORUM_TEST_DB_SI_AI_HSTDN,
  CFP_OFFICE_TEST_DB, CFP_FORUM_TEST_ADMIN_DB
Không có → SQLite tạm (bỏ qua các test quyền DB).
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert, text

from services.forum.app import Stores, create_app
from services.forum.office import roles_t
from services.forum.registry import Registry
from tests.forum.pgschema import schema_of, truncate_all
from tests.forum.office_flow import CID, H, SAMPLE, ok, register, run_flow


@pytest.fixture(scope="module")
def urls(tmp_path_factory):
    os.environ.update(CFP_FORUM_RL_AUTH_PER_MIN="1000", CFP_FORUM_RL_WRITE_PER_MIN="1000", CFP_FORUM_COOKIE_SECURE="0")
    env = {"auth": os.environ.get("CFP_FORUM_TEST_AUTH_DB"), "sieu-bo-doi": os.environ.get("CFP_FORUM_TEST_DB_SIEU_BO_DOI"),
           "si-ai-hstdn": os.environ.get("CFP_FORUM_TEST_DB_SI_AI_HSTDN"), "office": os.environ.get("CFP_OFFICE_TEST_DB")}
    admin = os.environ.get("CFP_FORUM_TEST_ADMIN_DB")
    if all(env.values()) and admin:
        truncate_all(admin, list(env.values()))
        env["admin"] = admin
        return env
    d = tmp_path_factory.mktemp("office")
    return {k: f"sqlite:///{d / (k + '.db')}" for k in env}


def stores(urls):
    return Stores(urls["auth"], {"sieu-bo-doi": urls["sieu-bo-doi"], "si-ai-hstdn": urls["si-ai-hstdn"]}, urls["office"])


def client(st):
    return TestClient(create_app(st))


def grant(urls, st, uid, role):
    eng = create_engine(urls["admin"], connect_args={"options": "-c search_path=cfp_office"}) if "admin" in urls else st.office
    with eng.begin() as c:
        if "admin" in urls:
            c.exec_driver_sql("SET LOCAL ROLE office_governance")
        c.execute(insert(roles_t).values(user_id=uid, role=role))


@pytest.fixture(scope="module")
def world(urls):
    st = stores(urls)
    gov, lead, rev, other = client(st), client(st), client(st), client(st)
    ids = {"gov": register(gov, f"gov{uuid.uuid4().hex[:6]}@example.org", "Governance"),
           "lead": register(lead, f"lead{uuid.uuid4().hex[:6]}@example.org", "Claude Lead"),
           "rev": register(rev, f"rev{uuid.uuid4().hex[:6]}@example.org", "ReviewSI"),
           "other": register(other, f"oth{uuid.uuid4().hex[:6]}@example.org", "Người Khác")}
    grant(urls, st, ids["gov"], "governance")
    grant(urls, st, ids["rev"], "reviewer")
    out = run_flow(gov, lead, rev, ids["lead"], ids["rev"])
    return {"st": st, "gov": gov, "lead": lead, "rev": rev, "other": other, "ids": ids, "out": out}


# ---------- unit: Registry chỉ đọc

def test_registry_chain_and_no_invented_ids():
    reg = Registry()
    assert [e["id"] for e in reg.chain("691121")] == ["911", "6911", "69112", "691121"]
    assert reg.get("999999999") is None
    assert reg.get("691183").type == "registry_record"  # hồ sơ md có sẵn, không suy diễn thêm


# ---------- integration: luồng xuyên suốt

def test_full_flow_and_reload_after_restart(world, urls):
    st2 = stores(urls)  # engine mới = khởi động lại
    c = client(st2)
    c.cookies = world["lead"].cookies  # người thực thi (maintainer) xem nhiệm vụ; khách không thấy (SEC-01)
    d = ok(c.get(f"/api/office/offices/{CID}"), 200)
    assert [x["id"] for x in d["registry_chain"]] == ["911", "6911", "69112", CID]
    assert d["taxonomy"]["group"]["code"] == "246" and d["taxonomy"]["chapter"]["id"] == "6"
    assert {b["name"] for b in d["brand"]} >= {"Claude", "Claude API", "Claude Code"}
    assert all(b["source_type"] == "CFP_PUBLIC_SOURCE" for b in d["brand"])
    t = d["tasks"][0]
    assert t["status"] == "ACCEPTED"
    assert [h["to_status"] for h in t["history"]] == ["QUEUED", "ACKED", "IN_PROGRESS", "IN_REVIEW", "ACCEPTED"]
    assert t["evidence"][0]["sha"] == "553e7a7" and t["reviews"][0]["decision"] == "ACCEPT"


def test_bidirectional_links(world):
    c, o = world["lead"], world["out"]
    ent = ok(c.get(f"/api/office/enterprises/{o['enterprise']}"), 200)
    assert {"ref": f"task:{o['task']}", "relation": "uses"} in ent["links"]["incoming"]
    assert {"ref": "registry:911", "relation": "located_in"} in ent["links"]["outgoing"]
    task_links = ok(c.get(f"/api/office/links?ref=task:{o['task']}"), 200)
    assert {f"enterprise:{o['enterprise']}", f"topic:{o['topic']}", f"dataset:{o['dataset']}",
            f"registry:{CID}", f"pair:{o['pair']}"} <= {x["ref"] for x in task_links["outgoing"]}
    topic = ok(c.get(f"/api/office/topics/{o['topic']}"), 200)
    assert topic["group"]["code"] == "246"
    assert {"ref": f"dataset:{o['dataset']}", "relation": "supports"} in topic["links"]["incoming"]


def test_search_by_chapter(world):
    c = world["other"]
    res = ok(c.get("/api/office/search", params={"q": "anthropic", "chapter": "7"}), 200)["results"]
    assert any(r["ref"].startswith("enterprise:") for r in res)
    res6 = ok(c.get("/api/office/search", params={"q": "claude"}), 200)["results"]
    assert any(r["ref"] == f"office:{CID}" for r in res6) and any(r["ref"].startswith("brand:") for r in res6)


# ---------- xác thực + phân quyền

def test_no_new_canonical_ids(world):
    g = world["gov"]
    r = g.post("/api/office/offices", json={**SAMPLE["office"], "canonical_id": "99999999"}, headers=H)
    assert r.status_code == 422 and "Registry" in r.json()["detail"]
    r = g.post("/api/office/offices", json={**SAMPLE["office"], "canonical_id": "69112"}, headers=H)  # developer
    assert r.status_code == 422
    r = world["lead"].post("/api/office/enterprises", json={**SAMPLE["enterprise"], "name": "X Corp", "country_id": "6911"},
                           headers=H)  # AI country ≠ country
    assert r.status_code == 422


def test_only_governance_opens_office(world):
    r = world["lead"].post("/api/office/offices", json={**SAMPLE["office"], "canonical_id": "691141"}, headers=H)
    assert r.status_code == 403
    assert TestClient(create_app(world["st"])).post("/api/office/offices", json=SAMPLE["office"], headers=H).status_code == 401


def test_brand_authorization_labels(world):
    lead, gov = world["lead"], world["gov"]
    item = {"kind": "service", "name": "Dịch vụ thử", "url": "https://www.anthropic.com/", "source_url": "https://www.anthropic.com/"}
    assert world["other"].post(f"/api/office/offices/{CID}/brand", json=item, headers=H).status_code == 403
    r = lead.post(f"/api/office/offices/{CID}/brand", json={**item, "source_type": "AUTHORIZED_PROMOTION",
                                                            "authorization_url": "https://www.anthropic.com/"}, headers=H)
    assert r.status_code == 403  # maintainer không tự gắn nhãn ủy quyền
    r = gov.post(f"/api/office/offices/{CID}/brand", json={**item, "source_type": "BRAND_CONFIRMED"}, headers=H)
    assert r.status_code == 422  # thiếu bằng chứng ủy quyền
    r = lead.post(f"/api/office/offices/{CID}/brand", json={**item, "url": "http://insecure.example"}, headers=H)
    assert r.status_code == 422


def test_duplicates_rejected(world):
    lead, o = world["lead"], world["out"]
    assert lead.post("/api/office/enterprises", json={**SAMPLE["enterprise"], "name": "  anthropic   PBC "},
                     headers=H).status_code == 409
    assert world["gov"].post(f"/api/office/offices/{CID}/brand", json={**SAMPLE["brand"][0], "name": "CLAUDE"},
                             headers=H).status_code == 409
    assert world["gov"].post("/api/office/offices", json=SAMPLE["office"], headers=H).status_code == 409
    again = lead.post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Luồng Link Mẫu SI AI xuyên suốt",
                                                 "acceptance": "x" * 5, "reviewer_id": world["ids"]["rev"],
                                                 "idempotency_key": f"office-flow-base-{world['ids']['lead']}"}, headers=H)
    assert again.status_code == 201 and again.json()["duplicate"] is True and again.json()["id"] == o["task"]


def test_task_state_machine_and_independent_review(world):
    lead, rev, other, ids, o = world["lead"], world["rev"], world["other"], world["ids"], world["out"]
    assert lead.post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Tự review", "acceptance": "abc",
                                                "reviewer_id": ids["lead"], "idempotency_key": "self-review-1"},
                     headers=H).status_code == 422
    assert lead.post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Reviewer không có vai trò",
                                                "acceptance": "abc", "reviewer_id": ids["other"],
                                                "idempotency_key": "no-role-1"}, headers=H).status_code == 422
    t = ok(lead.post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Vòng sửa", "acceptance": "abc",
                                                "reviewer_id": ids["rev"], "idempotency_key": "rework-1"}, headers=H), 201)["id"]
    assert other.post(f"/api/office/tasks/{t}/ack", json={}, headers=H).status_code in (403, 404)  # 404 khi RLS 003 ẩn
    assert lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H).status_code == 409  # phải ACK trước
    ok(lead.post(f"/api/office/tasks/{t}/ack", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)
    assert lead.post(f"/api/office/tasks/{t}/submit", json={}, headers=H).status_code == 422  # chưa có Evidence
    ok(lead.post(f"/api/office/tasks/{t}/evidence", json={"kind": "url", "url": "https://example.org/a",
                                                         "description": "bản nháp"}, headers=H), 201)
    ok(lead.post(f"/api/office/tasks/{t}/submit", json={}, headers=H), 200)
    assert lead.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "tự duyệt"},
                     headers=H).status_code == 403
    ok(rev.post(f"/api/office/tasks/{t}/review", json={"decision": "CHANGES_REQUESTED", "notes": "Thiếu test"}, headers=H), 201)
    ok(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/evidence", json={"kind": "test_report", "url": "https://example.org/b",
                                                         "description": "đã thêm test"}, headers=H), 201)
    ok(lead.post(f"/api/office/tasks/{t}/submit", json={}, headers=H), 200)
    ok(rev.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "Đạt"}, headers=H), 201)
    hist = [h["to_status"] for h in [x for x in ok(lead.get(f"/api/office/offices/{CID}"), 200)["tasks"] if x["id"] == t][0]["history"]]
    assert hist == ["QUEUED", "ACKED", "IN_PROGRESS", "IN_REVIEW", "CHANGES_REQUESTED", "IN_PROGRESS", "IN_REVIEW", "ACCEPTED"]


def test_wip_limit_five(urls, world):
    st = world["st"]
    os.environ["CFP_OFFICE_MAX_WIP"] = "2"
    try:
        lead = client(st)  # app mới đọc CFP_OFFICE_MAX_WIP=2
        lead.cookies = world["lead"].cookies
        made = []
        for i in range(3):
            t = ok(lead.post("/api/office/tasks", json={"pair_id": world["out"]["pair"], "title": f"Song song {i}",
                                                        "acceptance": "abc", "reviewer_id": world["ids"]["rev"],
                                                        "idempotency_key": f"wip-{i}-{uuid.uuid4().hex[:6]}"}, headers=H), 201)["id"]
            ok(lead.post(f"/api/office/tasks/{t}/ack", json={}, headers=H), 200)
            made.append(t)
        codes = [lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H).status_code for t in made]
        assert codes == [200, 200, 409], codes
    finally:
        os.environ.pop("CFP_OFFICE_MAX_WIP", None)


def test_members_only_dataset(world):
    lead = world["lead"]
    d = ok(lead.post("/api/office/datasets", json={**SAMPLE["dataset"], "title": "Giáo trình nội bộ", "access": "members",
                                                  "version": "m1", "topic_id": world["out"]["topic"]}, headers=H), 201)["id"]
    anon = TestClient(create_app(world["st"]))
    assert anon.get(f"/api/office/datasets/{d}").status_code in (401, 404)  # 404 khi RLS 003 ẩn dòng
    assert not any(r["ref"] == f"dataset:{d}" for r in anon.get("/api/office/search", params={"q": "giáo trình"}).json()["results"])
    assert lead.get(f"/api/office/datasets/{d}").status_code == 200


def test_audit_log_and_access(world):
    o = world["out"]
    assert world["other"].get(f"/api/office/audit?ref=task:{o['task']}").status_code == 403
    ev = ok(world["rev"].get(f"/api/office/audit?ref=task:{o['task']}"), 200)["events"]
    assert [e["action"] for e in ev][:2] == ["task.create", "task.acked"] and ev[-1]["action"] == "task.accepted"


def test_csrf_required_on_office_writes(world):
    r = world["lead"].post("/api/office/topics", json=SAMPLE["topic"])
    assert r.status_code == 403


def test_office_ui_page(world):
    r = world["other"].get(f"/_internal/office/{CID}/")
    assert r.status_code == 200 and "noindex" in r.headers["x-robots-tag"]
    assert world["other"].get("/_internal/office/abc/").status_code == 404


# ---------- cô lập dữ liệu (chế độ Postgres / Supabase)

def _pg(urls):
    if "admin" not in urls:
        pytest.skip("chỉ áp dụng chế độ schema/role")


@pytest.mark.parametrize("role_key,target", [("sieu-bo-doi", ("office", "tasks")), ("si-ai-hstdn", ("office", "audit_log")),
                                             ("auth", ("office", "offices")), ("office", ("sieu-bo-doi", "posts")),
                                             ("office", ("si-ai-hstdn", "posts")), ("office", ("auth", "users"))])
def test_office_and_forums_cannot_cross(urls, world, role_key, target):
    _pg(urls)
    table = f"{schema_of(urls[target[0]])}.{target[1]}"
    eng = create_engine(urls[role_key])
    with eng.connect() as conn, pytest.raises(Exception) as ei:
        conn.execute(text(f"SELECT count(*) FROM {table}"))
    assert "permission denied" in str(ei.value)
    eng.dispose()


@pytest.mark.parametrize("sql", ["UPDATE audit_log SET action = 'x'", "DELETE FROM audit_log",
                                 "DELETE FROM evidence", "UPDATE reviews SET decision = 'ACCEPT'",
                                 "INSERT INTO office_roles VALUES (999, 'governance')"])
def test_office_role_append_only_and_no_self_grant(urls, world, sql):
    _pg(urls)
    eng = create_engine(urls["office"])
    with eng.connect() as conn, pytest.raises(Exception) as ei:
        conn.execute(text(sql))
    assert "permission denied" in str(ei.value)
    eng.dispose()


def test_forum_data_untouched_by_office(urls, world):
    _pg(urls)
    total = 0
    for key in ("sieu-bo-doi", "si-ai-hstdn"):  # đếm bằng chính role của diễn đàn (RLS cho phép thấy)
        eng = create_engine(urls[key])
        with eng.connect() as conn:
            total += conn.execute(text("select count(*) from posts")).scalar_one()
            total += conn.execute(text("select count(*) from members")).scalar_one()
        eng.dispose()
    assert total == 0


def test_office_rows_visible_only_to_office_role(urls, world):
    _pg(urls)
    eng = create_engine(urls["office"])
    with eng.connect() as conn:
        rls_003 = conn.execute(text("select to_regprocedure('cfp_office.in_progress_count()') is not null")).scalar()
        conn.execute(text("select set_config('cfp.user_id', :u, false)"), {"u": str(world["ids"]["gov"])})
        assert conn.execute(text("select count(*) from tasks")).scalar_one() >= 1
        assert conn.execute(text("select count(*) from audit_log")).scalar_one() >= 1
        if rls_003:  # 003: không có danh tính → không thấy gì (fail-closed)
            conn.execute(text("select set_config('cfp.user_id', '', false)"))
            assert conn.execute(text("select count(*) from tasks")).scalar_one() == 0
    eng.dispose()


def test_migration_002_matches_code():
    """Migration Supabase phải khớp metadata trong code (phát hiện lệch schema)."""
    from pathlib import Path
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable
    from services.forum.office import md
    sql = (Path(__file__).resolve().parents[2] / "services/forum/sql/002_office.sql").read_text(encoding="utf-8")
    for t in md.sorted_tables:
        ddl = str(CreateTable(t, if_not_exists=True).compile(dialect=postgresql.dialect())).strip() + ";"
        assert ddl in sql, f"002_office.sql lệch với code ở bảng {t.name}"
    for t in md.sorted_tables:
        assert f"alter table cfp_office.{t.name} force row level security;" in sql
    assert "create policy office_governance_roles on cfp_office.office_roles" in sql


def test_groups_follow_directive():
    from services.forum.registry import GROUPS
    assert [g["code"] for g in GROUPS] == ["DV", "000", "135", "246", "789"]
    assert sorted(c for g in GROUPS for c in g["chapters"]) == [str(i) for i in range(10)]


# ---------- SecuritySI review PR #195 @ de09d85 • ma trận người dùng A/B

def _anon(world):
    return TestClient(create_app(world["st"]))


def test_sec01_office_view_hides_tasks_from_anonymous_and_unrelated(world):
    o = world["out"]
    for who, c in (("anonymous", _anon(world)), ("unrelated", world["other"])):
        d = ok(c.get(f"/api/office/offices/{CID}"), 200)
        assert d["tasks"] == [], who
        assert d["maintainers"] is None and d["can_edit"] is False, who
        assert all(set(p) == {"id", "canonical_id", "software"} for p in d["pairs"]), who
        assert "created_by" not in d["office"], who
        refs = {x["ref"] for x in d["links"]["incoming"] + d["links"]["outgoing"]}
        assert not any(r.startswith("task:") for r in refs), who
        ent = ok(c.get(f"/api/office/enterprises/{o['enterprise']}"), 200)
        assert not any(x["ref"].startswith("task:") for x in ent["links"]["incoming"]), who
        assert ok(c.get(f"/api/office/links?ref=task:{o['task']}"), 200) == {"outgoing": [], "incoming": []}, who


def test_sec01_participants_and_staff_see_tasks(world):
    o = world["out"]
    for who in ("lead", "rev", "gov"):
        tasks = ok(world[who].get(f"/api/office/offices/{CID}"), 200)["tasks"]
        assert any(t["id"] == o["task"] for t in tasks), who
        t = next(t for t in tasks if t["id"] == o["task"])
        assert t["evidence"] and t["reviews"] and t["history"], who
    assert ok(world["gov"].get(f"/api/office/offices/{CID}"), 200)["maintainers"]


def test_sec02_idempotency_checked_after_authorization(world, urls):
    o, ids = world["out"], world["ids"]
    key = f"office-flow-base-{ids['lead']}"  # khoá thật của nhiệm vụ đã có
    body = {"pair_id": o["pair"], "title": "Luồng Link Mẫu SI AI xuyên suốt", "acceptance": "xxxxx",
            "reviewer_id": ids["rev"], "idempotency_key": key}
    r = world["other"].post("/api/office/tasks", json=body, headers=H)  # người ngoài đoán đúng khoá
    assert r.status_code == 403 and "id" not in r.json()
    # Một maintainer khác của cùng Văn Phòng dùng lại khoá → 409, không lộ id/trạng thái.
    m2 = client(world["st"])
    m2_id = register(m2, f"m2{uuid.uuid4().hex[:6]}@example.org", "Maintainer 2")
    ok(world["gov"].post(f"/api/office/offices/{CID}/maintainers/{m2_id}", headers=H), 201)
    r = m2.post("/api/office/tasks", json=body, headers=H)
    assert r.status_code == 409 and "id" not in r.json() and "status" not in r.json()
    r = world["lead"].post("/api/office/tasks", json=body, headers=H)  # chính chủ gửi lại → nhận lại nhiệm vụ cũ
    assert r.status_code == 201 and r.json()["id"] == o["task"] and r.json()["duplicate"] is True


def test_sec04_members_dataset_object_acl(world):
    lead = world["lead"]
    d = ok(lead.post("/api/office/datasets", json={**SAMPLE["dataset"], "title": "Tài liệu nội bộ ACL", "access": "members",
                                                  "version": f"acl-{uuid.uuid4().hex[:6]}"}, headers=H), 201)["id"]
    # SEC-06: vai trò reviewer không còn quyền xem tài liệu nội bộ không liên quan.
    for who in ("other", "rev"):
        assert world[who].get(f"/api/office/datasets/{d}").status_code in (403, 404), who  # 404 dưới RLS 003
        assert not any(x["ref"] == f"dataset:{d}" for x in
                       world[who].get("/api/office/search", params={"q": "nội bộ acl"}).json()["results"]), who
    for who in ("lead", "gov"):
        assert world[who].get(f"/api/office/datasets/{d}").status_code == 200, who
    assert world["gov"].get("/api/office/search", params={"q": "nội bộ acl"}).json()["results"]


def test_sec04_link_creation_requires_ownership(world):
    o, other, lead = world["out"], world["other"], world["lead"]
    body = {"from_ref": f"enterprise:{o['enterprise']}", "to_ref": f"topic:{o['topic']}", "relation": "researched_in"}
    assert other.post("/api/office/links", json=body, headers=H).status_code == 403
    assert other.post("/api/office/links", json={**body, "from_ref": "registry:911"}, headers=H).status_code == 403
    assert lead.post("/api/office/links", json=body, headers=H).status_code == 201  # lead tạo doanh nghiệp này
    own = ok(other.post("/api/office/topics", json={"title": f"Chủ đề riêng {uuid.uuid4().hex[:6]}", "chapter": "6"},
                        headers=H), 201)["id"]
    hidden = ok(lead.post("/api/office/datasets", json={**SAMPLE["dataset"], "title": "Ẩn với người ngoài", "access": "members",
                                                       "version": f"h-{uuid.uuid4().hex[:6]}"}, headers=H), 201)["id"]
    r = other.post("/api/office/links", json={"from_ref": f"topic:{own}", "to_ref": f"dataset:{hidden}",
                                              "relation": "uses"}, headers=H)
    assert r.status_code == 422  # không liên kết tới mục mình không được xem
    assert other.post("/api/office/links", json={"from_ref": f"topic:{own}", "to_ref": f"enterprise:{o['enterprise']}",
                                                 "relation": "about"}, headers=H).status_code == 201


def test_sec04_task_links_need_participation(world):
    o = world["out"]
    body = {"from_ref": f"task:{o['task']}", "to_ref": f"topic:{o['topic']}", "relation": "about"}
    assert world["other"].post("/api/office/links", json=body, headers=H).status_code == 422  # task không hiển thị
    assert world["lead"].post("/api/office/links", json=body, headers=H).status_code == 201


# ---------- SecuritySI re-review @ 4ed670a: SEC-06 (quyền tối thiểu) + idempotency đồng thời

def test_sec06_reviewer_role_sees_only_assigned_tasks(world):
    o, ids = world["out"], world["ids"]
    # Nhiệm vụ mới giao cho reviewer khác (governance) → người có vai trò reviewer không được thấy.
    t = ok(world["lead"].post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Không giao cho rev",
                                                        "acceptance": "abc", "reviewer_id": ids["gov"],
                                                        "idempotency_key": f"sec06-{uuid.uuid4().hex[:8]}"}, headers=H), 201)["id"]
    seen = {x["id"] for x in ok(world["rev"].get(f"/api/office/offices/{CID}"), 200)["tasks"]}
    assert o["task"] in seen and t not in seen
    assert world["rev"].get(f"/api/office/audit?ref=task:{t}").status_code == 403
    assert world["rev"].get(f"/api/office/audit?ref=task:{o['task']}").status_code == 200   # được chỉ định
    assert world["rev"].get(f"/api/office/audit?ref=office:{CID}").status_code == 403       # không phải nhiệm vụ
    assert world["lead"].get(f"/api/office/audit?ref=task:{t}").status_code == 200          # người thực thi
    assert world["other"].get(f"/api/office/audit?ref=task:{t}").status_code == 403
    assert world["gov"].get(f"/api/office/audit?ref=office:{CID}").status_code == 200


def test_sec06_unrelated_cannot_see_ids_of_participants(world):
    for who in ("other",):
        d = ok(world[who].get(f"/api/office/offices/{CID}"), 200)
        blob = str(d)
        assert "assignee_id" not in blob and "reviewer_id" not in blob and "lead_user_id" not in blob
        assert "created_by" not in blob


def test_task_refs_must_be_visible(world):
    hidden = ok(world["other"].post("/api/office/datasets", json={**SAMPLE["dataset"], "title": "Riêng người ngoài",
                                                                 "access": "members", "version": f"r-{uuid.uuid4().hex[:6]}"},
                                    headers=H), 201)["id"]
    r = world["lead"].post("/api/office/tasks", json={"pair_id": world["out"]["pair"], "title": "Tham chiếu ẩn",
                                                     "acceptance": "abc", "reviewer_id": world["ids"]["rev"],
                                                     "idempotency_key": f"hid-{uuid.uuid4().hex[:8]}",
                                                     "refs": [f"dataset:{hidden}"]}, headers=H)
    assert r.status_code == 422


def test_concurrent_same_idempotency_key_never_500(world):
    from concurrent.futures import ThreadPoolExecutor
    body = {"pair_id": world["out"]["pair"], "title": "Gửi đồng thời", "acceptance": "abc",
            "reviewer_id": world["ids"]["rev"], "idempotency_key": f"race-{uuid.uuid4().hex[:10]}"}
    clients = []
    for _ in range(4):
        c = client(world["st"])
        c.cookies = world["lead"].cookies
        clients.append(c)
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda c: c.post("/api/office/tasks", json=body, headers=H), clients))
    codes = [r.status_code for r in res]
    assert all(code == 201 for code in codes), codes
    assert len({r.json()["id"] for r in res}) == 1  # đúng một nhiệm vụ được tạo
