"""Integration + failure tests: autopilot (#207) against a REAL PR #195 backend (local uvicorn, ephemeral SQLite).

  python3 -m unittest discover -s sandbox/hub69-dispatch/tests -v
Needs fastapi/sqlalchemy/uvicorn and the #195 source (see office_harness.py). Without them the tests skip,
unless HUB69_REQUIRE_OFFICE=1 (CI) — then they fail.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))

from hub69_dispatch.adapters import FileSource  # noqa: E402
from hub69_dispatch.autopilot import Autopilot, Busy, SimulatedCrash  # noqa: E402
from hub69_dispatch.cli import load_config  # noqa: E402
from hub69_dispatch.office_client import OfficeClient, RetryPolicy  # noqa: E402
from office_harness import OfficeServer, deps_ok, office_src  # noqa: E402

FIXTURE = HERE / "fixtures" / "autopilot-working-link.json"
EVB = "https://github.com/charityfundplus/CFP.plus/blob/test/results"
T0 = datetime(2026, 11, 13, 13, 5, tzinfo=timezone.utc)
AGENTS_DOC, POLICY = load_config()
AGENTS = {a["key"]: a for a in AGENTS_DOC["agents"]}
SRC = office_src() if deps_ok() else None
REQUIRED = os.environ.get("HUB69_REQUIRE_OFFICE") == "1"


def one_task_fixture(tmp: Path, n: int = 1) -> FileSource:
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    p = tmp / "wl.json"
    p.write_text(json.dumps({"comments": doc["comments"][:n]}, ensure_ascii=False), encoding="utf-8")
    return FileSource(str(p))


@unittest.skipUnless(SRC or REQUIRED, "PR #195 backend not available (set HUB69_OFFICE_SRC)")
class OfficeIntegration(unittest.TestCase):
    def setUp(self):
        if not SRC:
            self.fail("HUB69_REQUIRE_OFFICE=1 but PR #195 source/deps missing")
        self.tmp = Path(tempfile.mkdtemp(prefix="hub69-test-"))
        self.srv = OfficeServer(SRC, self.tmp / "office").start()
        self.srv.grant_securitysi()
        self.state = self.tmp / "state"

    def tearDown(self):
        self.srv.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pilot(self, **kw) -> Autopilot:
        kw.setdefault("retry", RetryPolicy(attempts=3, base_delay=0))
        return Autopilot(base=self.srv.base, state_dir=self.state, agents=AGENTS, policy=POLICY,
                         secrets=self.srv.secrets, evidence_base=EVB, office_src=SRC, sleep=lambda s: None, **kw)

    def office_tasks(self, cid="691121") -> list[dict]:
        c = OfficeClient(self.srv.base)
        c.login(*self.srv.secrets["gov"])
        return c.get(f"/api/office/offices/{cid}")["tasks"]

    def assert_clean_handoff(self, task: dict):
        self.assertEqual(task["status"], "IN_REVIEW")
        self.assertEqual([h["to_status"] for h in task["history"]], ["QUEUED", "ACKED", "IN_PROGRESS", "IN_REVIEW"])
        self.assertEqual(len(task["evidence"]), 1)
        self.assertEqual(task["reviews"], [])  # the autopilot never reviews
        self.assertNotEqual(task["assignee_id"], task["reviewer_id"])

    # ------------------------------------------------------------------ acceptance
    def test_task_received_processed_stored_and_handed_to_reviewer(self):
        p = self.pilot()
        res = p.tick(FileSource(str(FIXTURE)), T0, "t1")
        st = {k: (p.store.task(k) or {}).get("stage") for k in ("wl#1", "wl#2", "wl#3", "wl#4")}
        self.assertEqual(st, {"wl#1": "HANDED_TO_REVIEWER", "wl#2": "HANDED_TO_REVIEWER",
                              "wl#3": "AWAITING_REAL_AGENT", "wl#4": None})
        self.assertIn("duplicate of open task wl#1", json.dumps(res["rejections"]))
        tasks = self.office_tasks()
        self.assertEqual(len(tasks), 2)
        for t in tasks:
            self.assert_clean_handoff(t)
        # Evidence sha in the Office == sha of the stored result file
        rec = p.store.task("wl#1")
        f = self.state / "results" / "wl-1.json"
        self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), rec["result_sha"])
        self.assertIn(rec["result_sha"], [e["sha"] for t in tasks for e in t["evidence"]])
        # read-back as the reviewer: it is assigned to them and visible; guest sees nothing
        rb = p.readback("wl#1")
        self.assertEqual(rb["reviewer_loop"]["status"], "IN_REVIEW")
        self.assertEqual(rb["reviewer_board"][0]["bucket"], "IN_REVIEW")
        self.assertEqual(sum(rb["guest_board_counts"].values()), 0)
        # routing: by capability + Working Link; SecuritySI explicitly named on wl#2
        self.assertEqual((rec["assignee"], rec["reviewer"]), ("691121", "ReviewSI"))
        self.assertEqual(p.store.task("wl#2")["reviewer"], "SecuritySI")
        self.assertEqual(p.store.task("wl#3")["assignee"], "691141")  # content: no executor → waits for real agent
        drafts = p.forum_drafts(["wl#1", "wl#2"])
        self.assertTrue(drafts and all(not d["posted"] and d["gate"] == "HOLD ACTIVATION" for d in drafts))

    def test_second_tick_and_office_restart_are_noops(self):
        p = self.pilot()
        p.tick(FileSource(str(FIXTURE)), T0, "t1")
        self.srv.stop()
        self.srv.start()  # same data dir → #195 state survives a process restart
        p2 = self.pilot()
        res = p2.tick(FileSource(str(FIXTURE)), T0 + timedelta(minutes=1), "t2")
        self.assertTrue(all(not h["changed"] for h in res["handled"]))
        writes = [x for x in p2.store.logs("t2") if x["step"] in ("office_create", "ack", "start", "evidence", "submit")]
        self.assertEqual(writes, [])
        self.assertEqual(len(self.office_tasks()), 2)

    # ------------------------------------------------------------------ crash / retry / dead letter
    def test_crash_after_every_step_recovers_exactly_once(self):
        for step in ("office_create", "ack", "start", "execute", "evidence", "submit"):
            with self.subTest(step=step):
                self.srv.stop()
                shutil.rmtree(self.tmp, ignore_errors=True)
                self.srv = OfficeServer(SRC, self.tmp / "office").start()
                src = one_task_fixture(self.tmp)
                with self.assertRaises(SimulatedCrash):
                    self.pilot(crash_after=step).tick(src, T0, "crash")
                self.pilot().tick(src, T0 + timedelta(minutes=1), "recover")
                tasks = self.office_tasks()
                self.assertEqual(len(tasks), 1)
                self.assert_clean_handoff(tasks[0])

    def test_lost_local_state_reuses_office_task_via_idempotency_key(self):
        src = one_task_fixture(self.tmp)
        self.pilot().tick(src, T0, "t1")
        shutil.rmtree(self.state)  # the dispatcher's own DB is gone; the Office must not get a duplicate
        p = self.pilot()
        p.tick(src, T0 + timedelta(minutes=1), "t2")
        self.assertEqual(len(self.office_tasks()), 1)
        self.assertIn("duplicate_reused", [x["outcome"] for x in p.store.logs("t2") if x["step"] == "office_create"])
        self.assert_clean_handoff(self.office_tasks()[0])

    def test_office_down_schedules_retry_then_completes(self):
        src = one_task_fixture(self.tmp)
        self.srv.stop()
        p = self.pilot(retry=RetryPolicy(attempts=2, base_delay=0))
        res = p.tick(src, T0, "down")
        self.assertEqual(res["handled"][0]["stage"], "RETRY")
        rec = p.store.task("wl#1")
        self.assertEqual((rec["attempts"], rec["dead"]), (1, 0))
        self.assertEqual(p.tick(src, T0 + timedelta(seconds=5), "too-early")["handled"], [])  # backoff respected
        self.srv.start()
        p2 = self.pilot()
        res = p2.tick(src, T0 + timedelta(minutes=5), "up")
        self.assertEqual(res["handled"][0]["stage"], "HANDED_TO_REVIEWER")
        self.assert_clean_handoff(self.office_tasks()[0])

    def test_transient_faults_inside_a_tick_are_retried(self):
        calls = {"n": 0}

        def flaky(method, path):
            if method == "POST" and path.endswith(("/evidence", "/ack")) and calls["n"] < 2:
                calls["n"] += 1
                raise ConnectionResetError("injected")
        p = self.pilot(transport=flaky)
        p.tick(one_task_fixture(self.tmp), T0, "flaky")
        self.assertEqual(calls["n"], 2)
        self.assert_clean_handoff(self.office_tasks()[0])
        self.assertTrue(any(x["step"] == "http" and x["outcome"] == "retry" for x in p.store.logs("flaky")))

    def test_permanent_error_dead_letters_until_requeued(self):
        tmp_srv = OfficeServer(SRC, self.tmp / "office2").start()  # SecuritySI NOT granted the reviewer role
        try:
            p = Autopilot(base=tmp_srv.base, state_dir=self.tmp / "s2", agents=AGENTS, policy=POLICY,
                          secrets=tmp_srv.secrets, evidence_base=EVB, office_src=SRC, sleep=lambda s: None,
                          retry=RetryPolicy(attempts=1, base_delay=0))
            src = one_task_fixture(self.tmp, 2)  # wl#2 names SecuritySI as reviewer
            p.tick(src, T0, "t1")
            rec = p.store.task("wl#2")
            self.assertEqual(rec["dead"], 1)
            self.assertIn("422", rec["last_error"])
            self.assertEqual(p.store.task("wl#1")["stage"], "HANDED_TO_REVIEWER")  # one bad task does not block others
            p.tick(src, T0 + timedelta(hours=2), "t2")
            self.assertEqual(p.store.task("wl#2")["dead"], 1)  # stays dead, no retry storm
            tmp_srv.grant_securitysi()  # the fix (sandbox: role granted by #195 admin CLI)
            p.requeue("wl#2", T0 + timedelta(hours=2))
            p.tick(src, T0 + timedelta(hours=3), "t3")
            self.assertEqual(p.store.task("wl#2")["stage"], "HANDED_TO_REVIEWER")
        finally:
            tmp_srv.stop()

    def test_gives_up_after_max_attempts(self):
        src = one_task_fixture(self.tmp)
        self.srv.stop()
        p = self.pilot(retry=RetryPolicy(attempts=1, base_delay=0))
        t = T0
        for i in range(6):
            t += timedelta(hours=2)
            p.tick(src, t, f"t{i}")
        rec = p.store.task("wl#1")
        self.assertEqual((rec["dead"], rec["attempts"]), (1, 5))

    def test_concurrent_tick_is_refused(self):
        p = self.pilot()
        with p.store.lock():
            with self.assertRaises(Busy):
                self.pilot().tick(one_task_fixture(self.tmp), T0, "x")


class CommittedPilotEvidence(unittest.TestCase):
    """Offline: the committed pilot is self-consistent (result files ↔ Evidence sha read back from the Office)."""
    D = HERE / "evidence" / "autopilot-pilot"

    def test_result_files_match_office_evidence_and_reviewer_handoff(self):
        rb = json.loads((self.D / "readback.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(rb), ["wl#1", "wl#2"])
        for key, r in rb.items():
            f = self.D / "results" / f"{key.replace('#', '-')}.json"
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            self.assertEqual([e["sha"] for e in r["evidence"]], [sha])
            self.assertEqual(r["office_status"], "IN_REVIEW")
            self.assertEqual(r["reviewer_loop"]["status"], "IN_REVIEW")
            self.assertEqual(r["reviews"], [])
        log = [json.loads(x) for x in (self.D / "run-log.jsonl").read_text(encoding="utf-8").splitlines()]
        later = [x for x in log if x["run"] != "tick-1" and x["step"] in ("office_create", "ack", "start", "evidence", "submit")]
        self.assertEqual(later, [], "ticks 2/3 must not write")


@unittest.skipUnless(SRC or REQUIRED, "PR #195 source not available")
class ExecutorDeterminism(unittest.TestCase):
    def test_registry_digest_does_not_depend_on_directory_order(self):
        from unittest import mock
        from hub69_dispatch.autopilot import exec_registry_integrity
        real = Path.glob
        ctx = {"office_src": SRC, "agents": AGENTS}
        digests = set()
        for order in (sorted, lambda xs: sorted(xs, reverse=True)):
            with mock.patch.object(Path, "glob", lambda self, pat: iter(order(list(real(self, pat))))):
                out = exec_registry_integrity({}, ctx)
            digests.add(out["digest"])
            self.assertEqual(out["problems"], [])
        self.assertEqual(len(digests), 1)
        self.assertEqual(out["finding_for_195"]["id"], "PR195-REGISTRY-GLOB-ORDER")


class NoPostingTests(unittest.TestCase):
    def test_autopilot_has_no_write_path_to_the_forum(self):
        src = (HERE / "hub69_dispatch" / "autopilot.py").read_text(encoding="utf-8")
        self.assertNotIn("post_comment", src)
        self.assertNotIn("/issues/", src)


if __name__ == "__main__":
    unittest.main()
