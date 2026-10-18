"""Editorial scope and publication boundaries, separate from Registry verification."""
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('foundation',ROOT/'scripts/build_foundation_pages.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class FoundationContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'content/site-standard.json').read_text())
    def test_all_chapters_have_distinct_substantive_domains(self):
        bodies=[]
        for i,name in enumerate(self.data['chapter_names']):
            record=self.data['foundations'][str(i)]
            self.assertEqual(record['name'],name)
            self.assertGreaterEqual(len(record['sections']),4)
            self.assertGreater(sum(len(p) for s in record['sections'] for p in s['paragraphs']),600)
            bodies.append(record['purpose'])
        self.assertEqual(len(set(bodies)),len(bodies))
    def test_committed_pages_match_shared_source(self):
        for key,record in self.data['foundations'].items():
            self.assertEqual((ROOT/key/'index.html').read_text(),module.render(key,record,self.data),key)
    def test_no_v_numeric_identity_or_promotion(self):
        text=(ROOT/'V/index.html').read_text()
        self.assertNotIn('rel="canonical"',text)
        self.assertIn('HUMAN DEFINITION REQUIRED',text)
        self.assertIn('không phải Canonical Numeric ID',text)
    def test_group_association_is_not_parent_assignment(self):
        for key,chapters in [('135',['1','3','5']),('246',['2','4','6']),('789',['7','8','9'])]:
            self.assertEqual(self.data['foundations'][key]['associated_chapters'],chapters)
            text=(ROOT/key/'index.html').read_text()
            self.assertIn('không suy từ chữ số',text)
            self.assertIn('REVIEW CANDIDATE',text)
    def test_privacy_authority_and_unknown_runtime_on_every_page(self):
        for key in self.data['foundations']:
            text=(ROOT/key/'index.html').read_text()
            for boundary in ['Capability ≠ Authority','Canonical Lock: NO','chưa xác minh','Quyền riêng tư']:
                self.assertIn(boundary,text,key)
    def test_country_and_subject_classification_boundaries(self):
        text=(ROOT/'9/index.html').read_text()
        for boundary in ['984','6984','4984','98441']:
            self.assertIn(boundary,text)
    def test_4376_source_projection_and_no_mapping_activation(self):
        import tempfile
        spec=importlib.util.spec_from_file_location("builder",ROOT/"scripts/build_public_site.py")
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)/"public";builder.build(destination)
            text=(destination/"4376/index.html").read_text()
            for token in ["Bảng Chữ Số Cổ","CFP-ALPHA-1","5 Đ","SOURCE CONFLICT / HUMAN REVIEW",'data-entity-type="ai"','data-entity-type="software"']:
                self.assertIn(token,text)
            self.assertFalse((destination/"content/number-system-sources.json").exists())
            self.assertFalse((destination/"D4376").exists())
    def test_priority_pages_remain_separate(self):
        self.assertEqual(set(self.data['pages']),{'000','69','5272','6535','6735','343','267'})
        self.assertIn('PENDING',(ROOT/'267/index.html').read_text())
if __name__=='__main__': unittest.main()
