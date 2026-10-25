"""Local Chromium QA; mobile viewport is not actual iPhone Safari."""
import json,threading,functools,sys
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[3]
out=Path(sys.argv[1]);out.mkdir(exist_ok=True)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f'http://127.0.0.1:{server.server_port}'
checks=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for width in [320,375,390,430,1280]:
            context=browser.new_context(viewport={'width':width,'height':844},is_mobile=width<500,has_touch=width<500)
            context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) else route.abort())
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            response=page.goto(origin+'/69');assert response.status==200
            page.wait_for_selector('#five-store-status tbody tr')
            assert page.locator('#five-store-status tbody tr').count()==5
            assert page.locator('#five-store-status tbody').inner_text().count('NOT VERIFIED')==5
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'page overflow at {width}'
            assert not errors,errors
            data=page.request.get(origin+'/69/store-status.json').json();assert len(data['stores'])==5 and data['allStoresSynced'] is False
            if width==390:
                page.locator('#five-store-status').screenshot(path=str(out/'HUB69-mobile-chromium.png'),style='.site-header {position:static!important}')
                assert page.locator('.store-table-scroll').evaluate('(e)=>e.scrollWidth>e.clientWidth')
                page.locator('.store-table-scroll').focus();page.keyboard.press('ArrowRight')
            if width==1280:page.locator('#five-store-status').screenshot(path=str(out/'HUB69-desktop-chromium.png'),style='.site-header {position:static!important}')
            checks.append({'viewportWidth':width,'route':'/69 -> /69/','status':200,'rows':5,'pageOverflow':False,'pageErrors':errors,'result':'PASS'})
            context.close()
        context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
        page=context.new_page();page.goto(origin+'/69/');assert page.locator('#five-store-status tbody tr').count()==5
        checks.append({'test':'five rows readable with JavaScript disabled','result':'PASS'})
        page.goto(origin+'/69/');links=page.locator('a[href^="/"]').evaluate_all('(nodes)=>[...new Set(nodes.map(n=>n.getAttribute("href")))]')
        for link in links:
            if link=='/':continue
            response=page.request.get(origin+link)
            assert response.status==200,(link,response.status)
            checks.append({'route':link,'status':response.status,'result':'PASS','scope':'LOCAL DRAFT SOURCE'})
        browser.close()
    receipt={'browser':'Chromium','mode':'LOCAL LOOPBACK STATIC PREVIEW','actualIPhoneSafari':'NOT TESTED — physical device/session unavailable','productionDeployment':False,'checks':checks}
    (out/'BROWSER_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'checks':len(checks),'failed':0,'actualIPhoneSafari':'NOT TESTED'}))
finally:server.shutdown();server.server_close()
