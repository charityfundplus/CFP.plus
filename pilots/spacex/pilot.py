"""Offline one-way snapshot importer. No network clients or source write capability."""
import argparse, hashlib, json, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_SHA256 = 'a63c5e0b8af157b0938014d51da94ea924b9721acd0a11a9107f5deea3c6f507'
FIELDS = {'id', 'parent_id', 'name', 'type', 'status'}
ALLOWED = {'691181': '69118'}  # existing Registry identity, fixture only; NOT SpaceX allocation

def writeback(*args, **kwargs):
    raise PermissionError('WRITEBACK_BLOCKED: no reverse capability')

def validate(records):
    if not isinstance(records, list) or not records or len(records) > 20:
        raise ValueError('Expected 1..20 records')
    result, seen = [], set()
    for item in records:
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise ValueError('Exact whitelist required')
        if any(not isinstance(v, str) or not v or len(v) > 200 for v in item.values()):
            raise ValueError('Invalid field')
        key = item['id']
        if key not in ALLOWED or item['parent_id'] != ALLOWED[key] or key in seen:
            raise ValueError('Unapproved or duplicate identity / parent')
        if item['name'] != 'ChatGPT' or item['type'] != 'ai':
            raise ValueError('Fixture identity mismatch')
        # No free-text input from production is accepted by this fixture importer.
        if item['status'] != 'SANDBOX_FIXTURE_ONLY':
            raise ValueError('Fixture status required')
        seen.add(key)
        result.append(dict(item))
    return sorted(result, key=lambda r: r['id'])

def import_snapshot(records, sandbox, *, enabled=False, reverse=False, schema_version=1):
    if reverse:
        writeback()
    if not enabled:
        raise PermissionError('KILL_SWITCH_OFF')
    if type(schema_version) is not int or schema_version != 1:
        raise ValueError('SCHEMA_VERSION_UNSUPPORTED')
    rows = validate(records)  # reject before creating destination
    sandbox = Path(sandbox).resolve()
    sandbox.mkdir(parents=True, exist_ok=True)
    db = sandbox / 'pilot.sqlite'
    if db.is_symlink():
        raise ValueError('Symlink destination rejected')
    payload = json.dumps(rows, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE IF NOT EXISTS snapshots (seq INTEGER PRIMARY KEY, digest TEXT UNIQUE, payload TEXT)')
        con.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, event TEXT, digest TEXT, utc TEXT DEFAULT CURRENT_TIMESTAMP)')
        current = con.execute('SELECT digest FROM snapshots ORDER BY seq DESC LIMIT 1').fetchone()
        if current and current[0] == digest:
            return 'UNCHANGED'
        if con.execute('SELECT 1 FROM snapshots WHERE digest=?', (digest,)).fetchone():
            raise ValueError('REPLAY_BLOCKED')
        con.execute('INSERT INTO snapshots(digest,payload) VALUES (?,?)', (digest,payload))
        con.execute("INSERT INTO audit(event,digest) VALUES ('IMPORT',?)", (digest,))
    return 'IMPORTED'

def export_ui(sandbox, ui):
    db = Path(sandbox).resolve() / 'pilot.sqlite'
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as con:
        row = con.execute('SELECT digest,payload FROM snapshots ORDER BY seq DESC LIMIT 1').fetchone()
        audit = con.execute('SELECT event,digest,utc FROM audit ORDER BY seq').fetchall()
    data = {'mode':'OFFLINE FIXTURE', 'digest':row[0], 'records':json.loads(row[1]), 'audit':audit}
    # External script data only, no HTML interpretation.
    target = Path(ui).resolve() / 'snapshot.js'
    target.write_text('window.PILOT_DATA = ' + json.dumps(data, ensure_ascii=True) + ';\n')
    return data

def fixture(registry):
    raw = Path(registry).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('SOURCE_SNAPSHOT_UNVERIFIED')
    source = json.loads(raw)
    child, parent = source['691181'], source['69118']
    if child['parent_id'] != parent['id'] or parent['ai_country_id'] != '6911' or parent['country_id'] != '911':
        raise ValueError('Registry chain mismatch')
    return [{k: child[k] for k in ('id','parent_id','name','type')} | {'status':'SANDBOX_FIXTURE_ONLY'}]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--enable', action='store_true')
    p.add_argument('--reverse', action='store_true')
    a = p.parse_args()
    if a.reverse:
        writeback()
    source = ROOT / 'registry.json'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    print(import_snapshot(fixture(source), ROOT / 'sandbox', enabled=a.enable))
    data = export_ui(ROOT / 'sandbox', ROOT / 'ui')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    print(json.dumps({'source_unchanged':True,'source_sha256':before,'digest':data['digest'],'records':data['records']}))
