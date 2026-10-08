"""HTTP routing/content gates for the built publication, including reserved slots."""
import argparse, functools, html, http.server, importlib.util, json, re, tempfile, threading, unittest
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('public_builder',R/'scripts/build_public_site.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
def verify(root,base):
 root=Path(root);rows=[];numeric=set(x.name for x in root.iterdir() if x.is_dir() and x.name.isdigit())
 ids={str(i) for i in range(10)}|{f'{i:02d}' for i in range(100)}|{f'{i:03d}' for i in range(1000)}|numeric
 for did in sorted(ids,key=lambda x:(len(x),x)):
  try:
   with urlopen(base+'/'+did,timeout=15) as response:status=response.status;body=response.read().decode()
  except HTTPError as error:status=error.code;body=error.read().decode()
  assigned_file=(root/did/'index.html').is_file()
  expected=200 if assigned_file else 404
  assert status==expected,(did,status,expected)
  if assigned_file:
   assert body==(root/did/'index.html').read_text(),('content mismatch',did)
   assert '<h1' in body,('missing heading',did)
  rows.append({'id':did,'url':base+'/'+did,'http':status,'routing_test':'PASS','source_page_present':assigned_file,'acceptance':'PENDING EVIDENCE' if assigned_file else 'UNASSIGNED / NO PROFILE'})
 for path in ['/Dockerfile','/.github/workflows/ctttc_ci.yml','/tests/website/test_numeric_content.py','/scripts/build_public_site.py','/nginx.conf','/content/site-standard.json','/registry/69110.md']:
  try:
   with urlopen(base+path,timeout=15) as response:status=response.status
  except HTTPError as error:status=error.code
  assert status==404,('internal exposure',path,status)
 for key in ['V','000','135','246','789',*(str(i) for i in range(10))]:
  with urlopen(base+'/'+key,timeout=15) as response:
   body=response.read().decode();assert response.status==200
   assert all('href="/'+group+'"' in body for group in ['V','000','135','246','789']),('group navigation',key)
   assert all('href="/'+str(chapter)+'"' in body for chapter in range(10)),('chapter navigation',key)
 return rows
class PublicationTests(unittest.TestCase):
 def test_build_and_http(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'public';bindings=builder.build(root)
   handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
   class Quiet(handler.func):
    def log_message(self,*args):pass
   server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   try:rows=verify(root,'http://127.0.0.1:'+str(server.server_port))
   finally:server.shutdown();server.server_close();thread.join()
   self.assertGreaterEqual(len(rows),1110)
   for record in bindings:
    body=(root/record['id']/'index.html').read_text()
    self.assertIn('<h1>'+record['id']+' • '+html.escape(record['name'])+'</h1>',body)
    self.assertIn('Canonical Lock: NO',body)
   self.assertEqual((root/'691141/index.html').read_text(),(R/'691141/index.html').read_text())
   self.assertFalse((root/'999/index.html').exists())
   self.assertNotIn('/id/index.html',(R/'nginx.conf').read_text())
   self.assertNotIn('COPY . /usr/share/nginx/html',(R/'Dockerfile').read_text())
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--root');parser.add_argument('--base');parser.add_argument('--evidence');args=parser.parse_args()
 if args.base:
  rows=verify(args.root,args.base)
  if args.evidence:Path(args.evidence).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
  print('PASS',len(rows),'HTTP routing/content checks + 7 exposure checks; NOT production acceptance')
 else:unittest.main(argv=['public-routing-tests'],verbosity=2)
