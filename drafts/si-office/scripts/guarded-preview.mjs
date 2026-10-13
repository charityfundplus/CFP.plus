import {readFileSync} from 'node:fs';import {dirname,join} from 'node:path';
import {createReviewSandbox} from './working-preview.mjs';
import {guardPreview} from './preview-guard.mjs';
export function createGuardedPreview({database,origin,revision,policy}){
 const preview=createReviewSandbox({database,origin,revision});
 try{const handler=preview.server.listeners('request')[0];preview.server.removeAllListeners('request');
  const guard=guardPreview(handler,{stateFile:join(dirname(database),'preview-guard-state.json'),policy});
  preview.server.on('request',guard.handler);return {...preview,guard};
 }catch(e){preview.service.close();throw e;}
}
export function verifyRenderActivation(env){
 if(!env.RENDER)return;
 if(env.CFP_PREVIEW_ACTIVATION_APPROVED!=='true'||! /^[a-f0-9]{40}$/.test(env.CFP_RENDER_APPROVED_COMMIT||''))throw Error('HUMAN_ACTIVATION_APPROVAL_REQUIRED');
 if(env.RENDER_GIT_COMMIT!==env.CFP_RENDER_APPROVED_COMMIT||env.CFP_PREVIEW_REVISION!==env.CFP_RENDER_APPROVED_COMMIT)throw Error('APPROVED_REVISION_MISMATCH');
}
if(process.argv[1]?.endsWith('/guarded-preview.mjs')){
 const revision=process.env.CFP_PREVIEW_REVISION;
 verifyRenderActivation(process.env);
 const p=createGuardedPreview({database:process.env.CFP_P2_DB,origin:process.env.CFP_P2_PREVIEW_ORIGIN,revision,policy:JSON.parse(readFileSync(process.env.CFP_PREVIEW_POLICY_FILE))});
 p.server.listen(Number(process.env.PORT||4189),process.env.RENDER?'0.0.0.0':'127.0.0.1');
 const timer=setInterval(()=>p.guard.check(),1000);timer.unref();
 process.on('SIGTERM',()=>p.server.close(()=>{p.service.close();process.exit(0);}));
}
