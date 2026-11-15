import base64, hashlib, json, pathlib, subprocess
from playwright.sync_api import sync_playwright, expect

root = pathlib.Path(__file__).resolve().parents[1]
state = pathlib.Path('/workspace/cfp-local-preview-state')
accounts = json.loads((state/'synthetic-review-accounts.json').read_text())['accounts']
pub = subprocess.check_output(['openssl','x509','-in',str(state/'cert.pem'),'-pubkey','-noout'])
der = subprocess.run(['openssl','pkey','-pubin','-outform','DER'],input=pub,capture_output=True,check=True).stdout
pin = base64.b64encode(hashlib.sha256(der).digest()).decode()
checks, errors = [], []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-crash-reporter','--disable-breakpad','--ignore-certificate-errors-spki-list='+pin])
    page = browser.new_page(viewport={'width':390,'height':844})
    page.on('pageerror',lambda error:errors.append(str(error)))
    response = page.goto('https://localhost:4190/p2')
    assert response.status == 200
    expect(page.locator('#p2-login-form button')).to_be_enabled()
    links = page.locator('.preview-nav a')
    assert links.count() == 4
    for i in range(4):
        target = links.nth(i).get_attribute('href')
        assert page.locator(target).count() == 1
        assert links.nth(i).bounding_box()['height'] >= 44
    for width in [360,390,768]:
        page.set_viewport_size({'width':width,'height':844})
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
    checks.append('Four template links resolve; touch targets >=44px; no overflow at360/390/768')
    def login(role):
        account = next(a for a in accounts if a['role']==role)
        page.locator('#p2-login-form [name=id]').fill(account['id'])
        page.locator('#p2-login-form [name=password]').fill(account['password'])
        page.locator('#p2-login-form button').click()
        expect(page.locator('#p2-account')).to_contain_text(account['id'])
        expect(page.locator('#p2-lesson-content')).not_to_be_empty()
    login('viewer')
    expect(page.locator('#p2-profile-form button')).to_be_disabled()
    expect(page.locator('#p2-hstdn-form button')).to_be_disabled()
    checks.append('Real HTTPS viewer login; profile/HSTDN write controls disabled')
    page.locator('#p2-logout').click()
    expect(page.locator('#p2-login-panel')).to_be_visible()
    login('editor')
    expect(page.locator('#p2-profile-form button')).to_be_enabled()
    page.locator('.preview-nav a').nth(2).click()
    assert page.url.endswith('#p2-learn')
    page.locator('#core-language').select_option('en')
    expect(page.locator('#p2-journey')).to_contain_text('Study records')
    assert page.locator('#p2-advanced article').count()==6
    page.set_viewport_size({'width':390,'height':844})
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
    checks.append('Editor mobile template navigation, course hydration and English journey')
    page.locator('#p2-logout').click()
    expect(page.locator('#p2-login-panel')).to_be_visible()
    assert not errors, errors
    checks.append('Logout works; no browser page errors; certificate exception scoped to test SPKI')
    (root/'docs').mkdir(exist_ok=True)
    page.screenshot(path=str(root/'docs/LOCAL_HTTPS_MOBILE.png'),full_page=False)
    browser.close()
report={'status':'PASS','scope':'New local HTTPS wrapper and template navigation only','url':'https://localhost:4190/p2','remotePhoneAccess':False,'certificate':'self-signed local development certificate; exact SPKI pinned for QA','checks':checks,'pageErrors':errors,'fullHistoricalSuitesRerun':False,'productionDeployment':False}
(root/'docs/LOCAL_HTTPS_BROWSER.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
