"""Local operational extension of the existing SpaceX pilot; no external connectors.

Operational UUID keys are not CFP canonical identities. Source Registry is read-only.
Two local SQLite databases demonstrate at-least-once outbox replication only.
"""
import hashlib
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
            ''')
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
        return {'sequence': sequence, 'hash': previous, 'digest': digest(records), 'records': records}

    def _verify_all(self):
        with self.connect() as db:
            for row in db.execute('SELECT workspace FROM audit UNION SELECT workspace FROM records'):
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
        try:
            with self.replica_connect() as replica:
                records = [self._record(r['payload'], actor['workspace'], r['key']) for r in replica.execute('SELECT key,payload FROM records WHERE workspace=? ORDER BY key', (actor['workspace'],))]
                integrity = all(r.get('workspace') == actor['workspace'] and digest({k: v for k, v in r.items() if k != 'content_hash'}) == r.get('content_hash') for r in records)
                replica_state = {'records': records, 'digest': digest(records), 'status': 'LOCAL AVAILABLE' if integrity else 'INTEGRITY FAILURE', 'integrity_valid': integrity, 'matches_source': integrity and digest(records) == verified['digest']}
        except OperationError as e:
            replica_state = {'records': [], 'digest': None, 'status': 'INTEGRITY FAILURE' if e.code == 'RECORD_INTEGRITY_FAILURE' else 'OFFLINE', 'integrity_valid': False, 'matches_source': False}
        except (sqlite3.Error, OSError):
            replica_state = {'records': [], 'digest': None, 'status': 'OFFLINE', 'integrity_valid': False, 'matches_source': False}
        return {'scope': 'LOCAL SANDBOX', 'user': actor, 'groups': GROUPS, 'chapters': [{'chapter': i, 'title': title, 'url': f'https://cfp.plus/{i}'} for i, title in enumerate(CHAPTERS)], 'records': verified['records'], 'digest': verified['digest'], 'queue': queue, 'replica': replica_state, 'audit': audit, 'audit_valid': True, 'connectors': [{'name': n, 'status': 'BLOCKED', 'reason': 'No tested authorized external binding'} for n in CONNECTORS]}

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
            id = uuid.uuid4().hex
            target = self._artifact('backup', id)
            try:
                with sqlite3.connect(target) as backup:
                    os.chmod(target, 0o600)
                    backup.executescript('CREATE TABLE records(workspace TEXT,key TEXT,payload TEXT,PRIMARY KEY(workspace,key)); CREATE TABLE audit(workspace TEXT,seq INTEGER,payload TEXT,hash TEXT,PRIMARY KEY(workspace,seq));')
                    for table in ['records', 'audit']:
                        rows = db.execute(f'SELECT * FROM {table} WHERE workspace=?', (actor['workspace'],)).fetchall()
                        if rows:
                            backup.executemany(f'INSERT INTO {table} VALUES({",".join("?" for _ in rows[0])})', [tuple(r) for r in rows])
                with sqlite3.connect(target) as saved:
                    saved.row_factory = sqlite3.Row
                    require(saved.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'BACKUP_INTEGRITY_FAILURE', 503)
                    checkpoint = self._verify(saved, actor['workspace'])
                    require(checkpoint['digest'] == verified['digest'] and checkpoint['hash'] == verified['hash'], 'BACKUP_INTEGRITY_FAILURE', 503)
                sha = hashlib.sha256(target.read_bytes()).hexdigest()
                receipt = {'backup_id': id, 'workspace': actor['workspace'], 'sha256': sha, 'digest': verified['digest'], 'record_count': len(verified['records']), 'audit_hash': verified['hash']}
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
                require(verified['digest'] == receipt['digest'] and verified['hash'] == receipt['audit_hash'], 'BACKUP_INTEGRITY_FAILURE', 409)
                id = uuid.uuid4().hex
                destination = self._artifact('restore', id)
                with sqlite3.connect(destination) as restored:
                    os.chmod(destination, 0o600)
                    backup.backup(restored)
                with sqlite3.connect(destination) as restored:
                    restored.row_factory = sqlite3.Row
                    check = self._verify(restored, actor['workspace'])
                    require(check['digest'] == receipt['digest'], 'RESTORE_INTEGRITY_FAILURE', 503)
            result = {'restore_id': id, 'backup_id': backup_id, 'digest': check['digest'], 'record_count': len(check['records']), 'source_unchanged': True, 'scope': 'NEW ISOLATED LOCAL SQLITE COPY'}
            self.event(db, actor, 'backup.restore', result)
            return result
