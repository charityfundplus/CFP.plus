(function(root){
  'use strict';
  const esc=root.HUB69Model.esc;
  const config=root.HUB69_TEMPLATE_CONFIG;
  const text=(item,lang)=>item?.[lang]||item?.vi||'';
  const enabled=()=>config.modules.filter(m=>m.enabled===true);
  const find=key=>enabled().find(m=>m.key===key);
  function route(hash){
    if(!hash.startsWith('#template'))return null;
    if(hash==='#template')return {view:'template'};
    const match=/^#template\/([a-z]+)(?:\/([a-z]+))?$/.exec(hash);
    if(!match)return {view:'template',templateInvalid:true};
    const module=find(match[1]);
    const child=match[2]&&module?.key==='office'&&config.officeChildren.find(c=>c.key===match[2]);
    return module&&(!match[2]||child)?{view:'template',module:module.key,child:child?.key}:{view:'template',templateInvalid:true};
  }
  function link(target,label){
    // Configuration is presentation, never an authorization or identity source.
    if(!/^#[a-z0-9/-]+$/.test(target)&&target!=='https://cfp.plus/69')return '<span>'+esc(label)+'</span>';
    return '<a class="btn" href="'+esc(target)+'">'+esc(label)+'</a>';
  }
  const normalize=value=>String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase();
  function results(lang='vi',query=''){
    const q=normalize(query).trim().slice(0,120);
    const rows=enabled().filter(m=>normalize(text(m.title,lang)+' '+text(m.summary,lang)).includes(q));
    return '<p role="status">'+rows.length+' / '+enabled().length+'</p><div class="record-grid">'+rows.map(m=>'<article class="panel"><h3>'+esc(text(m.title,lang))+'</h3><p>'+esc(text(m.summary,lang))+'</p>'+link('#template/'+m.key,lang==='en'?'Open section':'Mở mục')+'</article>').join('')+'</div>'+(rows.length?'':'<p>'+ (lang==='en'?'No matching sections.':'Không có mục phù hợp.')+'</p>');
  }
  function view(state={},lang='vi',query=''){
    lang=lang==='en'?'en':'vi';
    const en=lang==='en';
    const title=en?'Shared Website Template':'Mẫu Website Chung';
    let html='<section class="panel" lang="'+lang+'"><div class="section-top"><h2>'+title+'</h2><span class="tag amber">PILOT · READ/REVIEW</span></div><p>'+(en?'Local review template within HUB 69. New template labels support Vietnamese and English; inherited screens retain Vietnamese.':'Bản review local trong HUB 69. Khung mẫu mới hỗ trợ Việt/Anh; màn hình kế thừa giữ tiếng Việt.')+'</p><label for="template-language">'+(en?'Language':'Ngôn ngữ')+'</label> <select id="template-language"><option value="vi"'+(!en?' selected':'')+'>Tiếng Việt</option><option value="en"'+(en?' selected':'')+'>English</option></select><p>'+link('#template',title)+' '+link('https://cfp.plus/69','HUB 69')+'</p>';
    if(state.templateInvalid){return html+'<p role="alert">'+(en?'Section unavailable or disabled in configuration.':'Mục không tồn tại hoặc đã ẩn bằng cấu hình.')+'</p></section>';}
    if(!state.module){
      return html+'<label for="template-search">'+(en?'Search sections':'Tìm mục')+'</label><input id="template-search" type="search" maxlength="120" value="'+esc(query)+'"><div id="template-results">'+results(lang,query)+'</div></section>';
    }
    const m=find(state.module);
    if(!m)return html+'</section>';
    html+='<h3>'+esc(text(m.title,lang))+'</h3><p>'+esc(text(m.summary,lang))+'</p>';
    if(m.key==='office'){
      const child=state.child&&config.officeChildren.find(c=>c.key===state.child);
      if(child){
        html+='<h4>'+esc(text(child.title,lang))+'</h4><p>'+(en?'Open the existing source screen below. Task assignment, audit and evidence acceptance require authorized Core operations; this screen grants no access.':'Mở màn hình nguồn hiện hữu bên dưới. Giao nhiệm vụ, kiểm toán và nghiệm thu Evidence cần thao tác Core được cấp quyền; màn hình này không cấp quyền.')+'</p>'+link(child.target,en?'Open existing screen':'Mở màn hình hiện hữu');
      }else{
        html+='<dl class="profile-dl"><dt>'+(en?'Identity':'Định danh')+'</dt><dd>PENDING · Stable ID / Parent / DID / Canonical</dd><dt>'+(en?'Function':'Chức năng')+'</dt><dd>'+(en?'Navigate to topic work links':'Điều hướng tới Link con theo chủ đề')+'</dd><dt>'+(en?'Status':'Trạng thái')+'</dt><dd>HOLD ACTIVATION · PRODUCTION NO-GO</dd></dl><div class="profile-actions">'+config.officeChildren.map(c=>link('#template/office/'+c.key,text(c.title,lang))).join('')+'</div>';
      }
    }else if(m.key==='forum'){
      html+='<p class="callout">'+(en?'Forum design preview only. Live topics, replies, assignment and recipient ACK are not implemented or activated. No SI AI participation is asserted.':'Chỉ xem thiết kế diễn đàn. Topic, reply, giao việc và ACK người nhận chưa triển khai hoặc kích hoạt. Không xác nhận SI AI đã tham gia.')+'</p><div class="record-grid">'+root.HUB69P0.chapters.map(c=>'<article class="panel"><h4>'+(en?'Chapter ':'Chương ')+esc(c.id)+'</h4><p>'+esc(c.name)+'</p>'+link('#chapter/'+c.id,en?'Existing chapter':'Chương hiện hữu')+'</article>').join('')+'</div><h4>'+(en?'Proposed work areas':'Khu vực làm việc đề xuất')+'</h4><p>'+(en?'Public: reviewed/redacted publication only. Internal: Core session and explicit workspace/resource/action grants. Hiding a menu is not access control.':'Công khai: chỉ nội dung đã review và che dữ liệu nhạy cảm. Nội bộ: phiên Core và quyền workspace/resource/action cụ thể. Ẩn menu không thay thế kiểm soát truy cập.')+'</p><p>Intake → Task → ACK → Evidence → Independent Review → Human Governance</p>';
    }else{
      html+=link(m.target,en?'Open existing screen / gateway':'Mở màn hình / cổng hiện hữu');
      if(m.key==='contact')html+='<p>'+(en?'This preview does not collect personal information.':'Bản xem trước không thu thập thông tin cá nhân.')+'</p>';
    }
    return html+'</section>';
  }
  root.HUB69CommonTemplate=Object.freeze({route,view,results});
})(window);
