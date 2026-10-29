from pathlib import Path
import json
from playwright.sync_api import sync_playwright

root=Path(__file__).parent
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking'])
    for width in [320,390,430,1280]:
        context=browser.new_context(viewport={'width':width,'height':844},device_scale_factor=1,is_mobile=width<600,has_touch=width<600,reduced_motion='reduce')
        page=context.new_page()
        page.route('**/*',lambda route:route.continue_() if route.request.url.startswith('file:') else route.abort())
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content((root/'index.html').read_text(),wait_until='load')
        page.evaluate('document.fonts.ready')
        data=page.evaluate('''() => {
          const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};
          const chapters=[...document.querySelectorAll('[data-chapter]')];
          const clickable=[...document.querySelectorAll('main a,summary')];
          const cards=[...document.querySelectorAll('.chapter-map > *')].map(box);
          const overlaps=[];
          cards.forEach((a,i)=>cards.slice(i+1).forEach((b,j)=>{if(a.x<b.x+b.w-.5&&b.x<a.x+a.w-.5&&a.y<b.y+b.h-.5&&b.y<a.y+a.h-.5)overlaps.push([i,i+j+1])}));
          return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,chapters:chapters.map(e=>e.dataset.chapter),zones:[...document.querySelectorAll('[data-zone]')].map(e=>e.dataset.zone),smallTargets:clickable.filter(e=>{const r=box(e);return r.w<44||r.h<44}).map(e=>e.textContent),overlaps,brokenAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(e=>!document.getElementById(e.hash.slice(1))).map(e=>e.hash),earthInChapter0:!!document.querySelector('[data-chapter="0"] .earth')};
        }''')
        page.get_by_role('link',name='Diễn Đàn',exact=True).click()
        data['forumNavigation']=page.evaluate('location.hash')=='#dien-dan'
        page.get_by_text('Cách gửi phản hồi',exact=True).click()
        data['detailsOpen']=page.locator('details').first.get_attribute('open') is not None
        page.get_by_role('link',name='Đến Chương 6',exact=True).click()
        data['chapterNavigation']=page.evaluate('location.hash')=='#chuong-6'
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(root/f'preview-{width}.png'),full_page=True)
        data['pageErrors']=errors
        data['pass']=data['scrollWidth']<=width and data['chapters']==[str(i) for i in range(10)] and data['zones']==['000','0','135','246','789'] and not data['smallTargets'] and not data['overlaps'] and not data['brokenAnchors'] and data['forumNavigation'] and data['detailsOpen'] and data['chapterNavigation'] and data['earthInChapter0'] and not errors
        results.append(data)
        context.close()
    browser.close()
(root/'qa-results.json').write_text(json.dumps({'engine':'Chromium local, mobile viewport emulation; not physical Safari/iPhone','results':results},ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))
assert all(x['pass'] for x in results)
