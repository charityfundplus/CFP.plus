(function () {
  'use strict';
  if (window.HUB69_CONFIG?.mode !== 'app') return;
  const $ = id => document.getElementById(id);
  const el = (tag, text) => {const n = document.createElement(tag); n.textContent = text; return n;};
  let spaces = [], state = null, epoch = 0, busy = false;
  const nativeBlocked = () => window.Capacitor?.isNativePlatform?.() && !(location.protocol === 'https:' && location.origin === window.HUB69_CONFIG?.approvedStagingOrigin);
  function controls() {
    const write = !!state?.spaces?.find(space => space.key === state.space.key)?.write;
    $('social-space').disabled = busy || !state;
    for (const button of document.querySelectorAll('#view-social form button')) button.disabled = busy || !write;
  }
  function clear(message) {
    state = null;
    $('social-feed').replaceChildren(); $('social-worker-data').textContent = '';
    $('social-count').textContent = 'Chưa đọc dữ liệu hiện tại';
    $('social-status').textContent = message;
    controls();
  }
  async function api(path, body) {
    if (nativeBlocked()) throw Error('Gói native chưa cấu hình HTTPS sandbox được phê duyệt.');
    let response;
    try {response = await fetch('/api/' + path, {method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store', headers: {'Content-Type': 'application/json'}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});}
    catch {clear('Mất kết nối · chưa xác minh được dữ liệu hiện tại.');throw Error('Mất kết nối. Kết nối lại rồi đọc dữ liệu trước khi thử lại.');}
    const result = await response.json();
    if (!response.ok) {
      if (response.status === 401 || response.status >= 500) clear('Phiên hoặc dữ liệu hiện tại chưa được xác minh.');
      throw Error(result.error || 'Không truy cập được không gian.');
    }
    return result;
  }
  function requestKey(form, payload) {
    const serial = JSON.stringify(payload);
    if (form.dataset.payload !== serial) {form.dataset.payload = serial;form.dataset.requestKey = crypto.randomUUID();}
    return form.dataset.requestKey;
  }
  function render() {
    const write = state.spaces.find(space => space.key === state.space.key)?.write;
    $('social-status').textContent = state.space.label + ' · đã đọc qua API · ' + (write ? 'Có quyền viết' : 'Chỉ đọc');
    $('social-feed').replaceChildren(...state.posts.map(post => {
      const card = el('article', '');card.className = 'panel';card.dataset.postKey = post.key;
      card.append(el('strong', post.author), el('p', post.content), el('small', 'Mã bài: ' + post.key));
      const comments = el('div', '');comments.className='social-comments';
      for (const comment of state.comments.filter(c => c.post_key === post.key)) {const row = el('p', '');row.append(el('strong', comment.author + ': '), document.createTextNode(comment.content));comments.append(row);}
      card.append(comments);
      const form = document.createElement('form');form.className='social-comment-form';
      const label = el('label', 'Bình luận');const input = document.createElement('textarea');input.name='content';input.required=true;input.maxLength=5000;label.append(input);
      const button = el('button', 'Gửi bình luận');button.className='btn';button.disabled=!write;
      form.append(label,button);form.onsubmit=event=>{event.preventDefault();const payload={post_key:post.key,content:input.value};action(async()=>{
        ++epoch;
        const saved=await api('social/comments',{...payload,idempotency_key:requestKey(form,payload)});
        ++epoch;
        if(!saved.key||saved.post_key!==post.key)throw Error('Biên nhận bình luận không khớp bài đăng.');
        if(state&&saved.space===state.space.key){state={...state,comments:[...state.comments.filter(row=>row.key!==saved.key),saved]};render();}
        $('social-message').textContent='Bình luận đã lưu.';
      });};
      card.append(form);return card;
    }));
    $('social-count').textContent = state.posts.length + ' bài đăng trong không gian này';
    controls();
  }
  async function read() {
    if (location.hash !== '#social') return;
    const run = ++epoch;
    try {
      const discovered = await api('social/spaces');
      if (run !== epoch) return;
      spaces = discovered.spaces;
      const previous = $('social-space').value;
      $('social-space').replaceChildren(...spaces.map(space=>{const option=el('option',space.label+(space.write?'':' · Chỉ đọc'));option.value=space.key;return option;}));
      if (spaces.some(space=>space.key===previous)) $('social-space').value=previous;
      if (!spaces.length) {clear('Tài khoản chưa được cấp không gian.');return;}
      const next = await api('social/state',{space:$('social-space').value});
      if (run !== epoch) return;
      state=next;render();
    } catch(error) {if (run === epoch) {spaces=[];$('social-space').replaceChildren();clear('Chưa đọc được mạng xã hội. Đăng nhập tại Vận hành rồi thử lại. '+error.message);}}
  }
  async function action(fn) {
    if(busy)return;
    busy=true;controls();
    try{await fn();}catch(error){$('social-message').textContent=error.message;}finally{busy=false;controls();}
  }
  async function workerStatus() {
    try {
      const result=await api('worker/state');
      $('social-worker-data').textContent=JSON.stringify(result,null,2);
      $('social-worker-status').textContent=result.fresh?'Có heartbeat mới từ worker thử nghiệm cục bộ.':'Chưa có heartbeat mới; không xác nhận worker đang hoạt động.';
    } catch(error) {$('social-worker-data').textContent='';$('social-worker-status').textContent='Chưa xác minh được worker: '+error.message;}
  }
  window.addEventListener('DOMContentLoaded',()=>{
    $('social-refresh').onclick=()=>action(read);
    $('social-space').onchange=()=>action(read);
    $('social-post').onsubmit=event=>{
      event.preventDefault();const form=event.currentTarget,payload={space:$('social-space').value,content:form.elements.content.value};
      action(async()=>{
        ++epoch;
        const saved=await api('social/posts',{...payload,idempotency_key:requestKey(form,payload)});
        ++epoch;
        if(!saved.key||saved.space!==payload.space)throw Error('Biên nhận bài đăng không khớp không gian.');
        if(state&&state.space.key===saved.space){state={...state,posts:[...state.posts.filter(row=>row.key!==saved.key),saved]};render();}
        form.reset();delete form.dataset.payload;delete form.dataset.requestKey;$('social-message').textContent='Bài đăng đã lưu vào backend chung.';
      });
    };
    $('social-worker-refresh').onclick=()=>action(workerStatus);
    $('social-worker-task').onsubmit=event=>{
      event.preventDefault();const form=event.currentTarget;
      const payload={title:'Tính SHA256 văn bản thử nghiệm',recipient:'software-worker',content:JSON.stringify({operation:'sha256-text',text:form.elements.text.value})};
      action(async()=>{const task=await api('forum/tasks',{...payload,idempotency_key:requestKey(form,payload)});$('social-message').textContent='Đã giao nhiệm vụ kỹ thuật '+task.key+'. Chưa xác nhận hoàn thành cho đến khi có log và kết quả.';await workerStatus();});
    };
    read();
  });
  window.addEventListener('hashchange',read);
  window.addEventListener('offline',()=>{++epoch;clear('Mất kết nối · không giữ dữ liệu từ lần đọc cũ.');});
  window.addEventListener('online',read);
  window.addEventListener('message',event=>{const frame=$('operations-frame');if(event.origin===location.origin&&event.source===frame?.contentWindow&&event.data?.type==='cfp-session-changed')read();});
})();
