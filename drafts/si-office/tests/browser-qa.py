# Run within Firecrawl Python context (injected page), or locally with Python Playwright.
import os, json, hashlib, io, zipfile, urllib.request, pathlib, subprocess, time
import asyncio
class QAExpect:
 def __init__(self,locator):self.locator=locator
 async def poll(self,getter,predicate,label):
  last=None
  for _ in range(60):
   last=await getter()
   if predicate(last):return
   await asyncio.sleep(0.1)
  raise AssertionError(label+': '+str(last))
 async def to_have_attribute(self,name,value):await self.poll(lambda:self.locator.get_attribute(name),lambda v:v==value,'attribute '+name)
 async def to_have_text(self,value):await self.poll(lambda:self.locator.text_content(),lambda v:(v or '').strip()==value,'exact text')
 async def to_contain_text(self,value):await self.poll(lambda:self.locator.text_content(),lambda v:value in (v or ''),'text contains '+value)
 async def to_be_enabled(self):await self.poll(lambda:self.locator.is_enabled(),lambda v:v is True,'enabled')
 async def to_be_disabled(self):await self.poll(lambda:self.locator.is_disabled(),lambda v:v is True,'disabled')
def expect(locator):return QAExpect(locator)

async def run_browser_qa(page,commit='50d17cc1be8408e4e0fd9981a4ff0e15129e6efa',manifest_sha='7784dd502bc9031f86db9168beb3024f6d690ef0f4facc07c456bc6b9e65facb',expected_tests=40):
 report={'sourceCommit':commit,'mode':'REMOTE EPHEMERAL LOOPBACK / SYNTHETIC ONLY','checks':[],'status':'FAIL'}
 process=None
 errors=[]
 page.on('pageerror',lambda error:errors.append(str(error)))
 def passed(name):
  report['checks'].append(name)
 try:
  req=urllib.request.Request('https://api.github.com/repos/charityfundplus/CFP.plus/zipball/'+commit,headers={'User-Agent':'CFP-Synthetic-Browser-QA'})
  data=urllib.request.urlopen(req,timeout=20).read(10*1024*1024)
  root=pathlib.Path('/tmp/cfp-browser-qa');root.mkdir(exist_ok=True)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   for name in z.namelist():
    marker='/drafts/si-office/'
    if marker not in name or name.endswith('/'):continue
    relative=name.split(marker,1)[1];target=(root/relative).resolve()
    assert target.is_relative_to(root.resolve())
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
  raw=(root/'docs/EVIDENCE_MANIFEST.json').read_bytes();manifest=json.loads(raw)
  assert hashlib.sha256(raw).hexdigest()==manifest_sha
  for f in manifest['files']:
   b=(root/f['path']).read_bytes()
   assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],f['path']
  report['verifiedFiles']=len(manifest['files'])
  test=subprocess.run(['node','scripts/run-tests.mjs'],cwd=root,capture_output=True,text=True,timeout=20)
  assert test.returncode==0,test.stdout[-2000:]+test.stderr[-1000:]
  assert ('tests '+str(expected_tests)) in test.stdout and ('pass '+str(expected_tests)) in test.stdout,test.stdout[-500:]
  report['handlerTests']=str(expected_tests)+'/'+str(expected_tests);report['nodeVersion']=subprocess.check_output(['node','--version'],text=True).strip()
  log=open('/tmp/cfp-browser-qa-server.log','w')
  process=subprocess.Popen(['node','server.mjs'],cwd=root,env={**os.environ,'PORT':'4188'},stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
  for i in range(30):
   try:urllib.request.urlopen('http://127.0.0.1:4188/',timeout=1);break
   except Exception:time.sleep(0.1)
  await page.set_viewport_size({'width':1440,'height':1000})
  await page.goto('http://127.0.0.1:4188/',wait_until='networkidle',timeout=15000)
  await page.wait_for_selector('nav button',timeout=10000)
  assert await page.locator('nav button').count()==12
  passed('office: 12 modules loaded from actual local Node server')
  await page.locator('#language').select_option('en')
  await expect(page.locator('html')).to_have_attribute('lang','en')
  assert 'One office' in await page.locator('h1').inner_text()
  assert 'Inputs' in await page.locator('#module-contract').inner_text()
  passed('office: VI to EN and module contract')
  await page.locator('#register-open').click()
  await page.locator('#registration-form [name=name]').fill('Synthetic Office QA')
  await page.locator('#registration-form [name=source]').fill('https://example.org/source')
  await page.locator('#registration-form [name=identityEvidence]').fill('https://example.org/identity')
  await page.locator('#registration-form [name=synthetic]').check()
  await page.locator('#registration-form button').last.click()
  await expect(page.locator('#registration-count')).to_have_text('1')
  passed('office: SI/AI registration and identity evidence intake')
  await page.locator('nav button').nth(0).click()
  await page.locator('#module-extra button').first.click()
  await page.locator('#proposal-form [name=type]').select_option('country')
  await page.locator('#proposal-form [name=name]').fill('Synthetic Country QA')
  await page.locator('#proposal-form [name=source]').fill('https://example.org/country')
  await page.locator('#proposal-form [name=identityEvidence]').fill('https://example.org/country-identity')
  await page.locator('#proposal-form [name=synthetic]').check()
  await page.locator('#proposal-form button').last.click()
  await expect(page.locator('#module-extra')).to_contain_text('Synthetic Country QA')
  await page.locator('#module-extra button').first.click()
  await page.locator('#proposal-form [name=type]').select_option('developer')
  await page.locator('#proposal-form [name=name]').fill('Synthetic Developer QA')
  await page.locator('#proposal-country').select_option(label='Synthetic Country QA')
  await page.locator('#proposal-form [name=source]').fill('https://example.org/developer')
  await page.locator('#proposal-form [name=identityEvidence]').fill('https://example.org/developer-identity')
  await page.locator('#proposal-form [name=synthetic]').check()
  await page.locator('#proposal-form button').last.click()
  await expect(page.locator('#module-extra')).to_contain_text('Synthetic Developer QA')
  passed('office: Country and Developer proposals with local references')
  await page.locator('nav button').nth(7).click()
  await page.locator('#module-extra button').first.click()
  await page.locator('#hstdn-form [name=name]').fill('Synthetic HSTDN QA')
  await page.locator('#hstdn-form [name=jurisdiction]').fill('Synthetic jurisdiction')
  await page.locator('#hstdn-members').select_option(label='Synthetic Office QA')
  await page.locator('#hstdn-form [name=relation_type]').select_option('legal-parent-claim')
  await page.locator('#hstdn-form [name=source]').fill('https://example.org/legal')
  await page.locator('#hstdn-form [name=synthetic]').check()
  await page.locator('#hstdn-form button').last.click()
  await expect(page.locator('#module-extra')).to_contain_text('Synthetic HSTDN QA')
  assert 'NOT VERIFIED' in await page.locator('#module-extra').inner_text()
  passed('office: HSTDN legal claim remains NOT VERIFIED')
  for index,title in [(2,'Synthetic Product QA'),(3,'Synthetic Service QA')]:
   await page.locator('nav button').nth(index).click()
   await page.locator('#add-open').click()
   await page.locator('#record-form [name=title]').fill(title)
   await page.locator('#record-form [name=evidence]').fill('https://example.org/evidence')
   if index==2:await page.locator('#record-form [name=maturity]').select_option('research')
   else:await page.locator('#record-form [name=scope]').fill('Synthetic service scope')
   await page.locator('#record-form [name=officeRef]').select_option(label='Synthetic Office QA')
   await page.locator('#record-form [name=hstdnRef]').select_option(label='Synthetic HSTDN QA')
   await page.locator('#record-form [name=synthetic]').check()
   await page.locator('#record-form button').last.click()
   await expect(page.locator('#records')).to_contain_text(title)
  passed('office: product/service drafts linked to office and HSTDN')
  await page.locator('nav button').nth(8).click()
  await page.locator('#add-open').click()
  await page.locator('#record-form [name=title]').fill('<script>synthetic XSS probe</script>')
  await page.locator('#record-form [name=evidence]').fill('https://example.org/evidence')
  await page.locator('#record-form [name=synthetic]').check()
  await page.locator('#record-form button').last.click()
  row=page.locator('.record').filter(has_text='<script>synthetic XSS probe</script>')
  await row.wait_for()
  assert await row.locator('script').count()==0
  await row.locator('button').click()
  await expect(row).to_contain_text('UNDER REVIEW')
  await page.locator('#role').select_option('reviewer')
  await expect(row.locator('button')).to_be_enabled()
  await row.locator('button').click()
  await expect(row).to_contain_text('DEMO REVIEWED')
  passed('office: escaped XSS text and draft/review workflow')
  await page.locator('nav button').nth(9).click()
  await page.locator('#module-extra button').first.click()
  await expect(page.locator('.mock-receipt')).to_contain_text('externalRequests')
  receipt=await page.locator('.mock-receipt').inner_text()
  assert '"connected": false' in receipt and '"externalRequests": 0' in receipt
  passed('office: read-synthetic adapter receipt, no live integration')
  await page.locator('nav button').nth(6).click()
  await page.locator('#module-extra button').first.click()
  await expect(page.locator('#toast')).to_contain_text('NO-GO')
  await page.locator('#role').select_option('viewer')
  await expect(page.locator('#add-open')).to_be_disabled()
  assert await page.locator('#register-open').is_disabled()
  passed('office: payment denial and viewer write restriction')
  await page.locator('#language').select_option('vi')
  await expect(page.locator('html')).to_have_attribute('lang','vi')
  assert 'Một văn phòng' in await page.locator('h1').inner_text()
  await page.set_viewport_size({'width':390,'height':844})
  assert await page.evaluate('() => document.documentElement.scrollWidth <= innerWidth')
  passed('office: EN to VI; 390px no page overflow')
  await page.set_viewport_size({'width':1440,'height':1000})
  await page.goto('http://127.0.0.1:4188/core',wait_until='networkidle')
  await expect(page.locator('#core-pair-count')).to_have_text('1')
  await page.locator('#core-language').select_option('en')
  assert 'One Standard Core' in await page.locator('#core-heading').inner_text()
  await page.locator('#core-task-form [name=title]').fill('Core synthetic draft QA')
  await page.locator('#core-task-form [name=text]').fill('<script>synthetic text only</script>')
  await page.locator('#core-synthetic').check()
  await page.locator('#core-create-task').click()
  core_row=page.locator('#core-tasks .profile-card').filter(has_text='Core synthetic draft QA')
  await core_row.wait_for()
  await core_row.get_by_role('button',name='Run supervised',exact=True).click()
  await expect(core_row).to_contain_text('AWAITING HUMAN REVIEW')
  assert await core_row.locator('script').count()==0
  assert 'before-stage' in await core_row.locator('pre').last.text_content()
  await page.locator('#core-role').select_option('reviewer')
  await expect(page.locator('#core-upgrade')).to_be_enabled()
  await core_row.get_by_role('button',name='Acknowledge draft',exact=True).click()
  await expect(core_row).to_contain_text('REVIEWED DRAFT')
  passed('core: supervised task, escaped text and separate demo review')
  await page.locator('#core-upgrade').click()
  await expect(page.locator('#core-version')).to_have_text('0.1.1')
  await page.locator('#core-rollback').click()
  await expect(page.locator('#core-version')).to_have_text('0.1.0')
  passed('core: synchronized metadata upgrade and rollback')
  await page.locator('#core-template').select_option('training-demo')
  await page.locator('#core-instantiate').click()
  await expect(page.locator('#core-pair-count')).to_have_text('2')
  await page.locator('#core-pair-select').select_option('training-demo')
  await page.locator('#core-task-form [name=title]').fill('Overreach drill QA')
  await page.locator('#core-task-form [name=scenario]').select_option('overreach')
  await page.locator('#core-create-task').click()
  drill=page.locator('#core-tasks .profile-card').filter(has_text='Overreach drill QA')
  await drill.get_by_role('button',name='Run supervised',exact=True).click()
  await expect(drill).to_contain_text('BLOCKED')
  control=page.locator('#core-controls .record').filter(has_text='training-demo')
  await control.get_by_role('button',name='Recover (reviewer)',exact=True).click()
  await expect(page.locator('#core-alerts')).to_contain_text('ACKNOWLEDGED')
  passed('core: config replication, overreach safe stop and reviewer recovery')
  await page.locator('#core-template').select_option('us-hstdn-demo')
  await page.locator('#core-instantiate').click()
  await expect(page.locator('#core-pair-count')).to_have_text('3')
  await page.locator('#core-pair-select').select_option('us-hstdn-demo')
  await page.locator('#core-task-form [name=title]').fill('US HSTDN QA')
  await page.locator('#core-task-form [name=scenario]').select_option('normal')
  await page.locator('#core-create-task').click()
  hst_row=page.locator('#core-tasks .profile-card').filter(has_text='US HSTDN QA')
  await hst_row.get_by_role('button',name='Run supervised',exact=True).click()
  await expect(hst_row).to_contain_text('SYNTHETIC HSTDN PROFILE')
  assert 'NOT VERIFIED' in await hst_row.inner_text()
  passed('core: synthetic US HSTDN profile, no verified legal relation')
  await page.locator('#core-role').select_option('viewer')
  await expect(page.locator('#core-create-task')).to_be_disabled()
  assert await page.locator('#core-instantiate').is_disabled()
  await page.locator('#core-language').select_option('vi')
  await page.set_viewport_size({'width':390,'height':844})
  assert await page.evaluate('() => document.documentElement.scrollWidth <= innerWidth')
  assert not errors,errors
  report['pageErrors']=errors
  try:report['browserVersion']=await page.evaluate('() => navigator.userAgent')
  except Exception:report['browserVersion']='Metadata unavailable'
  req=urllib.request.Request('http://127.0.0.1:4188/api/session',data=json.dumps({'role':'viewer'}).encode(),headers={'Content-Type':'application/json','Origin':'http://127.0.0.1:4188'})
  qa_token=json.loads(urllib.request.urlopen(req).read())['token']
  req=urllib.request.Request('http://127.0.0.1:4188/api/core/state',headers={'Authorization':'Bearer '+qa_token})
  audit_state=json.loads(urllib.request.urlopen(req).read())
  previous='GENESIS'
  for event in audit_state['audit']:
   digest=event.pop('sha256')
   assert event['previousHash']==previous
   assert hashlib.sha256(json.dumps(event,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==digest
   previous=digest
  report['auditCheckpoint']={'events':len(audit_state['audit']),'sha256':previous,'independentPythonRecalculation':True}
  passed('core: audit chain independently recalculated in Python')
  passed('core: viewer restrictions, VI/EN, 390px and no page errors')
  report['status']='PASS'
 except Exception as exc:
  report['error']=str(exc)
 finally:
  if process is not None:
   process.terminate()
   try:process.wait(timeout=3)
   except Exception:process.kill()
  report['serverStopped']=process is None or process.poll() is not None
  report['pageErrors']=errors
  print('QA_BROWSER_REPORT',json.dumps(report,ensure_ascii=False))
 assert report['status']=='PASS',report.get('error','Browser QA incomplete')
 
 return report
 
async def local_main():
 from playwright.async_api import async_playwright
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  try:
   page=await browser.new_page()
   await run_browser_qa(page)
  finally:
   await browser.close()
if __name__=='__main__':
 asyncio.run(local_main())

