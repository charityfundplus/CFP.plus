(function(root){
  'use strict';
  const M=root.HUB69Model,esc=M.esc;
  const data=()=>root.HUB69_TRAINING;
  const validKey=key=>data().curriculum.basic.lessons.some(l=>l.key===key);
  function readProgress(storage){
    try{const p=JSON.parse(storage.getItem('hub69.study.v1')||'[]');return Array.isArray(p)?[...new Set(p.filter(validKey))]:[];}catch{return [];}
  }
  function saveProgress(storage,progress){try{storage.setItem('hub69.study.v1',JSON.stringify(progress.filter(validKey)));return true;}catch{return false;}}
  function view(progress=[],key=null){
    const {curriculum:c,source}=data();
    const lessons=key?c.basic.lessons.filter(l=>l.key===key):c.basic.lessons;
    return '<article class="panel"><div class="section-top"><h2>Đào tạo SI 🤖 AI 🤖</h2><span class="tag">'+progress.filter(validKey).length+' / 5 bài đã đọc</span></div><p class="muted">5 bài cơ bản · 12 bài thực hành · 6 hướng nâng cao. Dấu đã đọc chỉ lưu trên trình duyệt, không phải kết quả đánh giá hoặc quyền vận hành.</p><progress max="5" value="'+progress.filter(validKey).length+'" aria-label="Số bài đã đọc"></progress><p class="muted">Nguồn giáo trình: <a class="text-link" href="'+esc(source.url)+'" target="_blank" rel="noopener noreferrer">'+esc(source.revision.slice(0,7))+' ↗</a> · '+esc(c.version)+'</p><div class="chapter-nav">'+c.basic.lessons.map((l,i)=>'<a class="btn" href="#lesson/'+l.key+'">'+(i+1)+'. '+esc(l.title.vi)+'</a>').join('')+'</div></article>'+lessons.map(l=>'<article class="panel"><h2>'+esc(l.title.vi)+'</h2><ol class="study-steps">'+l.steps.vi.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol><p class="muted">Evidence cần có: '+esc(l.expectedEvidence)+'</p><label class="study-check"><input type="checkbox" id="study-'+l.key+'" data-study="'+l.key+'"'+(progress.includes(l.key)?' checked':'')+'> Tôi đã đọc bài này</label><p class="muted">Ghi nhận đọc: STUDY ACKNOWLEDGEMENT ONLY</p></article>').join('')+(key?'<a class="btn" href="#training">Về toàn bộ giáo trình</a>':'<article class="panel"><h2>12 bài thực hành có giám sát</h2><p class="muted">Chuẩn bị theo giáo trình đã có. Thực thi và nộp Evidence cần grant, fixture và reviewer của Core hiện hữu.</p>'+c.exercises.map((e,i)=>'<details class="study-detail"><summary>'+(i+1)+'. '+esc(e.name)+'</summary><p>'+esc(e.expectedOutput)+'</p><p class="muted">'+esc(e.deliveryMode)+' · Reviewer riêng: '+(e.requiresSeparateReview?'Bắt buộc':'Theo nguồn')+'</p></details>').join('')+'</article><article class="panel"><h2>6 hướng nâng cao</h2>'+c.advanced.map(a=>'<details class="study-detail"><summary>'+esc(a.title.vi)+' <span class="tag amber">NOT ASSESSED</span></summary><ol class="study-steps">'+a.steps.vi.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol><p class="muted">Evidence: '+esc(a.expectedEvidence)+'</p><p class="muted">Điều kiện: '+a.prerequisites.map(esc).join(' · ')+'</p></details>').join('')+'</article>');
  }
  root.HUB69Training=Object.freeze({validKey,readProgress,saveProgress,view});
})(typeof window!=='undefined'?window:globalThis);
