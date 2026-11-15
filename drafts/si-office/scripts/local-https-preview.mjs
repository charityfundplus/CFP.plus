import https from 'node:https';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createReviewSandbox} from './working-preview.mjs';

// Transport only: use the existing Core, account provisioning and HTTP handler.
export function createLocalHTTPSPreview({database,origin,revision,certificate,key}) {
 const url=new URL(origin);
 if(url.protocol!=='https:'||!['localhost','127.0.0.1'].includes(url.hostname)||url.username||url.password||url.pathname!=='/'||url.search||url.hash)throw Error('LOCAL_HTTPS_ORIGIN_REQUIRED');
 const port=Number(url.port||443);
 if(!Number.isInteger(port)||port<1||port>65535)throw Error('LOCAL_HTTPS_PORT_REQUIRED');
 // Validate TLS inputs before opening or provisioning any state.
 const server=https.createServer({cert:readFileSync(certificate),key:readFileSync(key),minVersion:'TLSv1.2'});
 let preview;
 try {preview=createReviewSandbox({database,origin:url.origin,revision});}
 catch(e){server.close();throw e;}
 const handler=preview.server.listeners('request')[0];
 server.on('request',(req,res)=>{
  res.setHeader('X-Robots-Tag','noindex, nofollow');
  if(req.headers.host!==url.host){res.writeHead(403,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify({error:'LOCAL_PREVIEW_HOST_DENIED'}));return;}
  return handler(req,res);
 });
 const close=()=>new Promise(resolve=>{
  const finish=()=>{preview.service.close();resolve();};
  if(server.listening)server.close(finish);else finish();
 });
 return {server,service:preview.service,accountsFile:preview.accountsFile,origin:url.origin,port,close};
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
 const p=createLocalHTTPSPreview({database:process.env.CFP_P2_DB,origin:process.env.CFP_P2_PREVIEW_ORIGIN,revision:process.env.CFP_PREVIEW_REVISION,certificate:process.env.CFP_LOCAL_TLS_CERT,key:process.env.CFP_LOCAL_TLS_KEY});
 p.server.on('error',async()=>{await p.close();console.error('LOCAL_HTTPS_START_FAILED');process.exitCode=1;});
 p.server.listen(p.port,'127.0.0.1',()=>console.log(JSON.stringify({mode:'LOCAL SYNTHETIC PREVIEW / PRODUCTION NO-GO',url:p.origin+'/p2',revision:process.env.CFP_PREVIEW_REVISION,phoneReachability:'NOT AVAILABLE WITHOUT APPROVED FORWARDING',accountsFile:p.accountsFile,passwordsPrinted:false})));
 for(const signal of ['SIGTERM','SIGINT'])process.once(signal,async()=>{await p.close();process.exit(0);});
}
