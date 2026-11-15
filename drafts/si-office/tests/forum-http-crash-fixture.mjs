import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
const service=new P2Sandbox(':memory:');
const server=createP2HTTP({service});
server.listen(0,'127.0.0.1',()=>console.log(server.address().port));
process.on('SIGTERM',()=>server.close(()=>{service.close();process.exit(0);}));
