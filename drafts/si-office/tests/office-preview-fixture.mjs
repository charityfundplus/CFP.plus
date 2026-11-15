import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
import {createLocalHTTPSPreview} from '../scripts/local-https-preview.mjs';
const tls=process.env.CFP_OFFICE_QA_TLS==='1';
const preview=tls?createLocalHTTPSPreview({database:process.env.CFP_P2_DB,origin:'https://localhost:4193',revision:'2814b357d8b31385aff530ca37eb8606674b608e',certificate:process.env.CFP_LOCAL_TLS_CERT,key:process.env.CFP_LOCAL_TLS_KEY}):null;
const s=preview?.service||new P2Sandbox(process.env.CFP_P2_DB);
for(const [id,role,workspace] of [['editor','editor','alpha'],['reviewer','reviewer','alpha'],['viewer','viewer','alpha'],['outsider','editor','beta']])s.provision({id,password:'Synthetic-office-browser',role,workspace,pairs:['hub69-content-demo']});
const server=preview?.server||createP2HTTP({service:s});server.listen(4193,'127.0.0.1');
process.on('SIGTERM',()=>server.close(()=>{s.close();process.exit(0);}));
