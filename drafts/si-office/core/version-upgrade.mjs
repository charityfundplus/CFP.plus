import {MODULES,clone,freeze} from './common.mjs';
const releases=freeze({'0.1.0-sandbox':{api:1,health:true},'0.1.1-sandbox':{api:1,health:true},'0.1.2-fault-sandbox':{api:1,health:false},'0.2.0-incompatible':{api:2,health:true}});
export class VersionUpgrade {
 version='0.1.0-sandbox';history=[];
 preflight(pairs,tasks){if(pairs.some(p=>p.busy||tasks.pending(p.config.key)))throw Error('UPGRADE_REQUIRES_QUIESCENCE');}
 apply(target,pairs,tasks){this.preflight(pairs,tasks);const r=releases[target];if(!r||r.api!==1)throw Error('INCOMPATIBLE_OR_UNTRUSTED_RELEASE');if(target===this.version)throw Error('VERSION_ALREADY_CURRENT');const before=this.version;if(!r.health)throw Error('UPGRADE_HEALTH_FAILURE; previous cohort unchanged');this.version=target;for(const p of pairs)p.modules=Object.fromEntries(MODULES.map(k=>[k,target]));this.history.push({from:before,to:target,time:new Date().toISOString(),kind:'upgrade'});return this.snapshot();}
 rollback(pairs,tasks){this.preflight(pairs,tasks);const last=this.history.findLast(x=>x.kind==='upgrade'&&x.to===this.version);if(!last)throw Error('NO_ROLLBACK_CHECKPOINT');const from=this.version;this.version=last.from;for(const p of pairs)p.modules=Object.fromEntries(MODULES.map(k=>[k,this.version]));this.history.push({from,to:this.version,time:new Date().toISOString(),kind:'rollback'});return this.snapshot();}
 snapshot(){return {version:this.version,api:1,history:clone(this.history),releaseMode:'Built-in sandbox release metadata; no executable code downloaded',available:Object.keys(releases)};}
}
