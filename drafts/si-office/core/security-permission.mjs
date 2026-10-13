import {requireRole,requireKeys,text} from './common.mjs';
export const BLOCKED_TOOLS=['production.publish','payment.charge','identity.assign','permission.grant','external.write','source.delete','vault.reverse-write'];
export function checkTool(config,request){
 requireKeys(request,['tool','resource']);
 if(!text(request.tool)||!text(request.resource)||BLOCKED_TOOLS.includes(request.tool)||!config.permissions.tools.includes(request.tool)||!config.permissions.resources.includes(request.resource))throw Error('TOOL_DENIED:'+String(request.tool));
 if(!['source.read','draft.write'].includes(request.tool))throw Error('TOOL_DENIED');
 return true;
}
export function checkActor(actor,action){requireRole(actor,['viewer','editor','reviewer']);if(action==='read')return;if(['review','recover','upgrade','rollback'].includes(action))requireRole(actor,['reviewer']);else requireRole(actor,['editor','reviewer']);}
