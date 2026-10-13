import {clone} from './common.mjs';
export class MonitoringRecovery {
 #alerts=[];#controllers=new Map();
 attach(pairKey,controller){this.#controllers.set(pairKey,controller);}
 detach(pairKey){this.#controllers.delete(pairKey);}
 stop(pair,tasks,reason='HUMAN_SAFE_STOP'){pair.epoch++;pair.status='STOPPED';pair.stopReason=reason;this.#controllers.get(pair.config.key)?.abort();tasks.interrupt(pair.config.key);this.alert(pair.config.key,reason);}
 alert(pairKey,reason){this.#alerts.push({pairKey,reason,time:new Date().toISOString(),status:'OPEN'});}
 recover(pair){if(pair.status!=='STOPPED'||pair.busy)throw Error('RECOVERY_REQUIRES_STOPPED_QUIESCENT_PAIR');pair.status='READY';pair.stopReason=null;pair.epoch++;for(const a of this.#alerts)if(a.pairKey===pair.config.key&&a.status==='OPEN')a.status='ACKNOWLEDGED';return 'RECOVERED; interrupted tasks retained, explicit retry required';}
 alerts(){return clone(this.#alerts);}
}
