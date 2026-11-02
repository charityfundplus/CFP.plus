"""Actual local API + Chromium mobile emulation; never claims physical iPhone QA."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile

from playwright.sync_api import sync_playwright, expect
from operations import DEMO_PASSWORD

ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.environ['CFP_SPACEX_EVIDENCE_DIR']) if os.environ.get('CFP_SPACEX_EVIDENCE_DIR') else Path(tempfile.mkdtemp(prefix='cfp-spacex-browser-'))
OUTPUT.mkdir(parents=True, exist_ok=True)
checks, errors = [], []
report = {'status': 'FAIL', 'scope': 'Real local HTTP + SQLite; Chromium mobile emulation, not physical Safari; synthetic test records only'}

with tempfile.TemporaryDirectory(prefix='cfp-spacex-state-') as tmp:
    state_dir = Path(tmp)
    with (OUTPUT/'browser-server.txt').open('w') as stderr:
        server = subprocess.Popen(['python3', 'operations_server.py', '--state-dir', tmp, '--port', '0', '--provision-demo'], cwd=ROOT, stdout=subprocess.PIPE, stderr=stderr, text=True)
        try:
            startup = json.loads(server.stdout.readline())
            origin = 'http://127.0.0.1:' + str(startup['port'])
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
                contexts = []

                def login(name):
                    context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
                    contexts.append(context)
                    page = context.new_page()
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.goto(origin + '/#operations')
                    expect(page.locator('#ops-connection')).to_contain_text('CHƯA ĐĂNG NHẬP')
                    page.locator('#ops-login [name=id]').fill(name)
                    page.locator('#ops-login [name=password]').fill(DEMO_PASSWORD)
                    page.locator('#ops-login button').click()
                    expect(page.locator('#ops-account')).to_contain_text(name)
                    expect(page.locator('#ops-connection')).to_have_attribute('data-connected', 'true')
                    return context, page

                context, page = login('editor')
                assert page.locator('#ops-navigation article').count() == 5
                links = page.locator('#ops-navigation a').evaluate_all('(nodes)=>nodes.map(n=>n.href)')
                assert sorted(links) == sorted('https://cfp.plus/' + str(i) for i in range(10))
                assert page.locator('#ops-connectors article').count() == 7
                assert all('BLOCKED' in s for s in page.locator('#ops-connectors article').all_text_contents())
                checks.append('Five canonical groups, ten existing chapter links, seven external connectors labelled BLOCKED')
                title = 'QA <img src=x onerror="window.spacexXSS=1">'
                page.locator('#ops-write [name=title]').fill(title)
                page.locator('#ops-group').select_option('246')
                page.locator('#ops-chapter').select_option('6')
                page.locator('#ops-write [name=content]').fill('Synthetic local operational data; no external source claim')
                page.locator('#ops-write button').click()
                expect(page.locator('#ops-records')).to_contain_text(title)
                assert page.locator('#ops-records img').count() == 0
                assert page.evaluate('window.spacexXSS') is None
                state = page.evaluate("fetch('/api/state').then(r=>r.json())")
                record = state['records'][0]
                assert state['queue'][0]['status'] == 'PENDING'
                checks.append('UI writes an actual SQLite record and durable outbox; title displayed safely as text')
                page.reload()
                expect(page.locator('#ops-records')).to_contain_text(title)
                checks.append('Authenticated API readback after page reload preserves exact record')
                page.locator('#ops-sync').click()
                expect(page.locator('#ops-sync-summary')).to_contain_text('0 đang chờ')
                expect(page.locator('#ops-integrity')).to_contain_text('khớp digest')
                state = page.evaluate("fetch('/api/state').then(r=>r.json())")
                assert state['records'] == state['replica']['records']
                assert state['digest'] == state['replica']['digest']
                checks.append('UI sync moves the outbox to actual local replica; content and digests agree')
                context.set_offline(True)
                page.locator('#ops-refresh').click()
                expect(page.locator('#ops-connection')).to_contain_text('MẤT KẾT NỐI')
                expect(page.locator('#ops-write button')).to_be_disabled()
                expect(page.locator('#ops-sync')).to_be_disabled()
                context.set_offline(False)
                page.locator('#ops-refresh').click()
                expect(page.locator('#ops-connection')).to_have_attribute('data-connected', 'true')
                expect(page.locator('#ops-write button')).to_be_enabled()
                assert page.locator('#ops-records article').count() == 1
                checks.append('Browser disconnect removes online claim and disables writes; reconnection verifies state without duplicates')
                for width in [390, 320, 1440]:
                    page.set_viewport_size({'width': width, 'height': 844})
                    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 2'), width
                page.set_viewport_size({'width': 390, 'height': 844})
                page.locator('#ops-records').scroll_into_view_if_needed()
                page.screenshot(path=str(OUTPUT/'operations-mobile.png'))
                page.locator('#ops-heading').scroll_into_view_if_needed()
                page.screenshot(path=str(OUTPUT/'operations-overview-mobile.png'))
                checks.append('No horizontal overflow at 320, 390 and 1440px; mobile screenshot recorded')
                _, viewer = login('viewer')
                expect(viewer.locator('#ops-records')).to_contain_text(title)
                expect(viewer.locator('#ops-write button')).to_be_disabled()
                expect(viewer.locator('#ops-backup')).to_be_disabled()
                _, foreign = login('foreign')
                assert foreign.locator('#ops-records article').count() == 0
                checks.append('Independent viewer context reads without write controls; foreign workspace cannot see source records')
                _, admin = login('admin')
                admin.locator('#ops-backup').click()
                expect(admin.locator('#ops-backup-id')).not_to_have_value('')
                admin.locator('#ops-restore button').click()
                expect(admin.locator('#ops-message')).to_contain_text('Đã kiểm chứng phục hồi')
                files = list(state_dir.glob('restore-*.sqlite'))
                assert len(files) == 1
                with sqlite3.connect(files[0]) as db:
                    restored = json.loads(db.execute('SELECT payload FROM records WHERE key=?', (record['key'],)).fetchone()[0])
                    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                    assert restored == record
                checks.append('Admin UI backup/restore creates a separate SQLite file whose actual content matches the saved record')
                page.locator('#ops-logout').click()
                expect(page.locator('#ops-connection')).to_contain_text('ĐÃ ĐĂNG XUẤT')
                expect(page.locator('#ops-write button')).to_be_disabled()
                assert not errors, errors
                checks.append('Logout revokes session; no browser page errors')
                report.update(status='PASS', checks=checks, page_errors=errors, record_key=record['key'], content_hash=record['content_hash'], source_digest=state['digest'], replica_digest=state['replica']['digest'], external_sync='BLOCKED', physical_phone='NOT RUN')
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
            if server.stdout:
                server.stdout.close()
            (OUTPUT/'operations-browser.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')

print(json.dumps(report, ensure_ascii=False, indent=2))
