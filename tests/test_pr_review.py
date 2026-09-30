import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "pr_review.py"
spec = importlib.util.spec_from_file_location("pr_review", MODULE_PATH)
pr_review = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = pr_review
spec.loader.exec_module(pr_review)


class PrReviewTests(unittest.TestCase):
    def test_relevant_paths(self):
        self.assertTrue(pr_review.is_relevant_file("registry/69116.md"))
        self.assertTrue(pr_review.is_relevant_file("governance/validation/spec.md"))
        self.assertTrue(pr_review.is_relevant_file("config/rules.yaml"))
        self.assertTrue(pr_review.is_relevant_file("scripts/pr_review.py"))
        self.assertFalse(pr_review.is_relevant_file("assets/logo.png"))

    def test_split_and_filter_diff(self):
        diff = (
            "diff --git a/registry/1.md b/registry/1.md\n--- a/registry/1.md\n+++ b/registry/1.md\n+X\n"
            "diff --git a/assets/a.png b/assets/a.png\n--- a/assets/a.png\n+++ b/assets/a.png\n+binary\n"
        )
        filtered, included, excluded = pr_review.filter_relevant_diff(diff)
        self.assertIn("registry/1.md", filtered)
        self.assertEqual(included, ["registry/1.md"])
        self.assertEqual(excluded, ["assets/a.png"])

    def test_chunking_preserves_content(self):
        diff = "diff --git a/registry/a.md b/registry/a.md\n" + ("+x\n" * 100)
        chunks, truncated = pr_review.chunk_diff(diff, max_chars=80)
        self.assertGreater(len(chunks), 1)
        self.assertFalse(truncated)
        self.assertEqual("".join(chunks), diff)

    def test_status_precedence(self):
        self.assertEqual(pr_review.normalize_status("## Status\n**PASS WITH CHANGES**"), "PASS WITH CHANGES")
        self.assertEqual(pr_review.normalize_status("FAIL"), "FAIL")
        self.assertEqual(pr_review.normalize_status("No status"), "FAIL")

    def test_comment_marker_and_governance_authority(self):
        body = pr_review.build_no_relevant_comment([], ["README.md"])
        self.assertIn(pr_review.COMMENT_MARKER, body)
        self.assertIn("Human Governance retains final decision authority", body)


if __name__ == "__main__":
    unittest.main()
