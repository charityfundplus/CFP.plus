"""CFP+ prototype API: Python standard library, SQLite; no external write permissions."""
import json, os, re, sqlite3, threading, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

DB = os.environ.get("CFP_DB", "cfp-core.sqlite3")
TOKEN = os.environ.get("CFP_API_TOKEN", "")
LOCK = threading.Lock()
def now(): return datetime.now(timezone.utc).isoformat()
def connect():
    db = sqlite3.connect(DB, timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS entities (id TEXT PRIMARY KEY, parent TEXT, name TEXT NOT NULL, summary TEXT NOT NULL, official_url TEXT, updated_at TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL, result TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS outbox (event_id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', created_at TEXT NOT NULL)")
    db.commit()
    return db
def valid_id(value): return isinstance(value,str) and bool(re.fullmatch(r"[0-9]{1,32}",value))
def response(handler, status, data):
    body=json.dumps(data,ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type","application/json; charset=utf-8")
    handler.send_header("Content-Length",str(len(body)))
    handler.send_header("Cache-Control","no-store")
    handler.end_headers();handler.wfile.write(body)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=="/health": return response(self,200,{"ok":True,"service":"cfp-core","time":now()})
        if path.startswith("/api/entities/"):
            key=path.removeprefix("/api/entities/")
            if not valid_id(key): return response(self,400,{"error":"invalid_id"})
            with connect() as db:
                row=db.execute("SELECT id,parent,name,summary,official_url,updated_at FROM entities WHERE id=?",(key,)).fetchone()
            return response(self,200 if row else 404,dict(zip(("id","parent","name","summary","official_url","updated_at"),row)) if row else {"error":"not_found"})
        return response(self,404,{"error":"not_found"})
    def do_POST(self):
        if not TOKEN or self.headers.get("Authorization")!="Bearer "+TOKEN:
            return response(self,401,{"error":"unauthorized"})
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=16384: return response(self,413,{"error":"invalid_body_size"})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise ValueError("object_required")
        except (ValueError,json.JSONDecodeError):
            return response(self,400,{"error":"invalid_json"})
        path=urlsplit(self.path).path
        if path=="/api/entities":
            key=data.get("id"); parent=data.get("parent")
            if not valid_id(key) or (parent is not None and not valid_id(parent)):
                return response(self,400,{"error":"invalid_id"})
            # Immutable identity: this API never changes an existing entity or its parent.
            name=data.get("name");summary=data.get("summary");url=data.get("official_url")
            if not isinstance(name,str) or not 0<len(name)<=200 or not isinstance(summary,str) or len(summary)>3000 or (url is not None and (not isinstance(url,str) or not url.startswith("https://") or len(url)>1000)):
                return response(self,400,{"error":"invalid_fields"})
            with LOCK,connect() as db:
                if db.execute("SELECT 1 FROM entities WHERE id=?",(key,)).fetchone(): return response(self,409,{"error":"id_exists_review_required"})
                db.execute("INSERT INTO entities VALUES(?,?,?,?,?,?)",(key,parent,name,summary,url,now()))
                db.commit()
            return response(self,201,{"id":key,"status":"CREATED_PROVISIONAL","did0":False})
        if path=="/api/events":
            key=data.get("entity_id");kind=data.get("kind")
            if not valid_id(key) or kind not in ("ADVICE_REQUEST","OFFICIAL_LINK_CLICK","FEEDBACK"):
                return response(self,400,{"error":"invalid_event"})
            if data.get("consent") is not True: return response(self,403,{"error":"consent_required"})
            payload=data.get("payload",{})
            if not isinstance(payload,dict) or len(json.dumps(payload))>4000: return response(self,400,{"error":"invalid_payload"})
            # Do not accept payment credentials, secrets or unverified purchase claims.
            if any(x in json.dumps(payload).lower() for x in ("card_number","password","cvv","access_token","payment_confirmed")):
                return response(self,400,{"error":"sensitive_or_unverified_data"})
            eid=str(uuid.uuid4());stamp=now();serialized=json.dumps(payload,ensure_ascii=False)
            with LOCK,connect() as db:
                db.execute("INSERT INTO events VALUES(?,?,?,?,?)",(eid,key,kind,serialized,stamp))
                db.execute("INSERT INTO outbox(event_id,kind,payload,status,created_at) VALUES(?,?,?,'PENDING',?)",(eid,kind,json.dumps({"entity_id":key,"payload":payload},ensure_ascii=False),stamp))
                db.commit()
            return response(self,201,{"event_id":eid,"status":"RECORDED","sync":"PENDING"})
        if path=="/api/tasks":
            key=data.get("entity_id");title=data.get("title")
            if not valid_id(key) or not isinstance(title,str) or not 0<len(title)<=200:
                return response(self,400,{"error":"invalid_task"})
            tid=str(uuid.uuid4());stamp=now()
            with LOCK,connect() as db:
                db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?)",(tid,key,title,"QUEUED",None,stamp,stamp));db.commit()
            return response(self,201,{"task_id":tid,"status":"QUEUED","execution":"NOT_STARTED"})
        return response(self,404,{"error":"not_found"})
if __name__=="__main__":
    connect().close()
    host=os.environ.get("CFP_BIND","127.0.0.1")
    port=int(os.environ.get("CFP_PORT","8765"))
    ThreadingHTTPServer((host,port),Handler).serve_forever()
