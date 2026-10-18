"""Regression gates for the existing website, not a second Registry."""
import importlib.util
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result
identity = module('identity_check', 'scripts/check_public_identity.py')
builder = module('site_builder', 'scripts/build_public_site.py')

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.canonical = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a': self.links.append(attrs.get('href', ''))
        if tag == 'link' and attrs.get('rel') == 'canonical': self.canonical.append(attrs.get('href'))

class P0Tests(unittest.TestCase):
    def test_exact_id_and_leading_zeros(self):
        self.assertEqual(identity.canonical_url('000'), 'https://cfp.plus/000')
        self.assertNotEqual(identity.canonical_url('000'), identity.canonical_url('0'))
        for value in [0, None, '', '６９', '69/1', '69?x=1', ' 69', 'D69', '69/']:
            with self.subTest(value=value), self.assertRaises(ValueError): identity.canonical_url(value)

    def test_source_identity_is_not_promoted(self):
        records = json.loads((ROOT/'registry/ai-entity-registry.json').read_text())
        before = json.dumps(records, sort_keys=True)
        findings = identity.check_entities(records)
        self.assertEqual(json.dumps(records, sort_keys=True), before)
        self.assertTrue(any(x['id']=='69118' and 'Parent absent' in x['finding'] for x in findings))
        self.assertEqual(records['691181']['parent_id'], '69118')
        self.assertTrue(any('DID field absent' in x['finding'] for x in findings))

    def test_reject_identity_parent_and_did_corruption(self):
        invalid = [
            {'69': {'id':'690'}},
            {'69': {'id':'69', 'parent_id':'6'}},
            {'69': {'id':'69', 'parent_id':'69'}},
            {'69': {'id':'69', 'did':'D69'}},
            {'6': {'id':'6','parent_id':'69'}, '69': {'id':'69','parent_id':'6'}},
        ]
        for records in invalid:
            with self.subTest(records=records), self.assertRaises(ValueError): identity.check_entities(records)

    def test_source_url_must_match_exact_identity(self):
        for link in ['https://cfp.plus/999','https://evil.example/69','https://cfp.plus/69?revision=2',
                     'https://cfp.plus/69#review','http://cfp.plus/69','https://cfp.plus/069']:
            with self.subTest(link=link), self.assertRaises(ValueError):
                identity.check_entities({'69': {'id':'69', 'public_link':link}})
        record = {'000': {'id':'000', 'public_link':'https://cfp.plus/000/'}}
        before = json.dumps(record)
        findings = identity.check_entities(record)
        self.assertTrue(any('Legacy trailing slash' in x['finding'] for x in findings))
        self.assertEqual(json.dumps(record), before)

    def test_map_groups_chapters_and_no_empty_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'public'; builder.build(root)
            for key in ['index.html','0123456789/index.html','69/index.html',*[f'{i}/index.html' for i in range(10)]]:
                parser = Links(); parser.feed((root/key).read_text())
                for href in parser.links:
                    self.assertTrue(href and href != '#', (key, href))
                    url = urlsplit(href)
                    if url.scheme or url.netloc: continue
                    target = root/url.path.lstrip('/') if url.path.startswith('/') else (root/key).parent/url.path
                    self.assertTrue(target.is_file() or (target/'index.html').is_file(), (key, href))
            parser = Links(); parser.feed((root/'0123456789/index.html').read_text())
            for key in ['V','000','135','246','789',*map(str, range(10))]: self.assertIn('/'+key, parser.links)
            self.assertEqual(parser.canonical, [identity.canonical_url('0123456789')])
            parser = Links(); parser.feed((root/'6/index.html').read_text())
            for key in ['69','6984','6911','6910','69118','691181','6535']: self.assertIn('/'+key, parser.links)
            # Existing conflicting Gemini profile remains a review hold.
            self.assertEqual((root/'691141/index.html').read_bytes(), (ROOT/'691141/index.html').read_bytes())

    def test_chapter_six_and_template_have_review_boundaries(self):
        chapter = (ROOT/'6/index.html').read_text()
        for value in ['Việt Nam','chưa được tạo ra','Software','Evidence','Canonical Lock: NO']:
            self.assertIn(value, chapter)
        standard = json.loads((ROOT/'content/site-standard.json').read_text())
        self.assertEqual(standard['chapter_names'][6], 'Siêu Trí Tuệ SI 🤖 AI 🤖 + Siêu Phần Mềm. Siêu Máy Tính & Công Nghệ')
        self.assertIn('Robot', standard['foundations']['6']['purpose'])
        template = (ROOT/'docs/HUB69_UNIVERSAL_MASTER_TEMPLATE.md').read_text()
        for value in ['HSTDN', 'DID', 'https://cfp.plus/{StableID}', 'UNKNOWN', 'PR #142']:
            self.assertIn(value, template)

if __name__ == '__main__': unittest.main(verbosity=2)
