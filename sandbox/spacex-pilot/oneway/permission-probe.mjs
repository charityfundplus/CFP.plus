import {writeFileSync,readFileSync} from 'node:fs';
try {writeFileSync(process.argv[2],'FORBIDDEN');console.error('SOURCE WRITE SUCCEEDED');process.exit(1);}
catch(e){if(e.code!=='ERR_ACCESS_DENIED')throw e;console.log(JSON.stringify({result:'DENIED',code:e.code,permission:e.permission,source:readFileSync(process.argv[2],'utf8')}));}
