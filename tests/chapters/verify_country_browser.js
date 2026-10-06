(async()=>{
 const results=[];
 const frame=document.createElement('iframe');frame.style.width='100%';frame.style.height='600px';document.body.append(frame);
 for(const root of ['910','911','981','982','984'])for(const chapter of '0123456789')for(const path of ['', '1','10']){
   const id=root+chapter+path;
   await new Promise((resolve,reject)=>{frame.onload=resolve;frame.onerror=reject;frame.src='/'+id});
   let panel;for(let i=0;i<100;i++){panel=frame.contentDocument.querySelector('#country-template');if(panel)break;await new Promise(r=>setTimeout(r,25));}
   if(!panel)throw Error('Country rendering missing '+id);
   const d=JSON.parse(frame.contentDocument.querySelector('#country-readback').textContent);
   if(d.country_root!==root||d.chapter!==chapter||d.descendant_path!==path||d.reconstructed!==id||!d.matches)throw Error('Roundtrip '+id);
   if(panel.dataset.sourceCommit.length!==40||!panel.textContent.includes('UNASSIGNED')||!panel.textContent.includes('4984 ≠ 98441'))throw Error('Status/source '+id);
   if(frame.contentDocument.documentElement.scrollWidth>frame.clientWidth+2)throw Error('Overflow '+id);
   results.push({id,readback:d,status:'PASS'});
 }
 // Rollback switch: disabled projection must not create another panel.
 const win=frame.contentWindow,oldFetch=win.fetch,count=frame.contentDocument.querySelectorAll('#country-template').length;
 win.fetch=async()=>({ok:true,json:async()=>({authority:'READ_ONLY_MIRROR',schema_version:'1',enabled:false})});
 const rendered=await win.renderCountryTemplate('98441');win.fetch=oldFetch;
 if(rendered||frame.contentDocument.querySelectorAll('#country-template').length!==count)throw Error('Disabled renderer rollback');
 frame.remove();return {status:'PASS',cases:results.length,results,rollback:'PASS',viewport:{width:innerWidth,height:innerHeight}};
})()
