"""Kiểm thử bộ công cụ 87788 • Siêu Bộ Tam. Chạy: python3 -m unittest discover -s tests -v"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import trio  # noqa: E402

PLATFORMS = json.loads(trio.PLATFORMS_PATH.read_text("utf-8"))["platforms"]

FIXTURE = """# t
## Chương 0 • Nền Tảng
| ID | Tên | Link | Tình trạng | Nhóm |
| :--- | :--- | :--- | :--- | :--- |
| `0` | Nền Tảng | [Mở](https://app.notion.com/p/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa) | CANDIDATE REVIEW | 000 |
| `00` | Nền Tảng Tổng Thể | [Mở](https://app.notion.com/p/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb) | CANDIDATE REVIEW | 000 |
## Chương 2 • Con Người
| `2` | Con Người | [Mở](https://app.notion.com/p/cccccccccccccccccccccccccccccccc) | CANDIDATE REVIEW | 135 |
| `22` | Trùng trang | [Mở](https://app.notion.com/p/cccccccccccccccccccccccccccccccc) | CANDIDATE REVIEW | 246 |
| `3x` | Sai định dạng | PENDING | PENDING | 135 |
| `0` | Trùng ID | PENDING | PENDING | 000 |
| `5` | Sai Chương | PENDING | PENDING | 135 |
"""


def fixture_rows():
    return trio.parse_index(FIXTURE)


class TestInventory(unittest.TestCase):
    def test_real_source_counts(self):
        rows, excluded, prov = trio.load_inventory()
        inv = trio.check_inventory(rows, excluded)
        self.assertEqual(prov["index"]["rows"], 91)
        self.assertEqual(prov["index"]["commit"], "77102841601f262a7b91389244896b19e58de821")
        self.assertEqual(len(inv["active"]), 104)  # 90 + 6 bổ sung + 7 hồ sơ Siêu Bộ Tam + 6873 Muse
        self.assertEqual(inv["chapters_covered"], [str(d) for d in range(10)])
        self.assertFalse([f for f in inv["findings"] if f["severity"] == "HIGH"])
        self.assertNotIn("2273", [r["id"] for r in inv["active"]])

    def test_check_cli_reports_active_count(self):
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = trio.main(["check"])
        out = json.loads(buf.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(out["active_count"], 104)
        self.assertNotIn("active", out)

    def test_packs_for_selected_id_and_unknown_id_rejected(self):
        rows, excluded, _ = trio.load_inventory()
        inv = trio.check_inventory(rows, excluded)
        plats = json.loads(trio.PLATFORMS_PATH.read_text("utf-8"))["platforms"]
        with tempfile.TemporaryDirectory() as d:
            made = trio.make_packs(inv["active"], plats, Path(d), ("6873",), ("claude_project", "gemini"))
            self.assertEqual(made, ["packs/6873-claude_project.md", "packs/6873-gemini.md"])
            self.assertIn("f38caac9a557828a98dc81dc26193587", (Path(d) / made[0]).read_text("utf-8"))
            with self.assertRaises(trio.GuardError):
                trio.make_packs(inv["active"], plats, Path(d), ("99999",), ("gemini",))

    def test_leading_zero_ids_distinct(self):
        ids = [r["id"] for r in fixture_rows()]
        self.assertIn("0", ids)
        self.assertIn("00", ids)

    def test_findings_detected(self):
        inv = trio.check_inventory(fixture_rows(), {})
        codes = {(f["code"], f["id"]) for f in inv["findings"]}
        self.assertIn(("ID_OUTSIDE_0_9", "3x"), codes)
        self.assertIn(("ID_DUPLICATE", "0"), codes)
        self.assertIn(("GROUP_MISMATCH", "2"), codes)
        self.assertIn(("CHAPTER_MISMATCH", "5"), codes)
        self.assertIn(("LINK_SHARED", "2,22"), codes)
        self.assertIn(("LINK_MISSING", "5"), codes)
        # ID trùng không được cộng hai lần
        self.assertEqual([r["id"] for r in inv["active"]].count("0"), 1)

    def test_excluded_not_active(self):
        inv = trio.check_inventory(fixture_rows(), {"00": "loại"})
        self.assertNotIn("00", [r["id"] for r in inv["active"]])


class TestPlanGuards(unittest.TestCase):
    def setUp(self):
        rows, excluded, _ = trio.load_inventory()
        self.active = trio.check_inventory(rows, excluded)["active"]
        self.by_id = {r["id"]: r for r in self.active}
        self.plan = trio.make_plan(self.active, PLATFORMS)

    def test_plan_deterministic(self):
        again = trio.make_plan(list(reversed(self.active)), PLATFORMS)
        self.assertEqual(self.plan["plan_sha256"], again["plan_sha256"])

    def test_trio_order_and_not_verified(self):
        for item in self.plan["items"]:
            t = item["overlay"]["trio"]
            self.assertEqual([x["key"] for x in t], ["quantum", "si_ai", "software"])
            self.assertTrue(all(x["capability_status"] == "NOT VERIFIED" for x in t))

    def test_identity_preserved(self):
        for item in self.plan["items"]:
            src = self.by_id[item["id"]]
            ident = item["overlay"]["identity"]
            self.assertEqual((ident["id"], ident["name"], ident["link"]), (src["id"], src["name"], src.get("link")))

    def _ov(self):
        return json.loads(json.dumps(self.plan["items"][0]["overlay"]))

    def test_guard_forbidden_field(self):
        ov = self._ov()
        ov["trio"][0]["parent"] = "6"
        with self.assertRaises(trio.GuardError):
            trio.guard_overlay(ov, self.by_id)

    def test_guard_identity_change(self):
        ov = self._ov()
        ov["identity"]["name"] = "Đổi tên"
        with self.assertRaises(trio.GuardError):
            trio.guard_overlay(ov, self.by_id)
        # kẻ tấn công tính lại hash cho khớp: lớp so danh tính với nguồn vẫn phải chặn
        ov["identity_sha256"] = trio.sha256_bytes(trio.canon(ov["identity"]))
        with self.assertRaisesRegex(trio.GuardError, "Danh tính"):
            trio.guard_overlay(ov, self.by_id)

    def test_guard_hash_tamper(self):
        ov = self._ov()
        ov["identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(trio.GuardError, "identity_sha256"):
            trio.guard_overlay(ov, self.by_id)

    def test_guard_new_id(self):
        ov = self._ov()
        ov["identity"]["id"] = "999999999"
        with self.assertRaises(trio.GuardError):
            trio.guard_overlay(ov, self.by_id)

    def test_guard_unverified_claim(self):
        ov = self._ov()
        ov["trio"][0]["capability_status"] = "ACTIVE"
        with self.assertRaises(trio.GuardError):
            trio.guard_overlay(ov, self.by_id)

    def test_guard_order(self):
        ov = self._ov()
        ov["trio"].reverse()
        with self.assertRaises(trio.GuardError):
            trio.guard_overlay(ov, self.by_id)


class TestApplyRollback(unittest.TestCase):
    def setUp(self):
        rows, excluded, _ = trio.load_inventory()
        self.active = trio.check_inventory(rows, excluded)["active"]
        self.plan = trio.make_plan(self.active, PLATFORMS)
        self.out = Path(tempfile.mkdtemp(prefix="cfp87788-"))

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def files(self):
        return sorted(p.name for p in (self.out / "overlays").glob("*.json")) if (self.out / "overlays").exists() else []

    def test_batches_cover_all_and_verify(self):
        n = (self.plan["count"] + 9) // 10
        for b in range(n):
            trio.apply_plan(self.plan, self.out, 10, b)
        self.assertEqual(len(self.files()), 104)
        v = trio.verify(self.out, self.plan)
        self.assertEqual((v["checked"], v["hash_ok"], v["identity_ok"], v["matches_plan"]), (104, 104, 104, 104))
        self.assertEqual(v["problems"], [])

    def test_idempotent(self):
        trio.apply_plan(self.plan, self.out, 200, 0)
        r = trio.apply_plan(self.plan, self.out, 200, 0)
        self.assertEqual(r["written"], [])
        self.assertEqual(len(r["skipped"]), 104)

    def test_crash_recovery(self):
        with self.assertRaises(KeyboardInterrupt):
            trio.apply_plan(self.plan, self.out, 10, 0, run_id="crash", _crash_after=4)
        self.assertEqual(len(self.files()), 4)
        undone = trio.recover(self.out)
        self.assertEqual(undone, ["crash"])
        self.assertEqual(self.files(), [])
        self.assertEqual(trio.recover(self.out), [])  # không hoàn tác hai lần

    def test_rollback_restores_previous(self):
        trio.apply_plan(self.plan, self.out, 5, 0, run_id="r1")
        before = {f: (self.out / "overlays" / f).read_bytes() for f in self.files()}
        changed = json.loads(json.dumps(self.plan))
        changed["items"][0]["overlay"]["kind"] = "SUPER_PAIR_V2"
        r = trio.apply_plan(changed, self.out, 5, 0, run_id="r2")
        first = self.plan["items"][0]["id"] + ".json"
        self.assertEqual(r["written"], [self.plan["items"][0]["id"]])
        self.assertNotEqual((self.out / "overlays" / first).read_bytes(), before[first])
        trio.rollback(self.out, "r2")
        after = {f: (self.out / "overlays" / f).read_bytes() for f in self.files()}
        self.assertEqual(before, after)

    def test_refuses_overwrite_other_identity(self):
        trio.apply_plan(self.plan, self.out, 1, 0, run_id="a")
        first = self.plan["items"][0]["id"]
        p = self.out / "overlays" / f"{first}.json"
        p.write_text(json.dumps({"identity": {"id": "OTHER"}}))
        with self.assertRaises(trio.GuardError):
            trio.apply_plan(self.plan, self.out, 1, 0, run_id="b")

    def test_refuses_outside_sandbox(self):
        with self.assertRaises(trio.GuardError):
            trio._safe_out(Path("/etc/cfp"))

    def test_refuses_production_env(self):
        import os
        os.environ["CFP_PRODUCTION"] = "1"
        try:
            with self.assertRaises(trio.GuardError):
                trio._safe_out(self.out)
        finally:
            del os.environ["CFP_PRODUCTION"]

    def test_packs(self):
        made = trio.make_packs(self.active, PLATFORMS, self.out)
        self.assertEqual(len(made), 12)
        txt = (self.out / "packs" / "87788-claude_code.md").read_text("utf-8")
        self.assertIn("87788", txt)
        self.assertIn("NOT VERIFIED", txt)
        self.assertIn("Siêu Lượng Tử", txt.split("Siêu Phần Mềm")[0])


if __name__ == "__main__":
    unittest.main()
