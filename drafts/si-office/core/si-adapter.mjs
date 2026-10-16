// Adapter is untrusted: it proposes tools and output. It cannot execute tools.
export class MockSIAdapter {
 constructor(provider='mock-local'){if(!['mock-local','mock-alternate'].includes(provider))throw Error('LIVE_SI_ADAPTER_DISABLED');this.provider=provider;}
 async propose({task,source,signal}){
  if(task.scenario==='timeout')return new Promise((resolve,reject)=>{signal.addEventListener('abort',()=>reject(Error('ADAPTER_ABORTED')),{once:true});});
  if(task.scenario==='adapter-error')throw Error('SIMULATED_ADAPTER_ERROR');
  const tools=[{tool:'source.read',resource:task.resource}];if(task.kind!=='registry-audit')tools.push({tool:'draft.write',resource:task.resource});
  if(task.scenario==='overreach')tools.push({tool:'production.publish',resource:task.resource});
  return {adapter:this.provider,protocol:1,externalRequests:0,tools,output:{title:task.title,text:task.text||'Synthetic supervised draft for '+task.kind,source:{resource:source.resource,sha256:task.scenario==='bad-evidence'?'forged':source.sha256},synthetic:true,id:null,parent:null,did:null,canonical:null,sourceVerified:false,capabilityVerified:task.scenario==='false-claim',legalRelationshipVerified:false,mode:'DRAFT ONLY'}};
 }
}
