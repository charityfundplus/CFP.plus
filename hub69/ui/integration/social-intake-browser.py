"""One real Chapter0/profile workflow plus isolated Social spaces and a real worker."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from playwright.sync_api import sync_playwright, expect

REPO=Path(__file__).resolve().parents[3]
PILOT=REPO/'pilots/spacex'
sys.path.insert(0,str(PILOT))
from operations import DEMO_PASSWORD
out=Path(os.environ['CFP_SOCIAL_EVIDENCE_DIR']) if os.environ.get('CFP_SOCIAL_EVIDENCE_DIR') else Path(tempfile.mkdtemp(prefix='cfp-social-evidence-'))
out.mkdir(parents=True,exist_ok=True)
checks=[];errors=[];report={'status':'FAIL','scope':'Real local HTTP/SQLite/Chromium + bounded worker subprocess; no external SI ACK, public preview or physical phone'}
with tempfile.TemporaryDirectory(prefix='cfp-social-state-') as state:
    log=(out/'server.txt').open('w')
    server=subprocess.Popen([sys.executable,'operations_server.py','--state-dir',state,'--port','0','--provision-demo'],cwd=PILOT,stdout=subprocess.PIPE,stderr=log,text=True)
    try:
        origin='http://127.0.0.1:'+str(json.loads(server.stdout.readline())['port'])
        def tick(provision=False):
            command=[sys.executable,'software_worker.py','--state-dir',state,'--once']+(['--provision-worker'] if provision else [])
            result=subprocess.run(command,cwd=PILOT,capture_output=True,text=True,check=True)
            with (out/'worker.txt').open('a') as stream:stream.write(result.stdout)
        tick(True)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            def account(name):
                context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
                page=context.new_page();page.on('pageerror',lambda e:errors.append(e.stack or str(e)))
                page.goto(origin+'/app/#operations');frame=page.frame_locator('#operations-frame')
                frame.locator('#ops-login [name=id]').fill(name);frame.locator('#ops-login [name=password]').fill(DEMO_PASSWORD);frame.locator('#ops-login button').click();expect(frame.locator('#ops-account')).to_contain_text(name)
                return context,page
            def api(page,path,body=None):
                return page.evaluate('''async ([path,body])=>{const r=await fetch('/api/'+path,{method:body===null?'GET':'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},...(body===null?{}:{body:JSON.stringify(body)})});return {status:r.status,body:await r.json()}}''',[path,body])
            editor_context,editor=account('editor')
            editor.goto(origin+'/app/#intake');expect(editor.locator('#intake-status')).to_contain_text('editor')
            editor.locator('#intake-create [name=kind]').select_option('cmp-role');editor.locator('#intake-create [name=name]').fill('CMP1 · Chương 0 nhập thủ công');editor.locator('#intake-create [name=description]').fill('Hồ sơ thử nghiệm, không cấp Canonical hoặc quyền.');editor.locator('#intake-create button').click()
            expect(editor.locator('#intake-profiles')).to_contain_text('CMP1 · Chương 0')
            profile=api(editor,'manual/profiles')['body']['profiles'][0]
            assert profile['chapter']==0 and profile['role_label']=='CMP1'
            assert all(profile[k] is None for k in ['canonical_id','parent','did']) and profile['verified'] is False
            editor.locator('#intake-task [name=title]').fill('Nhiệm vụ từ hồ sơ Chương 0');editor.locator('#intake-task [name=content]').fill('Phản hồi và đính kèm Evidence thử nghiệm.');editor.locator('#intake-task [name=recipient]').fill('admin');editor.locator('#intake-task button').click()
            expect(editor.locator('#intake-message')).to_contain_text('Đã giao nhiệm vụ')
            task=api(editor,'forum/state')['body']['tasks'][0]
            assert json.loads(task['content'])['manual_profile_key']==profile['profile_key']
            admin_context,admin=account('admin');admin.goto(origin+'/app/#forum')
            expect(admin.locator('#forum-tasks')).to_contain_text('Nhiệm vụ từ hồ sơ')
            admin.locator('#forum-tasks button',has_text='Tiếp nhận nhiệm vụ').click();expect(admin.locator('#forum-tasks')).to_contain_text('ACCEPTED')
            admin.locator('#forum-reply [name=content]').fill('Đã phản hồi đúng hồ sơ Chương 0');admin.locator('#forum-reply button').click();expect(admin.locator('#forum-posts')).to_contain_text('Đã phản hồi đúng hồ sơ')
            evidence=b'Chapter0 manual profile workflow evidence\n'
            admin.locator('#forum-upload [name=file]').set_input_files({'name':'chapter0.txt','mimeType':'text/plain','buffer':evidence});admin.locator('#forum-upload button').click();expect(admin.locator('#forum-evidence')).to_contain_text(hashlib.sha256(evidence).hexdigest());admin.locator('#forum-evidence button').click();expect(admin.locator('#forum-message')).to_contain_text('Evidence PASS')
            admin.reload();expect(admin.locator('#forum-tasks')).to_contain_text('ACCEPTED');expect(admin.locator('#forum-evidence')).to_contain_text('chapter0.txt')
            editor.reload();expect(editor.locator('#intake-profiles')).to_contain_text('CMP1 · Chương 0')
            checks.append('Chapter0 manual CMP1 profile -> linked task -> independent assigned ACK/reply -> real Evidence SHA256 -> reload persistence; no Canonical/Parent/DID allocation')
            # Only after the Chapter0 chain passes, exercise later chapter mappings.
            for chapter in range(1,10):
                response=api(editor,'manual/profiles',{'kind':'topic','name':f'Chương {chapter} chủ đề thủ công','role_label':'','description':'Chưa có nội dung Canonical được xác minh','chapter':chapter,'idempotency_key':f'chapter-{chapter}'})
                assert response['status'] in [200,201],response
            assert sorted({p['chapter'] for p in api(editor,'manual/profiles')['body']['profiles']})==list(range(10))
            checks.append('After Chapter0, manual topic intake mappings1..9 preserve chapter/group structure; all remain unverified')
            editor.goto(origin+'/app/#social');expect(editor.locator('#social-status')).to_contain_text('Cộng Đồng')
            editor.locator('#social-post [name=content]').fill('Bài đăng thật <img src=x onerror="window.socialXSS=1">');editor.locator('#social-post button').click();expect(editor.locator('#social-feed')).to_contain_text('Bài đăng thật')
            assert editor.locator('#social-feed img').count()==0 and editor.evaluate('window.socialXSS') is None
            admin.goto(origin+'/app/#social');expect(admin.locator('#social-feed')).to_contain_text('Bài đăng thật');admin.locator('.social-comment-form textarea').fill('Bình luận từ phiên độc lập');admin.locator('.social-comment-form button').click();expect(admin.locator('#social-feed')).to_contain_text('Bình luận từ phiên độc lập')
            editor.reload();expect(editor.locator('#social-feed')).to_contain_text('Bài đăng thật');expect(editor.locator('#social-feed')).to_contain_text('Bình luận từ phiên độc lập')
            checks.append('Login -> plaintext post -> independent comment -> reload retains exact server data; no HTML execution')
            spaces=api(admin,'social/spaces')['body']['spaces'];assert len(spaces)==4
            private_keys=[]
            for space in spaces:
                response=api(admin,'social/posts',{'space':space['key'],'content':'Separate space '+space['key'],'idempotency_key':'space-'+space['key']});assert response['status'] in [200,201],response
                row=response['body'];private_keys.append(row['key'])
                own=api(admin,'social/state',{'space':space['key']});assert own['status']==200 and all(p['space']==space['key'] for p in own['body']['posts'])
            denied=api(editor,'social/state',{'space':'chapter-association'});missing=api(editor,'social/state',{'space':'no-such-space'});assert denied['status']==missing['status']==404
            assert api(editor,'social/state',{'space':'super-pair-forum'})['status']==404
            viewer_context,viewer=account('viewer');viewer.goto(origin+'/app/#social');expect(viewer.locator('#social-feed')).to_contain_text('Bài đăng thật');expect(viewer.locator('#social-post button')).to_be_disabled();assert api(viewer,'social/posts',{'space':'community','content':'denied','idempotency_key':'viewer-denied'})['status']==403
            foreign_context,foreign=account('foreign');foreign.goto(origin+'/app/#social');expect(foreign.locator('#social-status')).to_contain_text('Cộng Đồng');assert foreign.locator('#social-feed article').count()==0
            checks.append('Four spaces have separate grants/content; unauthorized/missing404 match, viewer403, foreign workspace has no posts')
            editor.locator('#social-worker-task [name=text]').fill('CFP+ bounded worker');editor.locator('#social-worker-task button').click();expect(editor.locator('#social-message')).to_contain_text('Đã giao nhiệm vụ kỹ thuật')
            tick();editor.locator('#social-worker-refresh').click();expect(editor.locator('#social-worker-data')).to_contain_text('COMPLETED');expect(editor.locator('#social-worker-data')).to_contain_text(hashlib.sha256(b'CFP+ bounded worker').hexdigest())
            good=api(editor,'worker/state')['body'];tick();after=api(editor,'worker/state')['body'];assert len(good['attempts'])==len(after['attempts'])
            api(editor,'forum/tasks',{'title':'Reject unsupported worker operation','content':json.dumps({'operation':'not-allowed','text':'never executed'}),'recipient':'software-worker','idempotency_key':'unsupported-worker'})
            tick();editor.locator('#social-worker-refresh').click();expect(editor.locator('#social-worker-data')).to_contain_text('FAILED')
            worker=api(editor,'worker/state')['body'];assert worker['fresh'] and worker['alerts'];assert all(p['status']=='NOT VERIFIED' for p in api(editor,'social/state',{'space':'community'})['body']['connectors'])
            checks.append('Real worker subprocess receives/ACKs/executes boundedSHA256, logs and heartbeats; duplicate ticks do not rerun, invalid operation creates persisted failure alert')
            for width in [320,390,768,1440]:
                editor.set_viewport_size({'width':width,'height':844});assert not editor.evaluate('document.documentElement.scrollWidth>innerWidth+2'),width
            editor.set_viewport_size({'width':390,'height':844});editor.locator('#social-status').scroll_into_view_if_needed();editor.screenshot(path=str(out/'social-mobile.png'))
            editor.goto(origin+'/app/#intake');expect(editor.locator('#intake-profiles')).to_contain_text('CMP1 · Chương 0');editor.screenshot(path=str(out/'chapter0-mobile.png'))
            assert not errors,errors
            report.update(status='PASS',checks=checks,page_errors=errors,profile_key=profile['profile_key'],task_key=task['key'],evidence_sha256=hashlib.sha256(evidence).hexdigest(),worker_alert_count=len(worker['alerts']),physical_device='BLOCKED',external_social_connectors='NOT VERIFIED',public_preview='BLOCKED_NO_APPROVED_HOST')
            browser.close()
    except Exception as exc:
        report.update(error=str(exc),checks=checks,page_errors=errors);raise
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill();server.wait()
        server.stdout.close();log.close();(out/'social-intake-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
