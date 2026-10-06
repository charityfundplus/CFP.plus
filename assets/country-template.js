// One read-only structural renderer; callers preserve exact existing identities.
window.renderCountryTemplate = async function(identifier) {
  try {
    const response = await fetch('/assets/country-template-projection.json', {cache:'no-store'});
    if (!response.ok) return false;
    const p = await response.json();
    if (p.authority !== 'READ_ONLY_MIRROR' || p.schema_version !== '1' || !p.enabled ||
        p.source?.authority !== 'CONFIGURATION_REFERENCE' || !/^[a-f0-9]{64}$/.test(p.source.sha256) ||
        !/^[a-f0-9]{40}$/.test(p.source_commit) || !/^[0-9]+$/.test(identifier) || identifier.length > p.max_identifier_length) return false;
    const sourceResponse=await fetch('/registry/country-route-map.json',{cache:'no-store'});
    if(!sourceResponse.ok)return false;
    const sourceBytes=await sourceResponse.arrayBuffer();
    const sourceHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',sourceBytes)),b=>b.toString(16).padStart(2,'0')).join('');
    if(sourceHash!==p.source.sha256)return false;
    const matches = p.countries.filter(c => identifier.startsWith(c.country_root) && identifier.length > c.country_root.length);
    if(matches.length !== 1 || p.countries.some(c=>c.country_root===identifier)) return false;
    const c=matches[0], chapter=identifier[c.country_root.length], path=identifier.slice(c.country_root.length+1);
    const view=c.chapters.find(v=>v.chapter===chapter); if(!view) return false;
    const readback={country_root:c.country_root,chapter,descendant_path:path,reconstructed:c.country_root+chapter+path,matches:c.country_root+chapter+path===identifier,scope:'STRUCTURAL_EQUALITY_ONLY'};
    const section=document.createElement('section');section.id='country-template';section.className='section panel';section.style.overflowWrap='anywhere';
    section.dataset.countryRoot=c.country_root;section.dataset.chapter=chapter;section.dataset.descendantPath=path;section.dataset.sourceCommit=p.source_commit;
    const add=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;section.append(n);return n};
    add('h2',`${c.display_name} • ${chapter} • ${view.display_name}`);
    add('p',`CONTENT • STRUCTURAL PREVIEW • UNASSIGNED • ${identifier}`);
    add('p','Canonical Parent: UNKNOWN • No permissions granted • No Canonical Lock');
    add('p',`Descendant Path: ${path || '(empty)'} • Evidence: CONFIGURATION_REFERENCE`);
    add('p','MAP ≠ SUBJECT ≠ CONTENT ≠ RELATIONSHIP • 4984 ≠ 98441');
    const out=add('pre',JSON.stringify(readback));out.id='country-readback';out.style.whiteSpace='pre-wrap';out.style.overflowWrap='anywhere';
    for(const v of c.chapters){const a=add('a',`${v.chapter} • Structural preview `);a.href='/'+c.country_root+v.chapter;}
    document.querySelector('main').append(section);return true;
  } catch(error) {return false;}
};
