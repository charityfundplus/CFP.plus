import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fiveStoreStatus} from '../core/store-status.mjs';
import {renderStoreTable} from '../scripts/render-hub69-stores.mjs';
test('five stores stay unverified without current receipt; mutable projections cannot upgrade state',()=>{
 const state=fiveStoreStatus();assert.deepEqual(state.stores.map(s=>s.name),['Notion','GitHub','Google','MCP','CMP']);
 for(const s of state.stores){assert.equal(s.syncVerified,false);assert.equal(s.syncStatus,'NOT VERIFIED');assert.equal(s.connected,false);assert.equal(s.readbackHash,null);assert.equal(s.syncEvidence,null);assert.equal(s.checkedAt,null);}
 state.stores[0].syncVerified=true;assert.equal(fiveStoreStatus().stores[0].syncVerified,false);assert.equal(state.allStoresSynced,false);
});
test('static HTML and downloadable JSON match runtime inventory with no JavaScript dependency',()=>{
 const html=readFileSync(new URL('../../../69/index.html',import.meta.url),'utf8'),json=JSON.parse(readFileSync(new URL('../../../69/store-status.json',import.meta.url)));
 assert.deepEqual(json,fiveStoreStatus());assert(html.includes(renderStoreTable()));assert.equal((renderStoreTable().match(/<tr>/g)||[]).length,6);assert(!renderStoreTable().includes('SYNC VERIFIED'));assert(!renderStoreTable().includes('app.notion.com'));assert(!renderStoreTable().includes('drive.google.com'));
 assert(html.includes('scope="col"'));assert(html.includes('scope="row"'));assert(html.includes('store-status.css'));
});
