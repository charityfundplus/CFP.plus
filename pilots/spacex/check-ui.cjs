const { chromium } = require('playwright');
const fs = require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 const results=[];
 for(const width of [390,1440]){
  const page=await browser.newPage({viewport:{width,height:1000}});
  const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('http://127.0.0.1:8765/');
  await page.locator('#records article').waitFor();
  const assert=(value,name)=>{if(!value)throw Error(name);results.push({width,name,status:'PASS'});};
  assert(await page.locator('#records article').count()===1,'adapter export renders');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no horizontal overflow');
  await page.locator('#search').fill('missing');
  assert(await page.locator('#records article').count()===0,'search no results');
  await page.locator('#search').fill('ChatGPT');
  assert(await page.locator('#records article').count()===1,'search matching record');
  await page.locator('#reverse').click();
  assert((await page.locator('#feedback').textContent()).includes('WRITEBACK BLOCKED'),'reverse button feedback');
  assert(errors.length===0,'no page errors');
  await page.locator('a[href="#research"]').click();
  assert(new URL(page.url()).hash==='#research','section navigation');
  await page.screenshot({path:__dirname+'/evidence/chromium-'+width+'.png',fullPage:true});
  await page.close();
 }
 await browser.close(); fs.writeFileSync(__dirname+'/evidence/ui-tests.json',JSON.stringify(results,null,2));
 console.log(results.length+' PASS');
})().catch(e=>{console.error(e);process.exit(1)});
