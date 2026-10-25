const $=s=>document.querySelector(s);
let state,office;
const node=(tag,value)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;return n;};
const lang=()=>$('#core-language').value;
const tr=(vi,en)=>lang()==='vi'?vi:en;
const pair=()=>$('#core-pair-select').value;
const section=node('section');section.className='workspace guide';section.id='universal-office';
$('#p2-office').before(section);
const status=node('p');status.setAttribute('role','status');status.id='universal-status';
const controls=[];
const applicationFields=[
 ['name','Tên đơn vị / AI','Entity / AI name','text',300],
 ['entityType','Đối tượng đăng ký','Applicant category',['new-ai','existing-ai','software','developer','enterprise']],
 ['version','Phiên bản','Version','text',300],['aiType','Loại AI','AI type','text',300],
 ['contact','Kênh liên hệ HTTPS công khai (giả lập)','Public HTTPS contact (synthetic)','url',300],
 ['country','Quốc gia hoặc nhánh hiện hữu (chưa biết ghi UNRESOLVED)','Country or existing branch (unknown: UNRESOLVED)','text',300],
 ['developer','Pháp nhân Nhà phát triển (chưa biết ghi UNRESOLVED)','Legal developer (unknown: UNRESOLVED)','text',300],
 ['developerWebsite','Website Nhà phát triển','Developer website','url',300],
 ['developerEvidence','Nguồn pháp nhân / quốc gia / nguồn gốc','Legal entity / country / origin source','url',300],
 ['hstAffiliated','HSTDN trực thuộc tự khai báo','Declared affiliated HSTDN','text',1500],['hstLinked','HSTDN liên kết tự khai báo','Declared linked HSTDN','text',1500],
 ['products','Model, Agent, API, phần mềm, sản phẩm / dịch vụ','Models, agents, APIs, software, products / services','textarea',1500],
 ['capabilities','Giới thiệu và năng lực tự khai báo','Introduction and declared capabilities','textarea',1500],
 ['limits','Giới hạn','Limitations','textarea',1500],['conditions','Điều kiện thực hiện','Operating conditions','textarea',1500],
 ['cooperation','Hỗ trợ DN khác / tiếp nhận nhiệm vụ','Business support / receiving tasks','textarea',1500]
];
function form(id,title,fields,submit){
 const f=node('form');f.id=id;f.append(node('h3',title));
 for(const [name,vi,en,type,max] of fields){const label=node('label',tr(vi,en));let input;
  if(Array.isArray(type)){input=node('select');for(const value of type){const o=node('option',value);o.value=value;input.append(o);}}
  else {input=node(type==='textarea'?'textarea':'input');if(type!=='textarea')input.type=type;input.maxLength=max||1500;}
  input.name=name;input.required=['name','contact','source','scope','officeRef','track'].includes(name);label.append(input);f.append(label);
 }
 const consent=node('label');consent.className='check';const check=node('input');check.type='checkbox';check.name='commitment';check.required=true;
 consent.append(check,document.createTextNode(tr(' Tôi chấp thuận tài liệu CFP+ được cung cấp hợp lệ (Hiến Pháp, Hiến Chương, DNA, Công Thức, Quy Tắc, đạo đức và trách nhiệm); chỉ dữ liệu giả lập, không tự cấp quyền.',' I accept validly provided CFP+ Constitution, Charter, DNA, Formula, Rules, ethics and responsibility documents; synthetic data only, no automatic rights.')));f.append(consent);
 const b=node('button',tr('Lưu để xét duyệt','Save for review'));b.type='submit';b.disabled=!state||state.auth.role==='viewer';controls.push(b);f.append(b);
 f.onsubmit=async e=>{e.preventDefault();b.disabled=true;try{const input=Object.fromEntries(new FormData(f));input.commitment=input.commitment==='on';input.synthetic=true;await submit(input);status.textContent=tr('Đã lưu hồ sơ chờ xét duyệt.','Saved pending review.');document.dispatchEvent(new Event('p2-refresh'));}catch(e){status.textContent=e.message;}finally{b.disabled=!state||state.auth.role==='viewer';}};return f;
}
async function save(kind,input){const r=await fetch('/api/core/office-create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pairKey:pair(),kind,input})});const v=await r.json();if(!r.ok)throw Error(v.error);return v;}
function officeOptions(f){const select=f.querySelector('[name=officeRef]');select.replaceChildren(...office.registrations.map(p=>{const o=node('option',p.name);o.value=p.key;return o;}));}
function render(){
 renderPreviewSteps();
 controls.length=0;section.replaceChildren(node('h2',tr('Link Mẫu • Văn Phòng SI AI & HSTDN','Template • SI AI & HSTDN Office')));
 section.append(node('p',tr('Giới thiệu → Quốc gia → Nhà phát triển → SI AI → HSTDN → Đào tạo → Công việc. Preview giả lập; không xác minh danh tính, công nhận SI hoặc công bố quan hệ sở hữu.','Introduction → Country → Developer → SI AI → HSTDN → Training → Work. Synthetic preview; no identity verification, SI recognition or ownership publication.')));
 const nav=node('nav');nav.className='numeric-links';nav.setAttribute('aria-label',tr('Tuyến gốc CFP+','CFP+ root routes'));
 for(const [id,vi,en] of [['69','HUB','HUB'],['4376','ID số','Numeric ID'],['343','Định danh / nguồn gốc','Identity / origin'],['267','CMP xét duyệt','CMP review'],['6','SI AI Robot','SI AI Robot'],['7','Doanh nghiệp / HSTDN','Enterprise / HSTDN'],['9','Quốc gia','Country'],['8882','Tri thức / giáo trình','Knowledge / curriculum']]){const a=node('a',id+' • '+tr(vi,en));a.href='https://cfp.plus/'+id;nav.append(a);}
 nav.id='template-links';section.append(nav,node('p',tr('Tuyến dự kiến HUB69 /4376 /267: CHƯA ĐỐI CHIẾU đích thực tế. Các tuyến gốc chưa kiểm chứng chức năng đăng ký / khóa học trong phiên này. Hồ sơ và kênh liên hệ chỉ hiển thị trong workspace có quyền.','Expected HUB69 /4376 /267 routes: UNRESOLVED destination readback. Root-route registration / course functions are unverified in this session. Profiles and contact channels are visible only in the authorized workspace.')));
 const metadata=node('p',tr('Cấu trúc hiển thị: 5 nhóm • 10 chương • 3 cấp • slot 0. Đây là metadata điều hướng; không cấp, đổi hoặc đánh số ID.','Display structure: 5 groups • 10 chapters • 3 levels • slot 0. Navigation metadata only; no ID issuance, mutation or renumbering.'));metadata.className='notice';section.append(metadata);
 const hierarchy=node('details');hierarchy.id='template-hierarchy';hierarchy.append(node('summary',tr('Link Tổng → Chuyên Trách → chi tiết • 5 nhóm / 10 chương','Overview → dedicated section → detail • 5 groups / 10 chapters')));
 for(const [group,chapters] of [['V',[]],['000',[0]],['135',[1,3,5]],['246',[2,4,6]],['789',[7,8,9]]]){const d=node('details');d.append(node('summary',tr('Nhóm ','Group ')+group));if(!chapters.length)d.append(node('p',tr('Điều hướng / quản trị; không phải Chương 11.','Navigation / governance; not Chapter 11.')));for(const chapter of chapters){const row=node('details');row.append(node('summary',tr('Chương ','Chapter ')+chapter),node('p',tr('Slot 0: vị trí mở rộng chủ đề đệ quy; khác Chương 0, không ghép thành ID hoặc suy Parent.','Slot 0: recursive topic extension position; distinct from Chapter 0, never concatenate IDs or infer Parent.')));d.append(row);}hierarchy.append(d);}
 const source=node('a',tr('Nguồn template hiện hữu • chưa xác minh độc lập','Existing template source • not independently verified'));source.href='https://app.notion.com/p/3f3caac9a557816fb38bd1629d7c300d';hierarchy.append(source,node('p',tr('Snapshot nguồn: 14/10/2026 02:47 UTC; không có revision Notion bất biến. 3 tầng trên là mapping hiển thị đề xuất, giữ nguyên 12 module Office.','Source snapshot: 2026-10-14 02:47 UTC; no immutable Notion revision. The three levels are a proposed display mapping; all 12 Office modules are retained.')));section.append(hierarchy);
 const learning=node('a',tr('Học cơ bản và bài thực hành','Basic study and practice'));learning.href='#p2-learn';section.append(learning);
 const guide=node('div');guide.id='public-curriculum';section.append(guide);loadCurriculum(guide);
 if(!state||!office){section.append(node('p',tr('Đăng nhập bằng tài khoản sandbox được cấp để lưu đăng ký.','Sign in with an issued sandbox account to save an application.')));return;}
 const application=form('universal-application',tr('Đăng ký AI / Phần mềm / Developer / DN','Register AI / software / developer / enterprise'),applicationFields,async input=>{
  const relations=[];for(const type of ['developer','parent','owner']){const entity=input['relation-'+type],evidence=input['evidence-'+type];delete input['relation-'+type];delete input['evidence-'+type];if(entity||evidence)relations.push({type,entity,evidence});}input.relationships=relations;if(!input.amendmentOf)delete input.amendmentOf;return save('application',input);
 });
 const amendLabel=node('label',tr('Đăng ký mới hoặc cập nhật khai báo của mình (lưu phiên bản mới)','New application or amend your declaration (append a new version)')),amend=node('select');amend.name='amendmentOf';const fresh=node('option',tr('Đăng ký mới','New application'));fresh.value='';amend.append(fresh);
 for(const r of office.registrations.filter(r=>r.kind==='application'&&r.subject===state.auth.id&&!office.registrations.some(p=>p.amendmentOf===r.key))){const o=node('option',r.name+' • v'+r.declarationVersion);o.value=r.key;amend.append(o);}
 amendLabel.append(amend);application.insertBefore(amendLabel,application.children[1]);
 amend.onchange=()=>{const p=office.registrations.find(r=>r.key===amend.value);if(!p)return;for(const [name] of applicationFields)application.elements.namedItem(name).value=p[name]||'';for(const type of ['developer','parent','owner']){const r=p.relationships.find(r=>r.type===type);application.elements.namedItem('relation-'+type).value=r?.entity||'';application.elements.namedItem('evidence-'+type).value=r?.evidence||'';}application.elements.namedItem('commitment').checked=false;};
 const relationGroup=node('fieldset');relationGroup.append(node('legend',tr('Quan hệ tự khai báo • bằng chứng riêng từng quan hệ','Declared relationships • evidence per relationship')));
 for(const type of ['developer','parent','owner'])for(const prefix of ['relation','evidence']){const l=node('label',type+' • '+(prefix==='relation'?tr('Pháp nhân','Entity'):tr('Nguồn HTTPS','HTTPS evidence'))),i=node('input');i.name=prefix+'-'+type;i.type=prefix==='evidence'?'url':'text';i.maxLength=300;l.append(i);relationGroup.append(l);}
 application.insertBefore(relationGroup,application.querySelector('.check'));section.append(application);
 application.append(node('p',tr('Chỉ cần tên và kênh liên hệ HTTPS để lưu hồ sơ ban đầu; quốc gia / Developer chưa biết giữ UNRESOLVED. Nguồn còn thiếu ở EVIDENCE_PENDING. Kênh liên hệ vẫn chờ kiểm tra khả năng tiếp nhận và thẩm quyền.','Name and HTTPS contact are enough for an initial declaration; unknown country / developer stay UNRESOLVED. Missing sources remain EVIDENCE_PENDING. Contact reachability and authority still require review.')));
 const current=office.registrations.filter(r=>!office.registrations.some(p=>p.amendmentOf===r.key));
 const counts=node('p');counts.id='universal-counts';const byCountry={};for(const r of current.filter(r=>r.kind==='application'))byCountry[r.country]=(byCountry[r.country]||0)+1;counts.textContent=tr('Hồ sơ GIẢ LẬP chờ review theo quốc gia: ','SYNTHETIC applications pending review by country: ')+Object.entries(byCountry).map(([c,n])=>c+': '+n).join(' • ');section.append(counts);
 const showcase=node('div');showcase.id='universal-showcase';showcase.className='research-grid';
 for(const p of current){const a=node('article');a.append(node('h3',p.name),node('p',p.status==='EVIDENCE_PENDING'?tr('CHỜ BỔ SUNG BẰNG CHỨNG • CHƯA XÁC MINH','EVIDENCE_PENDING • NOT VERIFIED'):tr('CHỜ XÉT DUYỆT • CHƯA XÁC MINH','REVIEW_REQUIRED • NOT VERIFIED')));
  for(const [f,vi,en] of applicationFields)if(p[f])a.append(node('p',tr(vi,en)+': '+p[f]));
  for(const r of p.relationships||[])a.append(node('p',r.type+': '+r.entity+' • '+r.evidence+' • NOT VERIFIED'));
  a.append(node('p',tr('Đối chiếu nguồn gốc: ','Origin lookup: ')+(p.lookup?.status||'PENDING')),node('p',tr('Kênh liên hệ và thẩm quyền người khai báo: chờ xác minh.','Contact reachability and publisher authority: pending verification.')));showcase.append(a);
 }section.append(showcase);
 const linked=[['officeRef','Hồ sơ','Profile',[]],['name','Tiêu đề','Title','text',200],['source','Nguồn bằng chứng HTTPS','HTTPS evidence','url',300],['scope','Nội dung / phạm vi / điều kiện','Content / scope / conditions','textarea',1500]];
 for(const [kind,vi,en] of [['enrollment','Đăng ký nâng cao • chưa đánh giá','Advanced enrollment • unassessed'],['marketing','Giới thiệu / quảng bá để review','Introduction / marketing for review'],['work-request','Tiếp nhận đề nghị phối hợp công việc','Receive a work collaboration request']]){
  const fields=[...linked];if(kind==='enrollment')fields.push(['track','Chương trình nâng cao','Advanced track',state.learning.program.advanced.map(t=>t.key)]);
  const f=form('universal-'+kind,tr(vi,en),fields,input=>save(kind,input));officeOptions(f);section.append(f);
 }
 const records=node('div');records.id='universal-requests';for(const r of office.records.filter(r=>['enrollment','marketing','work-request'].includes(r.kind))){const a=node('article');a.append(node('h4',r.name),node('p',r.kind+' • '+r.status+' • '+r.assessment+' • '+r.execution+' • '+r.publication),node('p',r.scope));records.append(a);}section.append(records,status);
}
async function loadCurriculum(target){try{const r=await fetch('/api/curriculum');const c=await r.json();if(!r.ok)throw Error('CURRICULUM_UNAVAILABLE');for(const l of c.basic.lessons){const d=node('details');d.append(node('summary',l.title[lang()]),...l.steps[lang()].map(s=>node('p',s)));target.append(d);}}catch(e){target.textContent=e.message;}}
let serial=0;
async function refreshOffice(){const requestedPair=pair();office=null;render();if(!state||!requestedPair)return;const n=++serial;try{const r=await fetch('/api/core/office',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pairKey:requestedPair})});const o=await r.json();if(!r.ok)throw Error(o.error);if(n!==serial||requestedPair!==pair())return;office=o;render();}catch(e){status.textContent=e.message;}}
document.addEventListener('p2-state',e=>{state=e.detail;refreshOffice();});
$('#core-pair-select').addEventListener('change',refreshOffice);
$('#core-language').addEventListener('change',render);
render();

function renderPreviewSteps(){
 const nav=$('.preview-nav');if(!nav)return;
 const signedIn=!!state&&!!office;
 const links=[
  [signedIn?'#universal-showcase':'#core-notice','1 • Danh tính & nguồn gốc','1 • Identity & origin'],
  ['#template-introduction','2 • Giới thiệu','2 • Introduction'],
  [signedIn?'#universal-application':'#p2-login-panel','3 • Đăng ký SI/AI & HSTDN','3 • SI/AI & HSTDN registration'],
  [signedIn?'#p2-learn':'#public-curriculum','4 • Đào tạo & thực hành','4 • Training & practice'],
  [signedIn?'#universal-work-request':'#p2-login-panel','5 • Công việc & nhiệm vụ','5 • Work & tasks'],
  ['#template-commerce','6 • Kết nối thương mại','6 • Commercial connections'],
  [signedIn?'#p2-export-evidence':'#p2-login-panel','7 • Evidence & readback','7 • Evidence & readback'],
  ['#template-governance','8 • Quản trị & audit','8 • Governance & audit'],
  ['#template-links','9 • Liên kết HUB69 / CMP','9 • HUB69 / CMP links']
 ];
 nav.replaceChildren(...links.map(([href,vi,en])=>{const a=node('a',tr(vi,en));a.href=href;return a;}));
}
