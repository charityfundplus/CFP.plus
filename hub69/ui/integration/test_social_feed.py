"""A delayed pre-write read must not hide a durably acknowledged post."""
import asyncio
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from playwright.async_api import async_playwright, expect

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'pilots/spacex'))
from operations import Operations,DEMO_PASSWORD
from operations_server import make_server

class FeedRaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_acknowledged_post_visible_before_slow_read_and_stale_read_cannot_erase_it(self):
        with tempfile.TemporaryDirectory(prefix='cfp-feed-race-') as state:
            operations=Operations(state);operations.provision_demo()
            server=make_server(operations);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            origin=f'http://127.0.0.1:{server.server_address[1]}'
            gate=asyncio.Event();captured=asyncio.Event();fulfilled=asyncio.Event()
            try:
                async with async_playwright() as p:
                    browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
                    context=await browser.new_context(base_url=origin)
                    response=await context.request.post('/api/session',data={'id':'editor','password':DEMO_PASSWORD},headers={'Origin':origin})
                    self.assertEqual(response.status,200)
                    page=await context.new_page();await page.goto('/app/#social')
                    await expect(page.locator('#social-status')).to_contain_text('Có quyền viết')
                    async def delayed(route):
                        response=await route.fetch()
                        data=await response.json()
                        captured.set()
                        await gate.wait()
                        await route.fulfill(response=response,json=data)
                        fulfilled.set()
                    await page.route('**/api/social/state',delayed)
                    # Background reconnect read: real source snapshot has zero posts.
                    await page.evaluate("window.dispatchEvent(new Event('online'))")
                    await asyncio.wait_for(captured.wait(),5)
                    await page.locator('#social-post textarea').fill('Committed post survives an older delayed read')
                    await page.locator('#social-post button').click()
                    await expect(page.locator('#social-feed')).to_contain_text('Committed post survives',timeout=3000)
                    gate.set();await asyncio.wait_for(fulfilled.wait(),5)
                    await asyncio.sleep(.1)
                    await expect(page.locator('#social-feed')).to_contain_text('Committed post survives')
                    await page.unroute('**/api/social/state',delayed)
                    await page.reload()
                    await expect(page.locator('#social-feed')).to_contain_text('Committed post survives')
                    await browser.close()
            finally:
                gate.set();server.shutdown();server.server_close();thread.join(timeout=5)

if __name__=='__main__':unittest.main()
