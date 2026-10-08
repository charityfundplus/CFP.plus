"""Build public assets from existing source; never assign IDs or infer lineage."""
import argparse, hashlib, html, json, re, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSETS={'.html','.css','.js','.png','.jpg','.jpeg','.svg','.webp','.ico','.woff','.woff2'}
PUBLIC_DIRS={'V','ai','cmp','foundation','hub69','id','website'}
REGISTRY_FILES={'ai-entity-registry.json','country-route-map.json','global-country-ai-index.json'}
def build(destination):
 destination=Path(destination).resolve()
 if destination==ROOT or ROOT in destination.parents:raise ValueError('Output must be outside source tree')
 destination.mkdir(parents=True,exist_ok=False)
 for source in ROOT.iterdir():
  if source.is_file() and (source.suffix in ASSETS or source.name in {'robots.txt','sitemap.xml'}):shutil.copy2(source,destination/source.name)
  elif source.is_dir() and (re.fullmatch('[0-9]+',source.name) or source.name in PUBLIC_DIRS):
   for asset in source.rglob('*'):
    if asset.is_file() and asset.suffix in ASSETS:
     target=destination/asset.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(asset,target)
 (destination/'registry').mkdir()
 for name in REGISTRY_FILES:shutil.copy2(ROOT/'registry'/name,destination/'registry'/name)
 entities=json.loads((ROOT/'registry/ai-entity-registry.json').read_text())
 countries={str(x['ai_country_id']):x for x in json.loads((ROOT/'registry/global-country-ai-index.json').read_text()) if x.get('ai_country_id')}
 for key,value in json.loads((ROOT/'registry/country-route-map.json').read_text()).items():
  if re.fullmatch('[0-9]+',key):countries[key]={**countries.get(key,{}),**value}
 bindings={key:(value,'registry/global-country-ai-index.json + registry/country-route-map.json') for key,value in countries.items()}
 # Preserve Country identity separately from its explicitly configured AI-directory ID.
 # The legacy Country redirect incorrectly substituted the latter for the former.
 for ai_key,value in countries.items():
  country_key=str(value.get('country_id') or '')
  if re.fullmatch('[0-9]+',country_key):
   country_record={**value,'type':'COUNTRY','related_ai_directory_id':ai_key}
   if country_key in bindings and bindings[country_key][0].get('name')!=value.get('name'):
    raise ValueError('Competing Country binding: '+country_key)
   bindings[country_key]=(country_record,'registry/global-country-ai-index.json country_id / country-route-map.json')
 for key,value in entities.items():
  if not re.fullmatch('[0-9]+',key):continue
  if value.get('id')!=key or not value.get('name'):raise ValueError('Invalid binding: '+key)
  if key in bindings and bindings[key][0].get('name')!=value['name']:raise ValueError('Competing binding: '+key)
  bindings[key]=(value,'registry/ai-entity-registry.json')
 rows=[];esc=lambda value:html.escape(str(value))
 for key,(record,source) in bindings.items():
  if key=='691141':continue
  if not record.get('name'):raise ValueError('Missing name: '+key)
  parent=record.get('parent_id')
  if parent and not re.fullmatch('[0-9]+',str(parent)):raise ValueError('Invalid Parent: '+key)
  children=[(child,value) for child,(value,_) in bindings.items() if value.get('parent_id')==key and child!='691141']
  status=record.get('status') or record.get('directory_status') or record.get('coverage') or 'PENDING / HUMAN REVIEW'
  relations='<p>Parent: '+(esc(parent) if parent else 'UNKNOWN — không suy diễn từ prefix hoặc Country context')+'</p>'
  if record.get('related_ai_directory_id'):
   relations+='<p>AI directory context: <a href="/'+record['related_ai_directory_id']+'">'+record['related_ai_directory_id']+'</a>. Country identity ≠ AI directory identity; không redirect hoặc gộp entity.</p>'
  if children:relations+='<ul>'+''.join('<li><a href="/'+child+'">'+esc(value['name'])+' • '+child+'</a></li>' for child,value in children)+'</ul>'
  body='<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+key+' • '+esc(record['name'])+' • CFP+</title><link rel="canonical" href="https://cfp.plus/'+key+'"><link rel="stylesheet" href="/styles.css"><style>main{max-width:1000px;margin:auto;padding:20px;overflow-wrap:anywhere}</style></head><body><main><nav><a href="/69">HUB 69</a> • <a href="/6">AI &amp; Công Nghệ</a> • <a href="/9">Quốc Gia</a></nav><h1>'+key+' • '+esc(record['name'])+'</h1><p>'+esc(record.get('intro') or 'Danh mục quốc gia theo cấu hình nguồn; dữ liệu hồ sơ và Evidence vận hành còn chờ kiểm chứng.')+'</p><p>Nội dung chuyên sâu: ĐANG HOÀN THIỆN; chỉ dùng dữ liệu đã có trong nguồn, không giả mạo hồ sơ đầy đủ.</p><p>Record Type: '+esc(record.get('type') or 'COUNTRY DIRECTORY CONTEXT')+'</p><p>Source status: '+esc(status)+'</p><section><h2>Quan hệ từ Registry</h2>'+relations+'</section><section><h2>Evidence và quản trị</h2><p>Source: '+esc(source)+' • ID '+key+'</p><p>Publication: REVIEW CANDIDATE. Registry reference ≠ VERIFIED; Link ≠ CONNECTED. Không chứng minh executor, permissions hoặc ACTIVE. Canonical Lock: NO.</p></section></main></body></html>\n'
  target=destination/key/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body)
  rows.append({'id':key,'name':record['name'],'source':source,'status':status,'parent':parent,'content_status':'SOURCE INTRO AVAILABLE' if record.get('intro') else 'INCOMPLETE CONTENT','assignment_status':'SOURCE REFERENCE — NOT INDEPENDENTLY VERIFIED','acceptance':'PENDING EVIDENCE'})
 # Reuse the observed Backend baseline through a versioned, read-only source snapshot.
 # Existing P0 IDs must not 404 merely because their Full Name/content is PENDING.
 snapshot=json.loads((ROOT/'content/backend-p0-source.json').read_text())
 if hashlib.sha256(snapshot['raw_json'].encode()).hexdigest()!=snapshot['source_sha256']:
  raise ValueError('Backend source snapshot integrity mismatch')
 seen=set()
 for pair in json.loads(snapshot['raw_json']):
  key=pair['id']
  if not re.fullmatch('[0-9]+',key) or key in seen or pair.get('canonical_locked'):
   raise ValueError('Invalid/duplicate/protected Backend snapshot ID: '+key)
  seen.add(key)
  if key in bindings:
   raise ValueError('Backend ID competes with Website directory binding: '+key)
  sections=[]
  for kind in ['ai','software']:
   entity=pair[kind]
   if entity['entity_type']!=kind:raise ValueError('Merged/mismatched entity: '+key)
   sections.append('<section data-entity-type="'+kind+'"><h2>'+('AI Record' if kind=='ai' else 'Software Record')+'</h2><p>Full Name: '+esc(entity.get('full_name') or 'PENDING — chưa xác nhận Full Name')+'</p><p>Alias: '+esc(', '.join(entity.get('aliases',[])) or 'PENDING')+'</p><p>Status: '+esc(entity['status'])+'</p><p>Permissions nguồn: '+esc(', '.join(entity.get('permissions',[])) or 'NONE / FAIL CLOSED')+'</p><p>Evidence records: '+str(len(entity.get('evidence',[])))+' • Readback records: '+str(len(entity.get('readback',[])))+'</p></section>')
  detail='<section><h2>Backend source readback</h2><p>Source: '+esc(snapshot['source_repository'])+' / '+snapshot['source_path']+' @'+snapshot['source_head']+'</p><p>AI ≠ Software. Nội dung nghiệp vụ: ĐANG HOÀN THIỆN. Snapshot ≠ live Backend connection; không cấp quyền, bind Parent hoặc nâng trạng thái.</p>'+''.join(sections)+'</section>'
  target=destination/key/'index.html'
  # Preserve current Human editorial pages; add independent source record detail.
  standard_content=json.loads((ROOT/'content/site-standard.json').read_text())
  if key in standard_content['pages'] or key in standard_content.get('foundations',{}):
   text=target.read_text();target.write_text(text.replace('</main>',detail+'</main>',1))
  else:
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_text('<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+key+' • Full Name PENDING • CFP+</title><link rel="canonical" href="https://cfp.plus/'+key+'"><link rel="stylesheet" href="/styles.css"></head><body><main><h1>'+key+' • Full Name PENDING</h1><p>ID có trong Backend P0. Không tạo lại ID; tên và nội dung đang hoàn thiện theo nguồn. Parent/Child: UNKNOWN — không suy diễn.</p>'+detail+'<p>Source SHA256: '+snapshot['source_sha256']+' • Canonical Lock: NO • Publication: REVIEW CANDIDATE</p><a href="/69">HUB 69</a></main></body></html>')
  rows.append({'id':key,'name':pair.get('display_name'),'source':snapshot['source_repository']+'@'+snapshot['source_head']+':'+snapshot['source_path'],'status':'BACKEND SOURCE RECORD / NO PROMOTION','parent':None,'content_status':'INCOMPLETE CONTENT','assignment_status':'HUMAN P0 ID LIST / LOCAL BACKEND SOURCE; NO NEW ASSIGNMENT','acceptance':'PENDING EVIDENCE'})
 # Human-provided foundation navigation, not new Registry assignments or Parent claims.
 standard=json.loads((ROOT/'content/site-standard.json').read_text())
 groups=['V','000','135','246','789']
 chapter_links=' '.join('<a href="/'+str(i)+'">'+str(i)+' • '+esc(name)+'</a>' for i,name in enumerate(standard['chapter_names']))
 group_links=' '.join('<a href="/'+group+'">'+group+'</a>' for group in groups)
 navigation='<nav aria-label="5 Nhóm • 10 Chương"><p>5 Nhóm: '+group_links+'</p><p>10 Chương: '+chapter_links+'</p><p>Điều hướng không tự xác nhận Parent/Child hoặc quyền hạn.</p></nav>'
 for group in ['V','135','246','789']:
  target=destination/group/'index.html'
  if not target.exists():
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_text('<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+group+' • Nhóm CFP+</title><link rel="stylesheet" href="/styles.css"></head><body><main><h1>'+group+' • Nhóm CFP+</h1><p>Nhóm trong khung 5 Nhóm do Human Governance cung cấp: V • 000 • 135 • 246 • 789.</p><p>Nội dung nghiệp vụ chuyên sâu: đang hoàn thiện theo nguồn chuẩn. Không tự đặt tên, cấp ID hoặc suy diễn Parent.</p>'+navigation+'<p>Source: Human Website Work Order 2026-10-08 • HUMAN PROVIDED / PENDING REVIEW • Canonical Lock: NO</p><a href="/69">HUB 69</a></main></body></html>')
 for key in ['000','69',*(str(i) for i in range(10))]:
  target=destination/key/'index.html'
  text=target.read_text();target.write_text(text.replace('</main>',navigation+'</main>',1))
 return rows
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--evidence');args=parser.parse_args();rows=build(args.output)
 if args.evidence:Path(args.evidence).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 print('Built',len(rows),'explicit Registry reference pages; no new bindings assigned')
