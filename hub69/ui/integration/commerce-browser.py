"""Loopback-only Chromium smoke. Requires Python playwright and system Chromium.
Not physical Safari/iPhone, native install, HTTPS staging or a complete WCAG audit.
Run after `node build.mjs`; no network other than this temporary local server.
"""
from pathlib import Path
import functools, hashlib, http.server, json, threading
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
out = root / 'evidence' / 'commerce'
out.mkdir(parents=True, exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root / 'dist')))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = 'http://127.0.0.1:' + str(server.server_port)
report = {'mode': 'Chromium loopback snapshot with synthetic fixtures', 'checks': [], 'errors': [], 'screenshots': [], 'physicalSafariIPhone': 'NOT RUN', 'httpsStaging': 'NOT RUN'}
def check(name, condition):
    report['checks'].append({'name': name, 'pass': bool(condition)})
    if not condition: raise AssertionError(name)
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        report['browserVersion'] = browser.version
        context = browser.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin + '/') else route.abort())
        page.goto(origin + '/index.html#catalog', wait_until='networkidle')
        page.evaluate('navigator.serviceWorker.ready')
        page.reload(wait_until='networkidle')
        check('loopback service worker controls page', page.evaluate('!!navigator.serviceWorker.controller'))
        check('four visibly synthetic items', page.locator('#commerce-results .catalog-card').count() == 4)
        page.locator('#commerce-search').fill('DAO TAO')
        check('Vietnamese accent-insensitive search', page.locator('#commerce-results .catalog-card').count() == 1)
        check('search retains keyboard focus', page.locator('#commerce-search').evaluate('(e)=>document.activeElement===e'))
        page.locator('#commerce-kind').select_option('product')
        check('category combines with query and announces empty results', page.locator('#commerce-results').inner_text().find('Không có kết quả') >= 0)
        page.locator('#commerce-search').fill('hoc lieu')
        page.locator('#commerce-results a').click()
        check('product detail never binds identity', 'Chưa gắn định danh' in page.locator('#commerce-content').inner_text())
        for width, height in [(390,844), (768,1024), (1440,1000)]:
            page.set_viewport_size({'width': width, 'height': height})
            for route in ['#home', '#app', '#catalog', '#commerce', '#partners', '#chapters', '#group/V', '#group/000', '#group/135', '#group/246', '#group/789'] + ['#chapter/'+str(i) for i in range(10)]:
                page.evaluate('(hash)=>location.hash=hash', route)
                page.wait_for_timeout(30)
                check(str(width)+' '+route+' no horizontal overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                check(str(width)+' '+route+' one visible main view', page.locator('section.view:visible').count() == 1)
            page.evaluate("location.hash='#catalog'")
            page.wait_for_timeout(50)
            path = out / ('catalog-'+str(width)+'.png')
            page.screenshot(path=str(path), full_page=True)
            report['screenshots'].append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        page.set_viewport_size({'width':390,'height':844})
        page.locator('#menu-toggle').click()
        check('mobile menu exposes expanded state', page.locator('#menu-toggle').get_attribute('aria-expanded') == 'true')
        page.keyboard.press('Escape')
        check('Escape restores menu focus', page.locator('#menu-toggle').evaluate('(e)=>document.activeElement===e') and page.locator('#menu-toggle').get_attribute('aria-expanded') == 'false')
        page.locator('#commerce-search').focus()
        check('search has accessible label', page.locator('label[for="commerce-search"]').inner_text() == 'Tìm sản phẩm, dịch vụ')
        cache_keys = page.evaluate('''async()=>{const result=[];for(const key of await caches.keys()){const c=await caches.open(key);for(const r of await c.keys())result.push(new URL(r.url).pathname);}return result;}''')
        check('worker caches only data-free offline notice', cache_keys == ['/offline.html'])
        manifest = page.request.get(origin+'/manifest.webmanifest').json()
        for icon in manifest['icons']:
            check('PWA icon '+icon['sizes']+' is served', page.request.get(origin+'/'+icon['src']).status == 200)
        context.set_offline(True)
        page.reload(wait_until='domcontentloaded')
        check('real offline navigation shows connection notice', page.locator('h1').inner_text() == 'HUB 69 • Mất kết nối')
        check('offline page has no data/login inputs', page.locator('input').count() == 0)
        context.set_offline(False)
        page.get_by_role('button', name='Thử kết nối lại HUB 69').click()
        page.wait_for_load_state('networkidle')
        check('reconnect returns to HUB69', page.locator('#view-home').is_visible())
        check('no JavaScript page errors', len(report['errors']) == 0)
        browser.close()
finally:
    server.shutdown(); server.server_close()
    (out / 'browser.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'checks': len(report['checks']), 'failed': sum(not c['pass'] for c in report['checks']), 'errors': report['errors']}))
