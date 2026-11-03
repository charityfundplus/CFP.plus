"""HTTP App bridge regression tests; Website and App reuse Operations auth/storage."""
import hashlib,http.client,json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from operations import Operations,DEMO_PASSWORD
import operations_server as bridge

class AppBridgeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.operations=Operations(self.root/'state');self.operations.provision_demo();self.server=bridge.make_server(self.operations);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.port=self.server.server_address[1];self.canonical_bytes=bridge.REGISTRY_PATH.read_bytes()
 def tearDown(self):
  self.assertEqual(bridge.REGISTRY_PATH.read_bytes(),self.canonical_bytes);self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
 def request(self,path,body=None,cookie='',method=None):
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5);headers={'Host':f'127.0.0.1:{self.port}','Origin':f'http://127.0.0.1:{self.port}','Content-Type':'application/json','Cookie':cookie};c.request(method or ('GET' if body is None else 'POST'),path,body=None if body is None else json.dumps(body),headers=headers);r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read());c.close();return result
 def login(self,name='editor'):
  status,headers,_=self.request('/api/session',{'id':name,'password':DEMO_PASSWORD});self.assertEqual(status,200);return headers['Set-Cookie'].split(';')[0]
 def test_registry_requires_current_shared_session(self):
  self.assertEqual(self.request('/api/app/registry')[0],401);cookie=self.login();self.assertEqual(self.request('/api/app/registry',cookie=cookie)[0],200);self.assertEqual(self.request('/api/logout',{},cookie)[0],200);self.assertEqual(self.request('/api/app/registry',cookie=cookie)[0],401)
 def test_registry_exact_pin_projection_source_unchanged_no_extra_database(self):
  cookie=self.login();before={p.name for p in self.operations.root.glob('*.sqlite')};status,headers,body=self.request('/api/app/registry',cookie=cookie);self.assertEqual(status,200);self.assertEqual(headers['Cache-Control'],'no-store');data=json.loads(body);sha=hashlib.sha256(self.canonical_bytes).hexdigest();self.assertEqual(data['registryBlobSHA'],'1f18068d66379ce90bb079dc56c77b4c4d66dcdf');self.assertEqual(data['sourceSHA256'],sha);self.assertEqual(data['sourceCommit'],'835616308111f6851c0387fa9f5eda60c9ffa624');self.assertFalse(data['activationAllowed']);self.assertFalse(data['published']);rows=json.loads(self.canonical_bytes);self.assertEqual(len(data['records']),26);self.assertEqual(len({r['id'] for r in data['records']}),26)
  for record in data['records']:
   original=rows[record['id']]
   for k,v in original.items():self.assertEqual(record[k],v)
   self.assertEqual(record['sourceCanonical'],original.get('public_link') or 'https://cfp.plus/'+record['id']);self.assertEqual(record['conflict'],original.get('ai_country_id')=='6911');self.assertFalse(record['operationsAllowed']);self.assertFalse(record['identityVerified']);self.assertIsNone(record['chapter']);self.assertIsNone(record['hstdn']);self.assertEqual(record['provenance']['sourceSHA256'],sha)
  self.assertEqual({p.name for p in self.operations.root.glob('*.sqlite')},before);self.assertEqual(before,{'operations.sqlite','replica.sqlite'})
 def test_registry_pin_mismatch_fails_closed_no_snapshot_fallback(self):
  cookie=self.login();changed=self.root/'invalid-registry.json';changed.write_bytes(self.canonical_bytes+b' ')
  with patch.object(bridge,'REGISTRY_PATH',changed):status,_,body=self.request('/api/app/registry',cookie=cookie)
  self.assertEqual(status,503);self.assertEqual(json.loads(body),{'error':'REGISTRY_SOURCE_INTEGRITY_FAILURE'});self.assertNotIn(b'"records"',body)
 def test_registry_missing_source_fails_closed(self):
  cookie=self.login()
  with patch.object(bridge,'REGISTRY_PATH',self.root/'absent.json'):status,_,body=self.request('/api/app/registry',cookie=cookie)
  self.assertEqual(status,503);self.assertEqual(json.loads(body),{'error':'REGISTRY_SOURCE_UNAVAILABLE'})
 def test_mount_allowlist_mime_manifest_and_sameorigin_frames(self):
  app=self.root/'app-dist';app.mkdir();(app/'index.html').write_text('<main>Existing built App fixture</main>');(app/'app.js').write_text('window.APP_FIXTURE=true;');(app/'manifest.webmanifest').write_text(json.dumps({'scope':'./','start_url':'./index.html#home'}))
  with patch.object(bridge,'APP_ROOT',app):
   status,headers,_=self.request('/app');self.assertEqual(status,308);self.assertEqual(headers['Location'],'/app/');status,headers,body=self.request('/app/');self.assertEqual(status,200);self.assertIn(b'Existing built App fixture',body);self.assertIn("frame-src 'self'",headers['Content-Security-Policy']);self.assertIn("frame-ancestors 'self'",headers['Content-Security-Policy']);self.assertNotIn('unsafe-inline',headers['Content-Security-Policy']);self.assertEqual(self.request('/app/app.js')[0],200);status,headers,body=self.request('/app/manifest.webmanifest');self.assertEqual(status,200);self.assertEqual(json.loads(body)['scope'],'./');self.assertEqual(self.request('/app/app.js',method='HEAD')[2],b'')
 def test_mount_rejects_traversal_unknown_symlink_missing_build(self):
  app=self.root/'app-dist';app.mkdir();(app/'index.html').symlink_to(bridge.REGISTRY_PATH)
  with patch.object(bridge,'APP_ROOT',app):
   for path in ['/app/../operations.py','/app/%2e%2e/registry/ai-entity-registry.json','/app/sub/app.js','/app/registry/ai-entity-registry.json','/app/.env','/app/package.json','/app//index.html','/app/index.html']:
    with self.subTest(path=path):self.assertEqual(self.request(path)[0],404)
   self.assertEqual(self.request('/app/app.js')[0],503)
  outside=self.root/'outside';outside.mkdir();linked=self.root/'linked';linked.symlink_to(outside,target_is_directory=True)
  with patch.object(bridge,'APP_ROOT',linked):self.assertEqual(self.request('/app/')[0],503)
 def test_existing_operations_share_auth_and_storage(self):
  cookie=self.login();payload={'title':'Shared Website App state','group':'789','chapter':7,'content':'Same backend; no App database','idempotency_key':'app-shared-1'};status,_,body=self.request('/api/records',payload,cookie);self.assertEqual(status,201);created=json.loads(body);self.assertEqual(self.request('/api/app/registry',cookie=cookie)[0],200);other=self.login();status,_,body=self.request('/api/state',cookie=other);self.assertEqual(status,200);self.assertEqual(json.loads(body)['records'],[created]);self.assertEqual(self.request('/')[0],200);self.assertEqual(self.request('/operations.js')[0],200)
if __name__=='__main__':unittest.main()
