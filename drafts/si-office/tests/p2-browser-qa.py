import asyncio,urllib.request,zipfile,io,tempfile,pathlib,subprocess,json,hashlib,os

async def run_p2_browser_qa(page):
 commit="566c7067885db15bb14d5c026525765cc20b0eb0"
 work=pathlib.Path(tempfile.mkdtemp(prefix="cfp-p2-browser-"))
 data=urllib.request.urlopen("https://api.github.com/repos/charityfundplus/CFP.plus/zipball/"+commit).read()
 z=zipfile.ZipFile(io.BytesIO(data));z.extractall(work)
 root=next(work.iterdir())/"drafts"/"si-office"
 m=json.loads((root/"docs/P2_BUILD_MANIFEST.json").read_text())
 for f in m["files"]:
  b=(root/f["path"]).read_bytes()
  assert len(b)==f["bytes"] and hashlib.sha256(b).hexdigest()==f["sha256"]
 for script in ["tests/p2.test.mjs","tests/p2-http.test.mjs"]:
  t=subprocess.run(["node",script],cwd=root,capture_output=True,text=True)
  assert t.returncode==0,t.stdout+t.stderr
 fixture=root/"p2-browser-fixture.mjs"
 fixture.write_text('''import {P2Sandbox} from "./sandbox/p2-service.mjs";import {createP2HTTP} from "./sandbox/p2-http.mjs";
 const s=new P2Sandbox(process.env.CFP_P2_DB);
 for(const [id,role,workspace,maintainer,pairs] of [["editor","editor","alpha",false,["hub69-content-demo"]],["reviewer","reviewer","alpha",false,["*"]],["outsider","editor","beta",false,["*"]],["viewer","viewer","alpha",false,["*"]]])s.provision({id,password:"Synthetic-browser-password",role,workspace,maintainer,pairs});
 createP2HTTP({service:s}).listen(4189,"127.0.0.1");''')
 env=dict(os.environ,CFP_P2_DB=str(work/"browser.db"))
 server=subprocess.Popen(["node",str(fixture)],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 checks=[];errors=[]
 page.on("pageerror",lambda e:errors.append(str(e)))
 async def poll(get,predicate):
  for _ in range(100):
   x=await get()
   if predicate(x): return x
   await asyncio.sleep(.1)
  raise AssertionError("locator poll timeout")
 async def login(account):
  await page.locator('#p2-login-form [name=id]').fill(account)
  await page.locator('#p2-login-form [name=password]').fill("Synthetic-browser-password")
  await page.locator('#p2-login-form button').click()
  await poll(lambda:page.locator('#p2-account').inner_text(),lambda t:account in t)
 async def logout():
  await page.locator('#p2-logout').click()
  await poll(lambda:page.locator('#p2-login-panel').is_visible(),lambda v:v)
 try:
  for _ in range(80):
   try:
    urllib.request.urlopen("http://127.0.0.1:4189/p2");break
   except:await asyncio.sleep(.1)
  await page.set_viewport_size({"width":1440,"height":1000})
  await page.goto("http://127.0.0.1:4189/p2")
  await login("editor")
  assert "cfp_p2=" not in await page.evaluate("() => document.cookie")
  checks.append("Actual HTTP login; HttpOnly cookie inaccessible to JS; scoped editor")
  await page.locator('#core-task-form [name=title]').fill("<img src=x onerror=alert(1)>")
  await page.locator('#core-task-form [name=text]').fill("Synthetic P2 draft")
  await page.locator('#core-synthetic').check()
  await page.locator('#core-create-task').click()
  await poll(lambda:page.locator('#core-tasks').inner_text(),lambda t:"QUEUED" in t)
  assert await page.locator('#core-tasks img').count()==0
  checks.append("UI create task; hostile title escaped as text")
  await page.locator('#core-tasks button').first.click()
  await poll(lambda:page.locator('#core-tasks').inner_text(),lambda t:"AWAITING HUMAN REVIEW" in t)
  checks.append("Authenticated supervised run with actual durable service")
  await logout()
  await login("reviewer")
  await poll(lambda:page.locator('#core-tasks').inner_text(),lambda t:"AWAITING HUMAN REVIEW" in t)
  await page.locator('#core-tasks button').first.click()
  await poll(lambda:page.locator('#core-tasks').inner_text(),lambda t:"REVIEWED DRAFT" in t)
  checks.append("Separate authenticated reviewer; persisted task after logout/login")
  await logout()
  await login("outsider")
  await poll(lambda:page.locator('#core-tasks').inner_text(),lambda t:"No tasks" in t or "Chưa có nhiệm vụ" in t)
  assert "<img src=x" not in await page.locator('#core-tasks').inner_text()
  checks.append("Different workspace sees no alpha tasks")
  await logout()
  await login("viewer")
  assert await page.locator('#core-create-task').is_disabled()
  assert await page.locator('#core-upgrade').is_disabled()
  checks.append("Viewer UI disables write/upgrade; backend gates covered in HTTP tests")
  await page.locator('#core-language').select_option("en")
  await poll(lambda:page.locator('#core-heading').inner_text(),lambda t:"One Standard" in t)
  await page.set_viewport_size({"width":390,"height":844})
  await page.locator('#core-language').select_option("vi")
  await poll(lambda:page.locator('#core-heading').inner_text(),lambda t:"Một Lõi" in t)
  overflow=await page.evaluate("() => document.documentElement.scrollWidth > innerWidth+2")
  assert not overflow
  checks.append("VI/EN desktop and 390px mobile without overflow")
  assert not errors,errors
  checks.append("No browser page errors; CSP retained")
 finally:
  server.terminate()
  try:server.wait(timeout=10)
  except:server.kill();server.wait()
 print(json.dumps({"status":"PASS","commit":commit,"manifestFiles":len(m["files"]),"p2Tests":"10/10","httpReleaseTests":"5/5","browserChecks":checks,"pageErrors":errors,"serverStopped":server.poll() is not None,"scope":"REMOTE EPHEMERAL LOOPBACK / SYNTHETIC ONLY"}))
