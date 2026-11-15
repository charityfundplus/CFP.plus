from pathlib import Path
import json,mimetypes,hashlib
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];program=json.loads((root/'configs/training-basic-v1.json').read_text());errors=[];checks=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':390,'height':844});page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  path=r.request.url.split('example.test')[-1]
  if path=='/api/curriculum':r.fulfill(json=program)
  elif path.startswith('/api/'):r.fulfill(status=401,json={'error':'AUTH_DENIED'})
  else:
   file=root/'public'/('p2.html' if path=='/p2' else path.lstrip('/'))
   r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(file.name)[0] or 'application/javascript')
 page.route('http://example.test/**',route);page.goto('http://example.test/p2')
 for language in ['vi','en']:
  page.locator('#core-language').select_option(language)
  expect(page.locator('.preview-nav a')).to_have_count(9)
  expect(page.locator('#template-commerce')).to_contain_text('giả lập' if language=='vi' else 'Synthetic')
  expect(page.locator('#template-hierarchy > details')).to_have_count(5)
  assert page.locator('#template-hierarchy > details > details').count()==10
  for width in [320,390]:
   page.set_viewport_size({'width':width,'height':844});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),(language,width)
  checks.append(language+':9anchors,5groups,10chapters,synthetic commerce notice;320/390px no overflow')
 assert not errors,errors
 out=root/'docs/continuation-20261014';out.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(out/'LINK_COMMERCIAL_RENDER_MOBILE.png'),full_page=True)
 report={'status':'PASS','scope':'Intercepted unauthenticated static UI render only; all API requests mocked401, no sockets/backend/real login/Safari/HTTPS','checks':checks,'pageErrors':errors};(out/'LINK_COMMERCIAL_RENDER.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report));b.close()
