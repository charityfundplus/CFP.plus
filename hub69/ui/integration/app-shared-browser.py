"""PWA + Website share one real backend/database. Chromium emulation only."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from playwright.sync_api import sync_playwright, expect

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO/'pilots/spacex'))
from operations import DEMO_PASSWORD

out = Path(os.environ['CFP_APP_EVIDENCE_DIR']) if os.environ.get('CFP_APP_EVIDENCE_DIR') else Path(tempfile.mkdtemp(prefix='cfp-app-evidence-'))
out.mkdir(parents=True, exist_ok=True)
report = {'status': 'FAIL', 'scope': 'Real local HTTP/API/SQLite; existing PWA + Website; Chromium touch emulation, not a physical phone'}
checks, errors = [], []
with tempfile.TemporaryDirectory(prefix='cfp-shared-app-state-') as state:
    with (out/'server.txt').open('w') as log:
        server = subprocess.Popen([sys.executable, 'operations_server.py', '--state-dir', state, '--port', '0', '--provision-demo'], cwd=REPO/'pilots/spacex', stdout=subprocess.PIPE, stderr=log, text=True)
        try:
            port = json.loads(server.stdout.readline())['port']
            origin = f'http://127.0.0.1:{port}'
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
                context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(e.stack or str(e)))
                page.goto(origin+'/app/#operations')
                local_navigation_ms=page.evaluate("performance.getEntriesByType('navigation')[0].domContentLoadedEventEnd")
                frame = page.frame_locator('#operations-frame')
                expect(frame.locator('#ops-login')).to_be_visible()
                frame.locator('#ops-login [name=id]').fill('editor')
                frame.locator('#ops-login [name=password]').fill(DEMO_PASSWORD)
                frame.locator('#ops-login button').click()
                expect(frame.locator('#ops-account')).to_contain_text('editor')
                expect(page.locator('#core-status')).to_contain_text('Registry API · 26')
                checks.append('App authenticates via existing Website session; reads authoritative pinned26 Registry rows through API')
                page.goto(origin+'/app/#id/691181')
                expect(page.locator('#profile')).to_contain_text('ChatGPT')
                assert page.evaluate("document.querySelector('#profile').textContent.includes('691181')")
                page.goto(origin+'/app/#id/000691181')
                expect(page.locator('#profile')).not_to_contain_text('ChatGPT')
                checks.append('Exact numeric ID lookup and leading-zero isolation preserve source identities')
                page.goto(origin+'/app/#chapters')
                assert page.locator('.group-nav a').count() == 5
                assert page.locator('.chapter-nav a').count() == 10
                page.goto(origin+'/app/#operations')
                frame = page.frame_locator('#operations-frame')
                expect(frame.locator('#ops-account')).to_contain_text('editor')
                frame.locator('#ops-write [name=title]').fill('App → shared Website record')
                frame.locator('#ops-write [name=content]').fill('Synthetic shared-state check')
                frame.locator('#ops-write button').click()
                expect(frame.locator('#ops-records')).to_contain_text('App → shared Website record')
                web = context.new_page()
                web.goto(origin+'/#operations')
                expect(web.locator('#ops-records')).to_contain_text('App → shared Website record')
                web.locator('#ops-write [name=title]').fill('Website → shared App record')
                web.locator('#ops-write [name=content]').fill('Synthetic reverse readback check')
                web.locator('#ops-write button').click()
                expect(web.locator('#ops-records')).to_contain_text('Website → shared App record')
                page.reload()
                frame = page.frame_locator('#operations-frame')
                expect(frame.locator('#ops-records')).to_contain_text('Website → shared App record')
                frame.locator('#ops-sync').click()
                expect(frame.locator('#ops-integrity')).to_contain_text('khớp digest')
                checks.append('App writes visible in Website; Website writes visible after App reload; both use exact same database and sync queue')
                context.set_offline(True)
                expect(page.locator('#core-status')).to_contain_text('Mất kết nối')
                assert page.locator('#profile').text_content() == '' or 'ChatGPT' not in page.locator('#profile').text_content()
                context.set_offline(False)
                expect(page.locator('#core-status')).to_contain_text('Registry API · 26')
                checks.append('Offline clears API Registry rows; reconnect rereads current authenticated data')
                for width in [320, 390, 768, 1440]:
                    page.set_viewport_size({'width': width, 'height': 844})
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+2'), width
                page.set_viewport_size({'width': 390, 'height': 844})
                page.screenshot(path=str(out/'app-mobile.png'))
                page.goto(origin+'/app/#id/691181')
                expect(page.locator('#profile')).to_contain_text('ChatGPT')
                page.screenshot(path=str(out/'app-id-mobile.png'))
                viewer_context = browser.new_context(viewport={'width': 390, 'height': 844})
                viewer = viewer_context.new_page()
                viewer.goto(origin+'/app/#operations')
                vf = viewer.frame_locator('#operations-frame')
                vf.locator('#ops-login [name=id]').fill('viewer')
                vf.locator('#ops-login [name=password]').fill(DEMO_PASSWORD)
                vf.locator('#ops-login button').click()
                expect(vf.locator('#ops-write button')).to_be_disabled()
                expect(vf.locator('#ops-records')).to_contain_text('App → shared Website record')
                checks.append('Independent viewer App session reads shared data and cannot write')
                page.goto(origin+'/app/#forum')
                expect(page.locator('#forum-status')).to_contain_text('editor')
                page.locator('#forum-create [name=title]').fill('Independent App forum task')
                page.locator('#forum-create [name=content]').fill('Synthetic recipient/evidence acceptance check')
                page.locator('#forum-create [name=recipient]').fill('admin')
                page.locator('#forum-create button').click()
                expect(page.locator('#forum-tasks')).to_contain_text('Independent App forum task')
                expect(page.locator('#forum-tasks')).to_contain_text('QUEUED')
                recipient_context = browser.new_context(viewport={'width': 390, 'height': 844})
                recipient = recipient_context.new_page()
                recipient.on('pageerror', lambda e: errors.append(e.stack or str(e)))
                recipient.goto(origin+'/app/#operations')
                rf = recipient.frame_locator('#operations-frame')
                rf.locator('#ops-login [name=id]').fill('admin')
                rf.locator('#ops-login [name=password]').fill(DEMO_PASSWORD)
                rf.locator('#ops-login button').click()
                expect(rf.locator('#ops-account')).to_contain_text('admin')
                recipient.goto(origin+'/app/#forum')
                expect(recipient.locator('#forum-notifications')).to_contain_text('QUEUED')
                recipient.locator('#forum-tasks button', has_text='Tiếp nhận nhiệm vụ').click()
                expect(recipient.locator('#forum-tasks')).to_contain_text('ACCEPTED')
                recipient.locator('#forum-reply [name=content]').fill('Independent recipient reply')
                recipient.locator('#forum-reply button').click()
                expect(recipient.locator('#forum-posts')).to_contain_text('Independent recipient reply')
                evidence_bytes = 'Evidence CFP+ thử nghiệm độc lập'.encode()
                recipient.locator('#forum-upload [name=file]').set_input_files({'name': 'evidence.txt', 'mimeType': 'text/plain', 'buffer': evidence_bytes})
                recipient.locator('#forum-upload button').click()
                expect(recipient.locator('#forum-evidence')).to_contain_text('evidence.txt')
                expect(recipient.locator('#forum-evidence')).to_contain_text(hashlib.sha256(evidence_bytes).hexdigest())
                recipient.locator('#forum-evidence button').click()
                expect(recipient.locator('#forum-message')).to_contain_text('Evidence PASS')
                recipient.reload()
                expect(recipient.locator('#forum-tasks')).to_contain_text('ACCEPTED')
                expect(recipient.locator('#forum-evidence')).to_contain_text('evidence.txt')
                recipient.locator('#forum-status').scroll_into_view_if_needed()
                recipient.screenshot(path=str(out/'app-forum-mobile.png'))
                checks.append('Forum task created; independent assigned recipient ACKs, replies, uploads actual UTF8 Evidence and verifies SHA256/task-key after reload')
                web.locator('#ops-logout').click()
                page.reload()
                expect(page.locator('#core-status')).to_contain_text('Đăng nhập')
                assert 'ChatGPT' not in page.locator('#profile').text_content()
                checks.append('Website logout revokes the shared session; App does not fall back to a Registry snapshot')
                assert not errors, errors
                checks.append('No browser page errors; responsive widths320/390/768/1440 checked')
                report.update(status='PASS', checks=checks, page_errors=errors, local_navigation_ms=local_navigation_ms, physical_device='NOT RUN', canva_design_match='BLOCKED', native_binary='NOT BUILT')
                browser.close()
        except Exception as exc:
            report.update(error=str(exc), checks=checks, page_errors=errors)
            raise
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
            server.stdout.close()
            (out/'app-browser.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
