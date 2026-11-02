"""Loopback-only HTTP bridge for the existing SpaceX pilot."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit
from operations import Operations, OperationError, require
UI=Path(__file__).parent/'ui'
ASSETS={'/':'index.html',**{'/'+n:n for n in ['index.html','app.js','style.css','snapshot.js','operations.js']}}

def make_server(operations,port=0):
 class Handler(BaseHTTPRequestHandler):
  server_version='CFP-Local-Sandbox'
  def setup(self):
   super().setup();self.connection.settimeout(5)
  def log_message(self,*args):pass
  def send(self,status,value,cookie=None,content_type='application/json; charset=utf-8'):
   body=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode()
   self.send_response(status)
   for k,v in {'Content-Type':content_type,'Content-Length':str(len(body)),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"}.items():self.send_header(k,v)
   if cookie:self.send_header('Set-Cookie',cookie)
   self.end_headers()
   if self.command!='HEAD':self.wfile.write(body)
  def token(self):
   values=[v.strip().split('=',1)[1] for v in self.headers.get('Cookie','').split(';') if v.strip().startswith('cfp_spacex=')]
   require(len(values)==1,'AUTH_DENIED',401);return values[0]
  def handle_request(self):
   try:
    port=self.server.server_address[1];host=self.headers.get('Host','')
    require(host in [f'127.0.0.1:{port}',f'localhost:{port}'],'HOST_DENIED',403)
    parsed=urlsplit(self.path);require(not parsed.scheme and not parsed.netloc and not parsed.query and not parsed.fragment,'INVALID_REQUEST_TARGET');path=parsed.path
    if self.command in ['GET','HEAD'] and path in ASSETS:
     try:body=(UI/ASSETS[path]).read_bytes()
     except OSError:return self.send(404,{'error':'ASSET_NOT_FOUND'})
     return self.send(200,body,content_type=(mimetypes.guess_type(ASSETS[path])[0] or 'application/octet-stream')+'; charset=utf-8')
    if self.command=='GET' and path=='/api/state':return self.send(200,operations.state(self.token()))
    require(self.command=='POST','METHOD_NOT_ALLOWED',405)
    require(self.headers.get('Origin')=='http://'+host,'ORIGIN_DENIED',403)
    require(self.headers.get('Content-Type','').split(';')[0].strip()=='application/json','JSON_REQUIRED',415)
    require(not self.headers.get('Transfer-Encoding'),'TRANSFER_ENCODING_DENIED')
    try:size=int(self.headers.get('Content-Length','-1'))
    except ValueError:raise OperationError('INVALID_CONTENT_LENGTH')
    require(0<=size<=16384,'PAYLOAD_TOO_LARGE',413)
    body=json.loads(self.rfile.read(size));require(isinstance(body,dict),'INVALID_FIELDS')
    if path=='/api/session':
     require(set(body)=={'id','password'},'INVALID_FIELDS');token=operations.login(body['id'],body['password']);state=operations.state(token)
     return self.send(200,{'user':state['user'],'scope':state['scope']},cookie='cfp_spacex='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=900')
    token=self.token()
    if path=='/api/records':return self.send(201,operations.create_record(token,body))
    if path=='/api/restore':
     require(set(body)=={'backup_id'},'INVALID_FIELDS');return self.send(200,operations.restore(token,body['backup_id']))
    require(not body,'INVALID_FIELDS')
    if path=='/api/sync':return self.send(200,operations.sync(token))
    if path=='/api/backup':return self.send(200,operations.backup(token))
    if path=='/api/logout':return self.send(200,operations.logout(token),cookie='cfp_spacex=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
    raise OperationError('NOT_FOUND',404)
   except OperationError as e:return self.send(e.status,{'error':e.code})
   except (ValueError,UnicodeError,KeyError,TypeError):return self.send(400,{'error':'INVALID_REQUEST'})
   except (sqlite3.Error,OSError):return self.send(503,{'error':'STORAGE_UNAVAILABLE'})
  do_GET=do_HEAD=do_POST=do_PUT=do_PATCH=do_DELETE=do_OPTIONS=handle_request
 server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True;return server

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--state-dir',type=Path,required=True);parser.add_argument('--port',type=int,default=8765);parser.add_argument('--provision-demo',action='store_true',help='Explicit synthetic local accounts only; password never printed')
 args=parser.parse_args();operations=Operations(args.state_dir)
 if args.provision_demo:operations.provision_demo()
 server=make_server(operations,args.port);print(json.dumps({'scope':'LOCAL SANDBOX','host':'127.0.0.1','port':server.server_address[1],'external_connectors':'BLOCKED'}),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
