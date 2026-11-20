"""Worker P0 • hàng đợi thật: idempotency, retry/backoff, dead-letter, lease, kill switch, quyền tối thiểu.

Postgres (004_worker.sql): CFP_WORKER_TEST_DB (role worker_app) + CFP_FORUM_TEST_ADMIN_DB (người vận hành).
Không có → SQLite tạm (bỏ qua các test quyền DB).
"""
import json
import os
import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.exc import DBAPIError

from services.forum import worker as W

T0 = datetime(2026, 11, 4, 14, 0, tzinfo=timezone.utc)


@pytest.fixture()
def env(tmp_path):
    url, admin = os.environ.get("CFP_WORKER_TEST_DB"), os.environ.get("CFP_FORUM_TEST_ADMIN_DB")
    if url and admin:
        eng = W.engine_for(url)
        adm = create_engine(admin)
        with adm.begin() as c:  # dọn dữ liệu test (người vận hành), giữ schema/quyền
            c.exec_driver_sql("truncate cfp_worker.jobs, cfp_worker.logs, cfp_worker.heartbeats restart identity")
            c.exec_driver_sql("update cfp_worker.control set value = 'false' where key = 'paused'")
        yield {"eng": eng, "admin": admin, "pg": True}
        eng.dispose(); adm.dispose()
    else:
        u = f"sqlite:///{tmp_path / 'w.db'}"
        yield {"eng": W.engine_for(u), "admin": u, "pg": False}


def jobs(eng, **where):
    q = select(W.jobs_t).order_by(W.jobs_t.c.id)
    for k, v in where.items():
        q = q.where(getattr(W.jobs_t.c, k) == v)
    with eng.connect() as c:
        return [dict(r) for r in c.execute(q).mappings()]


def events(eng):
    with eng.connect() as c:
        return [r for r in c.execute(select(W.logs_t.c.level, W.logs_t.c.event).order_by(W.logs_t.c.id)).all()]


def test_registry_job_runs_and_is_idempotent_per_window(env):
    w = W.Worker(env["eng"], "w1")
    r1 = w.tick(T0)
    r2 = w.tick(T0 + timedelta(minutes=5))  # cùng khung giờ → không tạo việc trùng
    assert [s for _, s in r1["ran"]] == ["done"] and r2["ran"] == []
    done = jobs(env["eng"], kind="registry_integrity")
    assert len(done) == 1 and done[0]["status"] == "done" and done[0]["attempts"] == 1
    res = json.loads(done[0]["result"])
    assert res["chain_691121"] == ["911", "6911", "69112", "691121"] and res["problems"] == []
    assert res["entities"] >= 267 and res["drift"] is False and res["previous_digest"] is None
    w.tick(T0 + timedelta(hours=1))  # khung mới → việc mới, so với digest trước, không drift
    second = json.loads(jobs(env["eng"], kind="registry_integrity")[-1]["result"])
    assert second["previous_digest"] == res["digest"] and second["drift"] is False
    st = W.status(env["eng"], T0 + timedelta(hours=1, seconds=10))
    assert st["alive"] and st["jobs"] == {"done": 2} and st["alerts_24h"] == 0
    assert st["heartbeats"][0]["ticks"] == 3 and st["last_done"]["summary"]["drift"] is False


def test_drift_raises_alert(env):
    w = W.Worker(env["eng"], "w1")
    w.tick(T0)
    with env["eng"].begin() as c:  # giả lập lần trước có dấu vân tay khác (Canonical ID/Parent bị đổi)
        c.execute(update(W.jobs_t).values(result=json.dumps({"digest": "khac"})))
    w.tick(T0 + timedelta(hours=1))
    assert ("alert", "registry_drift") in events(env["eng"])
    assert W.status(env["eng"], T0 + timedelta(hours=1))["alerts_24h"] == 1


def test_retry_with_backoff_then_dead_letter(env):
    calls = []

    def boom(eng, job):
        calls.append(job["attempts"])
        raise RuntimeError("nguồn lỗi")
    w = W.Worker(env["eng"], "w1", handlers={"flaky": boom}, schedule={"flaky": 86400}, backoff_base=60)
    assert [s for _, s in w.tick(T0)["ran"]] == ["retry"]
    j = jobs(env["eng"])[0]
    assert j["status"] == "queued" and j["attempts"] == 1
    assert W._aware(j["next_run_at"]) == T0 + timedelta(seconds=60)
    assert w.tick(T0 + timedelta(seconds=30))["ran"] == []  # chưa tới hạn backoff
    assert [s for _, s in w.tick(T0 + timedelta(seconds=60))["ran"]] == ["retry"]
    assert W._aware(jobs(env["eng"])[0]["next_run_at"]) == T0 + timedelta(seconds=60 + 120)  # luỹ thừa
    assert [s for _, s in w.tick(T0 + timedelta(seconds=180))["ran"]] == ["dead"]
    assert w.tick(T0 + timedelta(hours=2))["ran"] == []  # dead-letter không chạy lại
    j = jobs(env["eng"])[0]
    assert j["status"] == "dead" and j["attempts"] == 3 and "nguồn lỗi" in j["last_error"] and calls == [1, 2, 3]
    assert ("alert", "dead_letter") in events(env["eng"])


def test_expired_lease_is_recovered(env):
    w = W.Worker(env["eng"], "w1", lease_seconds=600)
    jid = w.enqueue("registry_integrity", "manual-1", T0)
    with env["eng"].begin() as c:  # worker khác chết giữa chừng
        c.execute(update(W.jobs_t).where(W.jobs_t.c.id == jid)
                  .values(status="running", attempts=1, started_at=T0, locked_by="dead-worker"))
    assert w.claim(T0 + timedelta(minutes=5)) is None  # đang running, giới hạn 1 việc
    w.recover_expired(T0 + timedelta(minutes=11))
    j = jobs(env["eng"], id=jid)[0]
    assert j["status"] == "queued" and j["last_error"] == "lease hết hạn"
    assert ("warn", "lease_expired") in events(env["eng"])


def test_kill_switch_pauses_and_resumes(env):
    w = W.Worker(env["eng"], "w1")
    W.set_paused(env["admin"], True, "test-governance")
    assert w.tick(T0) == {"state": "paused"} and jobs(env["eng"]) == []
    st = W.status(env["eng"], T0)
    assert st["paused"] and st["heartbeats"][0]["state"] == "paused"
    W.set_paused(env["admin"], False, "test-governance")
    assert w.tick(T0)["state"] == "running" and len(jobs(env["eng"])) == 1
    assert ("alert", "kill_switch") in events(env["eng"])
    os.environ["CFP_WORKER_ENABLED"] = "0"
    try:
        assert w.tick(T0 + timedelta(hours=1)) == {"state": "paused"}
    finally:
        del os.environ["CFP_WORKER_ENABLED"]


def test_stale_heartbeat_reported(env):
    W.Worker(env["eng"], "w1").tick(T0)
    st = W.status(env["eng"], T0 + timedelta(minutes=10))
    assert st["alive"] is False and st["heartbeats"][0]["stale"] is True


def test_concurrent_workers_never_run_a_job_twice(env):
    if not env["pg"]:
        pytest.skip("cần Postgres (SKIP LOCKED + advisory lock)")
    seen, lock = [], threading.Lock()

    def slow(eng, job):
        with lock:
            seen.append(job["id"])
        return {"ok": True}
    ws = [W.Worker(env["eng"], f"w{i}", handlers={"k": slow}, schedule={}, max_running=1) for i in range(4)]
    for i in range(12):
        ws[0].enqueue("k", f"k-{i}", T0)
    th = [threading.Thread(target=x.tick, args=(T0,)) for x in ws]
    [t.start() for t in th]; [t.join() for t in th]
    assert sorted(seen) == sorted(set(seen)) and len(seen) == 12
    assert {j["status"] for j in jobs(env["eng"])} == {"done"}


def test_worker_role_least_privilege(env):
    if not env["pg"]:
        pytest.skip("cần Postgres + 004")
    eng = env["eng"]
    W.Worker(eng, "w1").tick(T0)
    for stmt in ("update cfp_worker.logs set message = 'sửa'", "delete from cfp_worker.logs",
                 "delete from cfp_worker.jobs", "update cfp_worker.control set value = 'true'",
                 "insert into cfp_worker.control (key, value) values ('x', 'y')",
                 "select count(*) from cfp_office.tasks", "select count(*) from cfp_forum_auth.users"):
        with pytest.raises(DBAPIError, match="permission denied"):
            with eng.begin() as c:
                c.exec_driver_sql(stmt)
    with eng.connect() as c:
        assert c.execute(text("select current_user")).scalar() == "worker_app"


def test_status_endpoint(env, tmp_path):
    from fastapi.testclient import TestClient
    from services.forum.app import Stores, create_app
    d = tmp_path
    url = os.environ.get("CFP_WORKER_TEST_DB") or env["admin"]
    st = Stores(f"sqlite:///{d/'a.db'}", {"sieu-bo-doi": f"sqlite:///{d/'s.db'}", "si-ai-hstdn": f"sqlite:///{d/'h.db'}"},
                None, url)
    W.Worker(env["eng"], "w1").tick()
    r = TestClient(create_app(st)).get("/api/worker/status").json()
    assert r["configured"] and r["alive"] and r["jobs"]["done"] == 1
    assert "result" not in json.dumps(r["recent"]) and r["mode"] == "SANDBOX"
    st.dispose()
    st2 = Stores(f"sqlite:///{d/'a2.db'}", {"sieu-bo-doi": f"sqlite:///{d/'s2.db'}", "si-ai-hstdn": f"sqlite:///{d/'h2.db'}"})
    assert TestClient(create_app(st2)).get("/api/worker/status").json() == {
        "mode": "SANDBOX", "configured": False, "alive": False, "note": "Chưa cấu hình CFP_WORKER_DB: không có worker chạy."}


def test_migration_004_matches_code():
    from pathlib import Path
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable
    sql = (Path(__file__).resolve().parents[2] / "services/forum/sql/004_worker.sql").read_text(encoding="utf-8")
    for t in W.md.sorted_tables:
        assert str(CreateTable(t, if_not_exists=True).compile(dialect=postgresql.dialect())).strip() + ";" in sql, t.name
        assert f"alter table cfp_worker.{t.name} force row level security;" in sql


@pytest.mark.parametrize("outcome", ["done", "error"])
def test_stale_worker_cannot_overwrite_after_lease_lost(env, outcome):
    """Fencing: A nhận việc rồi treo quá lease → B thu hồi + nhận lại + hoàn tất → A xong muộn không ghi đè được."""
    def ok(eng, job):
        return {"by": job["locked_by"], "attempt": job["attempts"]}

    def boom(eng, job):
        raise RuntimeError("A lỗi muộn")
    hs = {"slow": ok}
    a = W.Worker(env["eng"], "worker-A", lease_seconds=60, handlers={"slow": ok if outcome == "done" else boom}, schedule={})
    b = W.Worker(env["eng"], "worker-B", lease_seconds=60, handlers=hs, schedule={})
    jid = a.enqueue("slow", "race-1", T0)
    job_a = a.claim(T0)
    assert job_a["attempts"] == 1 and job_a["locked_by"] == "worker-A"
    b.recover_expired(T0 + timedelta(seconds=61))  # A coi như chết
    job_b = b.claim(T0 + timedelta(seconds=61))
    assert job_b and job_b["id"] == jid and job_b["attempts"] == 2
    assert b.execute(job_b, T0 + timedelta(seconds=62)) == "done"
    assert a.execute(job_a, T0 + timedelta(seconds=63)) == "stale"  # A trả kết quả muộn → bị từ chối
    j = jobs(env["eng"], id=jid)[0]
    assert j["status"] == "done" and j["attempts"] == 2 and json.loads(j["result"]) == {"by": "worker-B", "attempt": 2}
    evs = events(env["eng"])
    assert ("warn", "stale_commit") in evs and evs.count(("info", "done")) == 1
    assert ("alert", "dead_letter") not in evs and ("error", "retry") not in evs


def test_same_worker_old_attempt_is_fenced(env):
    """Cùng worker nhận lại việc ở lần thử mới → kết quả của lần thử cũ không được ghi."""
    w = W.Worker(env["eng"], "w1", lease_seconds=60, handlers={"k": lambda e, j: {"a": j["attempts"]}}, schedule={})
    jid = w.enqueue("k", "same-1", T0)
    old = w.claim(T0)
    w.recover_expired(T0 + timedelta(seconds=61))
    new = w.claim(T0 + timedelta(seconds=61))
    assert w.execute(old, T0 + timedelta(seconds=62)) == "stale"
    assert w.execute(new, T0 + timedelta(seconds=63)) == "done"
    assert json.loads(jobs(env["eng"], id=jid)[0]["result"]) == {"a": 2}
