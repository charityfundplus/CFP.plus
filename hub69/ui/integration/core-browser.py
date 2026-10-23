"""Real Core HTTP + actual Registry read + Chromium UI, synthetic Office only."""
import sys,json,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
origin=sys.argv[1]
out=Path(__file__).resolve().parents[1]/'evidence'/'commerce'
report={'mode':'Real Core + pinned Git Registry + synthetic Office on loopback Chromium','checks':[],'errors':[],'physicalIPhone':'NOT RUN','httpsStaging':'NOT RUN'}
def check(name,condition):
 report['checks'].append({'name':name,'pass':bool(condition)})
 print(name, bool(condition),flush=True)
 if not condition:raise AssertionError(name)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  report['browserVersion']=browser.version
  context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
  page=context.new_page()
  page.on('pageerror',lambda e:report['errors'].append(str(e)))
  page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(origin+'/') else r.abort())
  page.goto(origin+'/hub69/index.html#catalog',wait_until='domcontentloaded')
  check('anonymous catalog is hidden with no snapshot fallback','Danh mục Core chưa sẵn sàng' in page.locator('#commerce-content').inner_text())
  page.wait_for_function("document.getElementById('commerce-content').textContent.includes('Danh mục Core chưa sẵn sàng')")
  login=context.request.post(origin+'/api/session',headers={'Origin':origin},data={'id':'editor','password':'Synthetic-Browser-Only'})
  check('existing Core authenticates browser session',login.status==200)
  page.locator('#commerce-content [data-core-retry]').click()
  page.wait_for_function("document.getElementById('commerce-content').textContent.includes('Core learning kit')")
  check('Core catalog renders three sandbox records',page.locator('#commerce-results .catalog-card').count()==3)
  page.locator('#commerce-search').fill('learning')
  page.locator('[data-catalog-read]').click()
  page.wait_for_function("document.querySelector('#commerce-results .catalog-card') && document.getElementById('commerce-results').textContent.includes('1 kết quả')")
  check('server search returns one product',page.locator('#commerce-results .catalog-card').count()==1)
  page.locator('#commerce-results a').click()
  page.wait_for_function("document.getElementById('commerce-content').textContent.includes('Chưa gắn định danh')")
  check('detail keeps identity unbound','Chưa gắn định danh' in page.locator('#commerce-content').inner_text())
  page.evaluate("location.hash='#id/691181'")
  page.wait_for_function("document.getElementById('profile').textContent.includes('ChatGPT')")
  check('Website ID screen reads real Registry via same Core', 'ChatGPT' in page.locator('#profile').inner_text())
  page.evaluate("location.hash='#app'")
  page.wait_for_function("document.getElementById('app-content').textContent.includes('Đã đọc Core')")
  check('App uses same authenticated Core session','Đã đọc Core' in page.locator('#app-content').inner_text())
  page.locator('#app-content a[href="#catalog"]').click()
  page.wait_for_function("document.getElementById('commerce-content').textContent.includes('Core learning kit')")
  check('App shortcut opens integrated TMTC',page.locator('#view-commerce').is_visible())
  check('mobile integrated screen has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  path=out/'core-mobile.png';page.screenshot(path=str(path),full_page=True)
  report['screenshot']={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  page.locator('[data-core-logout]').click()
  page.wait_for_function("async()=> (await fetch('/api/v1/commerce/catalog?pairKey=hub69-content-demo',{cache:'no-store'})).status===401")
  page.wait_for_function("document.getElementById('commerce-content').textContent.includes('Danh mục Core chưa sẵn sàng')")
  check('logout removes commerce data','Core learning kit' not in page.locator('#commerce-content').inner_text())
  check('logout revokes server session',context.request.get(origin+'/api/v1/commerce/catalog?pairKey=hub69-content-demo').status==401)
  check('no JavaScript errors',len(report['errors'])==0)
  page.unroute_all(behavior='ignoreErrors')
  browser.close()
finally:(out/'core-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(report['checks']),'failed':sum(not c['pass'] for c in report['checks'])}))
