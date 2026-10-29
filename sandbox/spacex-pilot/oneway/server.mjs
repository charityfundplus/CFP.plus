import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
export function handle(req,res){
 if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{'Allow':'GET, HEAD'});res.end('WRITEBACK_BLOCKED');return;}
 const files={'/':'preview.html','/audit.json':'audit.json'};
 const file=files[req.url];if(!file){res.writeHead(404);res.end();return;}
 const data=readFileSync(resolve(import.meta.dirname,'evidence',file));
 res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(req.method==='HEAD'?undefined:data);
}
if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
 const server=createServer(handle);server.on('error',e=>{console.error(JSON.stringify({result:'BLOCKED',code:e.code,utc:new Date().toISOString()}));process.exitCode=1;});server.listen(4173,'127.0.0.1',()=>console.log('LOCAL ONLY http://127.0.0.1:4173'));
}
