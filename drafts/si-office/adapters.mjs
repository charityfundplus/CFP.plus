import {providers} from './public/office-contracts.js';
export function executeMock(request){
 if(!request||Object.keys(request).some(k=>!['provider','action','synthetic'].includes(k))||!providers.includes(request.provider)||request.action!=='read-synthetic'||request.synthetic!==true)throw Error('MOCK_ONLY: provider/action/synthetic invalid; no credentials allowed');
 return {provider:request.provider,adapter:'mock',version:'1',operation:'read-synthetic',sourceVerified:false,capabilityVerified:false,legalRelationshipVerified:false,connected:false,externalRequests:0,records:[{name:'Synthetic resource',status:'DRAFT'}],limitations:['No external READ/WRITE','No OAuth credentials','No production synchronization','No reverse write or cascade delete']};
}
