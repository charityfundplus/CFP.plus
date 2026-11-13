import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_index import validate

BASE = dict(asset_key="test", title="Test", chapter=6, source_uri="https://example.org", review_status="PENDING")

class TestIndex(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(BASE), [])
    def test_leap_day(self):
        self.assertEqual(validate({**BASE, "calendar_days": ["02-29"]}), [])
    def test_invalid_day(self):
        self.assertTrue(validate({**BASE, "calendar_days": ["02-30"]}))
    def test_invalid_chapter(self):
        self.assertTrue(validate({**BASE, "chapter": 10}))
    def test_root_mismatch(self):
        self.assertTrue(validate({**BASE, "canonical_entity_id": "7848"}))
    def test_evidence_gate(self):
        self.assertTrue(validate({**BASE, "review_status": "VERIFIED"}))
    def test_numeric_id(self):
        self.assertTrue(validate({**BASE, "canonical_entity_id": "ABC"}))

if __name__ == "__main__":
    unittest.main()
