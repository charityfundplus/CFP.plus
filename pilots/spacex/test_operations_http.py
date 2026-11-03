"""Independent integration checks: real local HTTP, durable SQLite, no live providers."""
import hashlib
import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from operations import Operations, DEMO_PASSWORD
from operations_server import make_server


class IndependentHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cfp-spacex-http-')
        self.root = Path(self.tmp.name)
        self.ops = Operations(self.root)
        self.ops.provision_demo()
        self.ops.provision('beta-admin', DEMO_PASSWORD, 'admin', 'beta')
        for space in ['community', 'chapter-association', 'si-ai-forum', 'super-pair-forum']:
            self.ops.grant_space('beta-admin', space, False)
        self.start()

    def start(self):
        self.server = make_server(self.ops)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def tearDown(self):
        self.stop()
        self.tmp.cleanup()

    def request(self, route, body=None, cookie='', **headers):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        base = {'Host': f'127.0.0.1:{self.port}', 'Origin': f'http://127.0.0.1:{self.port}', 'Content-Type': 'application/json', 'Cookie': cookie}
        base.update(headers)
        conn.request('GET' if body is None else 'POST', route, None if body is None else json.dumps(body), base)
        response = conn.getresponse()
        status, response_headers, raw = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return status, response_headers, json.loads(raw)

    def login(self, id):
        status, headers, body = self.request('/api/session', {'id': id, 'password': DEMO_PASSWORD})
        self.assertEqual(status, 200, body)
        self.assertIn('HttpOnly; SameSite=Strict', headers['Set-Cookie'])
        self.assertNotIn(DEMO_PASSWORD, json.dumps(body))
        return headers['Set-Cookie'].split(';')[0]

    def create(self, cookie, **overrides):
        payload = {'title': 'Independent operational record', 'content': 'Synthetic integration test only', 'group': '246', 'chapter': 6, 'idempotency_key': 'independent-1'}
        payload.update(overrides)
        return self.request('/api/records', payload, cookie)

    def state(self, cookie):
        status, _, body = self.request('/api/state', cookie=cookie)
        self.assertEqual(status, 200, body)
        return body

    def test_01_read_write_reload_independent_session_and_idempotency(self):
        author = self.login('editor')
        code, _, record = self.create(author)
        self.assertEqual(code, 201)
        self.stop()
        self.ops = Operations(self.root)
        self.start()
        second = self.login('editor')
        self.assertNotEqual(author, second)
        self.assertEqual(self.state(second)['records'], [record])
        self.assertEqual(self.create(second)[2], record)
        self.assertEqual(self.create(second, title='Conflicting retry')[0], 409)
        self.assertEqual(len(self.state(second)['records']), 1)

    def test_02_five_groups_ten_chapters_and_blocked_external_connectors(self):
        state = self.state(self.login('viewer'))
        self.assertEqual(state['groups'], {'V': [], '0': [0], '135': [1, 3, 5], '246': [2, 4, 6], '789': [7, 8, 9]})
        self.assertEqual([r['url'] for r in state['chapters']], [f'https://cfp.plus/{i}' for i in range(10)])
        self.assertEqual(len(state['connectors']), 7)
        self.assertTrue(all(c['status'] == 'BLOCKED' for c in state['connectors']))
        self.assertTrue(state['audit_valid'])

    def test_03_outage_survives_restart_then_catchup_without_duplicates(self):
        editor = self.login('editor')
        record = self.create(editor)[2]
        replica = self.root / 'replica.sqlite'
        replica.rename(self.root / 'replica.saved')
        replica.mkdir()  # Real SQLite open failure; no mocked connector response.
        result = self.request('/api/sync', {}, editor)
        self.assertEqual(result[0], 200)
        self.assertEqual(result[2]['results'][0]['status'], 'PENDING')
        self.stop()
        self.ops = Operations(self.root)
        self.start()
        self.assertEqual(self.state(editor)['queue'][0]['status'], 'PENDING')
        self.assertEqual(self.state(editor)['records'][0]['key'], record['key'])
        replica.rmdir()
        (self.root / 'replica.saved').rename(replica)
        self.assertEqual(self.request('/api/sync', {}, editor)[2]['results'][0]['status'], 'SYNCED')
        state = self.state(editor)
        self.assertEqual(state['digest'], state['replica']['digest'])
        self.assertEqual(state['records'], state['replica']['records'])
        self.assertEqual(self.request('/api/sync', {}, editor)[2]['results'], [])
        self.assertEqual(len(self.state(editor)['replica']['records']), 1)

    def test_04_backup_restore_actual_file_readback_and_cross_workspace_denial(self):
        editor, admin = self.login('editor'), self.login('admin')
        record = self.create(editor)[2]
        code, _, backup = self.request('/api/backup', {}, admin)
        self.assertEqual(code, 200)
        self.assertEqual(self.request('/api/restore', {'backup_id': backup['backup_id']}, self.login('beta-admin'))[0], 404)
        code, _, restore = self.request('/api/restore', {'backup_id': backup['backup_id']}, admin)
        self.assertEqual(code, 200)
        path = self.root / ('restore-' + restore['restore_id'] + '.sqlite')
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(json.loads(db.execute('SELECT payload FROM records WHERE key=?', (record['key'],)).fetchone()[0]), record)
        self.assertEqual(restore['digest'], backup['digest'])
        self.assertEqual(self.state(editor)['records'], [record])
        with sqlite3.connect(self.root / ('backup-' + backup['backup_id'] + '.sqlite')) as db:
            db.execute("UPDATE records SET payload='{}'")
        self.assertEqual(self.request('/api/restore', {'backup_id': backup['backup_id']}, admin)[0], 409)

    def test_05_permission_origin_session_and_path_boundaries(self):
        self.assertEqual(self.request('/api/state')[0], 401)
        editor, viewer = self.login('editor'), self.login('viewer')
        self.create(editor)
        self.assertEqual(self.create(viewer)[0], 403)
        for path in ['/api/sync', '/api/backup']:
            self.assertEqual(self.request(path, {}, viewer)[0], 403)
        self.assertEqual(self.request('/api/backup', {}, editor)[0], 403)
        self.assertEqual(self.state(self.login('foreign'))['records'], [])
        self.assertEqual(self.request('/api/sync', {}, editor, Origin='https://hostile.example')[0], 403)
        self.assertEqual(self.request('/api/state', cookie=editor, Host='hostile.example')[0], 403)
        self.assertEqual(self.request('/api/session', {'id': 'editor', 'password': DEMO_PASSWORD, 'role': 'admin'})[0], 400)
        self.assertEqual(self.request('/api/restore', {'backup_id': '../../operations'}, self.login('admin'))[0], 404)
        self.assertEqual(self.create(editor, group='000', chapter=0)[0], 400)
        self.assertEqual(self.request('/api/logout', {}, editor)[0], 200)
        self.assertEqual(self.request('/api/state', cookie=editor)[0], 401)

    def test_06_source_tampering_fails_closed_over_http(self):
        editor = self.login('editor')
        self.create(editor)
        with sqlite3.connect(self.root / 'operations.sqlite') as db:
            db.execute("UPDATE records SET payload='{}' WHERE workspace='alpha'")
        code, _, body = self.request('/api/state', cookie=editor)
        self.assertEqual(code, 503)
        self.assertEqual(body['error'], 'RECORD_INTEGRITY_FAILURE')


if __name__ == '__main__':
    unittest.main()
