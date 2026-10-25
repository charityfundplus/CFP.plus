import hashlib,json,os,pathlib,subprocess,tempfile,time
from playwright.sync_api import sync_playwright,expect
root=pathlib.Path(__file__).resolve().parents[1];errors=[];checks=[]
with tempfile.TemporaryDirectory(prefix='cfp-assessment-export-') as temp:
 d=pathlib.Path(temp);env=dict(os.environ,CFP_NEW_SCOPE_LOCAL_QA='true',CFP_ASSESSMENT_QA_DIR=temp)
 server=subprocess.Popen(['node','tests/assessment-export-fixture.mjs'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(150):
   if (d/'ready.json').exists():break
   if server.poll() is not None:raise RuntimeError('Fixture stopped before ready')
   time.sleep(.05)
  else:raise RuntimeError('Fixture not ready')
  url=json.loads((d/'ready.json').read_text())['url'];accounts=json.loads((d/'accounts.json').read_text())
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-background-networking','--disable-crash-reporter','--disable-breakpad'])
   page=browser.new_page(viewport={'width':390,'height':844});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url)
   def login(id):
    a=next(a for a in accounts if a['id']==id);page.locator('#p2-login-form [name=id]').fill(id);page.locator('#p2-login-form [name=password]').fill(a['password']);page.locator('#p2-login-form button').click();expect(page.locator('#p2-account')).to_contain_text(id)
   def download_payload():
    with page.expect_download() as wait:page.locator('#p2-export-evidence').click()
    item=wait.value;path=d/('export-'+str(len(checks))+'.json');item.save_as(path);outer=json.loads(path.read_text());assert hashlib.sha256(outer['payloadJSON'].encode()).hexdigest()==outer['sha256'];return json.loads(outer['payloadJSON'])
   login('learner');payload=download_payload();assert len(payload['assessments'])==1;row=payload['assessments'][0];assert row['subject']=='learner' and row['competencyAssessment']=='NOT ASSESSED' and not row['certification'];assert row['taskKey'] in [t['key'] for t in payload['tasks']];assert row['artifactSetDigest'];checks.append('VI/mobile390 actual download retains own task-bound dossier and verifies payload SHA256')
   page.locator('#p2-logout').click();expect(page.locator('#p2-login-panel')).to_be_visible();login('viewer');page.locator('#core-language').select_option('en');payload=download_payload();assert payload['assessments']==[];assert not errors;checks.append('EN/mobile390 viewer export excludes other subjects; new module loads without page errors')
   browser.close()
 finally:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait()
report={'scope':'NEW assessment export module only; HTTP loopback fixture, not remote HTTPS/iPhone QA','checks':checks,'passed':len(checks),'pageErrors':errors,'unaffectedBrowserSuitesRerun':False,'fixtureStateRemoved':True,'realCompetencyAssessed':False}
out=root/'docs/continuation-20261014';out.mkdir(exist_ok=True);(out/'ASSESSMENT_EXPORT_BROWSER.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
