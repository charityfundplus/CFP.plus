import https from 'node:https';
import {readFileSync,writeFileSync} from 'node:fs';
import {randomBytes} from 'node:crypto';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
const service=new P2Sandbox(process.env.CFP_FLOW_DB),accounts=['editor','reviewer','viewer'].map(role=>({id:'flow-'+role,role,workspace:'flow-qa',pairs:['*'],password:randomBytes(18).toString('base64url')}));
for(const account of accounts)service.provision(account);
writeFileSync(process.env.CFP_FLOW_ACCOUNTS,JSON.stringify(accounts),{mode:0o600,flag:'wx'});
const origin='https://localhost:4215',http=createP2HTTP({service,previewOrigin:origin});
// No pinned-revision header for an uncommitted QA candidate.
const server=https.createServer({cert:readFileSync(process.env.CFP_FLOW_CERT),key:readFileSync(process.env.CFP_FLOW_KEY)},http.listeners('request')[0]);
server.listen(4215,'127.0.0.1');
process.on('SIGTERM',()=>server.close(()=>{service.close();process.exit(0);}));
