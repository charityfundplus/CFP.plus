import json,hashlib,pathlib,tempfile,subprocess,os,time,urllib.request
from playwright.sync_api import sync_playwright,expect
root=pathlib.Path(__file__).resolve().parents[1]
checks=[];errors=[]
with tempfile.TemporaryDirectory(prefix='cfp-preview-') as tmp:
 env=dict(os.environ,CFP_P2_DB=str(pathlib.Path(tmp)/'preview.db'))
 server=subprocess.Popen(['node','tests/training-continuation-fixture.mjs'],cwd=root,env=env,stdout=subprocess.DEVNULL)
 hub=subprocess.Popen(['python3','-m','http.server','4192','--bind','127.0.0.1'],cwd=root.parents[1],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   try:urllib.request.urlopen('http://127.0.0.1:4191/p2');break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-crash-reporter','--disable-breakpad'])
   page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto('http://127.0.0.1:4191/p2')
   def login(account):
    page.locator('#p2-login-form [name=id]').fill(account);page.locator('#p2-login-form [name=password]').fill('Synthetic-preview-fixture');page.locator('#p2-login-form button').click();expect(page.locator('#p2-account')).to_contain_text(account)
   def logout():
    page.locator('#p2-logout').click();expect(page.locator('#p2-login-panel')).to_be_visible()
   login('learner');expect(page.locator('#p2-journey')).to_contain_text('11/12')
   page.locator('#p2-exercise').select_option('office-exercise-12');page.locator('#p2-load-exercise').click();page.locator('#core-synthetic').check();page.locator('#core-create-task').click()
   task=page.locator('#core-tasks .profile-card').filter(has_text='Synthetic exercise 12')
   expect(task).to_contain_text('QUEUED');task.locator('button').first.click();expect(task).to_contain_text('AWAITING HUMAN REVIEW')
   # Pick the new task, avoiding a false positive from another exercise.
   page.locator('#p2-feedback-task').select_option(label='Synthetic exercise 12 • Báo Cáo • Evidence • KPI • AWAITING HUMAN REVIEW')
   page.locator('#p2-feedback-form [name=feedback]').fill('Browser final exercise evidence');page.locator('#p2-feedback-form button').click();expect(page.locator('#p2-learning-evidence')).to_contain_text('Browser final exercise evidence')
   expect(page.locator('#p2-journey')).to_contain_text('11/12');checks.append('Unreviewed exercise with feedback does not advance progress')
   logout();login('reviewer');task.locator('button').first.click();expect(task).to_contain_text('REVIEWED DRAFT');logout();login('learner')
   expect(page.locator('#p2-journey')).to_contain_text('12/12');expect(page.locator('#p2-journey')).to_contain_text('Đủ bằng chứng');checks.append('UI practice → feedback → separate review → basic draft evidence ready')
   with page.expect_download() as download:page.locator('#p2-export-evidence').click()
   packet=json.loads(pathlib.Path(download.value.path()).read_text());assert hashlib.sha256(packet['payloadJSON'].encode()).hexdigest()==packet['sha256']
   payload=json.loads(packet['payloadJSON']);assert len(payload['tasks'])==12 and payload['journey']['basicDraftReady'] and payload['journey']['certification'] is False
   assert all(t['owner']=='learner' for t in payload['tasks']);assert 'cfp_p2=' not in packet['payloadJSON'];checks.append('Downloaded current evidence: SHA-256 verified, 12 scoped tasks, no cookie or certification')
   page.locator('#core-language').select_option('en');expect(page.locator('#p2-journey')).to_contain_text('Study records: 5/5');assert page.locator('#p2-advanced article').count()==6
   page.set_viewport_size({'width':390,'height':844});assert not page.evaluate('document.documentElement.scrollWidth > innerWidth+2');checks.append('Journey and six advanced guides VI/EN; mobile 390px without overflow')
   logout();login('other');expect(page.locator('#p2-journey')).to_contain_text('0/12');expect(page.locator('#p2-journey')).to_contain_text('0/5');checks.append('Shared team learner cannot inherit another subject study or assessments')
   logout();login('outsider');expect(page.locator('#p2-journey')).to_contain_text('0/12');checks.append('Foreign workspace progress stays empty')
   assert not errors,errors;checks.append('No browser page errors');browser.close()
 finally:
  for process in [server,hub]:
   process.terminate()
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:process.kill();process.wait()
report={'scope':'Current training regression; synthetic local preview only; HUB source not tested','checks':checks,'pageErrors':errors,'status':'PASS','publicPreview':'NOT DEPLOYED','servicesStopped':True}
(root/'docs/OFFICE_TRAINING_BROWSER.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
