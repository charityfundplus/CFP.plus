"""Targeted regression of PR157 findings; all approvals/identities are synthetic."""
import copy, unittest
from datetime import datetime,timezone
from jsonschema.exceptions import ValidationError
from test_contract import fixture,validate
from publication_policy import project,digest,published_page
class FindingTests(unittest.TestCase):
 def setUp(self):
  self.r,self.a=fixture();self.now=datetime(2026,10,19,tzinfo=timezone.utc)
 def rebound(self):self.a['recordHash']=digest(self.r)
 def publish(self):return project(self.r,self.a,trusted_revision=self.r['sourceRevision'],now=self.now)
 def page(self,records=None,approvals=None,**kw):
  return published_page([self.r] if records is None else records,{self.r['id']:self.a} if approvals is None else approvals,trusted_revision=self.r['sourceRevision'],now=self.now,**kw)
 def test_public_schema_rejects_unpublished_and_active(self):
  for state in ['discovered','pending_review','active']:
   with self.subTest(state=state):
    self.r['status']=state;self.rebound()
    with self.assertRaises(ValidationError):validate('PublishedRecord',self.r)
    with self.assertRaises(ValueError):self.publish()
 def test_public_schema_rejects_empty_evidence(self):
  self.r['evidence']=[]
  with self.assertRaises(ValidationError):validate('PublishedRecord',self.r)
 def test_all_populated_bindings_need_evidence(self):
  for key in ['si','ai','robot']:
   with self.subTest(key=key):
    self.r[key]=[{'id':'00069','evidence':[]}];self.rebound()
    with self.assertRaises(ValidationError):self.publish()
    self.r[key]=[]
 def test_software_evidence_required(self):
  self.r['software']=[{'name':'SYNTHETIC','version':None,'evidence':[]}];self.rebound()
  with self.assertRaises(ValidationError):self.publish()
 def test_capability_evidence_required(self):
  self.r['capability']=[{'name':'SYNTHETIC','status':'approved','evidence':[]}];self.rebound()
  with self.assertRaises(ValidationError):self.publish()
 def test_active_capability_forbidden_during_hold_even_with_evidence(self):
  self.r['capability']=[{'name':'SYNTHETIC','status':'active','evidence':self.r['evidence']}];self.rebound()
  with self.assertRaises(ValidationError):self.publish()
 def test_approved_binding_and_capability_with_evidence_preserve_identity(self):
  self.r['ai']=[{'id':'00069','evidence':self.r['evidence']}]
  self.r['capability']=[{'name':'SYNTHETIC','status':'approved','evidence':self.r['evidence']}];self.rebound()
  self.assertEqual(self.publish()['ai'][0]['id'],'00069')
 def test_unapproved_excluded_before_count_search_and_page(self):
  self.a['signatureVerified']=False
  page=self.page(query=self.r['name']);self.assertEqual(page['total'],0);self.assertEqual(page['records'],[])
 def test_first_page_and_continuation_share_both_pins(self):
  records=[];approvals={}
  for id in ['0001','0002','0003']:
   r=copy.deepcopy(self.r);r['id']=id;r['canonicalLink']='https://cfp.plus/'+id
   a=copy.deepcopy(self.a);a['recordHash']=digest(r);records.append(r);approvals[id]=a
  first=self.page(records,approvals,limit=1);validate('PublishedPage',first)
  second=self.page(records,approvals,limit=1,offset=1,revision=first['sourceRevision'],approval_revision=first['approvalSetRevision'])
  self.assertEqual(second['records'][0]['id'],'0002');self.assertEqual(first['approvalSetRevision'],second['approvalSetRevision'])
 def test_continuation_requires_both_pins(self):
  for kw in [{},{'revision':self.r['sourceRevision']},{'approval_revision':'a'*64}]:
   with self.subTest(kw=kw),self.assertRaisesRegex(ValueError,'PIN_REQUIRED'):self.page(offset=1,**kw)
 def test_revocation_during_pagination_conflicts(self):
  first=self.page();self.a['signatureVerified']=False
  with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):self.page(offset=1,revision=first['sourceRevision'],approval_revision=first['approvalSetRevision'])
 def test_expiry_during_pagination_conflicts(self):
  first=self.page();self.a['expiresAt']='2026-10-18T00:00:00Z'
  with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):self.page(offset=1,revision=first['sourceRevision'],approval_revision=first['approvalSetRevision'])
 def test_source_change_conflicts(self):
  with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):self.page(revision='b'*40)
 def test_approval_renewal_changes_pin_without_source_change(self):
  first=self.page();self.a['decisionURL']='https://example.invalid/new-decision'
  with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):self.page(offset=1,revision=first['sourceRevision'],approval_revision=first['approvalSetRevision'])
 def test_pending_record_never_in_public_page(self):
  self.r['status']='pending_review';self.rebound();p=self.page();self.assertEqual(p['total'],0)
 def test_public_page_schema_requires_approval_pin(self):
  p=self.page();del p['approvalSetRevision']
  with self.assertRaises(ValidationError):validate('PublishedPage',p)
class LowApprovalTypeTests(unittest.TestCase):
 def setUp(self):
  self.r,self.a=fixture();self.now=datetime(2026,10,19,tzinfo=timezone.utc)
 def project(self):return project(self.r,self.a,trusted_revision=self.r['sourceRevision'],now=self.now)
 def page(self,**kw):return published_page([self.r],{self.r['id']:self.a},trusted_revision=self.r['sourceRevision'],now=self.now,**kw)
 def test_expiry_type_and_parse_failures_are_valueerror(self):
  for value in [None,1,True,[],{},b'2026-10-20T00:00:00Z','invalid-date']:
   with self.subTest(value=value):
    self.a['expiresAt']=value
    with self.assertRaisesRegex(ValueError,'APPROVAL_EXPIRY_INVALID'):self.project()
  del self.a['expiresAt']
  with self.assertRaisesRegex(ValueError,'APPROVAL_EXPIRY_INVALID'):self.project()
 def test_fields_type_failures_are_valueerror(self):
  for value in [None,1,True,'id',{},('id',),['id',1],['id',None]]:
   with self.subTest(value=value):
    self.a['fields']=value
    with self.assertRaisesRegex(ValueError,'APPROVAL_FIELDS_INVALID'):self.project()
  del self.a['fields']
  with self.assertRaisesRegex(ValueError,'APPROVAL_FIELDS_INVALID'):self.project()
 def test_malformed_receipts_do_not_abort_mixed_page(self):
  good=copy.deepcopy(self.r);good['id']='00069';good['canonicalLink']='https://cfp.plus/00069'
  good_approval=copy.deepcopy(self.a);good_approval['recordHash']=digest(good)
  for field,value in [('expiresAt',None),('expiresAt',1),('fields',None),('fields',['id',1])]:
   with self.subTest(field=field,value=value):
    bad=copy.deepcopy(self.a);bad[field]=value
    page=published_page([self.r,good],{self.r['id']:bad,good['id']:good_approval},trusted_revision=self.r['sourceRevision'],now=self.now)
    validate('PublishedPage',page);self.assertEqual(page['total'],1);self.assertEqual([r['id'] for r in page['records']],['00069'])
 def test_malformed_only_receipt_is_excluded(self):
  self.a['expiresAt']=None;p=self.page();self.assertEqual(p['total'],0);self.assertEqual(p['records'],[])
 def test_receipt_becomes_malformed_rejects_continuation(self):
  for field,value in [('expiresAt',None),('fields',['id',1])]:
   with self.subTest(field=field):
    self.r,self.a=fixture();first=self.page();self.a[field]=value
    with self.assertRaisesRegex(ValueError,'PUBLICATION_SNAPSHOT_CHANGED'):
     self.page(offset=1,revision=first['sourceRevision'],approval_revision=first['approvalSetRevision'])

if __name__=='__main__':unittest.main(verbosity=2)
