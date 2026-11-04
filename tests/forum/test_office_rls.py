"""SEC-P0-195-03 • RLS theo người dùng ở tầng PostgreSQL (003_office_rls.sql).

Kết nối TRỰC TIẾP bằng role office_app (bỏ qua FastAPI) và đặt danh tính như backend
(set_config('cfp.user_id', …, true)) để chứng minh database tự chặn đọc/ghi chéo người dùng.
Chỉ chạy ở chế độ Postgres có 003; nếu không → skip.
"""
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from tests.forum.office_flow import H, ok
from tests.forum.test_office_api import client, grant, register, stores, urls, world  # noqa: F401 (fixtures)


@pytest.fixture(scope="module")
def rls(urls, world):  # noqa: F811
    import os
    required = os.environ.get("CFP_REQUIRE_003") == "1"  # CI: thiếu 003 là lỗi, không được skip
    if "admin" not in urls:
        if required:
            pytest.fail("CFP_REQUIRE_003=1 nhưng không chạy ở chế độ Postgres")
        pytest.skip("cần Postgres + 003")
    eng = create_engine(urls["office"])
    with eng.connect() as c:
        if not c.execute(text("select to_regprocedure('cfp_office.in_progress_count()') is not null")).scalar():
            if required:
                pytest.fail("CFP_REQUIRE_003=1 nhưng 003_office_rls.sql chưa áp")
            pytest.skip("003_office_rls.sql chưa áp")
    yield eng
    eng.dispose()


def q(eng, uid, sql, **params):
    with eng.begin() as c:
        c.execute(text("select set_config('cfp.user_id', :u, true)"), {"u": "" if uid is None else str(uid)})
        return c.execute(text(sql), params).all()


def count(eng, uid, table, where="true", **params):
    return q(eng, uid, f"select count(*) from {table} where {where}", **params)[0][0]


def test_no_identity_is_fail_closed(rls, world):
    for t in ("tasks", "evidence", "reviews", "task_events", "audit_log"):
        assert count(rls, None, t) == 0, t
    assert count(rls, None, "offices") >= 1  # hồ sơ công khai vẫn đọc được
    with pytest.raises(DBAPIError, match="row-level security"):
        q(rls, None, "insert into research_topics (title, title_key, chapter, field, summary, created_by) "
                     "values ('x','x-k','6','','',1)")


def test_unrelated_user_sees_nothing_internal(rls, world):
    other, t = world["ids"]["other"], world["out"]["task"]
    assert count(rls, other, "tasks") == 0
    assert count(rls, other, "evidence") == 0 and count(rls, other, "reviews") == 0
    assert count(rls, other, "task_events") == 0 and count(rls, other, "audit_log") == 0
    assert count(rls, other, "links", "from_ref = :r or to_ref = :r", r=f"task:{t}") == 0


def test_participants_see_their_task(rls, world):
    t = world["out"]["task"]
    for who in ("lead", "rev"):  # người thực thi + reviewer được chỉ định
        uid = world["ids"][who]
        assert count(rls, uid, "tasks", "id = :t", t=t) == 1, who
        assert count(rls, uid, "evidence", "task_id = :t", t=t) >= 1, who
        assert count(rls, uid, "audit_log", "ref = :r", r=f"task:{t}") >= 1, who


def test_reviewer_role_without_assignment_is_denied(rls, world):
    o, ids = world["out"], world["ids"]
    t2 = ok(world["lead"].post("/api/office/tasks", json={"pair_id": o["pair"], "title": "RLS: giao cho gov review",
                                                         "acceptance": "abc", "reviewer_id": ids["gov"],
                                                         "idempotency_key": f"rls-{uuid.uuid4().hex[:8]}"}, headers=H), 201)["id"]
    assert count(rls, ids["rev"], "tasks", "id = :t", t=t2) == 0       # vai trò reviewer, không được giao
    assert count(rls, ids["gov"], "tasks", "id = :t", t=t2) == 1       # governance
    assert count(rls, ids["lead"], "tasks", "id = :t", t=t2) == 1      # người thực thi/maintainer


def test_governance_sees_everything(rls, world):
    g = world["ids"]["gov"]
    with create_engine(world_admin(world)).connect() as c:
        total = c.execute(text("select count(*) from cfp_office.tasks")).scalar_one()
    assert count(rls, g, "tasks") == total and total >= 1
    assert count(rls, g, "audit_log") >= 1


def world_admin(world):
    import os
    return os.environ["CFP_FORUM_TEST_ADMIN_DB"]


@pytest.mark.parametrize("sql", [
    # ghi Evidence cho nhiệm vụ không phải của mình
    "insert into evidence (task_id, kind, url, description, submitted_by) values (:t, 'url', 'https://x.example/1', 'x', :me)",
    # giả danh người khác khi ghi Evidence
    "insert into evidence (task_id, kind, url, description, submitted_by) values (:t, 'url', 'https://x.example/2', 'x', :lead)",
    # review thay reviewer được chỉ định
    "insert into reviews (task_id, reviewer_id, decision, notes) values (:t, :me, 'ACCEPT', 'x')",
    # ghi lịch sử cho nhiệm vụ không được xem
    "insert into task_events (task_id, actor_id, to_status, note) values (:t, :me, 'ACCEPTED', 'x')",
    # nhật ký kiểm toán giả danh
    "insert into audit_log (actor_id, action, ref, data) values (:lead, 'x', 'office:691121', '{}')",
    # mở Văn Phòng khi không phải governance
    "insert into offices (canonical_id, display_name, platform, specialties, capabilities, limits, verification, created_by) "
    "values ('691141', 'x', 'x', '', '', '', 'x', :me)",
    # tự thêm mình làm maintainer
    "insert into office_maintainers (canonical_id, user_id) values ('691121', :me)",
    # giao nhiệm vụ trong Văn Phòng mình không duy trì
    "insert into tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) "
    "values (:pair, 'x', '', 'x', :me, :lead, 'QUEUED', 'rls-attack-1', :me)",
])
def test_unrelated_writes_rejected_by_rls(rls, world, sql):
    ids, o = world["ids"], world["out"]
    with pytest.raises(DBAPIError, match="row-level security"):
        q(rls, ids["other"], sql, t=o["task"], me=ids["other"], lead=ids["lead"], pair=o["pair"])


def test_unrelated_cannot_update_task_state(rls, world):
    o, other = world["out"], world["ids"]["other"]
    with rls.begin() as c:
        c.execute(text("select set_config('cfp.user_id', :u, true)"), {"u": str(other)})
        n = c.execute(text("update tasks set status = 'ACCEPTED' where id = :t"), {"t": o["task"]}).rowcount
    assert n == 0


def test_members_dataset_hidden_at_db_level(rls, world):
    lead, other = world["ids"]["lead"], world["ids"]["other"]
    d = ok(world["lead"].post("/api/office/datasets", json={"title": "RLS tài liệu nội bộ", "kind": "document",
                                                           "url": "https://example.org/rls-doc", "author": "CFP+",
                                                           "version": f"v-{uuid.uuid4().hex[:6]}",
                                                           "source_url": "https://example.org/rls-doc",
                                                           "access": "members", "chapter": "6"}, headers=H), 201)["id"]
    assert count(rls, lead, "datasets", "id = :d", d=d) == 1
    assert count(rls, other, "datasets", "id = :d", d=d) == 0
    assert count(rls, None, "datasets", "id = :d", d=d) == 0


def test_wip_counter_is_global_under_rls(rls, world):
    with rls.connect() as c:
        c.execute(text("select set_config('cfp.user_id', '', false)"))
        assert c.execute(text("select cfp_office.in_progress_count()")).scalar_one() >= 0
