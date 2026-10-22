// Local file/browser QA only. No server, deployment, auth provisioning or external navigation.
// Phone viewports are desktop-engine emulation, never real iPhone/Safari evidence.
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {resolve,join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const out=resolve(process.env.CFP_QA_OUTPUT||join(root,'evidence/shared-design-qa'));
await mkdir(out,{recursive:true});
const sourceRevision=execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const artifact=await readFile(join(root,'HUB69-review.html'));
const report={sourceRevision,artifactSHA256:createHash('sha256').update(artifact).digest('hex'),
  engine:process.env.CFP_QA_BROWSER||'firefox',mode:'local file / desktop engine with phone viewport emulation',
  actualIPhone:'BLOCKED: no physical device or approved HTTPS staging',httpsStaging:'BLOCKED: no approved URL or deployed revision',
  checks:[],screenshots:[],externalRequests:[],errors:[]};
const check=(name,pass,detail)=>report.checks.push({name,pass,...(detail?{detail}:{})});
async function bounded(promise,label,ms=15000){
  let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(label+' timed out after '+ms+'ms')),ms);})]);}finally{clearTimeout(timer);}
}
let browser;
try{
  const pw=await import(process.env.CFP_PLAYWRIGHT_MODULE?pathToFileURL(process.env.CFP_PLAYWRIGHT_MODULE).href:'playwright');
  browser=await bounded(pw[report.engine].launch({timeout:15000}),'browser launch');report.browserVersion=browser.version();
  const axePath=process.env.CFP_AXE_PATH;
  if(!axePath)throw Error('CFP_AXE_PATH must identify the installed axe-core/axe.min.js');
  const context=await bounded(browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),'browser context');
  const page=await bounded(context.newPage(),'browser page');
  page.setDefaultTimeout(15000);
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url()))report.externalRequests.push(r.url());});
  await page.route(/^https?:/,r=>r.abort());
  const base=pathToFileURL(join(root,'HUB69-review.html')).href;
  const routes=['#home','#master','#id','#id/691181','#id/000','#id/<script>',
    '#chapters',...['V','000','135','246','789'].map(g=>'#group/'+g),
    ...Array.from({length:10},(_,i)=>'#chapter/'+i),'#hstdn/vn','#hstdn/us','#technology',
    '#commerce','#partners','#partners/vn/supplier','#partners/us/buyer','#reference/8682','#reference/8882','#app'];
  report.routes=routes;
  async function go(hash){
    await page.goto(base+hash);
    await page.waitForFunction(()=>{const s=window.HUB69P0?.route(location.hash);return s&&document.getElementById('view-'+s.view)?.hidden===false;});
    await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
  }
  for(const width of [320,390,768,1440]){
    await page.setViewportSize({width,height:width<700?844:1000});
    for(const hash of routes){
      await go(hash);
      const state=await page.evaluate(()=>({
        views:document.querySelectorAll('.view:not([hidden])').length,
        width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,
        title:document.title,view:window.HUB69P0.route(location.hash).view,
        missing:[...document.querySelectorAll('.view:not([hidden]) a[href^="#"]')].map(a=>a.getAttribute('href')).filter(h=>h!=='#content'&&window.HUB69P0.route(h).invalid)
      }));
      // Missing source IDs and intentionally invalid ID paths may lead to the explicit error presenter.
      check(`${width} ${hash}: one view and title`,state.views===1&&!state.title.includes('undefined'));
      check(`${width} ${hash}: no horizontal overflow`,state.scroll<=state.width+1,state);
      check(`${width} ${hash}: navigation destinations`,state.missing.length===0,state.missing);
    }
  }
  await page.setViewportSize({width:390,height:844});await go('#home');
  await page.locator('#menu-toggle').click();
  check('mobile menu opens with expanded state',await page.locator('#menu-toggle').getAttribute('aria-expanded')==='true');
  await page.locator('#primary-nav a[href="#partners"]').click();
  await page.waitForURL('**#partners');
  check('mobile menu closes after navigation',await page.locator('#menu-toggle').getAttribute('aria-expanded')==='false');
  await page.locator('#partner-country').selectOption('vn');
  await page.waitForURL('**#partners/vn/all');
  await page.locator('#partner-role').selectOption('supplier');
  await page.waitForURL('**#partners/vn/supplier');
  check('mobile country and role filters operate in real DOM',await page.locator('.catalog-card').count()===1);
  await page.keyboard.press('Tab');
  const focused=await page.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e);return {tag:e.tagName,outline:s.outlineStyle,width:s.outlineWidth};});
  check('keyboard focus has visible outline',focused.outline!=='none'&&parseFloat(focused.width)>=3,focused);
  await go('#home');await page.locator('#home-id').fill('000');await page.locator('.lookup button').click();await page.waitForURL('**#id/000');
  check('real form preserves zeros and shows missing ID',await page.locator('#profile').innerText().then(t=>t.includes('000')));
  await go('#app');check('offline App login stays disabled',await page.getByRole('button',{name:/Đăng nhập/}).isDisabled());
  report.axeVersion=JSON.parse(await readFile(resolve(axePath,'../package.json'),'utf8')).version;
  for(const [width,hash] of [[1440,'#home'],[390,'#home'],[390,'#chapter/5'],[390,'#chapter/6'],[390,'#hstdn/vn'],[390,'#chapter/9'],[390,'#partners'],[390,'#reference/8882'],[390,'#app']]){
    await page.setViewportSize({width,height:844});await go(hash);
    if(!await page.evaluate(()=>!!window.axe))await page.addScriptTag({path:axePath});
    const audit=await page.evaluate(async()=>{
      const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});
      return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.length}))};
    });
    check(`axe ${width} ${hash}`,audit.violations.length===0,audit);
  }
  for(const [name,width,hash] of [['desktop-hub',1440,'#home'],['phone-hub-firefox',390,'#home'],['phone-chapter5-firefox',390,'#chapter/5'],['phone-partners-firefox',390,'#partners/vn/supplier'],['phone-app-firefox',390,'#app']]){
    await page.setViewportSize({width,height:width<700?844:1000});await go(hash);
    const file=name+'.png';await page.screenshot({path:join(out,file),fullPage:true});report.screenshots.push({file,width,hash,device:'desktop Firefox / emulated width; not physical iPhone'});
  }
  check('no page JS errors',report.errors.length===0,report.errors);
  check('standalone makes zero external HTTP requests',report.externalRequests.length===0,report.externalRequests);
  await context.close();
  const videoContext=await browser.newContext({viewport:{width:390,height:844},recordVideo:{dir:join(out,'video'),size:{width:390,height:844}}});
  const videoPage=await videoContext.newPage();await videoPage.goto(base+'#home');await videoPage.locator('#menu-toggle').click();await videoPage.locator('#primary-nav a[href="#partners"]').click();await videoPage.locator('#partner-country').selectOption('us');await videoPage.locator('#partner-role').selectOption('buyer');await videoPage.goto(base+'#app');
  const video=videoPage.video();await videoContext.close();report.video=await video.path();
  report.status=report.checks.every(c=>c.pass)?'PASS_LOCAL_BROWSER_ONLY':'FAIL';
}catch(e){report.status='BLOCKED';report.errors.push(e.stack||String(e));}
finally{if(browser)try{await bounded(browser.close(),'browser close',3000);}catch(e){report.errors.push(e.message);}}
report.counts={total:report.checks.length,pass:report.checks.filter(c=>c.pass).length,fail:report.checks.filter(c=>!c.pass).length};
await writeFile(join(out,'browser-results.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,counts:report.counts,errors:report.errors,failures:report.checks.filter(c=>!c.pass)}));
process.exit(report.status==='PASS_LOCAL_BROWSER_ONLY'?0:1);
