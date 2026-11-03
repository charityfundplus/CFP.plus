"""Durable technical-account forum flows in the existing Operations database."""
import base64
import hashlib
import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from operations import Operations, OperationError, DEMO_PASSWORD, digest, canonical
from operations_server import make_server


class ForumTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ops = Operations(self.root)
        self.ops.provision_demo()
        self.ops.provision('recipient', DEMO_PASSWORD, 'editor', 'alpha')
        self.ops.provision('beta-admin', DEMO_PASSWORD, 'admin', 'beta')
        self.ops.grant_space('recipient', 'si-ai-forum', True)
        for space in ['community', 'chapter-association', 'si-ai-forum', 'super-pair-forum']:
            self.ops.grant_space('beta-admin', space, True)
        self.author = self.ops.login('editor', DEMO_PASSWORD)
        self.recipient = self.ops.login('recipient', DEMO_PASSWORD)
        self.viewer = self.ops.login('viewer', DEMO_PASSWORD)
        self.foreign = self.ops.login('foreign', DEMO_PASSWORD)
        self.admin = self.ops.login('admin', DEMO_PASSWORD)
        self.beta_admin = self.ops.login('beta-admin', DEMO_PASSWORD)
        self.task_input = {'title': 'Technical sandbox assignment', 'content': 'No external AI ACK claim', 'recipient': 'recipient', 'idempotency_key': 'task-1'}

    def tearDown(self):
        self.temp.cleanup()

    def task(self):
        return self.ops.forum_create_task(self.author, self.task_input)

    def upload(self, task, raw=b'Synthetic independent Evidence\n'):
        return {'task_key': task['key'], 'name': 'evidence.txt', 'content_base64': base64.b64encode(raw).decode(), 'idempotency_key': 'evidence-1'}

    def assert_error(self, code, status, fn):
        with self.assertRaisesRegex(OperationError, code) as raised:
            fn()
        self.assertEqual(raised.exception.status, status)

    def test_full_task_ack_reply_evidence_readback_restart_and_actual_restore(self):
        task = self.task()
        self.assertEqual(task['status'], 'QUEUED')
        self.assertEqual(self.ops.forum_state(self.recipient)['notifications'][0]['task_key'], task['key'])
        accepted = self.ops.forum_ack(self.recipient, {'task_key': task['key']})
        self.assertEqual(accepted['status'], 'ACCEPTED')
        self.assertEqual(accepted['version'], 2)
        self.assertEqual(self.ops.forum_ack(self.recipient, {'task_key': task['key']}), accepted)
        post = self.ops.forum_post(self.recipient, {'task_key': task['key'], 'content': 'Accepted; technical local account', 'idempotency_key': 'reply-1'})
        raw = 'Evidence kiểm thử • UTF8\n'.encode()
        evidence = self.ops.forum_evidence(self.recipient, self.upload(task, raw))
        self.assertEqual(evidence['sha256'], hashlib.sha256(raw).hexdigest())
        reopened = Operations(self.root)
        independent = reopened.login('recipient', DEMO_PASSWORD)
        readback = reopened.forum_read_evidence(independent, evidence['key'])
        self.assertEqual(base64.b64decode(readback['content_base64']), raw)
        self.assertEqual(readback['task_key'], task['key'])
        state = reopened.forum_state(independent)
        self.assertEqual(state['tasks'], [accepted])
        self.assertEqual(state['posts'], [post])
        self.assertEqual(state['evidence'], [evidence])
        self.assertTrue(state['audit_valid'])
        receipt = reopened.backup(self.admin)
        restored = reopened.restore(self.admin, receipt['backup_id'])
        self.assertEqual(restored['forum_digest'], state['digest'])
        self.assertEqual(restored['forum_count'], 3)
        with sqlite3.connect(reopened._artifact('restore', restored['restore_id'])) as db:
            db.row_factory = sqlite3.Row
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            for table, expected in [('forum_tasks', accepted), ('forum_posts', post), ('forum_evidence', evidence)]:
                records = db.execute('SELECT payload FROM ' + table).fetchall()
                self.assertEqual(len(records), 1)
                self.assertEqual(json.loads(records[0]['payload']), expected)
            verified = reopened._verify(db, 'alpha')
            self.assertEqual(verified['forum_digest'], receipt['forum_digest'])
        self.assertEqual(reopened.forum_state(independent)['tasks'], [accepted])

    def test_author_cannot_impersonate_assigned_recipient_or_self_promote(self):
        task = self.task()
        self.assert_error('FORUM_ASSIGNED_RECIPIENT_REQUIRED', 403, lambda: self.ops.forum_ack(self.author, {'task_key': task['key']}))
        self.assert_error('FORUM_ASSIGNED_RECIPIENT_REQUIRED', 403, lambda: self.ops.forum_ack(self.admin, {'task_key': task['key']}))
        self.assert_error('INVALID_FIELDS', 400, lambda: self.ops.forum_ack(self.recipient, {'task_key': task['key'], 'recipient': 'editor'}))
        self.assertEqual(self.ops.forum_state(self.author)['tasks'][0]['status'], 'QUEUED')

    def test_viewer_write_denial_foreign_workspace_and_recipient_no_disclosure(self):
        task = self.task()
        evidence = self.ops.forum_evidence(self.author, self.upload(task))
        for fn in [lambda: self.ops.forum_create_task(self.viewer, self.task_input), lambda: self.ops.forum_ack(self.viewer, {'task_key': task['key']}), lambda: self.ops.forum_post(self.viewer, {'task_key': task['key'], 'content': 'No', 'idempotency_key': 'p'}), lambda: self.ops.forum_evidence(self.viewer, self.upload(task))]:
            self.assert_error('PERMISSION_DENIED', 403, fn)
        self.assertEqual(self.ops.forum_state(self.foreign)['tasks'], [])
        self.assertEqual(self.ops.forum_state(self.foreign)['evidence'], [])
        self.assertEqual(self.ops.forum_state(self.foreign)['notifications'], [])
        for key in [task['key'], '00000000-0000-0000-0000-000000000000']:
            self.assert_error('FORUM_TASK_NOT_FOUND', 404, lambda key=key: self.ops.forum_ack(self.foreign, {'task_key': key}))
        for key in [evidence['key'], '00000000-0000-0000-0000-000000000000']:
            self.assert_error('FORUM_EVIDENCE_NOT_FOUND', 404, lambda key=key: self.ops.forum_read_evidence(self.foreign, key))
        for recipient in ['foreign', 'not-present']:
            self.assert_error('FORUM_RECIPIENT_NOT_FOUND', 404, lambda recipient=recipient: self.ops.forum_create_task(self.author, {**self.task_input, 'recipient': recipient}))
        self.assertEqual(self.ops.forum_read_evidence(self.viewer, evidence['key']), evidence)

    def test_idempotency_and_immutable_append_only_posts(self):
        task = self.task()
        self.assertEqual(self.task(), task)
        self.assert_error('IDEMPOTENCY_CONFLICT', 409, lambda: self.ops.forum_create_task(self.author, {**self.task_input, 'title': 'Different'}))
        data = {'task_key': task['key'], 'content': 'First immutable response', 'idempotency_key': 'reply-1'}
        post = self.ops.forum_post(self.recipient, data)
        self.assertEqual(self.ops.forum_post(self.recipient, data), post)
        self.assert_error('IDEMPOTENCY_CONFLICT', 409, lambda: self.ops.forum_post(self.recipient, {**data, 'content': 'Overwrite denied'}))
        evidence_data = self.upload(task)
        evidence = self.ops.forum_evidence(self.author, evidence_data)
        self.assertEqual(self.ops.forum_evidence(self.author, evidence_data), evidence)
        self.assert_error('IDEMPOTENCY_CONFLICT', 409, lambda: self.ops.forum_evidence(self.author, {**evidence_data, 'content_base64': base64.b64encode(b'Different').decode()}))
        self.assertEqual(self.ops.forum_state(self.author)['posts'], [post])

    def test_evidence_bounds_plaintext_and_filename_labels(self):
        task = self.task()
        data = self.upload(task, b'A' * 32768)
        evidence = self.ops.forum_evidence(self.author, data)
        self.assertEqual(evidence['size'], 32768)
        self.assertEqual(base64.b64decode(self.ops.forum_read_evidence(self.recipient, evidence['key'])['content_base64']), b'A' * 32768)
        self.assert_error('EVIDENCE_TOO_LARGE', 413, lambda: self.ops.forum_evidence(self.author, self.upload(task, b'A' * 32769)))
        for encoded in ['!not-base64', base64.b64encode(b'\xff\xff').decode(), base64.b64encode(b'a\0b').decode()]:
            self.assert_error('EVIDENCE_TEXT_BASE64_REQUIRED', 400, lambda encoded=encoded: self.ops.forum_evidence(self.author, {**data, 'content_base64': encoded}))
        for name in ['../file.txt', 'folder/file.txt', 'folder\\file.txt', 'bad\r\nname.txt']:
            self.assert_error('INVALID_EVIDENCE_NAME', 400, lambda name=name: self.ops.forum_evidence(self.author, {**data, 'name': name}))

    def test_tampered_forum_payload_and_missing_rows_detected(self):
        task = self.task()
        with self.ops.connect() as db:
            original = db.execute('SELECT payload FROM forum_tasks WHERE key=?', (task['key'],)).fetchone()['payload']
        for payload in ['{}', 'invalid-json', '[]', canonical({**task, 'title': 'Tampered'})]:
            with self.ops.connect() as db:
                db.execute('UPDATE forum_tasks SET payload=? WHERE key=?', (payload, task['key']))
            self.assert_error('FORUM_INTEGRITY_FAILURE', 503, lambda: self.ops.forum_state(self.author))
        with self.ops.connect() as db:
            db.execute('UPDATE forum_tasks SET payload=? WHERE key=?', (original, task['key']))
            db.execute('DELETE FROM forum_tasks WHERE key=?', (task['key'],))
        self.assert_error('FORUM_INTEGRITY_FAILURE', 503, lambda: Operations(self.root))

    def test_tampered_evidence_and_failed_audit_commit_roll_back(self):
        task = self.task()
        evidence = self.ops.forum_evidence(self.author, self.upload(task))
        forged = {**evidence, 'content_base64': base64.b64encode(b'Forged').decode()}
        forged['content_hash'] = digest({k: v for k, v in forged.items() if k != 'content_hash'})
        with self.ops.connect() as db:
            db.execute('UPDATE forum_evidence SET payload=? WHERE key=?', (canonical(forged), evidence['key']))
        self.assert_error('FORUM_INTEGRITY_FAILURE', 503, lambda: self.ops.forum_read_evidence(self.author, evidence['key']))
        with self.ops.connect() as db:
            db.execute('UPDATE forum_evidence SET payload=? WHERE key=?', (canonical(evidence), evidence['key']))
            db.execute("CREATE TRIGGER deny_forum_audit BEFORE INSERT ON audit WHEN NEW.payload LIKE '%forum.post.create%' BEGIN SELECT RAISE(ABORT,'AUDIT_OFFLINE'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.ops.forum_post(self.recipient, {'task_key': task['key'], 'content': 'Must roll back', 'idempotency_key': 'fail-post'})
        self.assertEqual(self.ops.forum_state(self.author)['posts'], [])
        with self.ops.connect() as db:
            self.assertIsNone(db.execute("SELECT * FROM requests WHERE key='forum-post:fail-post'").fetchone())

    def test_backup_contains_forum_evidence_cross_workspace_denied(self):
        task = self.task()
        self.ops.forum_evidence(self.author, self.upload(task))
        receipt = self.ops.backup(self.admin)
        self.assertEqual(receipt['forum_count'], 2)
        self.assert_error('ARTIFACT_NOT_FOUND', 404, lambda: self.ops.restore(self.beta_admin, receipt['backup_id']))
        self.assert_error('PERMISSION_DENIED', 403, lambda: self.ops.restore(self.recipient, receipt['backup_id']))

    def test_actual_http_full_flow_shared_session_and_no_new_database(self):
        server = make_server(self.ops)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        def request(path, body=None, cookie='', origin=None):
            c = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            headers = {'Host': f'127.0.0.1:{port}', 'Origin': origin or f'http://127.0.0.1:{port}', 'Content-Type': 'application/json', 'Cookie': cookie}
            c.request('GET' if body is None else 'POST', path, body=None if body is None else json.dumps(body), headers=headers)
            r = c.getresponse()
            data = r.read()
            result = (r.status, dict(r.getheaders()), json.loads(data))
            c.close()
            return result
        try:
            before = {p.name for p in self.root.glob('*.sqlite')}
            self.assertEqual(request('/api/forum/state')[0], 401)
            _, headers, _ = request('/api/session', {'id': 'editor', 'password': DEMO_PASSWORD})
            author = headers['Set-Cookie'].split(';')[0]
            _, headers, _ = request('/api/session', {'id': 'recipient', 'password': DEMO_PASSWORD})
            recipient = headers['Set-Cookie'].split(';')[0]
            status, _, task = request('/api/forum/tasks', self.task_input, author)
            self.assertEqual(status, 200)
            self.assertEqual(request('/api/forum/ack', {'task_key': task['key']}, author)[0], 403)
            self.assertEqual(request('/api/forum/ack', {'task_key': task['key']}, recipient)[2]['status'], 'ACCEPTED')
            self.assertEqual(request('/api/forum/posts', {'task_key': task['key'], 'content': 'Actual HTTP reply', 'idempotency_key': 'http-post'}, recipient)[0], 200)
            status, _, evidence = request('/api/forum/evidence', self.upload(task, b'A' * 32768), recipient)
            self.assertEqual(status, 200)
            status, _, read = request('/api/forum/evidence/' + evidence['key'], cookie=author)
            self.assertEqual(status, 200)
            self.assertEqual(base64.b64decode(read['content_base64']), b'A' * 32768)
            self.assertEqual(read['task_key'], task['key'])
            state = request('/api/forum/state', cookie=recipient)[2]
            self.assertEqual(state['notifications'][0]['status'], 'ACCEPTED')
            self.assertEqual(request('/api/forum/posts', {}, author, origin='https://evil.example')[0], 403)
            self.assertEqual(request('/api/app/registry', cookie=author)[0], 200)
            self.assertEqual({p.name for p in self.root.glob('*.sqlite')}, before)
            self.assertEqual(request('/api/logout', {}, author)[0], 200)
            self.assertEqual(request('/api/forum/state', cookie=author)[0], 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
