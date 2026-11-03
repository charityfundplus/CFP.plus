"""Actual social persistence, explicit spaces and bounded software-worker evidence."""
import base64
import hashlib
import http.client
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from operations import Operations, OperationError, DEMO_PASSWORD, SPACES, canonical
from operations_server import make_server


class SocialWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ops = Operations(self.root)
        self.ops.provision_demo()
        self.editor = self.ops.login('editor', DEMO_PASSWORD)
        self.admin = self.ops.login('admin', DEMO_PASSWORD)
        self.viewer = self.ops.login('viewer', DEMO_PASSWORD)
        self.foreign = self.ops.login('foreign', DEMO_PASSWORD)

    def tearDown(self):
        self.temp.cleanup()

    def error(self, code, status, fn):
        with self.assertRaisesRegex(OperationError, code) as caught:
            fn()
        self.assertEqual(caught.exception.status, status)

    def post(self, token=None, space='community', key='post-1'):
        return self.ops.social_post(token or self.editor, {'space': space, 'content': 'Local social post • not simulation', 'idempotency_key': key})

    def profile(self, chapter=0, role='CMP1', key='profile-1'):
        return self.ops.manual_create_profile(self.editor, {'kind': 'cmp-role', 'name': 'Manual CMP sandbox', 'role_label': role, 'description': 'Unverified local manual intake', 'chapter': chapter, 'idempotency_key': key})

    def worker(self, *extra):
        run = subprocess.run([sys.executable, str(Path(__file__).parent / 'software_worker.py'), '--state-dir', str(self.root), '--once', *extra], text=True, capture_output=True, timeout=10, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        return json.loads(run.stdout.strip().splitlines()[-1])

    def task(self, content):
        return self.ops.forum_create_task(self.editor, {'title': 'Local real software task', 'content': content, 'recipient': 'software-worker', 'idempotency_key': 'worker-task'})

    def test_post_independent_comment_reload_and_idempotency(self):
        post = self.post()
        self.assertEqual(self.post(), post)
        comment_data = {'post_key': post['key'], 'content': 'Independent technical admin reply', 'idempotency_key': 'comment-1'}
        comment = self.ops.social_comment(self.admin, comment_data)
        self.assertEqual(self.ops.social_comment(self.admin, comment_data), comment)
        self.error('IDEMPOTENCY_CONFLICT', 409, lambda: self.ops.social_comment(self.admin, {**comment_data, 'content': 'Changed'}))
        reopened = Operations(self.root)
        independent = reopened.login('editor', DEMO_PASSWORD)
        state = reopened.social_state(independent, {'space': 'community'})
        self.assertEqual(state['posts'], [post])
        self.assertEqual(state['comments'], [comment])
        self.assertTrue(state['audit_valid'])
        self.assertTrue(all(c['status'] == 'NOT VERIFIED' for c in state['connectors']))

    def test_four_spaces_explicit_grants_isolation_and_legacy_forum_closed(self):
        self.assertEqual([s['key'] for s in self.ops.social_spaces(self.admin)['spaces']], list(SPACES))
        self.assertEqual([s['key'] for s in self.ops.social_spaces(self.editor)['spaces']], ['community', 'si-ai-forum'])
        for space in SPACES:
            post = self.post(self.admin, space, 'post:' + space)
            self.assertEqual(self.ops.social_state(self.admin, {'space': space})['posts'], [post])
        for space in ['chapter-association', 'super-pair-forum', 'unknown-space']:
            self.error('SPACE_NOT_FOUND', 404, lambda space=space: self.ops.social_state(self.editor, {'space': space}))
        self.error('PERMISSION_DENIED', 403, lambda: self.post(self.viewer))
        private_post = self.ops.social_state(self.admin, {'space': 'super-pair-forum'})['posts'][0]
        self.error('SOCIAL_POST_NOT_FOUND', 404, lambda: self.ops.social_comment(self.editor, {'post_key': private_post['key'], 'content': 'Denied', 'idempotency_key': 'denied'}))
        self.assertEqual(self.ops.social_state(self.foreign, {'space': 'community'})['posts'], [])
        self.error('SOCIAL_POST_NOT_FOUND', 404, lambda: self.ops.social_comment(self.foreign, {'post_key': private_post['key'], 'content': 'Denied', 'idempotency_key': 'denied'}))
        self.ops.provision('community-only', DEMO_PASSWORD, 'editor', 'alpha')
        self.ops.grant_space('community-only', 'community', True)
        restricted = self.ops.login('community-only', DEMO_PASSWORD)
        self.error('SPACE_NOT_FOUND', 404, lambda: self.ops.forum_state(restricted))
        self.error('SPACE_NOT_FOUND', 404, lambda: self.ops.forum_create_task(restricted, {'title': 'Denied', 'content': 'Denied', 'recipient': 'admin', 'idempotency_key': 'denied'}))
        self.error('SPACE_NOT_FOUND', 404, lambda: self.ops.worker_state(restricted))
        visible_audit = self.ops.state(restricted)
        self.assertIn('AUTHORIZED_PROJECTION', visible_audit['audit_scope'])
        self.assertTrue(all(not e['action'].startswith(('forum.', 'worker.')) and (not e['action'].startswith('social.') or e['details'].get('space') == 'community') for e in visible_audit['audit']))

    def test_social_tamper_and_audit_failure_rollback(self):
        post = self.post()
        with self.ops.connect() as db:
            db.execute('UPDATE social_posts SET payload=? WHERE key=?', ('{}', post['key']))
        self.error('SOCIAL_WORKER_INTEGRITY_FAILURE', 503, lambda: self.ops.social_state(self.editor, {'space': 'community'}))
        with self.ops.connect() as db:
            db.execute('UPDATE social_posts SET payload=? WHERE key=?', (canonical(post), post['key']))
            db.execute("CREATE TRIGGER deny_social_comment BEFORE INSERT ON audit WHEN NEW.payload LIKE '%social.comment.create%' BEGIN SELECT RAISE(ABORT,'AUDIT_OFFLINE'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.ops.social_comment(self.admin, {'post_key': post['key'], 'content': 'Must roll back', 'idempotency_key': 'failed-comment'})
        self.assertEqual(self.ops.social_state(self.editor, {'space': 'community'})['comments'], [])

    def test_backup_restore_includes_social_grants_and_content_and_no_grant_admin_denied(self):
        post = self.post()
        comment = self.ops.social_comment(self.admin, {'post_key': post['key'], 'content': 'Persist backup', 'idempotency_key': 'comment-1'})
        self.ops.provision('restricted-admin', DEMO_PASSWORD, 'admin', 'alpha')
        restricted = self.ops.login('restricted-admin', DEMO_PASSWORD)
        self.error('PERMISSION_DENIED', 403, lambda: self.ops.backup(restricted))
        receipt = self.ops.backup(self.admin)
        self.error('PERMISSION_DENIED', 403, lambda: self.ops.restore(restricted, receipt['backup_id']))
        restored = self.ops.restore(self.admin, receipt['backup_id'])
        self.assertEqual(restored['social_count'], 2)
        with sqlite3.connect(self.ops._artifact('restore', restored['restore_id'])) as db:
            self.assertEqual(json.loads(db.execute('SELECT payload FROM social_posts').fetchone()[0]), post)
            self.assertEqual(json.loads(db.execute('SELECT payload FROM social_comments').fetchone()[0]), comment)
            self.assertGreater(db.execute('SELECT count(*) FROM space_grants').fetchone()[0], 0)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        self.assertEqual(restored['extended_digest'], receipt['extended_digest'])

    def test_actual_worker_process_completes_hash_evidence_and_does_not_rerun(self):
        self.assertEqual(self.worker('--provision-worker')['result'], 'IDLE')
        raw = 'Hash actual software output • UTF8'.encode()
        task = self.task(canonical({'operation': 'sha256-text', 'text': raw.decode()}))
        result = self.worker()
        self.assertEqual(result['result'], 'COMPLETED')
        self.assertEqual(result['task_key'], task['key'])
        self.assertEqual(result['output']['sha256'], hashlib.sha256(raw).hexdigest())
        reopened = Operations(self.root)
        state = reopened.worker_state(self.editor)
        self.assertTrue(state['heartbeat_fresh'])
        self.assertFalse(state['process_liveness_verified'])
        self.assertEqual(len(state['attempts']), 1)
        attempt = state['attempts'][0]
        self.assertEqual([h['status'] for h in attempt['history']], ['RECEIVED', 'RUNNING', 'COMPLETED'])
        self.assertEqual(attempt['attempt'], 1)
        evidence = reopened.forum_read_evidence(self.admin, result['evidence_key'])
        data = json.loads(base64.b64decode(evidence['content_base64']))
        self.assertEqual(data['task_key'], task['key'])
        self.assertEqual(data['output'], result['output'])
        self.assertEqual(self.worker()['result'], 'IDLE')
        self.assertEqual(len(reopened.worker_state(self.editor)['attempts']), 1)
        self.assertEqual(len(reopened.forum_state(self.editor)['evidence']), 1)
        receipt = reopened.backup(self.admin)
        restore = reopened.restore(self.admin, receipt['backup_id'])
        with sqlite3.connect(reopened._artifact('restore', restore['restore_id'])) as db:
            saved = json.loads(db.execute('SELECT payload FROM worker_attempts').fetchone()[0])
            self.assertEqual(saved['output'], result['output'])
            self.assertEqual(saved['task_key'], task['key'])
        reopened.clock = lambda: 10 ** 12
        # A fresh valid session at a later clock sees stale—not "online"—heartbeat.
        later = reopened.login('editor', DEMO_PASSWORD)
        self.assertFalse(reopened.worker_state(later)['heartbeat_fresh'])

    def test_worker_unsupported_operation_alert_no_execution_and_no_duplicate(self):
        self.worker('--provision-worker')
        task = self.task(canonical({'operation': 'shell', 'text': 'touch /tmp/must-not-execute'}))
        result = self.worker()
        self.assertEqual(result, {'result': 'FAILED', 'task_key': task['key'], 'error': 'UNSUPPORTED_OPERATION'})
        state = self.ops.worker_state(self.editor)
        self.assertEqual(state['alerts'][0]['code'], 'UNSUPPORTED_OPERATION')
        self.assertEqual(state['alerts'][0]['task_key'], task['key'])
        self.assertEqual(self.ops.forum_state(self.editor)['evidence'], [])
        self.assertEqual(self.worker()['result'], 'IDLE')
        self.assertEqual(len(self.ops.worker_state(self.editor)['attempts']), 1)
        self.assertFalse((Path('/tmp') / 'must-not-execute').exists())

    def test_manual_chapter_zero_through_nine_and_task_binding_same_records(self):
        profiles = [self.profile(chapter, 'CMP' + str((chapter % 9) + 1), 'profile-' + str(chapter)) for chapter in range(10)]
        readback = self.ops.manual_profiles(self.editor)['profiles']
        self.assertEqual({p['chapter'] for p in readback}, set(range(10)))
        for profile in profiles:
            self.assertFalse(profile['verified'])
            self.assertTrue(all(profile[k] is None for k in ['canonical_id', 'parent', 'did']))
        profile = profiles[0]
        task = self.ops.manual_create_task(self.editor, {'profile_key': profile['key'], 'title': 'Manual chapter0 assignment', 'content': 'Independent human technical reply', 'recipient': 'admin', 'idempotency_key': 'manual-task'})
        self.assertEqual(json.loads(task['content'])['manual_profile_key'], profile['key'])
        self.ops.forum_ack(self.admin, {'task_key': task['key']})
        self.ops.forum_post(self.admin, {'task_key': task['key'], 'content': 'Manual response', 'idempotency_key': 'manual-reply'})
        evidence = self.ops.forum_evidence(self.admin, {'task_key': task['key'], 'name': 'manual.txt', 'content_base64': base64.b64encode(b'manual evidence').decode(), 'idempotency_key': 'manual-evidence'})
        reopened = Operations(self.root)
        self.assertEqual(reopened.forum_read_evidence(self.editor, evidence['key'])['task_key'], task['key'])
        self.assertEqual(len(reopened.manual_profiles(self.editor)['profiles']), 10)
        self.error('MANUAL_PROFILE_NOT_FOUND', 404, lambda: self.ops.manual_create_task(self.foreign, {'profile_key': profile['key'], 'title': 'Denied', 'content': 'Denied', 'recipient': 'foreign', 'idempotency_key': 'foreign-manual'}))
        self.error('INVALID_FIELDS', 400, lambda: self.ops.manual_create_profile(self.editor, {'kind': 'cmp-role', 'name': 'Invalid', 'role_label': 'CMP1', 'description': 'No IDs', 'chapter': 0, 'idempotency_key': 'invalid', 'canonical_id': '123'}))
        self.error('INVALID_MANUAL_ROLE', 400, lambda: self.profile(0, 'CMP10', 'invalid-role'))
        with self.ops.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM records').fetchone()[0], 10)
        self.assertEqual({p.name for p in self.root.glob('*.sqlite')}, {'operations.sqlite', 'replica.sqlite'})

    def test_manual_profile_worker_wrapper_executes_only_whitelisted_operation(self):
        self.worker('--provision-worker')
        profile = self.profile()
        task = self.ops.manual_create_task(self.editor, {'profile_key': profile['key'], 'title': 'Manual bounded worker', 'content': canonical({'operation': 'sha256-text', 'text': 'profile-associated task'}), 'recipient': 'software-worker', 'idempotency_key': 'manual-worker-task'})
        result = self.worker()
        self.assertEqual(result['result'], 'COMPLETED')
        self.assertEqual(result['task_key'], task['key'])
        self.assertEqual(result['output']['sha256'], hashlib.sha256(b'profile-associated task').hexdigest())

    def test_actual_http_login_post_comment_and_space_access(self):
        server = make_server(self.ops)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        def request(path, body=None, cookie='', origin=None):
            c = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            c.request('GET' if body is None else 'POST', path, body=None if body is None else json.dumps(body), headers={'Origin': origin or f'http://127.0.0.1:{port}', 'Content-Type': 'application/json', 'Cookie': cookie})
            r = c.getresponse(); result = (r.status, dict(r.getheaders()), json.loads(r.read())); c.close(); return result
        try:
            self.assertEqual(request('/api/social/spaces')[0], 401)
            _, headers, _ = request('/api/session', {'id': 'editor', 'password': DEMO_PASSWORD})
            editor = headers['Set-Cookie'].split(';')[0]
            status, _, post = request('/api/social/posts', {'space': 'community', 'content': 'Actual HTTP post', 'idempotency_key': 'http-post'}, editor)
            self.assertEqual(status, 200)
            _, headers, _ = request('/api/session', {'id': 'admin', 'password': DEMO_PASSWORD})
            admin = headers['Set-Cookie'].split(';')[0]
            status, _, comment = request('/api/social/comments', {'post_key': post['key'], 'content': 'Actual independent response', 'idempotency_key': 'http-comment'}, admin)
            self.assertEqual(status, 200)
            status, _, state = request('/api/social/state', {'space': 'community'}, editor)
            self.assertEqual(status, 200)
            self.assertEqual(state['posts'], [post]); self.assertEqual(state['comments'], [comment])
            self.assertEqual(request('/api/social/state', {'space': 'chapter-association'}, editor)[0], 404)
            self.assertEqual(request('/api/social/state', {'space': 'nonexistent'}, editor)[0], 404)
            self.assertEqual(request('/api/social/posts', {'space': 'community', 'content': 'Denied', 'idempotency_key': 'cross-origin'}, editor, origin='https://evil.example')[0], 403)
            self.assertEqual(request('/api/social/grants', {}, editor)[0], 404)
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == '__main__':
    unittest.main()
