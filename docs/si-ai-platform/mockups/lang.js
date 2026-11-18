// CFP+ mockups • VI/EN toggle. Vietnamese is canonical; works without JS (VI only).
(function () {
  var root = document.documentElement;
  function set(lang) {
    root.setAttribute('data-ui-lang', lang);
    var btns = document.querySelectorAll('.lang button');
    for (var i = 0; i < btns.length; i++) btns[i].setAttribute('aria-pressed', String(btns[i].getAttribute('data-lang') === lang));
    try { localStorage.setItem('cfp-ui-lang', lang); } catch (e) { /* storage unavailable */ }
  }
  var saved = 'vi';
  try { saved = localStorage.getItem('cfp-ui-lang') || 'vi'; } catch (e) { /* ignore */ }
  set(saved === 'en' ? 'en' : 'vi');
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('.lang button');
    if (b) set(b.getAttribute('data-lang'));
  });
})();
