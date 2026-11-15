"""Collect production evidence without treating HTTP 200 as page acceptance."""
import concurrent.futures,csv,hashlib,html,importlib.util,json,re,tempfile
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('builder',R/'scripts/build_public_site.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)/'public';bindings=builder.build(root)
 ids={str(i) for i in range(10)}|{f'{i:02}' for i in range(100)}|{f'{i:03}' for i in range(1000)}|{x.name for x in root.iterdir() if x.is_dir() and x.name.isdigit()}
 expected={}
 for did in ids:
  file=root/did/'index.html'
  if file.exists():
   match=re.search(r'<h1[^>]*>(.*?)</h1>',file.read_text(),re.S)
   if match:expected[did]=html.unescape(re.sub('<[^>]+>','',match[1])).strip()
 def fetch(did):
  row={'id':did,'url':'https://cfp.plus/'+did,'candidate_source_page':did in expected,'result':'PENDING','publication_claim':False}
  try:
   with urlopen(Request(row['url'],headers={'User-Agent':'CFP-ReadOnly-Verification/1.0'}),timeout=30) as response:
    body=response.read().decode('utf-8','replace');row.update(http=response.status,final_url=response.url,sha256=hashlib.sha256(body.encode()).hexdigest())
   match=re.search(r'<h1[^>]*>(.*?)</h1>',body,re.S);heading=html.unescape(re.sub('<[^>]+>','',match[1])).strip() if match else ''
   row.update(server_heading=heading,expected_heading=expected.get(did,''))
   if did in expected and heading!=expected[did]:row['result']='FAIL / SERVER CONTENT MISMATCH'
   elif did not in expected:row['result']='PENDING / UNASSIGNED IN AVAILABLE SOURCES'
   else:row['result']='PENDING / NEEDS RENDER, LINEAGE, CONTENT AND PUBLICATION EVIDENCE'
  except HTTPError as error:row.update(http=error.code,result='FAIL / EXPECTED SOURCE PAGE' if did in expected else 'PENDING / NO SOURCE ASSIGNMENT')
  except Exception as error:row.update(result='UNKNOWN / REQUEST ERROR',error_type=type(error).__name__)
  return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(fetch,sorted(ids,key=lambda x:(len(x),x))))
 Path('production-http-evidence.json').write_text(json.dumps({'collector':'COMPLETED','website_acceptance':'NOT PASS','count':len(rows),'rows':rows},ensure_ascii=False,indent=2))
 with open('production-http-evidence.csv','w') as file:
  writer=csv.DictWriter(file,fieldnames=sorted({key for row in rows for key in row}));writer.writeheader();writer.writerows(rows)
 print('Collected',len(rows),'production GET observations; no deployment/acceptance claim')
