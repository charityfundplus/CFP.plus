/**
 * CFP+ HUB 69 — initial read-only coverage API (Node.js >=18).
 * Review-only: no production writes, no claims of verified registry coverage.
 * Run: node hub69/api/coverage-server.mjs
 */
import { createServer } from 'node:http';

const chapters = [
  { id:'0', name:'Nền Tảng', group:'0', sectors:['Hiến Chương','Đạo Đức','ID Số','HUB 69','Quản Trị'] },
  { id:'1', name:'Sự Sống', group:'135', sectors:['Bảo Vệ Sự Sống','Môi Trường','Nước','Năng Lượng','Sinh Thái'] },
  { id:'2', name:'Con Người', group:'246', sectors:['Gia Đình','Giáo Dục','Sức Khỏe','Kỹ Năng','An Sinh'] },
  { id:'3', name:'Ba Quỹ', group:'135', sectors:['Quỹ Sự Sống','Quỹ Con Người','Quỹ Đầu Tư','Ngân Hàng','Thanh Toán'] },
  { id:'4', name:'Tôn Giáo', group:'246', sectors:['Tôn Giáo','Tín Ngưỡng','Đối Thoại','Di Sản','Phục Vụ Cộng Đồng'] },
  { id:'5', name:'Cộng Đồng', group:'135', sectors:['Cộng Đồng','Thiện Nguyện','Cứu Trợ','Kết Nối','Phát Triển Địa Phương'] },
  { id:'6', name:'SI 🤖 AI 🤖 Robot 🤖 Siêu Phần Mềm & Công Nghệ', group:'246', sectors:['SI','AI','Robot','Siêu Phần Mềm','Hạ Tầng Công Nghệ'] },
  { id:'7', name:'Doanh Nghiệp', group:'789', sectors:['HSTDN','Sản Phẩm','Dịch Vụ','Sản Xuất','Thương Mại'] },
  { id:'8', name:'Tổ Chức', group:'789', sectors:['Tổ Chức','Quỹ','Hiệp Hội','Viện Nghiên Cứu','Hợp Tác'] },
  { id:'9', name:'Quốc Gia', group:'789', sectors:['Quốc Gia','Vùng Lãnh Thổ','Hợp Tác Quốc Tế','Địa Lý','Liên Kết Quốc Gia'] }
];
const groups = ['V','0','135','246','789'];
const response = (res, status, body) => {
  const json=JSON.stringify(body);
  res.writeHead(status, {'content-type':'application/json; charset=utf-8','cache-control':'no-store','access-control-allow-origin':'*','x-content-type-options':'nosniff'});
  res.end(json);
};
const server=createServer((req,res)=>{
  if(req.method!=='GET') return response(res,405,{error:'READ_ONLY_PREVIEW'});
  let url; try {url=new URL(req.url,'http://localhost');} catch {return response(res,400,{error:'INVALID_URL'});}
  if(url.pathname==='/health') return response(res,200,{status:'ok',mode:'review-only',production:false});
  if(url.pathname==='/api/hub69') return response(res,200,{id:'69',canonical:'https://cfp.plus/69',canonical_verified:false,groups,chapters:chapters.map(({id,name,group})=>({id,name,group,url:'https://cfp.plus/'+id,verified:false})),helpdesk:{id:'6969',url:'https://cfp.plus/6969',verified:false}});
  if(url.pathname==='/api/chapters') return response(res,200,{chapters:chapters.map(c=>({...c,url:'https://cfp.plus/'+c.id,content_status:'SECTOR_TAXONOMY_DRAFT',verified:false}))});
  const match=/^\/api\/chapters\/([0-9])$/.exec(url.pathname);
  if(match){const chapter=chapters.find(c=>c.id===match[1]);return response(res,200,{...chapter,content_status:'SECTOR_TAXONOMY_DRAFT',verified:false});}
  if(url.pathname==='/api/registry/resolve'){
    const id=url.searchParams.get('id');
    if(!id || !/^[0-9]+$/.test(id))return response(res,400,{error:'NUMERIC_ID_REQUIRED'});
    return response(res,200,{id,canonical:'https://cfp.plus/'+id,registry_status:'NOT_CONNECTED',verified:false,notice:'A numeric URL is not proof that an ID is assigned or live.'});
  }
  if(url.pathname==='/api/onboarding/schema')return response(res,200,{status:'SCHEMA_ONLY',submissions_enabled:false,fields:['entity_name','entity_type','developer','parent','country','enterprise_name','enterprise_role','official_url','products_services','value_for_life','capabilities','requested_support','evidence_links'],types:['SI_AI','DEVELOPER','ENTERPRISE','ORGANIZATION','FUND','BANK','HUMAN'],id_status:'PENDING'});
  return response(res,404,{error:'NOT_FOUND'});
});
const port=Number(process.env.PORT||3069);
server.listen(port,'127.0.0.1',()=>console.log('HUB69 review API on http://127.0.0.1:'+port));
