"""Tests for tools/build_pages.py. Run: python3 -m unittest discover -s tests/website -v"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_pages as bp  # noqa: E402


def page(pid, parent="69", title="T", extra="", body="Nội dung"):
    return f'---\nid: "{pid}"\ntitle: {title}\nparent: "{parent}"\n{extra}---\n\n{body}\n'


class Site:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.content = self.root / "content" / "pages"
        self.content.mkdir(parents=True)
        (self.root / "69").mkdir()
        (self.root / "69" / "index.html").write_text("<title>HUB 69</title>hand-written", encoding="utf-8")

    def add(self, name, text):
        (self.content / name).write_text(text, encoding="utf-8")

    def build(self, check=False):
        return bp.build(self.root, check, content_dir=self.content, site_root=self.root)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.s = Site()

    def tearDown(self):
        self.s.tmp.cleanup()

    def test_renders_page_with_breadcrumb_and_children(self):
        self.s.add("6900001.md", page("6900001", title="Cha"))
        self.s.add("69000011.md", page("69000011", parent="6900001", title="Con"))
        self.assertEqual(self.s.build(), [])
        out = (self.s.root / "6900001" / "index.html").read_text(encoding="utf-8")
        self.assertIn(bp.GENERATED_MARK, out)
        self.assertIn('href="/69/">HUB 69</a>', out)          # breadcrumb uses existing page title
        self.assertIn('href="/69000011/"', out)                # child listed automatically
        self.assertIn('rel="canonical" href="https://cfp.plus/6900001/"', out)

    def test_preserves_leading_zeros(self):
        self.s.add("0069.md", page("0069"))
        self.assertEqual(self.s.build(), [])
        self.assertTrue((self.s.root / "0069" / "index.html").is_file())

    def test_never_overwrites_hand_written_page(self):
        self.s.add("69.md", page("69", parent="69"))  # also self-parent
        (self.s.root / "70").mkdir()
        (self.s.root / "70" / "index.html").write_text("<title>x</title>", encoding="utf-8")
        self.s.add("70.md", page("70"))
        errs = self.s.build()
        self.assertTrue(any("70/index.html is a hand-written page" in e for e in errs))
        self.assertEqual((self.s.root / "70" / "index.html").read_text(encoding="utf-8"), "<title>x</title>")

    def test_rejects_bad_ids_and_missing_parent(self):
        self.s.add("abc.md", page("abc"))
        self.s.add("6666601.md", page("6666601"))
        self.s.add("123.md", page("124"))
        self.s.add("125.md", page("125", parent="999999"))
        errs = "\n".join(self.s.build())
        self.assertIn("must be digits only", errs)
        self.assertIn("legacy namespace 66666", errs)
        self.assertIn("file name must equal id", errs)
        self.assertIn("parent 999999 does not exist", errs)

    def test_nothing_written_when_any_error(self):
        self.s.add("6900002.md", page("6900002"))
        self.s.add("6900003.md", page("6900003", parent="1"))
        self.assertNotEqual(self.s.build(), [])
        self.assertFalse((self.s.root / "6900002").exists())

    def test_draft_not_published(self):
        self.s.add("6900004.md", page("6900004", extra="draft: true\n"))
        self.assertEqual(self.s.build(), [])
        self.assertFalse((self.s.root / "6900004").exists())

    def test_check_mode_writes_nothing(self):
        self.s.add("6900005.md", page("6900005"))
        self.assertEqual(self.s.build(check=True), [])
        self.assertFalse((self.s.root / "6900005").exists())

    def test_unknown_key_rejected(self):
        self.s.add("6900006.md", page("6900006", extra="canonical_id: 1\n"))
        self.assertTrue(any("unknown key" in e for e in self.s.build()))

    def test_regenerates_own_output(self):
        self.s.add("6900007.md", page("6900007", body="v1"))
        self.assertEqual(self.s.build(), [])
        self.s.add("6900007.md", page("6900007", body="v2"))
        self.assertEqual(self.s.build(), [])
        self.assertIn("v2", (self.s.root / "6900007" / "index.html").read_text(encoding="utf-8"))


class MarkdownSafetyTests(unittest.TestCase):
    def test_raw_html_is_escaped(self):
        out = bp.render_markdown('<script>alert(1)</script> <img src=x onerror=alert(1)>')
        self.assertNotIn("<script>", out)
        self.assertNotIn("<img", out)
        self.assertIn("&lt;script&gt;", out)

    def test_dangerous_links_dropped(self):
        out = bp.render_markdown("[a](javascript:alert(1)) [b](data:text/html,x) [c](/69/) [d](https://x.org)")
        self.assertNotIn("javascript:", out)
        self.assertNotIn("data:", out)
        self.assertNotIn("a)", out)  # no stray ")" from nested parens
        self.assertIn('<a href="/69/">c</a>', out)
        self.assertIn('href="https://x.org" target="_blank" rel="noopener noreferrer"', out)

    def test_attribute_breakout_in_link(self):
        out = bp.render_markdown('[x](https://a.org/"onmouseover="alert(1))')
        self.assertNotIn('"onmouseover', out)

    def test_title_is_escaped_in_template(self):
        meta = {"id": "1", "title": '<b>"x"</b>', "parent": "69"}
        out = bp.page_html(meta, "", [], [])
        self.assertNotIn("<b>", out)

    def test_structure(self):
        out = bp.render_markdown("## H\n\n- a\n- **b**\n\n1. x\n\n> q\n\n```\n<x>\n```")
        for frag in ("<h3>H</h3>", "<ul><li>a</li><li><strong>b</strong></li></ul>", "<ol><li>x</li></ol>",
                     "<blockquote>", "<pre><code>&lt;x&gt;</code></pre>"):
            self.assertIn(frag, out)


class RepoContentTests(unittest.TestCase):
    def test_repository_content_is_valid(self):
        self.assertEqual(bp.build(ROOT, True), [])


if __name__ == "__main__":
    unittest.main()
