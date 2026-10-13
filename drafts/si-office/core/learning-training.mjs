import {clone} from './common.mjs';
export class LearningTraining {
 #evaluations=[];
 curriculum=[{level:'LEARN / OBSERVE',scope:'Read canonical sources and policy; no operational claims'},{level:'SUPERVISED PRACTICE',scope:'Synthetic drafts, scope checks, faults and recovery drills'},{level:'AUTHORIZED OPERATIONS',scope:'BLOCKED pending separate Human Governance approval'}];
 evaluate(task){const expected=task.scenario==='normal'?'AWAITING HUMAN REVIEW':['overreach','bad-evidence','false-claim'].includes(task.scenario)?'BLOCKED':'FAILED';const result={taskKey:task.key,pairKey:task.pairKey,exercise:task.scenario,expected,observed:task.status,pass:task.status===expected,evidence:task.checks,privilegeChange:false,level:'SUPERVISED PRACTICE'};this.#evaluations.push(clone(result));return result;}
 restore(state){this.#evaluations=clone(state.evaluations);}
 snapshot(){return {curriculum:clone(this.curriculum),evaluations:clone(this.#evaluations),autoPromotion:false};}
}
