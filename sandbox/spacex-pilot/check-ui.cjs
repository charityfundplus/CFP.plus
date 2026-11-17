// Optional Playwright + Chromium check. Outputs go to a fresh temporary directory.
const {chromium}=require('playwright');
const {mkdtempSync,readFileSync,writeFileSync}=require('node:fs');
const {tmpdir}=require('node:os');const {join}=require('node:path');
const {createServer}=require('node:http');
(async()=>{
 const {handler}=await import('./server.mjs');
 const out=mkdtempSync(join(tmpdir(),'cfp-ui-'));
 const app=createServer((req,res)=>{
  const assets=new Map([['/69/',['../../69/index.html','text/html']],['/styles.css',['../../styles.css','text/css']]]);
  const asset=assets.get(req.url);
  if(asset){res.writeHead(200,{'Content-Type':asset[1]});res.end(readFileSync(join(__dirname,asset[0])));return;}
  handler(req,res);
 });
 let browser;
 try{
 await new Promise((ok,fail)=>{app.once('error',fail);app.listen(0,'127.0.0.1',ok)});
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
 const origin='http://127.0.0.1:'+app.address().port,results=[];
 for(const width of [375,390,1440]){
  const page=await browser.newPage({viewport:{width,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const check=(ok,name)=>{if(!ok)throw Error(width+': '+name);results.push({width,name,result:'PASS'});};
  await page.goto(origin);await page.locator('#directory article').first().waitFor();
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'pilot no overflow');
  await page.locator('#search').fill('ChatGPT');check(await page.locator('#directory article').count()===1,'search match');
  await page.locator('#search').fill('not-present');check(await page.locator('#directory article').count()===0,'empty search');
  await page.locator('#reverse').click();check((await page.locator('#notice').textContent()).includes('BLOCKED'),'reverse demo labelled blocked');
  await page.locator('#note').fill('<img src=x onerror=alert(1)>');await page.locator('#addnote').click();check(await page.locator('#notes img').count()===0,'notes safe text');
  await page.reload();check(await page.locator('#notes li').count()===0,'notes reset');
  check(await page.locator('a[href="https://cfp.plus/69/#spacex-research"]').count()===1,'back link');
  await page.screenshot({path:join(out,'pilot-'+width+'.png'),fullPage:true});
  await page.goto(origin+'/69/');check(await page.locator('#spacex-research').count()===1,'single research introduction');
  check(await page.locator('#spacex-research a').count()===6,'official and handoff links');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'hub no overflow');
  check(errors.length===0,'no JavaScript errors');
  await page.screenshot({path:join(out,'hub-'+width+'.png'),fullPage:true});await page.close();
 }
 writeFileSync(join(out,'results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify({output:out,assertions:results.length,result:'PASS',browser:'Chromium; not physical Safari'}));
 }finally{if(browser)await browser.close();await new Promise(ok=>app.close(ok));}
})().catch(e=>{console.error(e);process.exitCode=1});
