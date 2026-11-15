import unittest,json,re,subprocess,hashlib,html
from pathlib import Path
R=Path(__file__).resolve().parents[2]
class ContentTests(unittest.TestCase):
 def test_single_declaration_source_and_rendered_content(self):
  d=json.loads((R/'content/site-standard.json').read_text()); self.assertFalse(d['canonical_lock']);self.assertEqual(len(d['manifest']),16)
  for did,p in d['pages'].items():
   with self.subTest(did=did):
    text=(R/did/'index.html').read_text(); self.assertIn('<h1>'+did+' • '+html.escape(p['name'])+'</h1>',text);self.assertIn('https://cfp.plus/'+did+'"',text);self.assertNotIn('CFP+ AI Office',text)
    for s in p['sections']:
     for item in s['items']:self.assertIn(html.escape(item),text)
    self.assertIn('Canonical Lock: NO',text);self.assertIn('Parent/Child Canonical: chưa đủ Evidence',text)
 def test_no_generated_subjects_or_child_assignment(self):
  d=json.loads((R/'content/site-standard.json').read_text());self.assertEqual(set(d['pages']),{'000','69','5272','6535','6735','343','267'})
  self.assertIn('KEEP PENDING',(R/'267/index.html').read_text());self.assertIn('Master75 Membership: UNKNOWN',(R/'267/index.html').read_text())
 def test_6535_eight_steps_and_no_automatic_certification(self):
  p=json.loads((R/'content/site-standard.json').read_text())['pages']['6535'];flow=next(s for s in p['sections'] if s['title']=='Lộ trình đồng hành');self.assertEqual(len(flow['items']),8);self.assertIn('không đồng nghĩa được công nhận đạt chuẩn',(R/'6535/index.html').read_text())
 def test_root_names_and_navigation(self):
  d=json.loads((R/'content/site-standard.json').read_text())
  for i,n in enumerate(d['chapter_names']):self.assertIn('<h1>'+str(i)+' • '+html.escape(n)+'</h1>',(R/str(i)/'index.html').read_text())
  for did in d['pages']:
   for link in re.findall('href="(/[^"?#]*)"',(R/did/'index.html').read_text()):
    self.assertTrue((R/link.lstrip('/')).is_file() or (R/link.lstrip('/')/'index.html').is_file(),link)
 def test_repeatable_generation(self):
  files=[R/x/'index.html' for x in json.loads((R/'content/site-standard.json').read_text())['pages']];before=[hashlib.sha256(x.read_bytes()).hexdigest() for x in files];subprocess.run(['python','scripts/build_priority_pages.py'],cwd=R,check=True);self.assertEqual(before,[hashlib.sha256(x.read_bytes()).hexdigest() for x in files])
 def test_protected_conflict(self):
  s=(R/'691141/index.html').read_text();self.assertIn('CONFLICT FOUND / HUMAN REVIEW',s);self.assertIn('Không chọn hoặc thay đổi Parent',s);self.assertNotIn('Google Cloud AI',s)
 def test_no_prefix_fallback_or_automatic_active(self):
  s=(R/'id/index.html').read_text();self.assertNotIn('id.startsWith(c)',s);self.assertNotIn('ACTIVE STRUCTURE',s);self.assertIn('Không suy diễn Parent/Lineage',s);self.assertIn("x.parent_id||''",s)
if __name__=='__main__':unittest.main(verbosity=2)
