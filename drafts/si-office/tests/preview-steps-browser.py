import base64,hashlib,json,pathlib,subprocess,tempfile,os,time,ssl,urllib.request
from playwright.sync_api import sync_playwright,expect
root=pathlib.Path(__file__).resolve().parents[1];checks=[];errors=[]
with tempfile.TemporaryDirectory(prefix='cfp-preview-steps-') as temp:
    directory=pathlib.Path(temp);cert=directory/'cert.pem';key=directory/'key.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
    pub=subprocess.check_output(['openssl','x509','-in',str(cert),'-pubkey','-noout']);der=subprocess.run(['openssl','pkey','-pubin','-outform','DER'],input=pub,capture_output=True,check=True).stdout;pin=base64.b64encode(hashlib.sha256(der).digest()).decode()
    env=dict(os.environ,CFP_FLOW_DB=str(directory/'state.db'),CFP_FLOW_ACCOUNTS=str(directory/'accounts.json'),CFP_FLOW_CERT=str(cert),CFP_FLOW_KEY=str(key))
    server=subprocess.Popen(['node','tests/intake-flow-fixture.mjs'],cwd=root,env=env,stdout=subprocess.DEVNULL)
    try:
        for attempt in range(100):
            try:urllib.request.urlopen('https://localhost:4215/p2',context=ssl.create_default_context(cafile=str(cert)));break
            except Exception:
                if server.poll() is not None:raise RuntimeError('Fixture terminated')
                time.sleep(.1)
        else:raise RuntimeError('Fixture readiness failed')
        accounts=json.loads((directory/'accounts.json').read_text())
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-crash-reporter','--disable-breakpad','--ignore-certificate-errors-spki-list='+pin]);page=browser.new_page(viewport={'width':390,'height':844});page.on('pageerror',lambda e:errors.append(str(e)));page.goto('https://localhost:4215/p2')
            expect(page.locator('#public-curriculum')).not_to_be_empty()
            def links_resolve():
                anchors=page.locator('.preview-nav a');assert anchors.count()==7
                for a in anchors.all():assert page.locator(a.get_attribute('href')).count()==1
            links_resolve();assert page.locator('.preview-nav a').nth(1).get_attribute('href')=='#p2-login-panel';assert page.locator('.preview-nav a').nth(5).get_attribute('href')=='#p2-login-panel'
            checks.append('Anonymous seven-step navigation resolves; registration/work/evidence lead to issued-account login')
            account=next(a for a in accounts if a['role']=='viewer');page.locator('#p2-login-form [name=id]').fill(account['id']);page.locator('#p2-login-form [name=password]').fill(account['password']);page.locator('#p2-login-form button').click();expect(page.locator('#universal-application')).to_be_visible();links_resolve()
            assert page.locator('.preview-nav a').nth(2).get_attribute('href')=='#universal-showcase';expect(page.locator('.preview-nav a').nth(2)).to_contain_text('Chờ review');expect(page.locator('#universal-work-request button')).to_be_disabled()
            page.locator('.preview-nav a').nth(5).click();assert page.url.endswith('#universal-work-request')
            checks.append('Authenticated links use existing universal intake/review/study/work/export; viewer permissions retained')
            page.locator('#core-language').select_option('en');expect(page.locator('.preview-nav a').nth(2)).to_contain_text('Pending review');links_resolve()
            for width in [320,390]:page.set_viewport_size({'width':width,'height':844});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
            page.locator('#p2-logout').click();expect(page.locator('#p2-login-panel')).to_be_visible();links_resolve();assert not errors,errors;checks.append('VI/EN320/390, logout resets links, no page errors; certificate QA limited to exact local SPKI')
            browser.close()
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill();server.wait()
result={'status':'PASS','scope':'Only new seven-step navigation integrated with concurrent8b53169 intake; underlying intake/full training suites not rerun','checks':checks,'pageErrors':errors,'syntheticOnly':True,'servicesStopped':True,'remoteIPhoneURL':None,'realVerification':'NOT VERIFIED'};(root/'docs/PREVIEW_STEPS_BROWSER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
