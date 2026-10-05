import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class ProjectionTests(unittest.TestCase):
 def test_source_and_all_existing_numeric_routes(self):
  d=json.loads((ROOT/'assets/chapter-projection.json').read_text())
  self.assertEqual(d['authority'],'READ_ONLY_MIRROR');self.assertRegex(d['source_commit'],r'^[0-9a-f]{40}$')
  self.assertEqual([x['chapter'] for x in d['chapters']],list('0123456789'))
  keys=[]
  for c in d['chapters']:
   self.assertEqual(c['canonical_url'],'https://cfp.plus/'+c['chapter'])
   self.assertEqual({e['entity_type'] for e in c['entities']},{'AI','SOFTWARE'})
   for e in c['entities']:
    keys.append(e['entity_key']);self.assertEqual(e['permissions'],[]);self.assertEqual(e['readback'],[]);self.assertTrue(e['evidence'])
   self.assertEqual(len(c['relationships']),10);self.assertEqual(c['descendants'],[])
   self.assertEqual(len(c['pair_references']),len(set(c['pair_references'])))
   html=(ROOT/c['chapter']/'index.html').read_text();self.assertIn('/assets/chapter-pairs.js',html)
  self.assertEqual(len(keys),20);self.assertEqual(len(set(keys)),20)
  self.assertFalse(d['canonical_lock']);self.assertEqual(d['conflicts'][0]['status'],'CONFLICT FOUND / HUMAN REVIEW')
if __name__=='__main__':unittest.main()
