"""HUB 69 dispatcher regression tests (stdlib only): python3 -m unittest discover -s sandbox/hub69-dispatch/tests -v"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from hub69_dispatch.cli import load_config  # noqa: E402
from hub69_dispatch.engine import run  # noqa: E402
from hub69_dispatch.protocol import parse_comment  # noqa: E402

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
AGENTS_DOC, POLICY = load_config()
AGENTS = {a["key"]: a for a in AGENTS_DOC["agents"]}


class Thread:
    """Builds a synthetic comment thread (refs 'sim#N', clearly not GitHub ids)."""

    def __init__(self):
        self.comments, self.n = [], 0

    def post(self, body: str, login: str = "charityfundplus") -> str:
        self.n += 1
        ref = f"sim#{self.n}"
        self.comments.append({"ref": ref, "body": body, "author_login": login,
                              "created_at": f"2026-11-13T{self.n // 60:02d}:{self.n % 60:02d}:00Z", "url": None})
        return ref

    def task(self, title, assignee, reviewer, priority="P1"):
        return self.post(f"**SI AI / Siêu Bộ Đôi:** CMP 267\n**Nhiệm vụ:** {title}\n**Assignee:** {assignee}\n"
                         f"**Reviewer:** {reviewer}\n**Priority:** {priority}\n**Trạng thái:** OPEN")

    def step(self, task, actor, status, result="", verdict=""):
        body = f"**SI AI / Siêu Bộ Đôi:** {actor}\n**Task:** {task}\n**Trạng thái:** {status}\n"
        if result:
            body += f"**Kết quả và Evidence URL:** {result}\n"
        if verdict:
            body += f"**Verdict:** {verdict}\n"
        return self.post(body)

    def run(self):
        msgs = []
        for c in self.comments:
            msgs += parse_comment(c, "test", {"charityfundplus"}, {})
        return run(msgs, POLICY, AGENTS, NOW)


def by_key(snap):
    return {t["key"]: t for t in snap["tasks"]}


class ProtocolTests(unittest.TestCase):
    def test_real_issue201_comment_is_relayed_ack_without_task(self):
        data = json.loads((HERE / "fixtures" / "issue201-live-20261113.json").read_text(encoding="utf-8"))
        msgs = []
        for c in data["comments"]:
            msgs += parse_comment(c, "github", {"charityfundplus"}, {})
        self.assertEqual(len(msgs), 1, "the invitation letter is not a protocol message")
        m = msgs[0]
        self.assertEqual((m.kind, m.actor_name.split()[0], m.provenance, m.task),
                         ("ACK", "Perplexity", "relayed_by_operator", None))
        snap, out = run(msgs, POLICY, AGENTS, NOW)
        self.assertEqual(snap["tasks"], [])
        self.assertIn("no task reference", snap["rejections"][0]["reason"])

    def test_office_page_copy_text_is_understood(self):
        """Text produced by the HUB 69 office page 'copy for forum' button (written by its Node test)."""
        sample = ROOT / "sandbox" / "hub69-working-office" / "evidence" / "copy-template-sample.txt"
        c = {"ref": "201#3", "body": sample.read_text(encoding="utf-8"), "author_login": "charityfundplus"}
        m = parse_comment(c, "github", {"charityfundplus"}, {})[0]
        self.assertEqual((m.kind, m.task, m.actor, m.provenance), ("ACK", "201#6813472700", "691121", "relayed_by_operator"))

    def test_compact_header_and_bound_login(self):
        c = {"ref": "201#1", "body": "HUB69 ACK 201#9\nactor: 691121", "author_login": "claude-bot",
             "created_at": "2026-11-13T00:00:00Z"}
        m = parse_comment(c, "github", {"charityfundplus"}, {"claude-bot": "691121"})[0]
        self.assertEqual((m.kind, m.task, m.actor, m.provenance), ("ACK", "201#9", "691121", "direct_bound_login"))

    def test_dispatcher_comments_are_ignored_anti_loop(self):
        c = {"ref": "201#2", "body": "<!-- hub69-dispatch key=abc -->\n**Trạng thái:** ACK", "author_login": "x"}
        self.assertEqual(parse_comment(c, "github", set(), {}), [])


class LifecycleTests(unittest.TestCase):
    def test_full_loop_task_ack_result_evidence_review(self):
        th = Thread()
        t = th.task("Sửa P1 localStorage", "691121", "ReviewSI")
        th.step(t, "Claude Code (691121)", "ACK")
        th.step(t, "Claude Code", "OUTPUT READY", "commit https://github.com/x/y/commit/abc test log https://e/x.log")
        th.step(t, "ReviewSI", "REVIEW", verdict="PASS")
        snap, out = th.run()
        task = by_key(snap)[t]
        self.assertEqual(task["state"], "VERIFIED")
        self.assertEqual([h["kind"] for h in task["history"]], ["TASK", "ACK", "RESULT", "EVIDENCE", "REVIEW"])
        self.assertIsNone(task["slot"], "verified task frees its slot")
        self.assertEqual(snap["slots"]["active"], 0)
        self.assertEqual([o["kind"] for o in out], ["HUMAN_DECISION"], "never auto-closes; asks Human Governance")

    def test_rule_violations_are_rejected_with_reason(self):
        th = Thread()
        t = th.task("Kiểm thử mobile", "Codex 2", "ReviewSI")
        th.step(t, "Codex 1", "ACK")                                   # wrong actor
        th.step(t, "Codex 2", "OUTPUT READY", "xong")                  # result before ACK
        th.step(t, "Codex 2", "ACK")
        th.post(f"HUB69 EVIDENCE {t}\nactor: Codex 2\n**Kết quả:** không có link")  # result missing + no URL
        th.step(t, "Codex 2", "OUTPUT READY", "https://e/run.log")
        th.step(t, "Codex 2", "REVIEW", verdict="PASS")                # self-review
        th.step(t, "SecuritySI", "REVIEW", verdict="PASS")             # not the assigned reviewer
        snap, _ = th.run()
        reasons = [r["reason"] for r in snap["rejections"]]
        self.assertTrue(any("ACK must come from assignee" in r for r in reasons))
        self.assertTrue(any("RESULT not valid in state DISPATCHED" in r for r in reasons))
        self.assertTrue(any("EVIDENCE needs at least one URL" in r for r in reasons))
        self.assertTrue(any("self-review rejected" in r for r in reasons))
        self.assertTrue(any("assigned reviewer ReviewSI" in r for r in reasons))
        self.assertEqual(by_key(snap)[t]["state"], "IN_REVIEW")

    def test_task_needs_independent_reviewer_and_no_duplicates(self):
        th = Thread()
        th.task("A", "691121", "691121")
        th.task("A", "691121", "")
        ok = th.task("B", "691121", "ReviewSI")
        th.task("b ", "Codex 1", "ReviewSI")
        snap, _ = th.run()
        self.assertEqual(list(by_key(snap)), [ok])
        reasons = " | ".join(r["reason"] for r in snap["rejections"])
        self.assertIn("reviewer must differ", reasons)
        self.assertIn("independent", reasons)
        self.assertIn("duplicate of open task", reasons)

    def test_review_fail_returns_to_rework_and_keeps_slot(self):
        th = Thread()
        t = th.task("X", "691121", "ReviewSI")
        th.step(t, "691121", "ACK")
        th.step(t, "691121", "OUTPUT READY", "https://e/1")
        th.step(t, "ReviewSI", "REVIEW", verdict="FAIL")
        snap, _ = th.run()
        task = by_key(snap)[t]
        self.assertEqual((task["state"], task["slot"]), ("ACKED", "shared"))

    def test_blocked_is_visible_and_resumable(self):
        th = Thread()
        t = th.task("Y", "691121", "ReviewSI")
        th.step(t, "691121", "ACK")
        th.post(f"**SI AI / Siêu Bộ Đôi:** 691121\n**Task:** {t}\n**Trạng thái:** BLOCKED\n"
                f"**Vướng mắc / Next Action:** thiếu SMOKE_* secrets")
        snap, out = th.run()
        self.assertEqual(by_key(snap)[t]["state"], "BLOCKED")
        self.assertIn("SMOKE_", [o for o in out if o["kind"] == "BLOCKER"][0]["body"])
        th.step(t, "691121", "OUTPUT READY", "https://e/2")
        snap, _ = th.run()
        self.assertEqual(by_key(snap)[t]["state"], "IN_REVIEW")


class SlotTests(unittest.TestCase):
    def test_max_five_with_one_reserved_p0_for_openai(self):
        th = Thread()
        p1 = [th.task(f"P1 việc {i}", "691121" if i % 2 else "Codex 1", "ReviewSI") for i in range(6)]
        p0_other = th.task("P0 không thuộc OpenAI", "691141", "ReviewSI", "P0")
        p0_openai = th.task("P0 hồ sơ OpenAI 69118", "691181", "SecuritySI", "P0")
        snap, out = th.run()
        tasks = by_key(snap)
        active = [t for t in tasks.values() if t["slot"]]
        self.assertEqual(len(active), 5)
        self.assertEqual(tasks[p0_openai]["slot"], "reserved_p0")
        self.assertEqual(sum(1 for t in active if t["slot"] == "shared"), 4)
        # P0 of a non-reserved owner outranks P1 for the shared slots... but they were already granted in time
        # order, so it waits: slots are never pre-empted from running work.
        self.assertEqual(tasks[p0_other]["state"], "OFFERED")
        self.assertEqual(sum(1 for k in p1 if tasks[k]["state"] == "DISPATCHED"), 4)
        self.assertTrue(any(o["kind"] == "WAITING_SLOT" and o["task"] == p0_other for o in out))

    def test_reserved_slot_is_not_used_by_others_and_freed_slot_goes_to_highest_priority(self):
        th = Thread()
        firsts = [th.task(f"việc {i}", "Codex 1", "ReviewSI") for i in range(4)]
        late_p1 = th.task("việc P1 muộn", "Codex 2", "ReviewSI")
        late_p0 = th.task("việc P0 muộn", "691141", "ReviewSI", "P0")
        snap, _ = th.run()
        self.assertEqual(snap["slots"]["active"], 4, "5th slot stays reserved for OpenAI P0")
        th.step(late_p1, "Codex 2", "ACK")  # no slot yet → rejected
        t0 = firsts[0]
        th.step(t0, "Codex 1", "ACK")
        th.step(t0, "Codex 1", "OUTPUT READY", "https://e/3")
        th.step(t0, "ReviewSI", "REVIEW", verdict="PASS")
        snap, _ = th.run()
        tasks = by_key(snap)
        self.assertEqual(tasks[late_p0]["state"], "DISPATCHED", "P0 beats older P1 for the freed slot")
        self.assertEqual(tasks[late_p1]["state"], "OFFERED")
        self.assertTrue(any("no execution slot" in r["reason"] for r in snap["rejections"]))


class RoutingTests(unittest.TestCase):
    def auto(self, th, title, cap, reviewer="auto"):
        return th.post(f"**SI AI / Siêu Bộ Đôi:** CMP 267\n**Nhiệm vụ:** {title}\n**Năng lực:** {cap}\n"
                       f"**Assignee:** auto\n**Reviewer:** {reviewer}\n**Priority:** P2\n**Trạng thái:** OPEN")

    def test_capability_routing_prefers_executor_and_independent_reviewer(self):
        th = Thread()
        a = self.auto(th, "Registry check", "registry_check")
        b = self.auto(th, "Bản tin", "content")
        snap, _ = th.run()
        t = by_key(snap)
        self.assertEqual((t[a]["assignee"], t[a]["reviewer"], t[a]["routed"]), ("691121", "ReviewSI", "auto"))
        self.assertEqual(t[b]["assignee"], "691141")  # capable + Working Link, lowest key; no executor → waits
        for x in t.values():
            self.assertNotEqual(x["assignee"], x["reviewer"])

    def test_unknown_capability_is_rejected_not_guessed(self):
        th = Thread()
        self.auto(th, "Bay lên mặt trăng", "rocketry")
        snap, _ = th.run()
        self.assertEqual(snap["tasks"], [])
        self.assertIn("no agent with capability 'rocketry'", snap["rejections"][0]["reason"])

    def test_routing_balances_load_among_capable_agents(self):
        th = Thread()
        keys = [self.auto(th, f"Nội dung {i}", "content") for i in range(3)]
        snap, _ = th.run()
        got = [by_key(snap)[k]["assignee"] for k in keys]
        self.assertEqual(len(set(got)), 3, got)

    def test_every_routable_agent_has_its_working_link_page(self):
        for a in AGENTS.values():
            if a.get("working_link"):
                self.assertTrue((ROOT / a["working_link"]).is_file(), a["key"])


class OutboxAndGateTests(unittest.TestCase):
    def test_outbox_is_idempotent_and_detects_already_posted(self):
        th = Thread()
        th.task("Z", "691121", "ReviewSI")
        _, out1 = th.run()
        _, out2 = th.run()
        self.assertEqual([o["key"] for o in out1], [o["key"] for o in out2])
        th.post(out1[0]["body"])  # dispatcher reply appears in channel → ignored by parser
        _, out3 = th.run()
        self.assertEqual([o["key"] for o in out3], [o["key"] for o in out1])
        self.assertTrue(re.search(r"<!-- hub69-dispatch key=\w+ -->", out1[0]["body"]))

    def test_post_is_held_without_human_approval(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("HUB69_")}
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, str(HERE / "run.py"), "post", "--source",
                                f"file:{HERE / 'fixtures' / 'issue201-live-20261113.json'}", "--out", d,
                                "--now", "2026-11-13T12:00:00Z"], env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
            self.assertIn("HOLD ACTIVATION", p.stdout)
            self.assertFalse((Path(d) / "sent.json").exists())
            env["HUB69_DISPATCH_ENABLED"] = "1"  # enabled but no approval link → still HOLD
            p = subprocess.run([sys.executable, str(HERE / "run.py"), "post", "--source",
                                f"file:{HERE / 'fixtures' / 'issue201-live-20261113.json'}", "--out", d], env=env,
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 3)


class RegistryTests(unittest.TestCase):
    def test_numeric_agent_keys_exist_in_registry_with_same_parent(self):
        reg = json.loads((ROOT / "registry" / "ai-entity-registry.json").read_text(encoding="utf-8"))
        for a in AGENTS_DOC["agents"]:
            if a["key"].isdigit():
                self.assertIn(a["key"], reg, a["key"])
                self.assertEqual(reg[a["key"]].get("parent_id"), a["parent"], a["key"])
                self.assertEqual(reg[a["key"]]["name"], a["name"], a["key"])
            else:
                self.assertEqual(a.get("id"), "PENDING", f"{a['key']} must not claim an ID")
        self.assertEqual(set(POLICY["reserved_p0"]["owners"]), {"69118", "691181"})
        self.assertEqual(POLICY["max_parallel"], 5)


if __name__ == "__main__":
    unittest.main()
