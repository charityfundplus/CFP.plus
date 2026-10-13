import entities from './ai-entity-registry.json' with {type:'json'};
import routes from './country-route-map.json' with {type:'json'};
export const modules = ['Danh Tính & Lineage','Giới Thiệu & Năng Lực','Danh Mục Sản Phẩm','Danh Mục Dịch Vụ','Quảng Cáo & Tiếp Thị','Khách Hàng & CRM','Thương Mại & Thanh Toán','HSTDN & Đối Tác','Văn Phòng & Công Việc','SI AI • API • MCP','Quản Trị • Đạo Đức • Bảo Mật','Báo Cáo • Evidence • KPI'];
export const registry = {entities:Object.values(entities).filter(x=>x.id),countries:Object.entries(routes).map(([id,x])=>({id,...x})),blockedCountries:['6911'],sourceCommit:'835616308111f6851c0387fa9f5eda60c9ffa624'};
export function validateRegistration(x){
 const keys=['name','country','developer','source','synthetic'];
 if(!x || Object.keys(x).some(k=>!keys.includes(k))) throw Error('Không được cấp hoặc thay đổi ID / DID / Parent / Canonical.');
 if(x.synthetic!==true) throw Error('Chỉ dữ liệu giả lập.');
 for(const k of ['name','country','developer','source']) if(typeof x[k]!=='string'||!x[k].trim()||x[k].length>300) throw Error('Thiếu hoặc sai trường '+k);
 const country=registry.countries.find(c=>c.id===x.country), developer=registry.entities.find(e=>e.id===x.developer&&e.type==='developer');
 if(!country||!developer||developer.ai_country_id!==country.id) throw Error('Country → Developer không khớp Registry.');
 if(registry.blockedCountries.includes(country.id)) throw Error('CONFLICT: mapping HUB69 và Registry khác nhau; cần Human Governance.');
 if(!safeURL(x.source)) throw Error('Nguồn phải là HTTPS công khai.');
 return {...x,id:null,did:null,canonical:null,status:'REVIEW CANDIDATE'};
}
export function safeURL(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!/^(localhost|.*\.local|127\..*|10\..*|192\.168\..*|172\.(1[6-9]|2\d|3[01])\..*|\[.*\])$/.test(u.hostname);}catch{return false;}}
export function createState(){return {records:modules.map((name,i)=>({key:'sample-'+i,module:i,title:'Mẫu • '+name,status:'DRAFT',evidence:'',synthetic:true})),registrations:[],audit:[]};}
export function authorize(role,action){return action==='read'||(action==='write'&&['editor','reviewer'].includes(role))||(action==='review'&&role==='reviewer');}
export function transition(record,action,evidence){if(action==='submit'&&record.status==='DRAFT')return 'UNDER REVIEW';if(action==='review'&&record.status==='UNDER REVIEW'&&safeURL(evidence))return 'DEMO REVIEWED';throw Error('Chuyển trạng thái không hợp lệ hoặc thiếu Evidence HTTPS.');}
