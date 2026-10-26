import copy, json, pathlib, unittest
from datetime import datetime,timezone
from jsonschema import Draft202012Validator,FormatChecker
from publication_policy import project,digest,retry_delay
D=pathlib.Path(__file__).parent
SPEC=json.loads((D/'openapi.json').read_text())
SCHEMAS=SPEC['components']['schemas']
def validate(name,value):
    Draft202012Validator({'$ref':'#/components/schemas/'+name,'components':SPEC['components']},format_checker=FormatChecker()).validate(value)
def fixture():
    revision='835616308111f6851c0387fa9f5eda60c9ffa624'
    r={'id':'691181','parent':'69118','did':None,'name':'SYNTHETIC TEST ONLY','type':'ai','si':[],'ai':[],'software':[],'robot':[],'capability':[],'owner':None,'status':'approved','sourceStatus':'SYNTHETIC TEST','evidence':[{'url':'https://example.invalid/evidence','sourceRevision':revision,'sha256':'a'*64,'verifiedAt':'2026-10-19T00:00:00Z','claim':'synthetic schema exercise'}],'canonicalLink':'https://cfp.plus/691181','sourceRevision':revision,'readOnly':True,'activationAllowed':False}
    a={'signatureVerified':True,'audience':'public','sourceRevision':revision,'decisionURL':'https://example.invalid/decision','expiresAt':'2026-10-20T00:00:00Z','recordHash':digest(r),'fields':list(r)}
    return r,a
class ContractTests(unittest.TestCase):
 def setUp(self):self.r,self.a=fixture();self.now=datetime(2026,10,19,tzinfo=timezone.utc)
 def publish(self):return project(self.r,self.a,trusted_revision=self.r['sourceRevision'],now=self.now)
 def test_read_only_paths(self):
    self.assertEqual(len(SPEC['paths']),4)
    for path,item in SPEC['paths'].items():
      self.assertEqual(list(item),['get']);self.assertNotIn('requestBody',item['get'])
      self.assertEqual(item['get'].get('security',SPEC['security']),[] if '/public/' in path else [{'CoreSession':[]}])
 def test_references_resolve(self):
    def walk(v):
      if isinstance(v,dict):
       if '$ref' in v:
        cur=SPEC
        for p in v['$ref'][2:].split('/'):cur=cur[p]
       for w in v.values():walk(w)
      elif isinstance(v,list):
       for w in v:walk(w)
    walk(SPEC)
 def test_schema_definitions(self):
    for s in SCHEMAS.values():Draft202012Validator.check_schema(s)
 def test_positive_projection(self):validate('PublishedRecord',self.publish());self.assertEqual(self.r,self.publish())
 def test_unknown_fields_rejected(self):
    self.r['token']='never-real';self.a['recordHash']=digest(self.r);self.a['fields']=list(self.r)
    with self.assertRaises(Exception):validate('PublishedRecord',self.publish())
 def test_unapproved_fields_denied(self):
    self.a['fields'].remove('owner')
    with self.assertRaises(ValueError):self.publish()
 def test_missing_signature_denied(self):
    self.a['signatureVerified']=False
    with self.assertRaises(ValueError):self.publish()
 def test_private_audience_denied(self):
    self.a['audience']='internal'
    with self.assertRaises(ValueError):self.publish()
 def test_expired_approval_denied(self):
    self.a['expiresAt']='2026-10-18T00:00:00Z'
    with self.assertRaises(ValueError):self.publish()
 def test_revision_swap_denied(self):
    self.a['sourceRevision']='b'*40
    with self.assertRaises(ValueError):self.publish()
 def test_content_change_denied(self):
    self.r['parent']='69'
    with self.assertRaises(ValueError):self.publish()
 def test_unknown_states_denied(self):
    for state in ['discovered','pending_review']:
     self.r['status']=state;self.a['recordHash']=digest(self.r)
     with self.assertRaises(ValueError):self.publish()
 def test_evidence_required(self):
    self.r['evidence']=[];self.a['recordHash']=digest(self.r)
    with self.assertRaises(ValueError):self.publish()
 def test_no_activation(self):
    self.r['activationAllowed']=True;self.a['recordHash']=digest(self.r)
    with self.assertRaises(ValueError):self.publish()
 def test_projection_copy(self):
    p=self.publish();p['evidence'].clear();self.assertEqual(len(self.r['evidence']),1)
 def test_numeric_strings_and_zero_preservation(self):
    validate('ID','00069')
    for bad in [69,'69.0','+69','69/','', '1'*257]:
     with self.assertRaises(Exception):validate('ID',bad)
 def test_retry_budget_and_denials(self):
    self.assertEqual(retry_delay(503,1),0.5);self.assertEqual(retry_delay(429,2,4),4)
    for status in [200,400,401,403,404,409,422]:self.assertIsNone(retry_delay(status,1))
    self.assertIsNone(retry_delay(503,3));self.assertIsNone(retry_delay(429,1,30))
 def test_adapter_hold(self):
    cfg=json.loads((D/'adapters.json').read_text());self.assertEqual(len(cfg['adapters']),5)
    for a in cfg['adapters']:
     self.assertFalse(a['enabled']);self.assertFalse(a['canonicalWrites']);self.assertIsNone(a['canonicalBinding']);self.assertEqual(a['allowedMethods'],['GET'])
 def test_idempotent_read(self):self.assertEqual(digest(self.publish()),digest(self.publish()))
 def test_oas_shape(self):
    self.assertEqual(SPEC['openapi'],'3.1.0');ids=[]
    for p,item in SPEC['paths'].items():
     op=item['get'];ids.append(op['operationId']);self.assertIn('200',op['responses'])
     if '{id}' in p:self.assertTrue(any(x.get('name')=='id' and x.get('required') for x in op['parameters']))
    self.assertEqual(len(ids),len(set(ids)))
if __name__=='__main__':unittest.main(verbosity=2)
