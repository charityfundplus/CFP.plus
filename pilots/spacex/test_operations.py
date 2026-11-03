import hashlib,http.client,json,sqlite3,tempfile,threading,unittest
from pathlib import Path
from operations import Operations,OperationError,DEMO_PASSWORD,digest
from operations_server import make_server
class OperationsTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.ops=Operations(self.root);self.ops.provision_demo()
  for name in ['editor','viewer','admin','foreign']:setattr(self,name,self.ops.login(name,DEMO_PASSWORD))
  self.record={'title':'Synthetic operations test','group':'246','chapter':6,'content':'Local only; no SpaceX affiliation','idempotency_key':'record-1'}
 def tearDown(self):self.temp.cleanup()
 def test_read_write_restart_independent_session_and_mapping(self):
  record=self.ops.create_record(self.editor,self.record);reopened=Operations(self.root);independent=reopened.login('editor',DEMO_PASSWORD);state=reopened.state(independent)
  self.assertEqual(state['records'],[record]);self.assertEqual(state['digest'],digest([record]));self.assertEqual(state['groups'],{'V':[],'0':[0],'135':[1,3,5],'246':[2,4,6],'789':[7,8,9]});self.assertEqual(len(state['chapters']),10);self.assertTrue(state['audit_valid']);self.assertTrue(all(c['status']=='BLOCKED' for c in state['connectors']))
 def test_idempotency_conflict_and_group_validation(self):
  record=self.ops.create_record(self.editor,self.record);self.assertEqual(self.ops.create_record(self.editor,self.record),record)
  with self.assertRaisesRegex(OperationError,'IDEMPOTENCY_CONFLICT'):self.ops.create_record(self.editor,{**self.record,'title':'Different'})
  with self.assertRaisesRegex(OperationError,'GROUP_CHAPTER_MISMATCH'):self.ops.create_record(self.editor,{**self.record,'group':'135'})
  self.assertEqual(len(self.ops.state(self.editor)['records']),1)
 def test_replication_real_offline_retry_durable_outbox(self):
  record=self.ops.create_record(self.editor,self.record);away=self.ops.replica.with_name('replica-away.sqlite');self.ops.replica.rename(away);self.ops.replica.mkdir()
  try:
   self.assertEqual(self.ops.sync(self.editor)['results'][0]['status'],'PENDING');state=self.ops.state(self.editor);self.assertEqual(state['replica']['status'],'OFFLINE');self.assertEqual(state['queue'][0]['attempts'],1);restarted_offline=Operations(self.root);self.assertEqual(restarted_offline.state(self.editor)['replica']['status'],'OFFLINE');self.assertEqual(restarted_offline.state(self.editor)['records'],[record])
  finally:self.ops.replica.rmdir();away.rename(self.ops.replica)
  restarted=Operations(self.root);self.assertEqual(restarted.sync(self.editor)['results'][0]['status'],'SYNCED');state=restarted.state(self.editor);self.assertEqual(state['replica']['records'],[record]);self.assertEqual(state['digest'],state['replica']['digest']);self.assertEqual(state['queue'][0]['attempts'],2);self.assertEqual(restarted.sync(self.editor)['results'],[])
 def test_replica_conflict_preserves_both_versions(self):
  record=self.ops.create_record(self.editor,self.record);other={**record,'title':'Conflicting destination'};other['content_hash']=digest({k:v for k,v in other.items() if k!='content_hash'})
  with self.ops.replica_connect() as db:db.execute('INSERT INTO records VALUES(?,?,?)',('alpha',record['key'],json.dumps(other)))
  self.assertEqual(self.ops.sync(self.editor)['results'][0]['status'],'CONFLICT');state=self.ops.state(self.editor);self.assertEqual(state['records'],[record]);self.assertEqual(state['replica']['records'],[other])
 def test_permissions_workspace_sessions_expiry(self):
  self.ops.create_record(self.editor,self.record)
  for op in [lambda:self.ops.create_record(self.viewer,self.record),lambda:self.ops.sync(self.viewer),lambda:self.ops.backup(self.editor)]:
   with self.assertRaisesRegex(OperationError,'PERMISSION_DENIED'):op()
  self.assertEqual(self.ops.state(self.foreign)['records'],[]);self.assertEqual(self.ops.state(self.foreign)['queue'],[]);self.assertTrue(all(e['workspace']=='beta' for e in self.ops.state(self.foreign)['audit']))
  independent=self.ops.login('editor',DEMO_PASSWORD);self.ops.logout(self.editor)
  with self.assertRaisesRegex(OperationError,'AUTH_DENIED'):self.ops.state(self.editor)
  self.assertEqual(len(self.ops.state(independent)['records']),1);self.ops.clock=lambda:10**12
  with self.assertRaisesRegex(OperationError,'AUTH_DENIED'):self.ops.state(independent)
 def test_backup_restores_actual_new_sqlite_and_workspace_isolation(self):
  record=self.ops.create_record(self.editor,self.record);receipt=self.ops.backup(self.admin);self.ops.provision('beta-admin',DEMO_PASSWORD,'admin','beta');[self.ops.grant_space('beta-admin',space,True) for space in ['community','chapter-association','si-ai-forum','super-pair-forum']];beta=self.ops.login('beta-admin',DEMO_PASSWORD)
  with self.assertRaisesRegex(OperationError,'ARTIFACT_NOT_FOUND'):self.ops.restore(beta,receipt['backup_id'])
  before=self.ops.state(self.admin)['records'];restored=self.ops.restore(self.admin,receipt['backup_id']);self.assertTrue(restored['source_unchanged']);self.assertEqual(restored['digest'],digest([record]))
  with sqlite3.connect(self.ops._artifact('restore',restored['restore_id'])) as db:
   self.assertEqual(json.loads(db.execute('SELECT payload FROM records').fetchone()[0]),record);self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertEqual(db.execute('SELECT DISTINCT workspace FROM records').fetchall(),[('alpha',)])
  self.assertEqual(self.ops.state(self.admin)['records'],before)
  for token in [self.editor,self.viewer]:
   with self.assertRaisesRegex(OperationError,'PERMISSION_DENIED'):self.ops.restore(token,receipt['backup_id'])
 def test_corrupt_backup_and_rewritten_manifest_fail_closed(self):
  self.ops.create_record(self.editor,self.record);receipt=self.ops.backup(self.admin);path=self.ops._artifact('backup',receipt['backup_id'])
  with path.open('ab') as f:f.write(b'corrupt')
  with self.assertRaisesRegex(OperationError,'BACKUP_INTEGRITY_FAILURE'):self.ops.restore(self.admin,receipt['backup_id'])
  sidecar=path.with_suffix('.json');fake=json.loads(sidecar.read_text());fake['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();sidecar.write_text(json.dumps(fake))
  with self.assertRaisesRegex(OperationError,'BACKUP_INTEGRITY_FAILURE'):self.ops.restore(self.admin,receipt['backup_id'])
  self.assertEqual(list(self.root.glob('restore-*')),[])
 def test_deleted_source_record_detected(self):
  self.ops.create_record(self.editor,self.record)
  with self.ops.connect() as db:db.execute('DELETE FROM records WHERE workspace=?',('alpha',))
  with self.assertRaisesRegex(OperationError,'RECORD_INTEGRITY_FAILURE'):Operations(self.root)
 def test_audit_tampering_detected(self):
  with self.ops.connect() as db:db.execute("UPDATE audit SET hash='bad' WHERE workspace=? AND seq=1",('alpha',))
  with self.assertRaisesRegex(OperationError,'AUDIT_INTEGRITY_FAILURE'):self.ops.state(self.editor)
 def test_malformed_persisted_record_audit_and_replica_are_integrity_failures(self):
  record=self.ops.create_record(self.editor,self.record)
  with self.ops.connect() as db:original_record=db.execute('SELECT payload FROM records WHERE key=?',(record['key'],)).fetchone()['payload'];original_audit=db.execute('SELECT payload FROM audit WHERE workspace=? AND seq=1',('alpha',)).fetchone()['payload']
  for bad in ['{}','[]','null','"text"','not json',json.dumps({**record,'chapter':'6'})]:
   with self.ops.connect() as db:db.execute('UPDATE records SET payload=? WHERE key=?',(bad,record['key']))
   with self.subTest(record=bad), self.assertRaisesRegex(OperationError,'RECORD_INTEGRITY_FAILURE') as caught:self.ops.state(self.editor)
   self.assertEqual(caught.exception.status,503)
  with self.ops.connect() as db:db.execute('UPDATE records SET payload=? WHERE key=?',(original_record,record['key']))
  for bad in ['{}','[]','null','"text"','not json']:
   with self.ops.connect() as db:db.execute('UPDATE audit SET payload=? WHERE workspace=? AND seq=1',(bad,'alpha'))
   with self.subTest(audit=bad),self.assertRaisesRegex(OperationError,'AUDIT_INTEGRITY_FAILURE') as caught:self.ops.state(self.editor)
   self.assertEqual(caught.exception.status,503)
  with self.ops.connect() as db:db.execute('UPDATE audit SET payload=? WHERE workspace=? AND seq=1',(original_audit,'alpha'))
  self.ops.sync(self.editor)
  for bad in ['{}','[]','null','"text"','not json']:
   with self.ops.replica_connect() as db:db.execute('UPDATE records SET payload=? WHERE key=?',(bad,record['key']))
   state=self.ops.state(self.editor)
   self.assertEqual(state['replica']['status'],'INTEGRITY FAILURE');self.assertFalse(state['replica']['integrity_valid']);self.assertEqual(state['replica']['records'],[]);self.assertEqual(state['records'],[record])
 def test_http_auth_origin_host_limits_and_static_ui(self):
  server=make_server(self.ops);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();port=server.server_address[1]
  def request(path,body=None,cookie='',origin=None,host=None):
   c=http.client.HTTPConnection('127.0.0.1',port,timeout=5);headers={'Host':host or f'127.0.0.1:{port}','Origin':origin or f'http://127.0.0.1:{port}','Content-Type':'application/json','Cookie':cookie};c.request('GET' if body is None else 'POST',path,body=None if body is None else json.dumps(body),headers=headers);r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read());c.close();return result
  try:
   self.assertEqual(request('/api/state')[0],401);status,headers,body=request('/api/session',{'id':'editor','password':DEMO_PASSWORD});self.assertEqual(status,200);self.assertIn('HttpOnly; SameSite=Strict',headers['Set-Cookie']);cookie=headers['Set-Cookie'].split(';')[0];self.assertNotIn(DEMO_PASSWORD.encode(),body)
   self.assertEqual(request('/api/records',self.record,cookie)[0],201);self.assertEqual(request('/api/state',cookie=cookie)[0],200);self.assertEqual(request('/api/sync',{},cookie,origin='https://evil.example')[0],403);self.assertEqual(request('/api/state',cookie=cookie,host='evil.example')[0],403);self.assertEqual(request('/api/session',{'id':'editor','password':DEMO_PASSWORD,'role':'admin'})[0],400);self.assertEqual(request('/api/records',{'content':'x'*20000},cookie)[0],413);self.assertEqual(request('/../operations.py')[0],405);self.assertEqual(request('/')[0],200);self.assertEqual(request('/api/logout',{},cookie)[0],200);self.assertEqual(request('/api/state',cookie=cookie)[0],401)
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
