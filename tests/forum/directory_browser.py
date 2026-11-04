"""Real API + persisted SQLite + Chromium mobile directory regression.

Run: python -m tests.forum.directory_browser
Requires playwright Python package and /usr/bin/chromium (override CFP_BROWSER).
Not an iPhone Safari or PostgreSQL RLS acceptance test.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from sqlalchemy import insert

from services.forum.app import Stores, create_app
from services.forum.office import roles_t
from tests.forum.office_flow import register, run_flow


def main():
    with tempfile.TemporaryDirectory(prefix="cfp-directory-") as tmp:
        urls = {k: f"sqlite:///{tmp}/{k}.db" for k in ("auth", "sieu-bo-doi", "si-ai-hstdn", "office")}
        os.environ["CFP_FORUM_COOKIE_SECURE"] = "0"
        stores = Stores(urls['auth'], {k: urls[k] for k in ('sieu-bo-doi', 'si-ai-hstdn')}, urls['office'])
        app = create_app(stores)
        clients = [TestClient(app) for _ in range(3)]
        ids = [register(c, f"directory-{i}@example.org", f"Sandbox {i}") for i, c in enumerate(clients)]
        with stores.office.begin() as c:
            c.execute(insert(roles_t), [{'user_id': ids[0], 'role': 'governance'}, {'user_id': ids[2], 'role': 'reviewer'}])
        seeded = run_flow(*clients, ids[1], ids[2], prefix='[Directory sandbox] ')
        stores.dispose()
        env = {**os.environ, 'CFP_FORUM_AUTH_DB': urls['auth'], 'CFP_FORUM_DB_SIEU_BO_DOI': urls['sieu-bo-doi'],
               'CFP_FORUM_DB_SI_AI_HSTDN': urls['si-ai-hstdn'], 'CFP_OFFICE_DB': urls['office']}
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        with open(Path(tmp) / 'server.log', 'w') as log:
            proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'services.forum.asgi:app', '--host', '127.0.0.1', '--port', str(port)], env=env, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    try:
                        if httpx.get(base + '/api/health').status_code == 200: break
                    except httpx.HTTPError: pass
                    time.sleep(.1)
                else: raise RuntimeError('server not ready')
                with sync_playwright() as pw:
                    browser_path = os.environ.get('CFP_BROWSER') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else pw.chromium.executable_path)
                    browser = pw.chromium.launch(executable_path=browser_path, args=['--no-sandbox'])
                    checks = []
                    for width in (320, 390, 768):
                        context = browser.new_context(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True)
                        context.request.post(base + '/api/auth/login', data={'email': 'directory-1@example.org', 'password': 'matkhau-office-p0'}, headers={'X-CFP-Forum': '1'})
                        page = context.new_page(); errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
                        page.goto(base + '/_internal/office/')
                        page.locator('[data-ready="1"]').wait_for()
                        assert page.locator('[data-testid="directory-office"]').count() == 1
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.get_by_label('Tìm theo tên hoặc ID Registry').fill('missing')
                        assert page.locator('[data-testid="directory-office"]').count() == 0
                        page.get_by_label('Tìm theo tên hoặc ID Registry').fill('691121')
                        page.get_by_test_id('directory-office').tap()
                        page.locator('[data-ready="1"]').wait_for()
                        assert '691121' in page.get_by_test_id('office-title').inner_text()
                        assert 'ACCEPTED' in page.get_by_test_id('tasks').inner_text()
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.get_by_role('link', name='HUB 69 • Danh bạ sandbox').tap()
                        page.locator('[data-ready="1"]').wait_for()
                        page.reload(); page.locator('[data-ready="1"]').wait_for()
                        assert page.get_by_test_id('directory-office').count() == 1
                        assert not errors, errors
                        checks.append(f'{width}px directory → office Evidence/Review → directory → reload PASS')
                        context.close()
                    # New invitation run: UI login, actual task lifecycle, independent reviewer.
                    context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
                    page = context.new_page()
                    page.goto(base + '/_internal/office/')
                    page.get_by_test_id('directory-office').tap()
                    page.get_by_label('Email', exact=True).fill('directory-1@example.org')
                    page.get_by_label('Mật khẩu', exact=True).fill('matkhau-office-p0')
                    page.get_by_role('button', name='Đăng nhập', exact=True).click()
                    page.get_by_text('Đã đăng nhập: Sandbox 1').wait_for()
                    response = context.request.post(base + '/api/office/tasks', headers={'X-CFP-Forum': '1'}, data={
                        'pair_id': seeded['pair'], 'title': 'Invitation live UI task', 'acceptance': 'Independent review and reload',
                        'reviewer_id': ids[2], 'idempotency_key': 'invitation-ui-regression'})
                    assert response.status == 201
                    tid = response.json()['id']
                    page.reload()
                    task = page.get_by_test_id('task').filter(has_text='Invitation live UI task')
                    task.get_by_role('button', name='ACK nhiệm vụ', exact=True).click()
                    task.get_by_test_id('task-status').filter(has_text='ACKED').wait_for()
                    task.get_by_role('button', name='Bắt đầu', exact=True).click()
                    task.get_by_test_id('task-status').filter(has_text='IN_PROGRESS').wait_for()
                    task.get_by_label('URL Evidence', exact=True).fill('https://github.com/charityfundplus/CFP.plus/pull/196')
                    task.get_by_label('SHA Evidence', exact=True).fill('0478292c6cd15c52aea72143cf35e6284a121623')
                    task.get_by_label('Mô tả Evidence', exact=True).fill('Sandbox browser lifecycle regression; not production approval')
                    task.get_by_role('button', name='Nộp Evidence', exact=True).click()
                    task.get_by_test_id('evidence').wait_for()
                    task.get_by_role('button', name='Gửi Review', exact=True).click()
                    task.get_by_test_id('task-status').filter(has_text='IN_REVIEW').wait_for()
                    denied = context.request.post(base + f'/api/office/tasks/{tid}/review', headers={'X-CFP-Forum': '1'}, data={'decision':'ACCEPT','notes':'Self review must fail'})
                    assert denied.status == 403
                    reviewer = browser.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True)
                    rp = reviewer.new_page(); rp.goto(base + '/_internal/office/691121/')
                    rp.get_by_label('Email', exact=True).fill('directory-2@example.org')
                    rp.get_by_label('Mật khẩu', exact=True).fill('matkhau-office-p0')
                    rp.get_by_role('button', name='Đăng nhập', exact=True).click()
                    rt = rp.get_by_test_id('task').filter(has_text='Invitation live UI task')
                    rt.get_by_label('Nhận xét Review', exact=True).fill('Independent sandbox session review')
                    rt.get_by_role('button', name='Chấp nhận kết quả', exact=True).click()
                    rt.get_by_test_id('task-status').filter(has_text='ACCEPTED').wait_for()
                    page.reload(); task.get_by_test_id('task-status').filter(has_text='ACCEPTED').wait_for()
                    assert task.get_by_test_id('evidence').count() == 1
                    assert task.get_by_test_id('review').count() == 1
                    assert 'QUEUED → ACKED → IN_PROGRESS → IN_REVIEW → ACCEPTED' in task.inner_text()
                    checks.append('New UI login → task API create → UI ACK/start/Evidence → separate reviewer → reload/readback PASS; self-review403')
                    reviewer.close(); context.close()
                    # Failed reads must show retry; no fictional offices on failure.
                    page = browser.new_page()
                    page.route('**/api/hub/69', lambda route: route.fulfill(status=503, body='{}'))
                    page.goto(base + '/_internal/office/')
                    page.get_by_role('alert').wait_for()
                    assert page.get_by_test_id('directory-office').count() == 0
                    page.unroute('**/api/hub/69'); page.get_by_role('button', name='Thử lại').click()
                    page.locator('[data-ready="1"]').wait_for()
                    assert page.get_by_test_id('directory-office').count() == 1
                    checks.append('API503 → visible error → retry real API PASS')
                    browser.close()
                    print(json.dumps({'checks': checks, 'engine': 'Chromium; not Safari', 'database': 'temporary SQLite; no external mutations'}, ensure_ascii=False, indent=2))
            finally:
                proc.terminate(); proc.wait(timeout=10)


if __name__ == '__main__':
    main()
