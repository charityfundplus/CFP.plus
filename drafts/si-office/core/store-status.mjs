import plan from '../configs/five-store-status.json' with {type:'json'};
// Read-only inventory. No live adapter or receipt verifier exists here.
// Imported claims, historical archive receipts and connectivity never grant sync.
export function fiveStoreStatus() {
 return {schemaVersion:1,scope:'SYNC_FIVE_STORES_PLAN',sourceRevision:plan.sourceRevision,
  activationAllowed:false,allStoresSynced:false,externalCalls:0,
  stores:plan.stores.map((s,i)=>({...structuredClone(s),slot:i+1,protocol:1,
   status:'DISCONNECTED / MISSING EVIDENCE',syncStatus:'NOT VERIFIED',
   connected:false,readOnly:true,externalCalls:0,syncVerified:false,
   sourceHash:null,readbackHash:null,syncEvidence:null}))};
}
