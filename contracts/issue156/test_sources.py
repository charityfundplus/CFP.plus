import json,pathlib,unittest
D=pathlib.Path(__file__).parent
class SourceTests(unittest.TestCase):
 def setUp(self):self.s=json.loads((D/'source-observations.json').read_text())
 def test_complete_inventory(self):
  for key in ['mainTreeTruncated','coreTreeTruncated','geminiTreeTruncated']:self.assertFalse(self.s[key])
 def test_chain_not_verified(self):
  e=self.s['entityRows']; countries=self.s['countryRows']; paths={r['path'] for r in self.s['mainRegistryPaths']}
  for id in ['6','69','696','6969']:
   self.assertNotIn(id,e);self.assertNotIn('registry/'+id+'.md',paths)
   self.assertFalse(any(id in [x['country_id'],x['ai_country_id']] for x in countries))
 def test_us_conflict_reported(self):
  self.assertEqual(self.s['entityRows']['69118']['name'],'OpenAI')
  self.assertIn('| 69118 | CoreWeave |',self.s['sources']['HUB69.md']['content'])
 def test_vn_conflict_reported(self):
  self.assertIn('**Parent Hub:** 698',self.s['sources']['registry/6984.md']['content'])
  self.assertIn('984',self.s['sources']['HUB69.md']['content'])
  self.assertFalse(any(x['country_id']=='984' for x in self.s['countryRows']))
 def test_entity_count_not_roster_acceptance(self):
  rows=[v for k,v in self.s['entityRows'].items() if not k.startswith('_')]
  self.assertEqual(sum(x['type']=='developer' for x in rows),20);self.assertEqual(sum(x['type']=='ai' for x in rows),6)
  self.assertFalse(any(x['type'] in ['si','super-pair','hstdn'] for x in rows))
if __name__=='__main__':unittest.main(verbosity=2)
