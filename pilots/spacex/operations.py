"""Local operational extension of the existing SpaceX pilot; no external connectors.

Operational UUID keys are not CFP canonical identities. Source Registry is read-only.
Two local SQLite databases demonstrate at-least-once outbox replication only.
"""
import hashlib
import base64
import binascii
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from pathlib import Path

GROUPS = {'V': [], '0': [0], '135': [1, 3, 5], '246': [2, 4, 6], '789': [7, 8, 9]}
CHAPTERS = ['Nền Tảng', 'Sự Sống', 'Con Người', 'Ba Quỹ', 'Tôn Giáo', 'Cộng Đồng', 'Siêu Trí Tuệ / Công Nghệ', 'Doanh Nghiệp / HSTDN', 'Tổ Chức', 'Quốc Gia']
DEMO_PASSWORD = 'Synthetic-Spacex-Only-20261102'
CONNECTORS = ['Notion', 'GitHub', 'Google Drive', 'Canva', 'Cloud', 'Supabase', 'HubSpot']
SPACES = {'community': 'Cộng Đồng', 'chapter-association': 'Chi Hội', 'si-ai-forum': 'Diễn Đàn SI AI', 'super-pair-forum': 'Diễn Đàn Siêu Bộ Đôi'}
EXTRA_TABLES = {'grants': 'space_grants', 'posts': 'social_posts', 'comments': 'social_comments', 'attempts': 'worker_attempts', 'heartbeats': 'worker_heartbeats'}
EMPTY_EXTENDED = {name: [] for name in EXTRA_TABLES}
WORKER_SUBJECT = 'software-worker'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class OperationError(Exception):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code, self.status = code, status


def require(condition, code, status=400):
    if not condition:
        raise OperationError(code, status)


def text(value, limit):
    return isinstance(value, str) and 0 < len(value.strip()) <= limit


class Operations:
    def __init__(self, state_dir, clock=time.time):
        self.root = Path(state_dir).absolute()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        require(not self.root.is_symlink(), 'STATE_SYMLINK_DENIED')
        self.source = self.root / 'operations.sqlite'
        self.replica = self.root / 'replica.sqlite'
        self.clock = clock
        for path in (self.source, self.replica):
            require(not path.is_symlink(), 'STATE_SYMLINK_DENIED')
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,salt TEXT NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL,workspace TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,subject TEXT NOT NULL REFERENCES users(id),expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,count INTEGER NOT NULL,until REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS records(workspace TEXT NOT NULL,key TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(workspace,key));
                CREATE TABLE IF NOT EXISTS requests(workspace TEXT NOT NULL,subject TEXT NOT NULL,key TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(workspace,subject,key));
                CREATE TABLE IF NOT EXISTS outbox(seq INTEGER PRIMARY KEY AUTOINCREMENT,workspace TEXT NOT NULL,key TEXT NOT NULL,digest TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0, UNIQUE(workspace,key));
                CREATE TABLE IF NOT EXISTS audit(workspace TEXT NOT NULL,seq INTEGER NOT NULL,payload TEXT NOT NULL,hash TEXT NOT NULL,PRIMARY KEY(workspace,seq));
                CREATE TABLE IF NOT EXISTS forum_tasks(workspace TEXT NOT NULL,key TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(workspace,key));
                CREATE TABLE IF NOT EXISTS forum_posts(workspace TEXT NOT NULL,key TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(workspace,key));
                CREATE TABLE IF NOT EXISTS forum_evidence(workspace TEXT NOT NULL,key TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(workspace,key));
            ''')
            for table in EXTRA_TABLES.values():
                db.execute(f'CREATE TABLE IF NOT EXISTS {table}(workspace TEXT NOT NULL,key TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(workspace,key))')
        # Destination failure never blocks recovery/read/write of the source.
        try:
            with self.replica_connect():
                pass
        except (sqlite3.Error, OSError, OperationError):
            pass
        self._verify_all()

    def connect(self):
        require(not self.source.is_symlink(), 'STATE_SYMLINK_DENIED')
        db = sqlite3.connect(self.source, timeout=5)
        os.chmod(self.source, 0o600)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA synchronous=FULL')
        return db

    def replica_connect(self):
        require(not self.replica.is_symlink(), 'STATE_SYMLINK_DENIED')
        db = sqlite3.connect(self.replica, timeout=5)
        os.chmod(self.replica, 0o600)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS records(workspace TEXT NOT NULL,key TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(workspace,key))')
        return db

    def event(self, db, actor, action, details):
        old = db.execute('SELECT seq,hash FROM audit WHERE workspace=? ORDER BY seq DESC LIMIT 1', (actor['workspace'],)).fetchone()
        event = {'sequence': old['seq'] + 1 if old else 1, 'utc': self.clock(), 'actor': actor['id'], 'workspace': actor['workspace'], 'action': action, 'details': details, 'previous_hash': old['hash'] if old else 'GENESIS'}
        db.execute('INSERT INTO audit VALUES(?,?,?,?)', (actor['workspace'], event['sequence'], canonical(event), digest(event)))
        return {**event, 'hash': digest(event)}

    def _record(self, payload, workspace, key=None):
        try:
            record = json.loads(payload)
            fields = {'key', 'workspace', 'subject', 'title', 'group', 'chapter', 'content', 'version', 'created_utc', 'content_hash'}
            require(isinstance(record, dict) and set(record) == fields, 'RECORD_INTEGRITY_FAILURE', 503)
            require(all(isinstance(record[k], str) for k in ['key', 'workspace', 'subject', 'title', 'group', 'content', 'content_hash']), 'RECORD_INTEGRITY_FAILURE', 503)
            require(record['workspace'] == workspace and (key is None or record['key'] == key), 'RECORD_INTEGRITY_FAILURE', 503)
            require(type(record['chapter']) is int and record['group'] in GROUPS and record['chapter'] in GROUPS[record['group']] and type(record['version']) is int and record['version'] == 1 and type(record['created_utc']) in [int, float], 'RECORD_INTEGRITY_FAILURE', 503)
            require(digest({k: v for k, v in record.items() if k != 'content_hash'}) == record['content_hash'], 'RECORD_INTEGRITY_FAILURE', 503)
            return record
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise OperationError('RECORD_INTEGRITY_FAILURE', 503) from e

    def _verify(self, db, workspace):
        previous, sequence, expected = 'GENESIS', 0, {}
        try:
            for row in db.execute('SELECT * FROM audit WHERE workspace=? ORDER BY seq', (workspace,)):
                event = json.loads(row['payload'])
                require(isinstance(event, dict) and set(event) == {'sequence', 'utc', 'actor', 'workspace', 'action', 'details', 'previous_hash'}, 'AUDIT_INTEGRITY_FAILURE', 503)
                require(type(event['sequence']) is int and type(event['utc']) in [int, float] and all(isinstance(event[k], str) for k in ['actor', 'workspace', 'action', 'previous_hash']) and isinstance(event['details'], dict), 'AUDIT_INTEGRITY_FAILURE', 503)
                sequence += 1
                require(event['sequence'] == sequence == row['seq'] and event['workspace'] == workspace and event['previous_hash'] == previous and digest(event) == row['hash'], 'AUDIT_INTEGRITY_FAILURE', 503)
                previous = row['hash']
                if event['action'] == 'record.create':
                    key, content_hash = event['details']['key'], event['details']['content_hash']
                    require(isinstance(key, str) and isinstance(content_hash, str) and key not in expected, 'AUDIT_INTEGRITY_FAILURE', 503)
                    expected[key] = content_hash
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise OperationError('AUDIT_INTEGRITY_FAILURE', 503) from e
        records = []
        for row in db.execute('SELECT * FROM records WHERE workspace=? ORDER BY key', (workspace,)):
            record = self._record(row['payload'], workspace, row['key'])
            require(expected.get(row['key']) == record['content_hash'], 'RECORD_INTEGRITY_FAILURE', 503)
            records.append(record)
        require(set(expected) == {r['key'] for r in records}, 'RECORD_INTEGRITY_FAILURE', 503)
        forum = self._forum_verify(db, workspace)
        extended = self._extended_verify(db, workspace)
        return {'sequence': sequence, 'hash': previous, 'digest': digest(records), 'records': records, 'forum': forum, 'forum_digest': digest(forum), 'extended': extended, 'extended_digest': digest(extended)}

    def _verify_all(self):
        with self.connect() as db:
            for row in db.execute('SELECT workspace FROM audit UNION SELECT workspace FROM records UNION SELECT workspace FROM forum_tasks UNION SELECT workspace FROM forum_posts UNION SELECT workspace FROM forum_evidence UNION SELECT workspace FROM space_grants UNION SELECT workspace FROM social_posts UNION SELECT workspace FROM social_comments UNION SELECT workspace FROM worker_attempts UNION SELECT workspace FROM worker_heartbeats'):
                self._verify(db, row['workspace'])

    def provision(self, id, password, role, workspace):
        require(isinstance(id, str) and re.fullmatch(r'[a-z][a-z0-9-]{1,60}', id) and isinstance(workspace, str) and re.fullmatch(r'[a-z][a-z0-9-]{1,60}', workspace), 'ACCOUNT_INVALID')
        require(text(password, 200) and len(password) >= 16 and role in ['viewer', 'editor', 'admin'], 'ACCOUNT_INVALID')
        salt = secrets.token_hex(16)
        encoded = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        with self.connect() as db:
            db.execute('INSERT INTO users VALUES(?,?,?,?,?)', (id, salt, encoded, role, workspace))
            self.event(db, {'id': 'local-provisioner', 'workspace': workspace}, 'account.provision', {'subject': id, 'role': role, 'synthetic_only': True})

    def provision_demo(self):
        for id, role, workspace in [('editor', 'editor', 'alpha'), ('viewer', 'viewer', 'alpha'), ('admin', 'admin', 'alpha'), ('foreign', 'editor', 'beta')]:
            with self.connect() as db:
                exists = db.execute('SELECT 1 FROM users WHERE id=?', (id,)).fetchone()
            if not exists:
                self.provision(id, DEMO_PASSWORD, role, workspace)
        # Explicit demo provisioning also explicitly grants technical spaces.
        for subject, spaces, write in [('editor', ['community', 'si-ai-forum'], True), ('viewer', ['community', 'si-ai-forum'], False), ('admin', list(SPACES), True), ('foreign', ['community', 'si-ai-forum'], True)]:
            for space in spaces:
                self.grant_space(subject, space, write)

    def login(self, id, password):
        require(text(id, 100) and isinstance(password, str) and len(password) <= 200, 'AUTH_DENIED', 401)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            attempt = db.execute('SELECT * FROM attempts WHERE id=?', (id,)).fetchone()
            require(not attempt or attempt['until'] <= self.clock(), 'LOGIN_RATE_LIMIT', 429)
            row = db.execute('SELECT * FROM users WHERE id=?', (id,)).fetchone()
            actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(row['salt']) if row else bytes(16), n=16384, r=8, p=1).hex()
            if not row or not hmac.compare_digest(actual, row['password']):
                count = attempt['count'] + 1 if attempt else 1
                db.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)', (id, count, self.clock() + 60 if count >= 5 else 0))
                db.commit()
                raise OperationError('AUTH_DENIED', 401)
            db.execute('DELETE FROM attempts WHERE id=?', (id,))
            token = secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), id, self.clock() + 900))
            self.event(db, row, 'session.login', {})
            return token

    def actor(self, db, token):
        require(isinstance(token, str) and len(token) <= 200, 'AUTH_DENIED', 401)
        row = db.execute('SELECT u.* FROM users u JOIN sessions s ON s.subject=u.id WHERE s.hash=? AND s.expires>?', (hashlib.sha256(token.encode()).hexdigest(), self.clock())).fetchone()
        require(row is not None, 'AUTH_DENIED', 401)
        return {'id': row['id'], 'role': row['role'], 'workspace': row['workspace']}

    def allowed(self, actor, roles):
        require(actor['role'] in roles, 'PERMISSION_DENIED', 403)

    def logout(self, token):
        with self.connect() as db:
            actor = self.actor(db, token)
            db.execute('DELETE FROM sessions WHERE hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
            self.event(db, actor, 'session.logout', {})
        return {'logged_out': True}

    def state(self, token):
        with self.connect() as db:
            # Keep audit, records and queue on the same committed read snapshot.
            db.execute('BEGIN')
            actor = self.actor(db, token)
            verified = self._verify(db, actor['workspace'])
            queue = [dict(r) for r in db.execute('SELECT seq,key,digest,status,attempts FROM outbox WHERE workspace=? ORDER BY seq', (actor['workspace'],))]
            audit = [{**json.loads(r['payload']), 'hash': r['hash']} for r in db.execute('SELECT * FROM audit WHERE workspace=? ORDER BY seq', (actor['workspace'],))]
            permitted = {s['key'] for s in self._allowed_spaces(db, actor)}
            audit = [e for e in audit if (not e['action'].startswith(('forum.', 'worker.')) or 'si-ai-forum' in permitted) and (not e['action'].startswith('social.') or e['details'].get('space') in permitted)]
        try:
            with self.replica_connect() as replica:
                records = [self._record(r['payload'], actor['workspace'], r['key']) for r in replica.execute('SELECT key,payload FROM records WHERE workspace=? ORDER BY key', (actor['workspace'],))]
                integrity = all(r.get('workspace') == actor['workspace'] and digest({k: v for k, v in r.items() if k != 'content_hash'}) == r.get('content_hash') for r in records)
                replica_state = {'records': records, 'digest': digest(records), 'status': 'LOCAL AVAILABLE' if integrity else 'INTEGRITY FAILURE', 'integrity_valid': integrity, 'matches_source': integrity and digest(records) == verified['digest']}
        except OperationError as e:
            replica_state = {'records': [], 'digest': None, 'status': 'INTEGRITY FAILURE' if e.code == 'RECORD_INTEGRITY_FAILURE' else 'OFFLINE', 'integrity_valid': False, 'matches_source': False}
        except (sqlite3.Error, OSError):
            replica_state = {'records': [], 'digest': None, 'status': 'OFFLINE', 'integrity_valid': False, 'matches_source': False}
        return {'scope': 'LOCAL SANDBOX', 'user': actor, 'groups': GROUPS, 'chapters': [{'chapter': i, 'title': title, 'url': f'https://cfp.plus/{i}'} for i, title in enumerate(CHAPTERS)], 'records': verified['records'], 'digest': verified['digest'], 'queue': queue, 'replica': replica_state, 'audit': audit, 'audit_valid': True, 'audit_scope': 'AUTHORIZED_PROJECTION; FULL SOURCE CHAIN VERIFIED SERVER-SIDE', 'connectors': [{'name': n, 'status': 'BLOCKED', 'reason': 'No tested authorized external binding'} for n in CONNECTORS]}

    def create_record(self, token, data):
        require(isinstance(data, dict) and set(data) == {'title', 'group', 'chapter', 'content', 'idempotency_key'}, 'INVALID_FIELDS')
        require(text(data['title'], 200) and isinstance(data['content'], str) and len(data['content']) <= 5000 and text(data['idempotency_key'], 100), 'INVALID_RECORD')
        require(isinstance(data['group'], str) and data['group'] in GROUPS and type(data['chapter']) is int and data['chapter'] in GROUPS[data['group']], 'GROUP_CHAPTER_MISMATCH')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.actor(db, token)
            self.allowed(actor, ['editor', 'admin'])
            self._verify(db, actor['workspace'])
            old = db.execute('SELECT digest,result FROM requests WHERE workspace=? AND subject=? AND key=?', (actor['workspace'], actor['id'], data['idempotency_key'])).fetchone()
            if old:
                require(old['digest'] == digest(data), 'IDEMPOTENCY_CONFLICT', 409)
                return json.loads(old['result'])
            record = {'key': str(uuid.uuid4()), 'workspace': actor['workspace'], 'subject': actor['id'], 'title': data['title'], 'group': data['group'], 'chapter': data['chapter'], 'content': data['content'], 'version': 1, 'created_utc': self.clock()}
            record['content_hash'] = digest(record)
            db.execute('INSERT INTO records VALUES(?,?,?)', (actor['workspace'], record['key'], canonical(record)))
            db.execute('INSERT INTO outbox(workspace,key,digest,status) VALUES(?,?,?,?)', (actor['workspace'], record['key'], record['content_hash'], 'PENDING'))
            self.event(db, actor, 'record.create', {'key': record['key'], 'content_hash': record['content_hash']})
            db.execute('INSERT INTO requests VALUES(?,?,?,?,?)', (actor['workspace'], actor['id'], data['idempotency_key'], digest(data), canonical(record)))
            return record

    def sync(self, token):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.actor(db, token)
            self.allowed(actor, ['editor', 'admin'])
            self._verify(db, actor['workspace'])
            pending = db.execute("SELECT * FROM outbox WHERE workspace=? AND status='PENDING' ORDER BY seq", (actor['workspace'],)).fetchall()
            results = []
            for item in pending:
                payload = db.execute('SELECT payload FROM records WHERE workspace=? AND key=?', (actor['workspace'], item['key'])).fetchone()['payload']
                try:
                    with self.replica_connect() as replica:
                        replica.execute('BEGIN IMMEDIATE')
                        old = replica.execute('SELECT payload FROM records WHERE workspace=? AND key=?', (actor['workspace'], item['key'])).fetchone()
                        if old and old['payload'] != payload:
                            status = 'CONFLICT'
                        else:
                            if not old:
                                replica.execute('INSERT INTO records VALUES(?,?,?)', (actor['workspace'], item['key'], payload))
                            status = 'SYNCED'
                except (sqlite3.Error, OSError, OperationError):
                    status = 'PENDING'
                db.execute('UPDATE outbox SET status=?,attempts=attempts+1 WHERE seq=?', (status, item['seq']))
                self.event(db, actor, 'replication.' + status.lower(), {'key': item['key'], 'content_hash': item['digest']})
                results.append({'key': item['key'], 'status': status})
            return {'results': results, 'scope': 'LOCAL SQLITE SOURCE TO LOCAL SQLITE REPLICA', 'external_sync': False}

    def _artifact(self, kind, id):
        require(isinstance(id, str) and re.fullmatch(r'[0-9a-f]{32}', id), 'ARTIFACT_NOT_FOUND', 404)
        path = self.root / (kind + '-' + id + '.sqlite')
        require(not path.is_symlink(), 'ARTIFACT_NOT_FOUND', 404)
        return path

    def backup(self, token):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.actor(db, token)
            self.allowed(actor, ['admin'])
            verified = self._verify(db, actor['workspace'])
            self._all_space_access(db, actor)
            id = uuid.uuid4().hex
            target = self._artifact('backup', id)
            try:
                with sqlite3.connect(target) as backup:
                    os.chmod(target, 0o600)
                    backup.executescript('CREATE TABLE records(workspace TEXT,key TEXT,payload TEXT,PRIMARY KEY(workspace,key)); CREATE TABLE audit(workspace TEXT,seq INTEGER,payload TEXT,hash TEXT,PRIMARY KEY(workspace,seq)); CREATE TABLE forum_tasks(workspace TEXT,key TEXT,payload TEXT,PRIMARY KEY(workspace,key)); CREATE TABLE forum_posts(workspace TEXT,key TEXT,payload TEXT,PRIMARY KEY(workspace,key)); CREATE TABLE forum_evidence(workspace TEXT,key TEXT,payload TEXT,PRIMARY KEY(workspace,key));')
                    for table in EXTRA_TABLES.values():
                        backup.execute(f'CREATE TABLE {table}(workspace TEXT,key TEXT,payload TEXT,PRIMARY KEY(workspace,key))')
                    for table in ['records', 'audit', 'forum_tasks', 'forum_posts', 'forum_evidence', *EXTRA_TABLES.values()]:
                        rows = db.execute(f'SELECT * FROM {table} WHERE workspace=?', (actor['workspace'],)).fetchall()
                        if rows:
                            backup.executemany(f'INSERT INTO {table} VALUES({",".join("?" for _ in rows[0])})', [tuple(r) for r in rows])
                with sqlite3.connect(target) as saved:
                    saved.row_factory = sqlite3.Row
                    require(saved.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'BACKUP_INTEGRITY_FAILURE', 503)
                    checkpoint = self._verify(saved, actor['workspace'])
                    require(checkpoint['digest'] == verified['digest'] and checkpoint['hash'] == verified['hash'] and checkpoint['forum_digest'] == verified['forum_digest'] and checkpoint['extended_digest'] == verified['extended_digest'], 'BACKUP_INTEGRITY_FAILURE', 503)
                sha = hashlib.sha256(target.read_bytes()).hexdigest()
                receipt = {'backup_id': id, 'workspace': actor['workspace'], 'sha256': sha, 'digest': verified['digest'], 'record_count': len(verified['records']), 'audit_hash': verified['hash'], 'forum_digest': verified['forum_digest'], 'forum_count': sum(len(rows) for rows in verified['forum'].values()), 'extended_digest': verified['extended_digest'], 'social_count': len(verified['extended']['posts']) + len(verified['extended']['comments']), 'worker_count': len(verified['extended']['attempts'])}
                manifest = target.with_suffix('.json')
                with manifest.open('x') as f:
                    os.chmod(manifest, 0o600)
                    json.dump(receipt, f)
                self.event(db, actor, 'backup.create', receipt)
                return receipt
            except Exception:
                target.unlink(missing_ok=True)
                target.with_suffix('.json').unlink(missing_ok=True)
                raise

    def restore(self, token, backup_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.actor(db, token)
            self.allowed(actor, ['admin'])
            self._verify(db, actor['workspace'])
            self._all_space_access(db, actor)
            target = self._artifact('backup', backup_id)
            manifest = target.with_suffix('.json')
            require(target.is_file() and manifest.is_file() and not manifest.is_symlink(), 'ARTIFACT_NOT_FOUND', 404)
            receipt = json.loads(manifest.read_text())
            require(receipt['workspace'] == actor['workspace'], 'ARTIFACT_NOT_FOUND', 404)
            # The source audit independently binds the receipt, not just a mutable sidecar.
            bound = any(json.loads(r['payload'])['details'] == receipt for r in db.execute("SELECT payload FROM audit WHERE workspace=?", (actor['workspace'],)) if json.loads(r['payload'])['action'] == 'backup.create')
            require(bound and hashlib.sha256(target.read_bytes()).hexdigest() == receipt['sha256'], 'BACKUP_INTEGRITY_FAILURE', 409)
            with sqlite3.connect(f'file:{target}?mode=ro', uri=True) as backup:
                backup.row_factory = sqlite3.Row
                require(backup.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'BACKUP_INTEGRITY_FAILURE', 409)
                verified = self._verify(backup, actor['workspace'])
                require(verified['digest'] == receipt['digest'] and verified['hash'] == receipt['audit_hash'] and verified['forum_digest'] == receipt.get('forum_digest', digest({'tasks': [], 'posts': [], 'evidence': []})) and verified['extended_digest'] == receipt.get('extended_digest', digest(EMPTY_EXTENDED)), 'BACKUP_INTEGRITY_FAILURE', 409)
                id = uuid.uuid4().hex
                destination = self._artifact('restore', id)
                with sqlite3.connect(destination) as restored:
                    os.chmod(destination, 0o600)
                    backup.backup(restored)
                with sqlite3.connect(destination) as restored:
                    restored.row_factory = sqlite3.Row
                    check = self._verify(restored, actor['workspace'])
                    require(check['digest'] == receipt['digest'] and check['forum_digest'] == receipt.get('forum_digest', digest({'tasks': [], 'posts': [], 'evidence': []})) and check['extended_digest'] == receipt.get('extended_digest', digest(EMPTY_EXTENDED)), 'RESTORE_INTEGRITY_FAILURE', 503)
            result = {'restore_id': id, 'backup_id': backup_id, 'digest': check['digest'], 'record_count': len(check['records']), 'forum_digest': check['forum_digest'], 'forum_count': sum(len(rows) for rows in check['forum'].values()), 'extended_digest': check['extended_digest'], 'social_count': len(check['extended']['posts']) + len(check['extended']['comments']), 'worker_count': len(check['extended']['attempts']), 'source_unchanged': True, 'scope': 'NEW ISOLATED LOCAL SQLITE COPY'}
            self.event(db, actor, 'backup.restore', result)
            return result

    def _forum_verify(self, db, workspace):
        """Validate forum rows against the already verified workspace audit chain."""
        results = {'tasks': [], 'posts': [], 'evidence': []}
        expected = {name: {} for name in results}
        actions = {'forum.task.create': 'tasks', 'forum.task.ack': 'tasks', 'forum.post.create': 'posts', 'forum.evidence.create': 'evidence'}
        try:
            for row in db.execute('SELECT payload FROM audit WHERE workspace=? ORDER BY seq', (workspace,)):
                event = json.loads(row['payload'])
                if event['action'] in actions:
                    details = event['details']
                    require(isinstance(details.get('key'), str) and isinstance(details.get('content_hash'), str), 'FORUM_INTEGRITY_FAILURE', 503)
                    expected[actions[event['action']]][details['key']] = details['content_hash']
            existing = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for name in results:
                table = 'forum_' + name
                if table not in existing:
                    require(not expected[name], 'FORUM_INTEGRITY_FAILURE', 503)
                    continue  # Allows verification of historical forum-free backup artifacts.
                for row in db.execute(f'SELECT key,payload FROM {table} WHERE workspace=? ORDER BY key', (workspace,)):
                    item = json.loads(row['payload'])
                    require(isinstance(item, dict) and item.get('key') == row['key'] and item.get('workspace') == workspace and isinstance(item.get('content_hash'), str), 'FORUM_INTEGRITY_FAILURE', 503)
                    require(digest({k: v for k, v in item.items() if k != 'content_hash'}) == item['content_hash'] == expected[name].get(row['key']), 'FORUM_INTEGRITY_FAILURE', 503)
                    if name == 'tasks':
                        require(set(item) == {'key', 'workspace', 'author', 'recipient', 'title', 'content', 'status', 'version', 'created_utc', 'acknowledged_utc', 'content_hash'}, 'FORUM_INTEGRITY_FAILURE', 503)
                        require(all(isinstance(item[k], str) for k in ['author', 'recipient', 'title', 'content']) and type(item['created_utc']) in [int, float], 'FORUM_INTEGRITY_FAILURE', 503)
                        require(item['status'] in ['QUEUED', 'ACCEPTED'] and type(item['version']) is int and item['version'] == (1 if item['status'] == 'QUEUED' else 2), 'FORUM_INTEGRITY_FAILURE', 503)
                        require(item['acknowledged_utc'] is None if item['status'] == 'QUEUED' else type(item['acknowledged_utc']) in [int, float], 'FORUM_INTEGRITY_FAILURE', 503)
                    elif name == 'posts':
                        require(set(item) == {'key', 'workspace', 'task_key', 'author', 'content', 'created_utc', 'content_hash'} and text(item['content'], 5000), 'FORUM_INTEGRITY_FAILURE', 503)
                    else:
                        require(set(item) == {'key', 'workspace', 'task_key', 'author', 'name', 'content_base64', 'content_type', 'size', 'sha256', 'created_utc', 'content_hash'}, 'FORUM_INTEGRITY_FAILURE', 503)
                        raw = base64.b64decode(item['content_base64'], validate=True)
                        raw.decode('utf-8')
                        require(item['content_type'] == 'text/plain' and type(item['size']) is int and item['size'] == len(raw) and 0 < len(raw) <= 32768 and hashlib.sha256(raw).hexdigest() == item['sha256'], 'FORUM_INTEGRITY_FAILURE', 503)
                    results[name].append(item)
                require(set(expected[name]) == {i['key'] for i in results[name]}, 'FORUM_INTEGRITY_FAILURE', 503)
            tasks = {item['key'] for item in results['tasks']}
            require(all(item['task_key'] in tasks for item in results['posts'] + results['evidence']), 'FORUM_INTEGRITY_FAILURE', 503)
            return results
        except (ValueError, KeyError, TypeError, AttributeError, binascii.Error) as e:
            raise OperationError('FORUM_INTEGRITY_FAILURE', 503) from e

    def _forum_context(self, db, token, write=False):
        actor = self.actor(db, token)
        if write:
            self.allowed(actor, ['editor', 'admin'])
        self._verify(db, actor['workspace'])
        self._space_access(db, actor, 'si-ai-forum', write=write)
        return actor

    def _forum_task(self, db, actor, key):
        require(isinstance(key, str) and len(key) == 36, 'FORUM_TASK_NOT_FOUND', 404)
        row = db.execute('SELECT payload FROM forum_tasks WHERE workspace=? AND key=?', (actor['workspace'], key)).fetchone()
        require(row is not None, 'FORUM_TASK_NOT_FOUND', 404)
        return json.loads(row['payload'])

    def _forum_idempotent(self, db, actor, kind, data):
        require(text(data.get('idempotency_key'), 100), 'IDEMPOTENCY_KEY_REQUIRED')
        key = 'forum-' + kind + ':' + data['idempotency_key']
        old = db.execute('SELECT digest,result FROM requests WHERE workspace=? AND subject=? AND key=?', (actor['workspace'], actor['id'], key)).fetchone()
        if old:
            require(old['digest'] == digest(data), 'IDEMPOTENCY_CONFLICT', 409)
            return key, json.loads(old['result'])
        return key, None

    def _forum_save(self, db, actor, table, action, item, request=None):
        item['content_hash'] = digest(item)
        db.execute(f'INSERT INTO forum_{table}(workspace,key,payload) VALUES(?,?,?)', (actor['workspace'], item['key'], canonical(item)))
        self.event(db, actor, action, {'key': item['key'], 'content_hash': item['content_hash'], 'task_key': item.get('task_key', item['key'])})
        if request:
            key, data = request
            db.execute('INSERT INTO requests VALUES(?,?,?,?,?)', (actor['workspace'], actor['id'], key, digest(data), canonical(item)))
        return item

    def forum_state(self, token):
        with self.connect() as db:
            db.execute('BEGIN')
            actor = self.actor(db, token)
            checked = self._verify(db, actor['workspace'])
            self._space_access(db, actor, 'si-ai-forum')
            result = checked['forum']
            return {**result, 'notifications': [{'key': 'assignment:' + t['key'], 'task_key': t['key'], 'title': t['title'], 'status': t['status'], 'created_utc': t['created_utc'], 'delivery': 'IN_APP_READBACK'} for t in result['tasks'] if t['recipient'] == actor['id']], 'digest': checked['forum_digest'], 'audit_valid': True, 'scope': 'LOCAL SANDBOX; TECHNICAL ACCOUNTS ONLY'}

    def forum_create_task(self, token, data, manual_profile_key=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self._forum_context(db, token, write=True)
            require(isinstance(data, dict) and set(data) == {'title', 'content', 'recipient', 'idempotency_key'}, 'INVALID_FIELDS')
            require(text(data['title'], 200) and text(data['content'], 5000) and text(data['recipient'], 100), 'INVALID_FORUM_TASK')
            if manual_profile_key is not None:
                row = db.execute('SELECT payload FROM records WHERE workspace=? AND key=?', (actor['workspace'], manual_profile_key)).fetchone()
                require(row is not None and self._manual_profile(json.loads(row['payload'])) is not None, 'MANUAL_PROFILE_NOT_FOUND', 404)
                data = {**data, 'content': canonical({'manual_profile_key': manual_profile_key, 'instruction': data['content']})}
                require(len(data['content']) <= 5000, 'INVALID_FORUM_TASK')
            recipient = db.execute('SELECT role FROM users WHERE id=? AND workspace=?', (data['recipient'], actor['workspace'])).fetchone()
            require(recipient is not None, 'FORUM_RECIPIENT_NOT_FOUND', 404)
            require(recipient['role'] in ['editor', 'admin'], 'FORUM_RECIPIENT_NOT_ELIGIBLE', 400)
            self._space_access(db, {'id': data['recipient'], 'role': recipient['role'], 'workspace': actor['workspace']}, 'si-ai-forum', write=True, missing='FORUM_RECIPIENT_NOT_FOUND')
            key, old = self._forum_idempotent(db, actor, 'task', data)
            if old:
                return old
            task = {'key': str(uuid.uuid4()), 'workspace': actor['workspace'], 'author': actor['id'], 'recipient': data['recipient'], 'title': data['title'], 'content': data['content'], 'status': 'QUEUED', 'version': 1, 'created_utc': self.clock(), 'acknowledged_utc': None}
            return self._forum_save(db, actor, 'tasks', 'forum.task.create', task, (key, data))

    def forum_ack(self, token, data):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self._forum_context(db, token, write=True)
            require(isinstance(data, dict) and set(data) == {'task_key'}, 'INVALID_FIELDS')
            task = self._forum_task(db, actor, data['task_key'])
            require(task['recipient'] == actor['id'], 'FORUM_ASSIGNED_RECIPIENT_REQUIRED', 403)
            if task['status'] == 'ACCEPTED':
                return task
            task.update(status='ACCEPTED', version=2, acknowledged_utc=self.clock())
            del task['content_hash']
            task['content_hash'] = digest(task)
            db.execute('UPDATE forum_tasks SET payload=? WHERE workspace=? AND key=?', (canonical(task), actor['workspace'], task['key']))
            self.event(db, actor, 'forum.task.ack', {'key': task['key'], 'task_key': task['key'], 'content_hash': task['content_hash']})
            return task

    def forum_post(self, token, data):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self._forum_context(db, token, write=True)
            require(isinstance(data, dict) and set(data) == {'task_key', 'content', 'idempotency_key'}, 'INVALID_FIELDS')
            task = self._forum_task(db, actor, data['task_key'])
            require(text(data['content'], 5000), 'INVALID_FORUM_POST')
            key, old = self._forum_idempotent(db, actor, 'post', data)
            if old:
                return old
            item = {'key': str(uuid.uuid4()), 'workspace': actor['workspace'], 'task_key': task['key'], 'author': actor['id'], 'content': data['content'], 'created_utc': self.clock()}
            return self._forum_save(db, actor, 'posts', 'forum.post.create', item, (key, data))

    def forum_evidence(self, token, data):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self._forum_context(db, token, write=True)
            require(isinstance(data, dict) and set(data) == {'task_key', 'name', 'content_base64', 'idempotency_key'}, 'INVALID_FIELDS')
            task = self._forum_task(db, actor, data['task_key'])
            require(text(data['name'], 200) and not any(c in data['name'] for c in ['/', '\\', '\0', '\r', '\n']), 'INVALID_EVIDENCE_NAME')
            require(isinstance(data['content_base64'], str), 'INVALID_EVIDENCE')
            require(len(data['content_base64']) <= 43692, 'EVIDENCE_TOO_LARGE', 413)
            try:
                raw = base64.b64decode(data['content_base64'], validate=True)
                decoded = raw.decode('utf-8')
            except (ValueError, UnicodeError, binascii.Error) as e:
                raise OperationError('EVIDENCE_TEXT_BASE64_REQUIRED') from e
            require(0 < len(raw) <= 32768, 'EVIDENCE_TOO_LARGE', 413)
            require('\0' not in decoded, 'EVIDENCE_TEXT_BASE64_REQUIRED')
            key, old = self._forum_idempotent(db, actor, 'evidence', data)
            if old:
                return old
            item = {'key': str(uuid.uuid4()), 'workspace': actor['workspace'], 'task_key': task['key'], 'author': actor['id'], 'name': data['name'], 'content_base64': data['content_base64'], 'content_type': 'text/plain', 'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'created_utc': self.clock()}
            return self._forum_save(db, actor, 'evidence', 'forum.evidence.create', item, (key, data))

    def forum_read_evidence(self, token, key):
        with self.connect() as db:
            db.execute('BEGIN')
            actor = self._forum_context(db, token)
            require(isinstance(key, str) and len(key) == 36, 'FORUM_EVIDENCE_NOT_FOUND', 404)
            row = db.execute('SELECT payload FROM forum_evidence WHERE workspace=? AND key=?', (actor['workspace'], key)).fetchone()
            require(row is not None, 'FORUM_EVIDENCE_NOT_FOUND', 404)
            return json.loads(row['payload'])

    def _extended_verify(self, db, workspace):
        results = {name: [] for name in EXTRA_TABLES}
        expected = {name: {} for name in EXTRA_TABLES}
        actions = {'social.grant': 'grants', 'social.post.create': 'posts', 'social.comment.create': 'comments', 'worker.attempt': 'attempts', 'worker.heartbeat': 'heartbeats'}
        try:
            for row in db.execute('SELECT payload FROM audit WHERE workspace=? ORDER BY seq', (workspace,)):
                event = json.loads(row['payload'])
                if event['action'] in actions:
                    details = event['details']
                    require(isinstance(details.get('key'), str) and isinstance(details.get('content_hash'), str), 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    expected[actions[event['action']]][details['key']] = details['content_hash']
            existing = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for name, table in EXTRA_TABLES.items():
                if table not in existing:
                    require(not expected[name], 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    continue
                for row in db.execute(f'SELECT key,payload FROM {table} WHERE workspace=? ORDER BY key', (workspace,)):
                    item = json.loads(row['payload'])
                    require(isinstance(item, dict) and item.get('key') == row['key'] and item.get('workspace') == workspace and isinstance(item.get('content_hash'), str), 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    require(digest({k: v for k, v in item.items() if k != 'content_hash'}) == item['content_hash'] == expected[name].get(row['key']), 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    if name == 'grants':
                        require(item.get('space') in SPACES and isinstance(item.get('subject'), str) and type(item.get('write')) is bool, 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    elif name in ['posts', 'comments']:
                        require(item.get('space') in SPACES and text(item.get('content'), 5000) and isinstance(item.get('author'), str), 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    elif name == 'attempts':
                        require(item.get('worker') == WORKER_SUBJECT and item.get('task_key') == item['key'] and item.get('attempt') == 1 and item.get('status') in ['RECEIVED', 'RUNNING', 'COMPLETED', 'FAILED'] and isinstance(item.get('history'), list), 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    else:
                        require(item.get('worker') == WORKER_SUBJECT and type(item.get('last_seen_utc')) in [int, float], 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
                    results[name].append(item)
                require(set(expected[name]) == {i['key'] for i in results[name]}, 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
            posts = {r['key']: r for r in results['posts']}
            require(all(c.get('post_key') in posts and c['space'] == posts[c['post_key']]['space'] for c in results['comments']), 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
            if results['attempts']:
                tasks = {r[0] for r in db.execute('SELECT key FROM forum_tasks WHERE workspace=?', (workspace,))}
                evidence = {r[0] for r in db.execute('SELECT key FROM forum_evidence WHERE workspace=?', (workspace,))}
                require(all(a['task_key'] in tasks and (a['status'] != 'COMPLETED' or a.get('evidence_key') in evidence and isinstance(a.get('output'), dict)) for a in results['attempts']), 'SOCIAL_WORKER_INTEGRITY_FAILURE', 503)
            return results
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise OperationError('SOCIAL_WORKER_INTEGRITY_FAILURE', 503) from e

    def _extended_save(self, db, actor, name, action, item):
        item.pop('content_hash', None)
        item['content_hash'] = digest(item)
        table = EXTRA_TABLES[name]
        db.execute(f'INSERT OR REPLACE INTO {table}(workspace,key,payload) VALUES(?,?,?)', (actor['workspace'], item['key'], canonical(item)))
        self.event(db, actor, action, {'key': item['key'], 'content_hash': item['content_hash'], **({'space': item['space']} if 'space' in item else {}), **({'task_key': item['task_key']} if 'task_key' in item else {})})
        return item

    def grant_space(self, subject, space, write=False):
        """Trusted local provisioner only. Deliberately not exposed as an HTTP route."""
        require(isinstance(subject, str) and space in SPACES and type(write) is bool, 'GRANT_INVALID')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            user = db.execute('SELECT workspace FROM users WHERE id=?', (subject,)).fetchone()
            require(user is not None, 'ACCOUNT_NOT_FOUND', 404)
            actor = {'id': 'local-provisioner', 'workspace': user['workspace']}
            self._verify(db, actor['workspace'])
            key = subject + ':' + space
            old = db.execute('SELECT payload FROM space_grants WHERE workspace=? AND key=?', (actor['workspace'], key)).fetchone()
            if old and json.loads(old['payload'])['write'] == write:
                return json.loads(old['payload'])
            item = {'key': key, 'workspace': actor['workspace'], 'subject': subject, 'space': space, 'write': write, 'created_utc': self.clock()}
            return self._extended_save(db, actor, 'grants', 'social.grant', item)

    def _space_access(self, db, actor, space, write=False, missing='SPACE_NOT_FOUND'):
        require(isinstance(space, str) and space in SPACES, missing, 404)
        row = db.execute('SELECT payload FROM space_grants WHERE workspace=? AND key=?', (actor['workspace'], actor['id'] + ':' + space)).fetchone()
        require(row is not None, missing, 404)
        grant = json.loads(row['payload'])
        if write:
            require(grant['write'] and actor['role'] in ['editor', 'admin'], 'PERMISSION_DENIED', 403)
        return grant

    def _all_space_access(self, db, actor):
        require({s['key'] for s in self._allowed_spaces(db, actor)} == set(SPACES), 'PERMISSION_DENIED', 403)

    def _allowed_spaces(self, db, actor):
        result = []
        for space, label in SPACES.items():
            row = db.execute('SELECT payload FROM space_grants WHERE workspace=? AND key=?', (actor['workspace'], actor['id'] + ':' + space)).fetchone()
            if row:
                grant = json.loads(row['payload'])
                result.append({'key': space, 'label': label, 'write': grant['write'] and actor['role'] in ['editor', 'admin']})
        return result

    def social_spaces(self, token):
        with self.connect() as db:
            db.execute('BEGIN')
            actor = self.actor(db, token)
            self._verify(db, actor['workspace'])
            return {'spaces': self._allowed_spaces(db, actor), 'scope': 'TECHNICAL SPACES; NOT CANONICAL IDS'}

    def social_state(self, token, data):
        with self.connect() as db:
            db.execute('BEGIN')
            actor = self.actor(db, token)
            checked = self._verify(db, actor['workspace'])
            require(isinstance(data, dict) and set(data) == {'space'}, 'INVALID_FIELDS')
            self._space_access(db, actor, data['space'])
            return {'space': {'key': data['space'], 'label': SPACES[data['space']]}, 'spaces': self._allowed_spaces(db, actor), 'posts': [p for p in checked['extended']['posts'] if p['space'] == data['space']], 'comments': [c for c in checked['extended']['comments'] if c['space'] == data['space']], 'connectors': [{'name': n, 'status': 'NOT VERIFIED'} for n in CONNECTORS], 'audit_valid': True, 'scope': 'LOCAL SANDBOX; TECHNICAL ACCOUNTS ONLY'}

    def social_post(self, token, data):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.actor(db, token)
            self._verify(db, actor['workspace'])
            require(isinstance(data, dict) and set(data) == {'space', 'content', 'idempotency_key'}, 'INVALID_FIELDS')
            self._space_access(db, actor, data['space'], write=True)
            require(text(data['content'], 5000), 'INVALID_SOCIAL_CONTENT')
            key, old = self._forum_idempotent(db, actor, 'social-post', data)
            if old:
                return old
            item = {'key': str(uuid.uuid4()), 'workspace': actor['workspace'], 'space': data['space'], 'author': actor['id'], 'content': data['content'], 'created_utc': self.clock()}
            self._extended_save(db, actor, 'posts', 'social.post.create', item)
            db.execute('INSERT INTO requests VALUES(?,?,?,?,?)', (actor['workspace'], actor['id'], key, digest(data), canonical(item)))
            return item

    def social_comment(self, token, data):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.actor(db, token)
            self._verify(db, actor['workspace'])
            require(isinstance(data, dict) and set(data) == {'post_key', 'content', 'idempotency_key'}, 'INVALID_FIELDS')
            require(isinstance(data['post_key'], str), 'SOCIAL_POST_NOT_FOUND', 404)
            row = db.execute('SELECT payload FROM social_posts WHERE workspace=? AND key=?', (actor['workspace'], data['post_key'])).fetchone()
            require(row is not None, 'SOCIAL_POST_NOT_FOUND', 404)
            post = json.loads(row['payload'])
            self._space_access(db, actor, post['space'], write=True, missing='SOCIAL_POST_NOT_FOUND')
            require(text(data['content'], 5000), 'INVALID_SOCIAL_CONTENT')
            key, old = self._forum_idempotent(db, actor, 'social-comment', data)
            if old:
                return old
            item = {'key': str(uuid.uuid4()), 'workspace': actor['workspace'], 'space': post['space'], 'post_key': post['key'], 'author': actor['id'], 'content': data['content'], 'created_utc': self.clock()}
            self._extended_save(db, actor, 'comments', 'social.comment.create', item)
            db.execute('INSERT INTO requests VALUES(?,?,?,?,?)', (actor['workspace'], actor['id'], key, digest(data), canonical(item)))
            return item

    def provision_worker(self):
        """Explicit local setup; no credentials printed or external identity inferred."""
        with self.connect() as db:
            row = db.execute('SELECT workspace,role FROM users WHERE id=?', (WORKER_SUBJECT,)).fetchone()
        if not row:
            self.provision(WORKER_SUBJECT, secrets.token_urlsafe(40), 'editor', 'alpha')
        else:
            require(row['workspace'] == 'alpha' and row['role'] == 'editor', 'WORKER_ACCOUNT_CONFLICT', 409)
        self.grant_space(WORKER_SUBJECT, 'si-ai-forum', True)
        return {'worker': WORKER_SUBJECT, 'workspace': 'alpha', 'scope': 'LOCAL SOFTWARE; NO EXTERNAL SI IDENTITY'}

    def worker_session(self):
        """Trusted process selector, not an HTTP authentication bypass."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT id,workspace,role FROM users WHERE id=?', (WORKER_SUBJECT,)).fetchone()
            require(row is not None and row['role'] == 'editor' and row['workspace'] == 'alpha', 'WORKER_NOT_PROVISIONED', 409)
            actor = dict(row)
            self._verify(db, actor['workspace'])
            self._space_access(db, actor, 'si-ai-forum', write=True)
            token = secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), actor['id'], self.clock() + 900))
            self.event(db, actor, 'worker.session', {'technical_process': True})
            return token

    def worker_state(self, token):
        with self.connect() as db:
            db.execute('BEGIN')
            actor = self.actor(db, token)
            checked = self._verify(db, actor['workspace'])
            self._space_access(db, actor, 'si-ai-forum')
            heartbeats = checked['extended']['heartbeats']
            latest = max(heartbeats, key=lambda h: h['last_seen_utc']) if heartbeats else None
            attempts = checked['extended']['attempts']
            return {'worker': WORKER_SUBJECT, 'heartbeat': latest, 'heartbeat_fresh': bool(latest and 0 <= self.clock() - latest['last_seen_utc'] <= 30), 'fresh': bool(latest and 0 <= self.clock() - latest['last_seen_utc'] <= 30), 'process_liveness_verified': False, 'attempts': attempts, 'alerts': [{'task_key': a['task_key'], 'worker': a['worker'], 'code': a['error'], 'utc': a['updated_utc']} for a in attempts if a['status'] == 'FAILED'], 'scope': 'LOCAL SHA256-TEXT SOFTWARE ONLY; NO EXTERNAL AI/PUSH/24H CLAIM'}

    def _worker_check(self, db, token):
        actor = self._forum_context(db, token, write=True)
        require(actor['id'] == WORKER_SUBJECT, 'WORKER_SUBJECT_REQUIRED', 403)
        return actor

    def _worker_attempt_save(self, db, actor, item, status, **changes):
        item.update(changes)
        item['status'] = status
        item['updated_utc'] = self.clock()
        item['history'].append({'status': status, 'utc': self.clock()})
        return self._extended_save(db, actor, 'attempts', 'worker.attempt', item)

    def worker_tick(self, token):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self._worker_check(db, token)
            heartbeat = {'key': actor['id'], 'workspace': actor['workspace'], 'worker': actor['id'], 'process_id': os.getpid(), 'last_seen_utc': self.clock()}
            self._extended_save(db, actor, 'heartbeats', 'worker.heartbeat', heartbeat)
            # A claim is durable before computation; never replay a prior claim.
            rows = db.execute('SELECT key,payload FROM forum_tasks WHERE workspace=? ORDER BY key', (actor['workspace'],)).fetchall()
            task = next((json.loads(r['payload']) for r in rows if json.loads(r['payload'])['recipient'] == actor['id'] and json.loads(r['payload'])['status'] == 'QUEUED' and not db.execute('SELECT 1 FROM worker_attempts WHERE workspace=? AND key=?', (actor['workspace'], r['key'])).fetchone()), None)
            if task is None:
                return {'result': 'IDLE', 'worker': actor['id'], 'heartbeat_utc': heartbeat['last_seen_utc']}
            item = {'key': task['key'], 'task_key': task['key'], 'workspace': actor['workspace'], 'worker': actor['id'], 'attempt': 1, 'operation': None, 'input_sha256': hashlib.sha256(task['content'].encode()).hexdigest(), 'output': None, 'evidence_key': None, 'error': None, 'status': 'RECEIVED', 'created_utc': self.clock(), 'updated_utc': self.clock(), 'history': [], 'process_id': os.getpid()}
            self._worker_attempt_save(db, actor, item, 'RECEIVED')
        try:
            self.forum_ack(token, {'task_key': task['key']})
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                actor = self._worker_check(db, token)
                item = json.loads(db.execute('SELECT payload FROM worker_attempts WHERE workspace=? AND key=?', (actor['workspace'], task['key'])).fetchone()['payload'])
                self._worker_attempt_save(db, actor, item, 'RUNNING')
            try:
                command = json.loads(task['content'])
            except (ValueError, TypeError) as e:
                raise OperationError('INVALID_WORKER_TASK') from e
            if isinstance(command, dict) and set(command) == {'manual_profile_key', 'instruction'}:
                with self.connect() as db:
                    actor = self._worker_check(db, token)
                    require(isinstance(command['manual_profile_key'], str), 'MANUAL_PROFILE_NOT_FOUND', 404)
                    profile = db.execute('SELECT payload FROM records WHERE workspace=? AND key=?', (actor['workspace'], command['manual_profile_key'])).fetchone()
                    require(profile is not None and self._manual_profile(json.loads(profile['payload'])) is not None, 'MANUAL_PROFILE_NOT_FOUND', 404)
                try:
                    command = json.loads(command['instruction'])
                except (ValueError, TypeError) as e:
                    raise OperationError('INVALID_WORKER_TASK') from e
            require(isinstance(command, dict) and set(command) == {'operation', 'text'} and command.get('operation') == 'sha256-text', 'UNSUPPORTED_OPERATION')
            require(isinstance(command['text'], str) and len(command['text'].encode()) <= 5000, 'WORKER_INPUT_TOO_LARGE')
            raw = command['text'].encode('utf-8')
            output = {'operation': 'sha256-text', 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                actor = self._worker_check(db, token)
                item = json.loads(db.execute('SELECT payload FROM worker_attempts WHERE workspace=? AND key=?', (actor['workspace'], task['key'])).fetchone()['payload'])
                require(item['status'] == 'RUNNING', 'WORKER_STATE_CONFLICT', 409)
                result_bytes = canonical({'task_key': task['key'], 'worker': actor['id'], 'input_sha256': item['input_sha256'], 'output': output}).encode()
                evidence = {'key': str(uuid.uuid4()), 'workspace': actor['workspace'], 'task_key': task['key'], 'author': actor['id'], 'name': 'sha256-text-result.json', 'content_base64': base64.b64encode(result_bytes).decode(), 'content_type': 'text/plain', 'size': len(result_bytes), 'sha256': hashlib.sha256(result_bytes).hexdigest(), 'created_utc': self.clock()}
                self._forum_save(db, actor, 'evidence', 'forum.evidence.create', evidence, ('worker-result:' + task['key'], {'task_key': task['key'], 'worker': actor['id']}))
                self._worker_attempt_save(db, actor, item, 'COMPLETED', operation='sha256-text', output=output, evidence_key=evidence['key'])
                return {'result': 'COMPLETED', 'task_key': task['key'], 'output': output, 'evidence_key': evidence['key']}
        except (OperationError, sqlite3.Error, ValueError, TypeError, OSError) as e:
            error = e.code if isinstance(e, OperationError) else 'WORKER_EXECUTION_FAILED'
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                actor = self._worker_check(db, token)
                item = json.loads(db.execute('SELECT payload FROM worker_attempts WHERE workspace=? AND key=?', (actor['workspace'], task['key'])).fetchone()['payload'])
                self._worker_attempt_save(db, actor, item, 'FAILED', error=error)
            return {'result': 'FAILED', 'task_key': task['key'], 'error': error}

    def _manual_profile(self, record):
        try:
            data = json.loads(record['content'])
        except (ValueError, TypeError, KeyError):
            return None
        fields = {'schema', 'kind', 'name', 'role_label', 'description', 'canonical_id', 'parent', 'did', 'verified'}
        if not isinstance(data, dict) or set(data) != fields or data.get('schema') != 'manual-profile-v1':
            return None
        if data['kind'] not in ['super-pair', 'cmp-role', 'topic'] or not text(data['name'], 200) or not text(data['description'], 3000):
            return None
        if data['kind'] == 'cmp-role' and data['role_label'] not in ['CMP' + str(i) for i in range(1, 10)]:
            return None
        if data['kind'] != 'cmp-role' and data['role_label'] not in [None, '']:
            return None
        if any(data[k] is not None for k in ['canonical_id', 'parent', 'did']) or data['verified'] is not False:
            return None
        return {**data, 'key': record['key'], 'profile_key': record['key'], 'chapter': record['chapter'], 'content_hash': record['content_hash']}

    def manual_profiles(self, token):
        with self.connect() as db:
            db.execute('BEGIN')
            actor = self.actor(db, token)
            checked = self._verify(db, actor['workspace'])
            profiles = [profile for record in checked['records'] if (profile := self._manual_profile(record)) is not None]
            return {'profiles': profiles, 'scope': 'MANUAL UNVERIFIED WORKSPACE INTAKE; NO CANONICAL ALLOCATION'}

    def manual_create_profile(self, token, data):
        require(isinstance(data, dict) and set(data) == {'kind', 'name', 'role_label', 'description', 'chapter', 'idempotency_key'}, 'INVALID_FIELDS')
        require(data['kind'] in ['super-pair', 'cmp-role', 'topic'] and text(data['name'], 200) and text(data['description'], 3000) and type(data['chapter']) is int and 0 <= data['chapter'] <= 9, 'INVALID_MANUAL_PROFILE')
        require(data['role_label'] in ['CMP' + str(i) for i in range(1, 10)] if data['kind'] == 'cmp-role' else data['role_label'] in [None, ''], 'INVALID_MANUAL_ROLE')
        profile = {'schema': 'manual-profile-v1', 'kind': data['kind'], 'name': data['name'], 'role_label': data['role_label'] or None, 'description': data['description'], 'canonical_id': None, 'parent': None, 'did': None, 'verified': False}
        group = next(key for key, chapters in GROUPS.items() if data['chapter'] in chapters)
        record = self.create_record(token, {'title': data['name'], 'group': group, 'chapter': data['chapter'], 'content': canonical(profile), 'idempotency_key': 'manual-profile:' + data['idempotency_key'] if text(data['idempotency_key'], 80) else None})
        return self._manual_profile(record)

    def manual_create_task(self, token, data):
        require(isinstance(data, dict) and set(data) == {'profile_key', 'title', 'content', 'recipient', 'idempotency_key'}, 'INVALID_FIELDS')
        require(isinstance(data['profile_key'], str) and len(data['profile_key']) == 36, 'MANUAL_PROFILE_NOT_FOUND', 404)
        return self.forum_create_task(token, {k: v for k, v in data.items() if k != 'profile_key'}, manual_profile_key=data['profile_key'])
