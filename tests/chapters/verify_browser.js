(async () => {
 const data=await (await fetch('/assets/chapter-projection.json')).json();
 const checks=[];
 const check=(label,ok)=>{checks.push({test:label,result:ok?'PASS':'FAIL'});if(!ok)throw Error(label)};
 for(const chapter of '0123456789'){
   const frame=document.createElement('iframe');frame.style.width='100%';frame.style.height='900px';
   document.body.append(frame);
   try {
     await new Promise((resolve,reject)=>{frame.onload=resolve;frame.onerror=reject;frame.src='/'+chapter;});
     let panel;
     for(let attempt=0;attempt<100;attempt++){
       panel=frame.contentDocument.getElementById('chapter-pair');
       if(panel?.querySelectorAll('article').length===2 || panel?.dataset.error)break;
       await new Promise(r=>setTimeout(r,50));
     }
     check(chapter+' meaningful existing page',frame.contentDocument.querySelector('h1')?.textContent.length>0);
     check(chapter+' independent entities',panel?.querySelectorAll('article').length===2&&new Set([...panel.querySelectorAll('article')].map(e=>e.dataset.entityType)).size===2);
     check(chapter+' source commit',panel.dataset.sourceCommit===data.source_commit);
     check(chapter+' canonical no slash',panel.querySelector('a').getAttribute('href')==='https://cfp.plus/'+chapter);
     const relations=panel.querySelectorAll('li[data-chapter]');check(chapter+' ten unique oversight references',relations.length===10&&new Set([...relations].map(e=>e.dataset.chapter)).size===10);
     const refs=[...panel.querySelectorAll('li[data-identity-reference]')].map(e=>e.dataset.identityReference);check(chapter+' no duplicated identity',refs.length===new Set(refs).size);
     check(chapter+' conservative status',panel.textContent.includes('DECLARED_NOT_ACTIVATED')&&panel.textContent.includes('Chưa có Readback vận hành'));
     check(chapter+' no prefix Parent inference',panel.textContent.includes('Không suy diễn Parent'));
     check(chapter+' mobile no horizontal overflow',frame.contentDocument.documentElement.scrollWidth<=frame.contentWindow.innerWidth+1);
   }finally{frame.remove()}
 }
 check('existing Country 911 reference',Object.values(await(await fetch('/registry/country-route-map.json')).json()).some(x=>x.country_id==='911'));
 check('conflict retained',data.conflicts[0].id==='691141'&&data.conflicts[0].status==='CONFLICT FOUND / HUMAN REVIEW');
 return {result:'PASS',checks:checks.length,results:checks,source_commit:data.source_commit,viewport:{width:innerWidth,height:innerHeight},browser:navigator.userAgent};
})()
