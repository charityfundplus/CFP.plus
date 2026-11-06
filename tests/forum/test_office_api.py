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
                                                 "acceptance": "API + migration + test PASS; dữ liệu còn sau restart", "reviewer_id": world["ids"]["rev"],
                                                 "refs": [f"enterprise:{o['enterprise']}", f"topic:{o['topic']}", f"dataset:{o['dataset']}", f"registry:{CID}"],
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
    body = {"pair_id": o["pair"], "title": "Luồng Link Mẫu SI AI xuyên suốt", "acceptance": "API + migration + test PASS; dữ liệu còn sau restart",
            "refs": [f"enterprise:{o['enterprise']}", f"topic:{o['topic']}", f"dataset:{o['dataset']}", f"registry:{CID}"],
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

def test_task_idempotency_cannot_bypass_office_authorization(world):
    """Replay keys must never reveal task receipts to an unrelated authenticated user."""
    payload = {"pair_id": world["out"]["pair"], "title": "Replay authorization regression",
               "acceptance": "Evidence required", "reviewer_id": world["ids"]["rev"],
               "idempotency_key": "replay-auth-regression", "refs": []}
    first = world["lead"].post('/api/office/tasks', json=payload, headers=H)
    assert first.status_code == 201
    other = world["other"].post('/api/office/tasks', json=payload, headers=H)
    assert other.status_code == 403
    duplicate = world["lead"].post('/api/office/tasks', json=payload, headers=H)
    assert duplicate.status_code == 201 and duplicate.json()['id'] == first.json()['id']
    for changed in ({"acceptance": "Different criteria"}, {"description": "Changed work"},
                    {"refs": ["registry:691121"]}):
        response = world["lead"].post('/api/office/tasks', json={**payload, **changed}, headers=H)
        assert response.status_code == 409


def test_task_comments_participants_only(world):
    """Trao đổi theo nhiệm vụ: người tham gia/staff ghi & đọc; người ngoài/khách không ghi, không thấy."""
    t = world["out"]["task"]
    ok(world["lead"].post(f"/api/office/tasks/{t}/comments", json={"body": "Đã cập nhật Evidence, nhờ xem lại."}, headers=H), 201)
    ok(world["rev"].post(f"/api/office/tasks/{t}/comments", json={"body": "Đã nhận, sẽ phản hồi."}, headers=H), 201)
    ok(world["gov"].post(f"/api/office/tasks/{t}/comments", json={"body": "Governance đã xem."}, headers=H), 201)
    assert world["other"].post(f"/api/office/tasks/{t}/comments", json={"body": "chen ngang"}, headers=H).status_code in (403, 404)
    assert _anon(world).post(f"/api/office/tasks/{t}/comments", json={"body": "khách"}, headers=H).status_code == 401
    assert world["lead"].post(f"/api/office/tasks/{t}/comments", json={"body": "   "}, headers=H).status_code == 422
    assert world["lead"].post(f"/api/office/tasks/{t}/comments", json={"body": "x"}).status_code == 403  # thiếu CSRF header
    before = next(x for x in ok(world["gov"].get(f"/api/office/offices/{CID}"), 200)["tasks"] if x["id"] == t)["status"]
    task = next(x for x in ok(world["gov"].get(f"/api/office/offices/{CID}"), 200)["tasks"] if x["id"] == t)
    notes = [h["note"] for h in task["history"] if h["to_status"] == "COMMENT"]
    assert notes == ["Đã cập nhật Evidence, nhờ xem lại.", "Đã nhận, sẽ phản hồi.", "Governance đã xem."]
    assert task["status"] == before == "ACCEPTED"  # trao đổi không đổi trạng thái
    assert "chen ngang" not in str(task["history"])
    audit = ok(world["gov"].get(f"/api/office/audit?ref=task:{t}"), 200)
    assert sum(1 for a in audit["events"] if a["action"] == "task.comment") == 3


def test_closure_after_independent_review(world):
    """Closure: chỉ sau ACCEPTED, chỉ governance/người giao việc, người thực thi không tự đóng."""
    lead, rev, gov, other, ids, o = world["lead"], world["rev"], world["gov"], world["other"], world["ids"], world["out"]
    t = ok(lead.post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Closure", "acceptance": "abc",
                                                "reviewer_id": ids["rev"], "idempotency_key": "closure-1"}, headers=H), 201)["id"]
    close = lambda c: c.post(f"/api/office/tasks/{t}/close", json={"note": "Đóng sau nghiệm thu"}, headers=H)
    assert close(gov).status_code == 409  # chưa ACCEPTED
    ok(lead.post(f"/api/office/tasks/{t}/ack", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/evidence", json={"kind": "url", "url": "https://example.org/closure",
                                                         "description": "bằng chứng"}, headers=H), 201)
    ok(lead.post(f"/api/office/tasks/{t}/submit", json={}, headers=H), 200)
    ok(rev.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "Đạt"}, headers=H), 201)
    assert close(lead).status_code == 403  # người thực thi (cũng là người giao) không tự đóng
    assert close(rev).status_code == 403  # reviewer không phải người đóng
    assert close(other).status_code in (403, 404)
    assert close(_anon(world)).status_code == 401
    view = lambda c: next(x for x in ok(c.get(f"/api/office/offices/{CID}"), 200)["tasks"] if x["id"] == t)
    assert view(gov)["can_close"] is True and view(lead)["can_close"] is False
    assert ok(close(gov), 200)["status"] == "CLOSED"
    assert close(gov).status_code == 409  # không đóng hai lần
    task = view(lead)
    assert task["status"] == "CLOSED" and task["can_close"] is False
    assert [h["to_status"] for h in task["history"]][-2:] == ["ACCEPTED", "CLOSED"]
    ev = ok(gov.get(f"/api/office/audit?ref=task:{t}"), 200)["events"]
    assert [e["action"] for e in ev if e["action"] == "task.closed"] == ["task.closed"]


def _activate(world, key, who):
    from services.forum.app import members_t
    with world["st"].forums[key].begin() as c:
        c.execute(insert(members_t).values(user_id=world["ids"][who], user_name=who, role="member", status="active"))


def test_task_discussion_in_correct_forum_with_backlinks(world):
    """Nhiệm vụ → mở thảo luận ở đúng Diễn Đàn → phản hồi → quay lại nhiệm vụ; quyền và tách kho được giữ."""
    lead, rev, gov, other, o = world["lead"], world["rev"], world["gov"], world["other"], world["out"]
    t = o["task"]
    url = f"/api/office/tasks/{t}/discussions"
    sbd = {"forum": "sieu-bo-doi", "title": "Thảo luận nhiệm vụ", "body": "Nhờ góp ý cách kiểm thử."}
    hst = {"forum": "si-ai-hstdn", "title": "HSTDN cho nhiệm vụ", "body": "Dữ liệu doanh nghiệp", "hstdn": "Tập đoàn X"}
    # Chưa là thành viên diễn đàn → diễn đàn tự từ chối (không có bài, không có liên kết)
    assert lead.post(url, json=sbd, headers=H).status_code == 403
    assert lead.post(url, json=hst, headers=H).status_code == 403
    assert _anon(world).post(url, json=sbd, headers=H).status_code == 401
    assert lead.post(url, json={**sbd, "forum": "khac"}, headers=H).status_code == 422
    ok(lead.post("/api/forums/sieu-bo-doi/join", headers=H), 200)
    ok(other.post("/api/forums/sieu-bo-doi/join", headers=H), 200)
    assert other.post(url, json=sbd, headers=H).status_code == 404  # không thấy nhiệm vụ → không mở được
    d = ok(lead.post(url, json=sbd, headers=H), 201)
    assert d["forum"] == "sieu-bo-doi" and d["url"] == f"/_internal/forum/sieu-bo-doi/#post-{d['post_id']}"
    # Bài nằm ở đúng diễn đàn, có phản hồi qua API diễn đàn
    posts = ok(_anon(world).get("/api/forums/sieu-bo-doi/posts"), 200)["posts"]
    assert any(p["id"] == d["post_id"] and p["title"] == "Thảo luận nhiệm vụ" for p in posts)
    ok(other.post(f"/api/forums/sieu-bo-doi/posts/{d['post_id']}/comments", json={"body": "Góp ý: thêm test 401."}, headers=H), 201)
    # Liên kết ngược bài → nhiệm vụ: chỉ người xem được nhiệm vụ
    back = lambda c: ok(c.get("/api/office/forum-links?forum=sieu-bo-doi"), 200)["links"]
    assert {"post_id": d["post_id"], "task_id": t, "office_id": CID} in back(lead)
    assert {"post_id": d["post_id"], "task_id": t, "office_id": CID} in back(gov)
    assert back(other) == [] and back(_anon(world)) == []
    # Quay lại nhiệm vụ: thảo luận hiện trong nhiệm vụ cho người tham gia
    task = lambda c: next(x for x in ok(c.get(f"/api/office/offices/{CID}"), 200)["tasks"] if x["id"] == t)
    assert [x["ref"] for x in task(rev)["discussions"]] == [f"forum:sieu-bo-doi:{d['post_id']}"]
    # HSTDN: thành viên đã duyệt mở thảo luận; người không phải thành viên HSTDN không thấy ref HSTDN
    _activate(world, "si-ai-hstdn", "lead")
    h = ok(lead.post(url, json=hst, headers=H), 201)
    assert lead.post(url, json={**hst, "hstdn": None}, headers=H).status_code == 422  # quy tắc HSTDN của diễn đàn
    assert [x["forum"] for x in task(lead)["discussions"]] == ["sieu-bo-doi", "si-ai-hstdn"]
    assert [x["forum"] for x in task(rev)["discussions"]] == ["sieu-bo-doi"]  # rev không là thành viên HSTDN
    assert ok(rev.get("/api/office/forum-links?forum=si-ai-hstdn"), 200)["links"] == []
    assert not any(p["id"] == h["post_id"] and p["title"] == hst["title"]
                   for p in ok(_anon(world).get("/api/forums/sieu-bo-doi/posts"), 200)["posts"])  # không lẫn kho
    # Không tự tạo liên kết forum giả qua API links; audit đủ
    assert lead.post("/api/office/links", json={"from_ref": f"task:{t}", "to_ref": "forum:sieu-bo-doi:999",
                                                "relation": "discussion"}, headers=H).status_code == 422
    ev = ok(gov.get(f"/api/office/audit?ref=task:{t}"), 200)["events"]
    assert sum(1 for e in ev if e["action"] == "task.discussion") == 2


def test_board_buckets_follow_real_state_and_permissions(world, urls):
    """Bảng điều phối: RUNNING/IN_REVIEW/BLOCKED/REVIEWED theo trạng thái thật, lọc theo quyền người xem."""
    lead, rev, gov, other, ids, o = world["lead"], world["rev"], world["gov"], world["other"], world["ids"], world["out"]
    t = ok(lead.post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Board", "acceptance": "abc",
                                                "reviewer_id": ids["rev"], "idempotency_key": "board-flow-1"}, headers=H), 201)["id"]
    item = lambda c: next((x for x in ok(c.get("/api/office/board"), 200)["tasks"] if x["id"] == t), None)
    assert item(lead)["bucket"] == "QUEUED"
    ok(lead.post(f"/api/office/tasks/{t}/ack", json={}, headers=H), 200)
    assert item(lead)["bucket"] == "RUNNING"
    ok(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/evidence", json={"kind": "url", "url": "https://example.org/board",
                                                         "description": "bằng chứng"}, headers=H), 201)
    ok(lead.post(f"/api/office/tasks/{t}/submit", json={}, headers=H), 200)
    assert item(rev)["bucket"] == "IN_REVIEW"
    ok(rev.post(f"/api/office/tasks/{t}/review", json={"decision": "CHANGES_REQUESTED", "notes": "Sửa"}, headers=H), 201)
    b = item(lead)
    assert b["bucket"] == "BLOCKED" and b["reason"] == "Reviewer yêu cầu chỉnh sửa"
    ok(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/submit", json={}, headers=H), 200)
    ok(rev.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "Đạt"}, headers=H), 201)
    b = item(gov)
    assert b["bucket"] == "REVIEWED" and b["evidence"] == 1 and b["review"]["decision"] == "ACCEPT"
    assert b["url"] == f"/_internal/office/{CID}/#task:{t}"
    # Quyền: khách rỗng; người ngoài không thấy; reviewer chỉ thấy việc được chỉ định
    guest = ok(_anon(world).get("/api/office/board"), 200)
    assert guest["viewer"] == "guest" and guest["tasks"] == [] and set(guest["counts"]) == {
        "QUEUED", "RUNNING", "IN_REVIEW", "BLOCKED", "REVIEWED"}
    assert item(other) is None
    assert ok(gov.get("/api/office/board"), 200)["viewer"] == "governance"
    board = ok(gov.get("/api/office/board"), 200)
    assert sum(board["counts"].values()) == len(board["tasks"])


def test_board_never_marks_reviewed_without_evidence(world, urls):
    """ACCEPTED/CLOSED nhưng thiếu Evidence hoặc Review độc lập → BLOCKED, không tính REVIEWED."""
    if urls["office"].startswith("postgresql"):
        pytest.skip("Ghi trực tiếp bỏ qua API chỉ làm trên SQLite (Postgres: RLS + quyền chặn ghi thẳng)")
    from services.forum.office import tasks_t
    lead, gov, ids, o = world["lead"], world["gov"], world["ids"], world["out"]
    t = ok(lead.post("/api/office/tasks", json={"pair_id": o["pair"], "title": "Board giả", "acceptance": "abc",
                                                "reviewer_id": ids["rev"], "idempotency_key": "board-forged"}, headers=H), 201)["id"]
    with world["st"].office.begin() as c:  # mô phỏng dữ liệu bị đổi trạng thái ngoài luồng
        c.execute(tasks_t.update().where(tasks_t.c.id == t).values(status="ACCEPTED"))
    b = next(x for x in ok(gov.get("/api/office/board"), 200)["tasks"] if x["id"] == t)
    assert b["bucket"] == "BLOCKED" and b["reason"] == "Thiếu execution evidence"


def test_ops_page_served_noindex(world):
    r = world["gov"].get("/_internal/ops/")
    assert r.status_code == 200 and "noindex" in r.headers.get("x-robots-tag", "")
    assert world["gov"].get("/_internal/ops/ops.js").status_code == 200


def test_sandbox_website_entry_points(world, urls, monkeypatch):
    """Khung website sandbox: trang tĩnh có sẵn (chỉ đọc) + thanh lối vào Siêu Bộ Đôi/Văn Phòng/Diễn Đàn."""
    from pathlib import Path
    c = _anon(world)
    root = Path(__file__).resolve().parents[2]
    for path, cid in (("/", None), ("/69/", "69"), (f"/{CID}/", CID)):
        r = c.get(path)
        assert r.status_code == 200 and "noindex" in r.headers["x-robots-tag"], path
        assert 'data-testid="sandbox-entry"' in r.text and 'href="/_internal/forum/sieu-bo-doi/"' in r.text
        assert "/_internal/site/sandbox.css" in r.text and "style=" not in r.text  # CSP style-src 'self'
        src = (root / (cid or "") / "index.html").read_text(encoding="utf-8")
        body = src.split("<body", 1)[1].split(">", 1)[1]
        assert body.strip()[:200] in r.text  # nội dung gốc giữ nguyên, chỉ chèn thêm
    assert f'href="/_internal/office/{CID}/"' in c.get(f"/{CID}/").text  # Văn Phòng cố định theo ID có sẵn
    assert 'href="/_internal/office/69/"' not in c.get("/69/").text  # 69 không phải Văn Phòng SI AI → không tự tạo
    assert c.get(f"/{CID}").status_code in (307, 308) or c.get(f"/{CID}", follow_redirects=False).status_code in (307, 308)
    for bad in ("/99999999/", "/abc/", "/%2e%2e%2fservices/", "/services/", "/1%2F..%2Fservices/"):
        assert c.get(bad).status_code == 404, bad
    assert "Disallow: /" in c.get("/robots.txt").text
    assert c.get("/_internal/site/sandbox.css").status_code == 200


def test_sandbox_website_flag_off(urls, monkeypatch):
    monkeypatch.setenv("CFP_SANDBOX_WEBSITE", "0")
    c = client(stores(urls))
    assert c.get("/").status_code == 404 and c.get(f"/{CID}/").status_code == 404
    assert c.get("/api/health").status_code == 200


def test_central_update_two_child_links_see_new_version(world, tmp_path):
    """B • Cập nhật tập trung: nội dung gốc đổi MỘT lần → 2 link con (task refs + liên kết Văn Phòng) thấy version
    mới; ref/URL/ID không đổi; link không lưu bản sao. ID không có trong nguồn → 422 (không tự cấp)."""
    import shutil
    from pathlib import Path
    lead, gov, ids, o = world["lead"], world["gov"], world["ids"], world["out"]
    repo = Path(__file__).resolve().parents[2]
    ref = "catalog:8682"
    t = ok(lead.post("/api/office/tasks", headers=H, json={
        "pair_id": o["pair"], "title": "Dùng tài liệu gốc 8682", "acceptance": "đọc bản gốc", "reviewer_id": ids["rev"],
        "idempotency_key": "catalog-ref-1", "refs": [ref]}), 201)["id"]
    ok(gov.post("/api/office/links", headers=H, json={"from_ref": f"office:{CID}", "to_ref": ref, "relation": "references"}), 201)
    bad = lead.post("/api/office/tasks", headers=H, json={
        "pair_id": o["pair"], "title": "ID bịa", "acceptance": "abc", "reviewer_id": ids["rev"],
        "idempotency_key": "catalog-ref-bad", "refs": ["catalog:99999999"]})
    assert bad.status_code == 422

    def children(client):
        a = next(x for x in ok(client.get(f"/api/office/links?ref=task:{t}"), 200)["outgoing"] if x["ref"] == ref)
        b = next(x for x in ok(client.get(f"/api/office/offices/{CID}"), 200)["links"]["outgoing"] if x["ref"] == ref)
        return a["source"], b["source"]
    v1 = children(gov)
    assert v1[0] == v1[1] and v1[0]["canonical_url"] == "https://cfp.plus/8682/"
    # cập nhật nội dung gốc MỘT lần (bản sao repo tạm) rồi dựng lại chỉ mục như một lần deploy
    root = tmp_path / "repo"
    (root / "8682").mkdir(parents=True)
    page = (repo / "8682" / "index.html").read_text(encoding="utf-8")
    (root / "8682" / "index.html").write_text(page.replace("</title>", " • bản cập nhật</title>", 1), encoding="utf-8")
    for c in (lead, gov):
        c.app.state.catalog.reload(root)
    v2 = children(gov)
    assert v2[0] == v2[1] and v2[0]["version"] != v1[0]["version"] and v2[0]["title"].endswith("bản cập nhật")
    assert v2[0]["canonical_url"] == v1[0]["canonical_url"] and v2[0]["canonical_id"] == "8682"
    for c in (lead, gov):  # trả lại nguồn thật cho các test khác
        c.app.state.catalog.reload()


def test_closed_loop_hub_to_lesson_to_next_task(world):
    """Vòng khép kín (yêu cầu 6685795225), chỉ bằng API thật: HUB 69 → CMP 267 → Văn Phòng → Diễn Đàn →
    Siêu Bộ Đôi thực thi → Evidence → Review độc lập → nghiệm thu → Closure → bài học → nhiệm vụ tiếp theo."""
    lead, rev, gov, other, ids, o = world["lead"], world["rev"], world["gov"], world["other"], world["ids"], world["out"]
    from sqlalchemy.exc import IntegrityError
    try:
        _activate(world, "sieu-bo-doi", "lead")
    except IntegrityError:
        pass  # đã là thành viên từ test trước (world dùng chung cả module)
    t = ok(lead.post("/api/office/tasks", headers=H, json={
        "pair_id": o["pair"], "title": "Vòng khép kín", "acceptance": "đủ 12 bước", "reviewer_id": ids["rev"],
        "idempotency_key": "closed-loop-1"}), 201)["id"]
    loop = lambda c: ok(c.get(f"/api/office/tasks/{t}/loop"), 200)  # noqa: E731
    first = loop(lead)
    assert first["closed_loop"] is False and first["next_stage"] == "discussion"
    assert [s["key"] for s in first["stages"]][:3] == ["hub69", "cmp267", "office"]
    ok(lead.post(f"/api/office/tasks/{t}/discussions", headers=H, json={
        "forum": "sieu-bo-doi", "title": "Thảo luận vòng khép kín", "body": "Mở từ nhiệm vụ."}), 201)
    ok(lead.post(f"/api/office/tasks/{t}/ack", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/evidence", headers=H, json={
        "kind": "url", "url": "https://example.org/loop", "description": "bằng chứng"}), 201)
    ok(lead.post(f"/api/office/tasks/{t}/submit", json={}, headers=H), 200)
    assert lead.post(f"/api/office/tasks/{t}/lessons", headers=H, json={
        "title": "Bài học sớm", "chapter": "6", "summary": "chưa đóng thì chưa được ghi"}).status_code == 409
    ok(rev.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "Đạt"}, headers=H), 201)
    ok(gov.post(f"/api/office/tasks/{t}/close", json={"note": "Đóng"}, headers=H), 200)
    les = ok(lead.post(f"/api/office/tasks/{t}/lessons", headers=H, json={
        "title": "Bài học vòng khép kín", "chapter": "6", "summary": "Mở thảo luận trước khi thực thi giúp review nhanh."}), 201)
    assert loop(lead)["next_stage"] == "next"
    nxt = ok(lead.post("/api/office/tasks", headers=H, json={
        "pair_id": o["pair"], "title": "Nhiệm vụ tiếp theo", "acceptance": "dựa trên bài học", "reviewer_id": ids["rev"],
        "idempotency_key": "closed-loop-2", "refs": [f"task:{t}", les["ref"]]}), 201)["id"]
    done = loop(gov)
    assert done["closed_loop"] is True and done["next_stage"] is None, [s for s in done["stages"] if not s["done"]]
    by = {s["key"]: s for s in done["stages"]}
    assert by["review"]["detail"]["decision"] == "ACCEPT" and by["evidence"]["detail"]["count"] == 1
    assert by["lesson"]["detail"]["refs"] == [les["ref"]] and by["next"]["detail"]["refs"] == [f"task:{nxt}"]
    assert by["discussion"]["detail"]["posts"][0]["forum"] == "sieu-bo-doi"
    topic = ok(lead.get(f"/api/office/topics/{les['topic_id']}"), 200)
    assert topic["chapter"] == "6" and topic["field"] == "lesson"
    # quyền: người ngoài không xem được vòng, khách 401; audit có bước bài học
    assert other.get(f"/api/office/tasks/{t}/loop").status_code == 404
    assert _anon(world).get(f"/api/office/tasks/{t}/loop").status_code == 401
    assert other.post(f"/api/office/tasks/{t}/lessons", headers=H, json={
        "title": "x bài học", "chapter": "1", "summary": "người ngoài không được ghi"}).status_code == 404
    acts = [e["action"] for e in ok(gov.get(f"/api/office/audit?ref=task:{t}"), 200)["events"]]
    assert "task.lesson" in acts and "task.closed" in acts


# ---------- Link Mẫu phổ thông (issue #198 • P0.3): hồ sơ chung theo quyền, ID HOLD ghi rõ

def test_linkmau_universal_by_permission(world):
    guest = client(world["st"])
    g = ok(guest.get(f"/api/office/linkmau/{CID}"), 200)
    assert g["id"] == CID and g["canonical_url"] == f"https://cfp.plus/{CID}/" and g["office"]["exists"]
    assert g["status"]["code"] == "parent_hold" and g["status"]["hold"] and g["parent"]["verified"] is False
    assert [x["id"] for x in g["parent"]["chain"]] == ["911", "6911", "69112", CID]
    assert {x["id"]: x["hold"] for x in g["parent"]["chain"]}["69112"] is True
    assert g["tasks"] == [] and g["evidence"] == [] and g["reviews"] == [] and g["history"] == []  # khách: không thấy
    assert ok(world["other"].get(f"/api/office/linkmau/{CID}"), 200)["tasks"] == []  # người ngoài: không thấy
    lead = ok(world["lead"].get(f"/api/office/linkmau/{CID}"), 200)
    tid = world["out"]["task"]
    assert tid in [t["id"] for t in lead["tasks"]]
    assert any(e["task_id"] == tid for e in lead["evidence"]) and any(r["decision"] == "ACCEPT" for r in lead["reviews"])
    assert lead["history"] and lead["access"] in ("insider", "participant")
    h = ok(guest.get("/api/office/linkmau/69115"), 200)  # 69115 đang HOLD (Meta ↔ Microsoft AI)
    assert h["status"]["code"] == "hold_conflict" and h["status"]["hold"] and "HOLD" in h["status"]["label"]
    assert not h["office"]["exists"] and h["tasks"] == []
    assert guest.get("/api/office/linkmau/99999999").status_code == 404  # không tự cấp ID
    page = guest.get(f"/_internal/linkmau/{CID}/")
    assert page.status_code == 200 and "noindex" in page.headers["x-robots-tag"]
    assert guest.get("/_internal/linkmau/99999999/").status_code == 404
