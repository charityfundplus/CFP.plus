"""PR189 Website integration on the existing runtime; no deployment or new DB."""
import hashlib
import http.client
import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from operations import Operations, DEMO_PASSWORD
import operations_server as bridge
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    sync_playwright = None


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.operations = Operations(Path(self.temp.name))
        self.operations.provision_demo()
        self.server = bridge.make_server(self.operations)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.base = f'http://127.0.0.1:{self.port}'
        self.registry_bytes = bridge.REGISTRY_PATH.read_bytes()

    def tearDown(self):
        self.assertEqual(bridge.REGISTRY_PATH.read_bytes(), self.registry_bytes)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, body=None, cookie='', method=None):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        c.request(method or ('GET' if body is None else 'POST'), path, body=None if body is None else json.dumps(body), headers={'Origin': self.base, 'Content-Type': 'application/json', 'Cookie': cookie})
        r = c.getresponse()
        result = (r.status, dict(r.getheaders()), r.read())
        c.close()
        return result

    def test_public_website_assets_csp_and_existing_app_links(self):
        status, headers, _ = self.request('/website')
        self.assertEqual(status, 308)
        self.assertEqual(headers['Location'], '/website/')
        status, headers, body = self.request('/website/')
        self.assertEqual(status, 200)
        self.assertIn('text/html', headers['Content-Type'])
        self.assertNotIn(b'<style>', body)
        self.assertNotIn(b'<script>', body)
        self.assertNotIn('unsafe-inline', headers['Content-Security-Policy'])
        self.assertIn(b'/app/#forum', body)
        self.assertIn(b'/app/#operations', body)
        self.assertIn(b'https://cfp.plus/69', body)
        for name in ['site.js', 'site.css', 'chapters.json']:
            self.assertEqual(self.request('/website/' + name)[0], 200)
        self.assertEqual(self.request('/website/', method='HEAD')[2], b'')

    def test_five_release_groups_ten_chapters_and_hundred_positions_preserve_zeros(self):
        data = json.loads(self.request('/website/chapters.json')[2])
        self.assertEqual(data['sourceCommit'], '488439a856e860037c3f6d8e94f938b7eda652ae')
        self.assertEqual(list(data['groups']), ['V', '0', '135', '246', '789'])
        self.assertFalse(data['positionsAreCanonical'])
        self.assertEqual([c['id'] for c in data['chapters']], [str(i) for i in range(10)])
        children = [id for c in data['chapters'] for id in c['children']]
        self.assertEqual(len(children), 100)
        self.assertEqual(len(set(children)), 100)
        self.assertEqual(children[:10], ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09'])
        for id in [str(i) for i in range(10)] + children:
            with self.subTest(id=id):
                self.assertEqual(self.request('/website/' + id)[0], 200)

    def test_registry_routes_exact_source_no_fabricated_parent_fallback(self):
        source = json.loads(self.registry_bytes)
        for row in source.values():
            if isinstance(row, dict) and row.get('id'):
                self.assertEqual(self.request('/website/' + row['id'])[0], 200)
        for id in ['000', '0000', '984', '691180000', '99999999', '-1', '69extra']:
            with self.subTest(id=id):
                status, _, body = self.request('/website/' + id)
                self.assertEqual(status, 404)
                self.assertNotIn(b'ChatGPT', body)
                self.assertNotIn(b'OpenAI', body)
        self.assertEqual(self.request('/api/app/registry')[0], 401)

    def test_registry_shared_auth_read_pin_and_source_no_extra_database(self):
        status, headers, _ = self.request('/api/session', {'id': 'editor', 'password': DEMO_PASSWORD})
        self.assertEqual(status, 200)
        cookie = headers['Set-Cookie'].split(';')[0]
        before = {p.name for p in self.operations.root.glob('*.sqlite')}
        status, _, body = self.request('/api/app/registry', cookie=cookie)
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(len(data['records']), 26)
        self.assertEqual(data['sourceSHA256'], hashlib.sha256(self.registry_bytes).hexdigest())
        self.assertEqual(data['registryBlobSHA'], bridge.REGISTRY_BLOB_SHA)
        self.assertFalse(data['activationAllowed'])
        self.assertEqual({p.name for p in self.operations.root.glob('*.sqlite')}, before)
        self.assertEqual(before, {'operations.sqlite', 'replica.sqlite'})
        changed = Path(self.temp.name) / 'changed-source.json'
        changed.write_bytes(self.registry_bytes + b' ')
        with patch.object(bridge, 'REGISTRY_PATH', changed):
            self.assertEqual(self.request('/website/691181')[0], 503)
            self.assertEqual(self.request('/api/app/registry', cookie=cookie)[0], 503)
        self.assertEqual(self.request('/website/00')[0], 200)

    def test_mount_rejects_traversal_source_files_and_symlink(self):
        for path in ['/website/../registry/ai-entity-registry.json', '/website/%2e%2e/operations.py', '/website/package.json', '/website/.env', '/website/site.js/extra', '/website//site.js', '/website/%30%30']:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        fake = Path(self.temp.name) / 'website'
        fake.mkdir()
        (fake / 'index.html').symlink_to(bridge.REGISTRY_PATH)
        with patch.object(bridge, 'WEBSITE_ROOT', fake):
            self.assertEqual(self.request('/website/')[0], 404)
        self.assertEqual(self.request('/website/', {}, method='POST')[0], 401)
        self.assertEqual(self.request('/')[0], 200)

    @unittest.skipUnless(sync_playwright and shutil.which('chromium'), 'Python Playwright and Chromium required')
    def test_browser_exact_search_navigation_shared_registry_mobile_and_no_errors(self):
        errors = []
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
            page.on('pageerror', lambda e: errors.append(str(e)))
            try:
                page.goto(self.base + '/website/')
                expect(page.locator('#chapterGrid article')).to_have_count(10)
                expect(page.locator('#chapterGrid .ids a')).to_have_count(100)
                self.assertEqual(page.locator('#groupNav a').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.group)'), ['V', '0', '135', '246', '789'])
                expect(page.locator('#registryStatus')).to_contain_text('Cần phiên đăng nhập')
                page.locator('#groupNav a[data-group="135"]').click()
                expect(page.locator('#chapterGrid article')).to_have_count(3)
                self.assertEqual(page.locator('#chapterGrid article').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.chapterId)'), ['1', '3', '5'])
                page.locator('nav[aria-label="Điều hướng chính"] a[href="/website/#chapters"]').click()
                expect(page.locator('#chapterGrid article')).to_have_count(10)
                page.locator('#search').fill('00')
                expect(page.locator('#chapterGrid article')).to_have_count(1)
                expect(page.locator('#chapterGrid article')).to_have_attribute('data-position-id', '00')
                page.locator('#chapterGrid article a').click()
                expect(page).to_have_url(self.base + '/website/00')
                expect(page.locator('#routePanel [data-position-id="00"]')).to_have_count(1)
                self.assertEqual(page.locator('#routePanel [data-registry-id]').count(), 0)
                result = page.evaluate('async (credentials) => {const r=await fetch("/api/session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(credentials)});return r.status}', {'id': 'editor', 'password': DEMO_PASSWORD})
                self.assertEqual(result, 200)
                page.locator('#registryRefresh').click()
                expect(page.locator('#registryStatus')).to_contain_text('26 hồ sơ')
                page.locator('#search').fill('691181')
                expect(page.locator('#registryGrid article')).to_have_count(1)
                expect(page.locator('#registryGrid article')).to_have_attribute('data-registry-id', '691181')
                expect(page.locator('#chapterGrid article')).to_have_count(0)
                page.locator('#search').fill('69118')
                expect(page.locator('#registryGrid article')).to_have_count(1)
                expect(page.locator('#registryGrid article')).to_have_attribute('data-registry-id', '69118')
                page.locator('#search').fill('000')
                expect(page.locator('#registryGrid article')).to_have_count(0)
                expect(page.locator('#chapterGrid article')).to_have_count(0)
                expect(page.locator('#empty')).to_be_visible()
                page.locator('#search').fill('ChatGPT')
                expect(page.locator('#registryGrid article')).to_have_count(1)
                page.locator('#registryGrid article a').first.click()
                expect(page).to_have_url(self.base + '/website/691181')
                expect(page.locator('#routePanel [data-registry-id="691181"]')).to_have_count(1)
                expect(page.locator('#routePanel')).to_contain_text('ChatGPT')
                for width in [390, 320]:
                    page.set_viewport_size({'width': width, 'height': 844})
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth+1'), width)
                self.assertEqual(errors, [])
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()
