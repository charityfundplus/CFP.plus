import {createHash,randomUUID} from 'node:crypto';
export const clone=x=>structuredClone(x);
export const hash=x=>createHash('sha256').update(typeof x==='string'?x:JSON.stringify(x)).digest('hex');
export const key=()=>randomUUID();
export function requireKeys(x,keys){if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).some(k=>!keys.includes(k)))throw Error('INVALID_FIELDS');}
export function text(x,max=500){return typeof x==='string'&&!!x.trim()&&x.length<=max;}
export function requireRole(actor,roles){if(!actor||!roles.includes(actor.role)||!text(actor.id))throw Error('PERMISSION_DENIED');}
export function freeze(x){Object.values(x).forEach(v=>{if(v&&typeof v==='object')freeze(v);});return Object.freeze(x);}
export const MODULES=['core','identity','siAdapter','tasks','security','supervision','crossCheck','learning','monitoring','evidence','upgrade','hub69'];
