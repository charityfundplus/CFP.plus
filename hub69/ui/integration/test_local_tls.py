"""Strict local HTTPS integration; not public staging or a device acceptance test."""
import base64
import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'pilots'/'spacex'))
from operations import Operations,DEMO_PASSWORD
from operations_server import make_server


class StrictLocalTLSTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='cfp-local-tls-')
        self.root=Path(self.temp.name)
        ca_key=self.root/'ca.key';ca=self.root/'ca.pem'
        key=self.root/'server.key';csr=self.root/'server.csr';cert=self.root/'server.pem'
        def run(*args):
            subprocess.run(['openssl',*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        run('req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(ca_key),'-out',str(ca),'-days','1','-subj','/CN=CFP Local Test CA')
        run('req','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(csr),'-subj','/CN=localhost')
        ext=self.root/'extensions.conf';ext.write_text('subjectAltName=DNS:localhost\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n')
        run('x509','-req','-in',str(csr),'-CA',str(ca),'-CAkey',str(ca_key),'-CAcreateserial','-out',str(cert),'-days','1','-extfile',str(ext))
        ca_key.chmod(0o600);key.chmod(0o600)
        self.ops=Operations(self.root/'state');self.ops.provision_demo()
        self.server=make_server(self.ops,port=0,secure=True)
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(cert,key)
        self.server.socket=context.wrap_socket(self.server.socket,server_side=True)
        self.port=self.server.server_address[1]
        self.origin=f'https://localhost:{self.port}'
        self.client_context=ssl.create_default_context(cafile=str(ca))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=5);self.temp.cleanup()

    def request(self,path,body=None,cookie='',origin=None):
        connection=http.client.HTTPSConnection('localhost',self.port,context=self.client_context,timeout=10)
        headers={'Origin':origin or self.origin,'Content-Type':'application/json','Cookie':cookie}
        connection.request('GET' if body is None else 'POST',path,None if body is None else json.dumps(body),headers)
        response=connection.getresponse();raw=response.read();status=response.status;headers=dict(response.getheaders());connection.close()
        return status,headers,json.loads(raw) if headers.get('Content-Type','').startswith('application/json') else raw

    def login(self,name):
        status,headers,body=self.request('/api/session',{'id':name,'password':DEMO_PASSWORD})
        self.assertEqual(status,200,body)
        self.assertIn('Secure',headers['Set-Cookie']);self.assertIn('HttpOnly; SameSite=Strict',headers['Set-Cookie'])
        return headers['Set-Cookie'].split(';')[0]

    def test_certificate_verification_and_hostname_are_required(self):
        for hostname,context in [('localhost',ssl.create_default_context()),('127.0.0.1',self.client_context)]:
            connection=http.client.HTTPSConnection(hostname,self.port,context=context,timeout=5)
            try:
                with self.assertRaises(ssl.SSLCertVerificationError):connection.request('GET','/')
            finally:connection.close()
        self.assertEqual(self.request('/')[0],200)
        self.assertEqual(self.request('/app/')[0],200)

    def test_https_login_registry_roles_write_sync_and_verified_restore(self):
        self.assertEqual(self.request('/api/state')[0],401)
        editor,viewer,admin=self.login('editor'),self.login('viewer'),self.login('admin')
        status,_,registry=self.request('/api/app/registry',cookie=editor)
        self.assertEqual(status,200);self.assertEqual(len(registry['records']),26)
        source=REPO/'registry'/'ai-entity-registry.json';self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),registry['sourceSHA256'])
        record={'title':'Strict HTTPS integration','group':'246','chapter':6,'content':'Synthetic test record','idempotency_key':'tls-record'}
        self.assertEqual(self.request('/api/records',record,viewer)[0],403)
        status,_,created=self.request('/api/records',record,editor);self.assertEqual(status,201)
        self.assertEqual(self.request('/api/sync',{},editor)[0],200)
        status,_,state=self.request('/api/state',cookie=editor);self.assertEqual(status,200)
        self.assertEqual(state['records'],state['replica']['records']);self.assertEqual(state['digest'],state['replica']['digest'])
        status,_,backup=self.request('/api/backup',{},admin);self.assertEqual(status,200)
        status,_,restored=self.request('/api/restore',{'backup_id':backup['backup_id']},admin);self.assertEqual(status,200)
        with sqlite3.connect(self.ops.root/('restore-'+restored['restore_id']+'.sqlite')) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(json.loads(db.execute('SELECT payload FROM records WHERE key=?',(created['key'],)).fetchone()[0]),created)
        self.assertEqual(self.request('/api/logout',{},editor)[0],200)
        self.assertEqual(self.request('/api/state',cookie=editor)[0],401)

    def test_https_forum_recipient_ack_evidence_and_origin_boundaries(self):
        editor,admin=self.login('editor'),self.login('admin')
        self.assertEqual(self.request('/api/sync',{},editor,origin=self.origin.replace('https:','http:'))[0],403)
        status,_,task=self.request('/api/forum/tasks',{'title':'TLS task','content':'Strict HTTPS only','recipient':'admin','idempotency_key':'tls-task'},editor);self.assertEqual(status,200)
        self.assertEqual(self.request('/api/forum/ack',{'task_key':task['key']},editor)[0],403)
        self.assertEqual(self.request('/api/forum/ack',{'task_key':task['key']},admin)[0],200)
        payload=b'Strict local TLS evidence\n'
        status,_,evidence=self.request('/api/forum/evidence',{'task_key':task['key'],'name':'tls-evidence.txt','content_base64':base64.b64encode(payload).decode(),'idempotency_key':'tls-evidence'},admin);self.assertEqual(status,200)
        status,_,readback=self.request('/api/forum/evidence/'+evidence['key'],cookie=editor);self.assertEqual(status,200)
        self.assertEqual(readback['task_key'],task['key']);self.assertEqual(base64.b64decode(readback['content_base64']),payload)
        self.assertEqual(readback['sha256'],hashlib.sha256(payload).hexdigest())


if __name__=='__main__':unittest.main()
