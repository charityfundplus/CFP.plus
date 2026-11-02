"""Independent Chromium mobile emulation; no physical iPhone claim."""
import json, os, pathlib, subprocess, tempfile, time, urllib.request, hashlib
from playwright.sync_api import sync_playwright, expect
root=pathlib.Path(__file__).resolve().parents[1]
out=pathlib.Path(os.environ['CFP_FORUM_QA_EVIDENCE_DIR']) if os.environ.get('CFP_FORUM_QA_EVIDENCE_DIR') else pathlib.Path(tempfile.mkdtemp(prefix='cfp-mobile-evidence-'))
out.mkdir(parents=True,exist_ok=True)
origin='http://127.0.0.1:4193'
checks=[]; errors=[]; result={'scope':'Local synthetic sandbox; Chromium mobile emulation, not a physical phone or Canva deployment','status':'FAIL'}
with tempfile.TemporaryDirectory(prefix='cfp-independent-browser-') as tmp:
 log=open(out/'browser-server.log','w')
 server=subprocess.Popen(['node','tests/office-preview-fixture.mjs'],cwd=root,env=dict(os.environ,CFP_P2_DB=str(pathlib.Path(tmp)/'state.db')),stdout=log,stderr=log)
 try:
  for _ in range(100):
   try:
    urllib.request.urlopen(origin+'/p2',timeout=1).close();break
   except Exception:
    if server.poll() is not None: raise RuntimeError('Local server failed')
    time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   contexts=[]
   def account(name):
    c=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);contexts.append(c)
    page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(origin+'/p2')
    page.locator('#p2-login-form [name=id]').fill(name);page.locator('#p2-login-form [name=password]').fill('Synthetic-office-browser');page.locator('#p2-login-form button').click();expect(page.locator('#p2-account')).to_contain_text(name)
    expect(page.locator('#core-pair-select')).to_have_value('hub69-content-demo')
    expect(page.locator('#core-kind')).to_have_value('website-draft')
    return c,page
   c,page=account('editor')
   page.locator('#core-language').select_option('en')
   title='QA <img src=x onerror="window.qaXSS=1">'
   page.locator('#core-task-form [name=title]').fill(title)
   page.locator('#core-task-form [name=text]').fill('Synthetic independent mobile test')
   page.locator('#core-task-form [type=checkbox]').check()
   page.locator('#core-create-task').click()
   expect(page.locator('#core-tasks')).to_contain_text(title)
   assert page.evaluate('window.qaXSS') is None
   checks.append('Create task through UI; HTML-like title rendered as text without execution')
   page.locator('#core-tasks button',has_text='Run supervised').click()
   expect(page.locator('#core-tasks')).to_contain_text('AWAITING HUMAN REVIEW')
   page.locator('#core-tasks').screenshot(path=str(out/'mobile-task.png'))
   state=page.evaluate("fetch('/api/core/state').then(r=>r.json())")
   task=next(t for t in state['tasks'] if t['title']==title)
   checks.append('Synthetic supervised execution produces task-bound output and audit')
   page.reload();page.locator('#p2-login-form [name=id]').fill('editor');page.locator('#p2-login-form [name=password]').fill('Synthetic-office-browser');page.locator('#p2-login-form button').click();expect(page.locator('#core-tasks')).to_contain_text(title)
   checks.append('Task survives page reload and reauthentication')
   reviewer,review_page=account('reviewer')
   review_page.locator('#core-language').select_option('en')
   expect(review_page.locator('#core-tasks')).to_contain_text(title)
   review_page.locator('#core-tasks button',has_text='Acknowledge draft').click()
   expect(review_page.locator('#core-tasks')).to_contain_text('REVIEWED DRAFT')
   checks.append('Separate browser context/reviewer can independently read and review draft')
   viewer,viewer_page=account('viewer');expect(viewer_page.locator('#core-create-task')).to_be_disabled()
   checks.append('Viewer task creation disabled')
   outsider,outsider_page=account('outsider');assert outsider_page.locator('#core-tasks article').count()==0
   checks.append('Foreign workspace has no task cards')
   layout=[]
   for width in [390,320]:
    review_page.set_viewport_size({'width':width,'height':844})
    overflow=review_page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
    layout.append({'width':width,'horizontalOverflow':overflow})
   assert not errors,errors
   result.update(status='PASS' if not any(x['horizontalOverflow'] for x in layout) else 'FAIL',checks=checks,layout=layout,pageErrors=errors,taskKey=task['key'],outputSha256=task['executionReceipt']['outputSha256'],recipientACK='UNAVAILABLE: draft review is not recipient ACK',evidenceUpload='UNAVAILABLE: generated synthetic output is not file upload')
   browser.close()
 except Exception as e:
  result.update(error=str(e),checks=checks,pageErrors=errors)
  raise
 finally:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait()
  log.close();(out/'mobile-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
if result['status']!='PASS':raise SystemExit(1)
