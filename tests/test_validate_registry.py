import tempfile
import unittest
from pathlib import Path
import importlib.util
import sys

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_registry.py"
spec = importlib.util.spec_from_file_location("validate_registry", MODULE_PATH)
validate_registry = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validate_registry
spec.loader.exec_module(validate_registry)


class ValidateRegistryTests(unittest.TestCase):
    def test_load_registry_files_parses_markdown_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_dir = Path(tmpdir) / "registry"
            registry_dir.mkdir()
            record_path = registry_dir / "1234.md"
            record_path.write_text(
                "# 1234 • Example\n\n"
                "**Canonical ID:** 1234  \n"
                "**Entity Name:** Example  \n"
                "**Parent Hub:** 12 • Example Hub  \n"
                "**Lifecycle Status:** Review Candidate  \n"
                "**Visibility:** Public\n\n"
                "## 1. Canonical Link\n\n"
                "https://github.com/charityfundplus/CFP.plus/blob/main/registry/1234.md\n",
                encoding="utf-8",
            )
            report = validate_registry.ValidationReport(registry_path=str(registry_dir))
            records = validate_registry.load_registry_files(str(registry_dir), report=report)

            self.assertEqual(1, len(records))
            self.assertEqual("1234", records[0].canonical_id)
            self.assertEqual("entry", records[0].record_type)
            self.assertEqual(
                "https://github.com/charityfundplus/CFP.plus/blob/main/registry/1234.md",
                records[0].canonical_link,
            )

    def test_validate_canonical_links_reports_parent_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_dir = Path(tmpdir) / "registry"
            registry_dir.mkdir()
            record_path = registry_dir / "1234.md"
            record_path.write_text(
                "# 1234 • Example\n\n"
                "**Canonical ID:** 1234  \n"
                "**Entity Name:** Example  \n"
                "**Parent ID:** 9999  \n"
                "**Lifecycle Status:** Review Candidate  \n"
                "**Visibility:** Public\n\n"
                "## 1. Canonical Link\n\n"
                "https://github.com/charityfundplus/CFP.plus/blob/main/registry/1234.md\n",
                encoding="utf-8",
            )
            report = validate_registry.ValidationReport(registry_path=str(registry_dir))
            records = validate_registry.load_registry_files(str(registry_dir), report=report)

            validate_registry.validate_structure(records, report)
            validate_registry.validate_metadata(records, report)
            validate_registry.validate_canonical_links(records, report)

            codes = {finding.code for finding in report.findings}
            self.assertIn("parent_child_mismatch", codes)

    def test_generate_report_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = validate_registry.ValidationReport(registry_path="registry")
            report.add("warning", "example_warning", "Example warning", "registry/1234.md")
            report.openai_review = {"status": "skipped", "reason": "No API key"}
            json_path = Path(tmpdir) / "report.json"
            md_path = Path(tmpdir) / "report.md"

            validate_registry.generate_report(report, str(json_path), str(md_path))

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            self.assertIn("example_warning", md_path.read_text(encoding="utf-8"))

    def test_validate_canonical_links_accepts_existing_links_outside_filtered_scope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_dir = Path(tmpdir) / "registry"
            registry_dir.mkdir()
            parent_path = registry_dir / "1234.md"
            child_path = registry_dir / "12340.md"

            parent_path.write_text(
                "# 1234 • Example Parent\n\n"
                "**Canonical ID:** 1234  \n"
                "**Entity Name:** Example Parent  \n"
                "**Parent Hub:** 12 • Example Hub  \n"
                "**Lifecycle Status:** Review Candidate  \n"
                "**Visibility:** Public\n\n"
                "## 1. Canonical Link\n\n"
                "https://github.com/charityfundplus/CFP.plus/blob/main/registry/1234.md\n\n"
                "- [12340 • Example Child](https://github.com/charityfundplus/CFP.plus/blob/main/registry/12340.md)\n",
                encoding="utf-8",
            )
            child_path.write_text(
                "# 12340 • Example Child\n\n"
                "**Canonical ID:** 12340  \n"
                "**Entity Name:** Example Child  \n"
                "**Parent ID:** 1234  \n"
                "**Lifecycle Status:** Review Candidate  \n"
                "**Visibility:** Public\n\n"
                "## 1. Canonical Link\n\n"
                "https://github.com/charityfundplus/CFP.plus/blob/main/registry/12340.md\n",
                encoding="utf-8",
            )

            report = validate_registry.ValidationReport(registry_path=str(registry_dir))
            records = validate_registry.load_registry_files(
                str(registry_dir),
                changed_files=[str(parent_path)],
                report=report,
            )

            validate_registry.validate_structure(records, report)
            validate_registry.validate_metadata(records, report)
            validate_registry.validate_canonical_links(records, report)

            codes = {finding.code for finding in report.findings}
            self.assertNotIn("missing_linked_record", codes)


if __name__ == "__main__":
    unittest.main()
