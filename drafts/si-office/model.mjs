import entities from './ai-entity-registry.json' with {type:'json'};
import routes from './country-route-map.json' with {type:'json'};
export const modules = ['Danh Tính & Lineage','Giới Thiệu & Năng Lực','Danh Mục Sản Phẩm','Danh Mục Dịch Vụ','Quảng Cáo & Tiếp Thị','Khách Hàng & CRM','Thương Mại & Thanh Toán','HSTDN & Đối Tác','Văn Phòng & Công Việc','SI AI • API • MCP','Quản Trị • Đạo Đức • Bảo Mật','Báo Cáo • Evidence • KPI'];
export const registry = {entities:Object.values(entities).filter(x=>x.id),countries:Object.entries(routes).map(([id,x])=>({id,...x})),blockedCountries:['6911'],sourceCommit:'835616308111f6851c0387fa9f5eda60c9ffa624'};
export function validateRegistration(x){
 const keys=['name','country','developer','source','synthetic','identityEvidence'];
 if(!x || Object.keys(x).some(k=>!keys.includes(k))) throw Error('Không được cấp hoặc thay đổi ID / DID / Parent / Canonical.');
 if(x.synthetic!==true) throw Error('Chỉ dữ liệu giả lập.');
 for(const k of ['name','country','developer','source']) if(typeof x[k]!=='string'||!x[k].trim()||x[k].length>300) throw Error('Thiếu hoặc sai trường '+k);
 const country=registry.countries.find(c=>c.id===x.country), developer=registry.entities.find(e=>e.id===x.developer&&e.type==='developer');
 if(!country||!developer||developer.ai_country_id!==country.id) throw Error('Country → Developer không khớp Registry.');
 if(registry.blockedCountries.includes(country.id)) throw Error('CONFLICT: mapping HUB69 và Registry khác nhau; cần Human Governance.');
 if(!safeURL(x.identityEvidence))throw Error('IDENTITY_EVIDENCE: public HTTPS required');
 if(!safeURL(x.source)) throw Error('Nguồn phải là HTTPS công khai.');
 return {...x,parent:null,id:null,did:null,canonical:null,status:'REVIEW CANDIDATE',sourceVerification:'NOT VERIFIED',capabilityVerification:'NOT VERIFIED',legalRelationshipVerification:'NOT VERIFIED'};
}
export function safeURL(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!/^(localhost|.*\.local|127\..*|10\..*|192\.168\..*|172\.(1[6-9]|2\d|3[01])\..*|\[.*\])$/.test(u.hostname);}catch{return false;}}
export function createState(){return {records:modules.map((name,i)=>({key:'sample-'+i,module:i,title:'Mẫu • '+name,status:'DRAFT',evidence:'',synthetic:true})),registrations:[],proposals:[],hstdn:[],audit:[]};}
export function authorize(role,action){return action==='read'||(action==='write'&&['editor','reviewer'].includes(role))||(action==='review'&&role==='reviewer');}
export function transition(record,action,evidence){if(action==='submit'&&record.status==='DRAFT')return 'UNDER REVIEW';if(action==='review'&&record.status==='UNDER REVIEW'&&safeURL(evidence))return 'DEMO REVIEWED';throw Error('Chuyển trạng thái không hợp lệ hoặc thiếu Evidence HTTPS.');}
export function validateHSTDN(x,state){
 const allowed=['name','jurisdiction','members','relation_type','source','synthetic'];
 if(!x||Object.keys(x).some(k=>!allowed.includes(k))||x.synthetic!==true)throw Error('SYNTHETIC_ONLY: invalid HSTDN fields');
 for(const k of ['name','jurisdiction'])if(typeof x[k]!=='string'||!x[k].trim()||x[k].length>300)throw Error('HSTDN: missing '+k);
 if(!Array.isArray(x.members)||!x.members.length||x.members.length>20||new Set(x.members).size!==x.members.length||x.members.some(k=>typeof k!=='string'||!state.registrations.some(r=>r.key===k)))throw Error('HSTDN: unknown or duplicate member');
 if(!['proposed-collaboration','research-reference','legal-parent-claim'].includes(x.relation_type)||!safeURL(x.source))throw Error('HSTDN: invalid relation/source');
 if(state.hstdn.some(r=>r.name.trim().toLocaleLowerCase()===x.name.trim().toLocaleLowerCase()))throw Error('DUPLICATE: HSTDN name already proposed');
 return {...x,id:null,parent:null,did:null,canonical:null,status:'REVIEW CANDIDATE',sourceVerification:'NOT VERIFIED',capabilityVerification:'NOT VERIFIED',legalRelationshipVerification:'NOT VERIFIED'};
}
export function validateProposal(x,state){
 const allowed=['type','name','countryRef','source','identityEvidence','synthetic'];
 if(!x||Object.keys(x).some(k=>!allowed.includes(k))||!['country','developer'].includes(x.type)||x.synthetic!==true||typeof x.name!=='string'||!x.name.trim()||x.name.length>300||!safeURL(x.source)||!safeURL(x.identityEvidence))throw Error('PROPOSAL: synthetic name/source/identity evidence required');
 if(x.type==='developer'&&!registry.countries.some(c=>c.id===x.countryRef)&&!state.proposals.some(p=>p.type==='country'&&p.key===x.countryRef))throw Error('PROPOSAL: unknown country reference');
 if(x.type==='country'&&x.countryRef)throw Error('PROPOSAL: country cannot declare parent');
 if(state.proposals.some(p=>p.type===x.type&&p.name.trim().toLocaleLowerCase()===x.name.trim().toLocaleLowerCase()))throw Error('DUPLICATE: proposal already exists');
 return {...x,id:null,parent:null,did:null,canonical:null,status:'REVIEW CANDIDATE',sourceVerification:'NOT VERIFIED',capabilityVerification:'NOT VERIFIED',legalRelationshipVerification:'NOT VERIFIED'};
}
