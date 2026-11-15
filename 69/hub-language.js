// Existing HUB69 enhancement; route/identity attributes are never rewritten.
const select=document.querySelector('#hub-language');const originals=new WeakMap();
for(const node of document.querySelectorAll('[data-en]'))originals.set(node,node.textContent);
select.addEventListener('change',()=>{const language=select.value==='en'?'en':'vi';document.documentElement.lang=language;for(const node of document.querySelectorAll('[data-en]'))node.textContent=language==='en'?node.dataset.en:originals.get(node);});
