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
    email = world["lead"].get("/api/auth/me").json()["user"]["email"]
    ok(c.post("/api/auth/login", json={"email": email, "password": "matkhau-office-p0"}, headers=H), 200)
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
    assert other.post(f"/api/office/tasks/{t}/ack", json={}, headers=H).status_code == 403
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
    assert anon.get(f"/api/office/datasets/{d}").status_code == 404
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
        assert conn.execute(text("select count(*) from tasks")).scalar_one() >= 1
        assert conn.execute(text("select count(*) from audit_log")).scalar_one() >= 1
    eng.dispose()
    eng = create_engine(urls["admin"])  # chủ bảng / người chạy migration: RLS FORCE → không thấy dữ liệu
    with eng.connect() as conn:
        assert conn.execute(text("select count(*) from cfp_office.tasks")).scalar_one() == 0
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


def test_private_office_read_and_link_boundaries(world):
    anon = client(world['st'])
    assert anon.get(f'/api/office/offices/{CID}').status_code == 401
    assert world['other'].get(f'/api/office/offices/{CID}').status_code == 403
    ref = f"task:{world['out']['task']}"
    for c in (anon, world['other']):
        assert c.get('/api/office/links', params={'ref': ref}).status_code == 404
        enterprise = c.get(f"/api/office/enterprises/{world['out']['enterprise']}").json()
        assert ref not in str(enterprise['links'])
    assert world['rev'].get(f'/api/office/offices/{CID}').status_code == 200
    assert world['other'].post('/api/office/links', json={
        'from_ref': ref, 'to_ref': 'registry:691121', 'relation': 'uses'}, headers=H).status_code == 403


def test_private_dataset_not_disclosed_to_unrelated_session(world):
    payload = {**SAMPLE['dataset'], 'url': 'https://example.org/private-regression',
               'title': 'Private regression unique', 'access': 'members'}
    did = ok(world['lead'].post('/api/office/datasets', json=payload, headers=H), 201)['id']
    for c in (client(world['st']), world['other']):
        assert c.get(f'/api/office/datasets/{did}').status_code == 404
        assert f'dataset:{did}' not in str(c.get('/api/office/search?q=Private%20regression').json())
    assert world['lead'].get(f'/api/office/datasets/{did}').status_code == 200


def test_reviewer_sees_only_assigned_tasks(world):
    t = ok(world['lead'].post('/api/office/tasks', headers=H, json={
        'pair_id': world['out']['pair'], 'title': 'Not assigned to reviewer',
        'acceptance': 'Only assigned reviewer sees this task', 'reviewer_id': world['ids']['gov'],
        'idempotency_key': 'other-reviewer-task'}), 201)['id']
    data = world['rev'].get(f'/api/office/offices/{CID}').json()
    assert t not in [task['id'] for task in data['tasks']]
    assert world['rev'].get('/api/office/links', params={'ref': f'task:{t}'}).status_code == 404
    for bad in ('task:abc', 'pair:999999999999999999999', 'dataset:１'):
        assert world['other'].get('/api/office/links', params={'ref': bad}).status_code == 404
