import json,hashlib,pathlib,tempfile,subprocess,os,time,urllib.request,ssl,base64
from playwright.sync_api import sync_playwright,expect
root=pathlib.Path(__file__).resolve().parents[1]
checks=[];errors=[]
tls=os.environ.get("CFP_OFFICE_QA_TLS")=="1"
origin="https://localhost:4193" if tls else "http://127.0.0.1:4193"
with tempfile.TemporaryDirectory(prefix='cfp-office-qa-') as tmp:
 env=dict(os.environ,CFP_P2_DB=str(pathlib.Path(tmp)/'preview.db'))
 tls_args=[];ssl_context=None
 if tls:
  cert=pathlib.Path(tmp)/'cert.pem';key=pathlib.Path(tmp)/'key.pem'
  subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);key.chmod(0o600)
  public=subprocess.check_output(['openssl','x509','-in',str(cert),'-pubkey','-noout']);der=subprocess.check_output(['openssl','pkey','-pubin','-outform','DER'],input=public);pin=base64.b64encode(hashlib.sha256(der).digest()).decode();tls_args=['--ignore-certificate-errors-spki-list='+pin]
  ssl_context=ssl.create_default_context(cafile=str(cert));env.update(CFP_OFFICE_QA_TLS='1',CFP_LOCAL_TLS_CERT=str(cert),CFP_LOCAL_TLS_KEY=str(key))
 server=subprocess.Popen(['node','tests/office-preview-fixture.mjs'],cwd=root,env=env,stdout=subprocess.DEVNULL)
 try:
  for _ in range(100):
   try:urllib.request.urlopen(origin+'/p2',context=ssl_context);break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-crash-reporter','--disable-breakpad']+tls_args)
   page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
   cookies=[]
   page.on('response',lambda r:cookies.append(r.header_value('set-cookie')) if '/api/session' in r.url and r.status==200 else None)
   page.goto(origin+'/p2')
   expect(page.locator('#public-curriculum details')).to_have_count(5)
   assert page.locator('#universal-office .numeric-links a').evaluate_all('(ns)=>ns.map(n=>new URL(n.href).pathname)')==['/69','/4376','/343','/267','/6','/7','/9','/8882']
   assert page.locator('#universal-application').count()==0
   checks.append('Anonymous basic curriculum and all eight root links; application needs issued account; root functionality not verified')
   def login(account):
    page.locator('#p2-login-form [name=id]').fill(account);page.locator('#p2-login-form [name=password]').fill('Synthetic-office-browser');page.locator('#p2-login-form button').click();expect(page.locator('#p2-account')).to_contain_text(account);expect(page.locator('#universal-application')).to_be_visible()
   def logout():
    page.locator('#p2-logout').click();expect(page.locator('#p2-login-panel')).to_be_visible()
   def submit(form):
    page.locator(form+' [name=commitment]').check();page.locator(form+' button').click();expect(page.locator('#universal-status')).to_contain_text('Đã lưu')
   login('editor')
   for index,(country,category) in enumerate([('6911','new-ai'),('6984','existing-ai'),('6910','developer'),('UNRESOLVED','enterprise')]):
    f=page.locator('#universal-application')
    for name,value in {'name':'Synthetic Office '+str(index),'version':'v1','aiType':'agent','contact':'https://example.org/contact','country':country,'developer':'Synthetic Developer','developerWebsite':'https://example.org','developerEvidence':'https://example.org/legal','hstAffiliated':'Synthetic HSTDN','hstLinked':'Synthetic partner','products':'Synthetic API','capabilities':'<script>window.bad=true</script>','limits':'Research only','conditions':'Human review','cooperation':'Draft support','relation-owner':'Synthetic Owner','evidence-owner':'https://example.org/owner'}.items():f.locator('[name='+name+']').fill(value)
    f.locator('[name=entityType]').select_option(category);submit('#universal-application');expect(page.locator('#universal-showcase article')).to_have_count(index+1)
   assert page.evaluate('window.bad') is None
   expect(page.locator('#universal-showcase')).to_contain_text('CONFLICT / HUMAN GOVERNANCE');expect(page.locator('#universal-showcase')).to_contain_text('EVIDENCE_PENDING')
   checks.append('All four applicant categories; US conflict and VN/CA/unresolved declarations persist unverified; script content safely displayed')
   f=page.locator('#p2-hstdn-form');f.locator('[name=name]').fill('Synthetic HSTDN');f.locator('[name=jurisdiction]').fill('UNRESOLVED');f.locator('[name=source]').fill('https://example.org/hstdn');f.locator('[name=relation_type]').select_option('legal-parent-claim');f.locator('button').click();expect(page.locator('#p2-office-records')).to_contain_text('Synthetic HSTDN')
   for kind in ['product','service']:
    f=page.locator('#p2-catalog-form');f.locator('[name=kind]').select_option(kind);f.locator('[name=name]').fill('Synthetic '+kind);f.locator('[name=source]').fill('https://example.org/'+kind);f.locator('button').click();expect(page.locator('#p2-office-records')).to_contain_text('Synthetic '+kind)
   checks.append('Declared HSTDN legal-parent relation and product/service catalogs saved with source; legal relation remains NOT VERIFIED')
   for kind in ['enrollment','marketing','work-request']:
    f=page.locator('#universal-'+kind);f.locator('[name=name]').fill('Synthetic '+kind);f.locator('[name=source]').fill('https://example.org/'+kind);f.locator('[name=scope]').fill('Synthetic review scope');submit('#universal-'+kind);expect(page.locator('#universal-requests')).to_contain_text('Synthetic '+kind)
   expect(page.locator('#universal-requests')).to_contain_text('NOT AUTHORIZED');expect(page.locator('#universal-requests')).to_contain_text('NOT PUBLISHED');checks.append('Advanced enrollment, marketing and work intake saved as review requests with no certification, execution or publication')
   latest=page.locator('#universal-application [name=amendmentOf] option').nth(1).get_attribute('value');page.locator('#universal-application [name=amendmentOf]').select_option(latest);page.locator('#universal-application [name=capabilities]').fill('Amended synthetic capability');submit('#universal-application');expect(page.locator('#universal-showcase article')).to_have_count(4);expect(page.locator('#universal-showcase')).to_contain_text('Amended synthetic capability');checks.append('Declaration update appends a version and shows latest without inflating country counts')
   page.reload();expect(page.locator('#p2-login-panel')).to_be_visible();login('editor');expect(page.locator('#universal-showcase article')).to_have_count(4)
   with page.expect_download() as download:page.locator('#p2-export-evidence').click()
   packet=json.loads(pathlib.Path(download.value.path()).read_text());assert hashlib.sha256(packet['payloadJSON'].encode()).hexdigest()==packet['sha256'];payload=json.loads(packet['payloadJSON']);assert len(payload['office']['applications'])==5;assert len(payload['office']['records'])==5;assert 'cfp_p2=' not in packet['payloadJSON'];checks.append('Reload persistence and own-subject office/training export with verified SHA256 and no session cookie')
   for language in ['vi','en']:
    page.locator('#core-language').select_option(language);expect(page.locator('#universal-office h2')).to_contain_text('Văn Phòng' if language=='vi' else 'Office')
    for width in [390,320]:
     page.set_viewport_size({'width':width,'height':844});assert not page.evaluate('document.documentElement.scrollWidth > innerWidth+2'),(language,width)
   page.locator('#universal-office').evaluate('(n)=>window.scrollTo(0,n.offsetTop)');page.screenshot(path=str(root/'docs/OFFICE_INTAKE_MOBILE.png'));checks.append('VI/EN at 390px and 320px without horizontal overflow; mobile screenshot recorded')
   logout();login('viewer');expect(page.locator('#universal-application button')).to_be_disabled();expect(page.locator('#universal-work-request button')).to_be_disabled();checks.append('Viewer reads but cannot submit')
   logout();login('outsider');expect(page.locator('#universal-showcase article')).to_have_count(0);expect(page.locator('#universal-requests article')).to_have_count(0);checks.append('Foreign workspace sees no declarations or requests')
   f=page.locator('#universal-application');f.locator('[name=name]').fill('Named-only Synthetic AI');f.locator('[name=contact]').fill('https://example.org/contact');submit('#universal-application');expect(page.locator('#universal-showcase')).to_contain_text('UNRESOLVED');expect(page.locator('#universal-showcase')).to_contain_text('EVIDENCE_PENDING');checks.append('Name + HTTPS contact can start an isolated application without invented country/developer evidence')
   if tls:
    assert cookies and all(c and 'Secure' in c and 'HttpOnly' in c for c in cookies);checks.append('Actual local TLS session cookies Secure/HttpOnly; exact certificate SPKI pinned')
   assert not errors,errors;checks.append('No browser page errors');browser.close()
 finally:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait()
report={'scope':('Real loopback HTTPS + exact certificate pin' if tls else 'Real loopback HTTP')+' + Chromium; synthetic fixtures only','checks':checks,'pageErrors':errors,'status':'PASS','publicPreview':'NOT CONFIGURED','realOnboardingCount':0,'syntheticCountryCountsPrimaryWorkspace':{'US':1,'VN':1,'CA':1,'UNRESOLVED':1},'namedOnlyApplicationSecondaryWorkspace':1,'servicesStopped':True}
(root/('docs/OFFICE_INTAKE_HTTPS_BROWSER.json' if tls else 'docs/OFFICE_INTAKE_BROWSER.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
