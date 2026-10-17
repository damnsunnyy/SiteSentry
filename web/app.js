const $ = (selector) => document.querySelector(selector);
const garden = `<!doctype html>
<html>
<head>
  <title>Northstar Garden</title>
  <meta name="description" content="A friendly neighborhood garden.">
</head>
<body>
  <header><a href="/">Northstar Garden</a></header>
  <div class="navigation"><a href="/">Home</a> <a href="/events">Events</a></div>
  <h1>Grow something good</h1>
  <h3>Join a workday</h3>
  <img src="tomatoes.jpg">
  <a href="/events">Click here</a>
  <form><input type="email"><button>Subscribe</button></form>
</body>
</html>`;
const studio = `<!doctype html>
<html lang="en">
<head>
  <title>Kindred Studio — thoughtful work for living spaces</title>
  <meta name="description" content="Meet Kindred Studio, a small interior design practice creating comfortable, lasting rooms with a focus on natural materials and everyday life.">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="https://kindred.example/">
</head>
<body>
  <header><a href="/">Kindred Studio</a></header>
  <nav aria-label="Main navigation"><a href="/work">Work</a><a href="/about">About</a></nav>
  <main>
    <h1>Rooms for the way you live</h1>
    <p>Thoughtful spaces, made to last.</p>
    <img src="studio.jpg" alt="Sunlight across a warm, minimal living room">
    <h2>Selected work</h2>
    <a href="/work">Explore our projects</a>
    <form><label for="email">Email address</label><input id="email" type="email"><button>Get studio notes</button></form>
  </main>
  <footer>Kindred Studio · contact us</footer>
</body>
</html>`;
const rules = [];
function add(rule,severity,title,message,fix){rules.push({rule,severity,title,message,fix});}
function audit(source){
  rules.length=0;
  const doc=new DOMParser().parseFromString(source,'text/html');
  const title=doc.title.trim();
  const lang=(doc.documentElement.getAttribute('lang')||'').trim();
  const description=doc.querySelector('meta[name="description"]')?.content.trim()||'';
  if(!lang)add('html.lang','warning','Document language is missing','Screen readers need the document language to pronounce content correctly.','Set a language on the root element, for example <html lang="en">.');
  if(!title)add('seo.title.missing','critical','Page title is missing','The browser tab and search result have no descriptive title.','Add a concise, unique <title> in the document head.');
  else if(title.length<15||title.length>60)add('seo.title.length','notice','Page title may be hard to scan',`The title has ${title.length} characters; this check flags titles under 15 or over 60.`,'Write a specific title that describes the page in roughly 15–60 characters.');
  if(!description)add('seo.description.missing','warning','Search description is missing','Search engines may choose unrelated page text for the result snippet.','Add a useful meta description to the document head.');
  else if(description.length<50||description.length>170)add('seo.description.length','notice','Search description length is unusual',`The description has ${description.length} characters; this check flags under 50 or over 170.`,'Summarize the page clearly in approximately 50–170 characters.');
  const h1s=[...doc.querySelectorAll('h1')].filter(node=>node.textContent.trim());
  if(!h1s.length)add('content.h1.missing','warning','No main heading was found','A clear page heading helps people understand the page structure.','Add one descriptive <h1> that names the page’s main topic.');
  else if(h1s.length>1)add('content.h1.multiple','notice','Several main headings were found',`Found ${h1s.length} non-empty h1 headings.`,'Use one clear page-level heading and nest section headings beneath it.');
  let previous=0;
  for(const heading of doc.querySelectorAll('h1,h2,h3,h4,h5,h6')){const level=Number(heading.tagName[1]);if(heading.textContent.trim()&&previous&&level>previous+1){add('content.heading.skip','notice','Heading levels skip a step',`Heading “${heading.textContent.trim().slice(0,55)}” jumps from h${previous} to h${level}.`,'Keep heading levels in order so keyboard and screen reader users can navigate the outline.');break;}if(heading.textContent.trim())previous=level;}
  const images=[...doc.images];const missing=images.filter(image=>!image.hasAttribute('alt'));
  if(missing.length)add('a11y.image.alt','critical','Images are missing alt attributes',`${missing.length} of ${images.length} images have no alt text attribute.`,'Describe informative images with concise alt text. Use alt="" only for decorative images.');
  const vague=[...doc.querySelectorAll('a')].filter(link=>['click here','here','read more','more','link'].includes(link.textContent.trim().toLowerCase())&&!link.getAttribute('aria-label'));
  if(vague.length)add('a11y.link.name','warning','Some links lack clear names',`Found ${vague.length} links with generic text such as “${vague[0].textContent.trim()}”.`,'Make link text describe its destination or purpose.');
  if(!doc.querySelector('meta[name="viewport"]')?.content.trim())add('mobile.viewport','warning','Mobile viewport is not declared','The page may render at a desktop width on phones.','Add a viewport meta tag with width=device-width and initial-scale=1.');
  if(!doc.querySelector('link[rel~="canonical"]'))add('seo.canonical.missing','notice','Canonical URL is not declared','Duplicate URL variants can be harder for crawlers to consolidate.','Add a rel="canonical" link pointing to the preferred public URL.');
  const fields=[...doc.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]),select,textarea')];
  const unlabelled=fields.filter(field=>{const id=field.id;return !(id&&doc.querySelector(`label[for="${CSS.escape(id)}"]`))&&!field.closest('label')&&!field.getAttribute('aria-label')&&!field.getAttribute('aria-labelledby');});
  if(unlabelled.length)add('a11y.form.label','critical','Form fields need accessible labels',`${unlabelled.length} of ${fields.length} checked form fields have no associated label or accessible name.`,'Associate a <label> with each field or provide a valid accessible name.');
  if(!doc.querySelector('main,nav,[role="main"],[role="navigation"]'))add('a11y.landmarks','notice','No main or navigation landmark found','Landmarks provide useful keyboard and screen reader shortcuts.','Wrap primary content in <main> and navigation in <nav>.');
  return {doc,title:title||'Untitled page',findings:[...rules],images:images.length,links:doc.querySelectorAll('a').length,forms:doc.forms.length};
}
function score(findings){const deduction={critical:18,warning:8,notice:3};return Math.max(0,100-findings.reduce((n,f)=>n+(deduction[f.severity]||0),0));}
function safeText(text){return String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function render(result){const value=score(result.findings);const counts={critical:0,warning:0,notice:0};result.findings.forEach(f=>counts[f.severity]++);$('#score-value').textContent=value;$('#score-ring').style.background=`radial-gradient(closest-side,var(--panel) 80%,transparent 82%),conic-gradient(var(--acid) ${value}%,#ffffff18 0)`;$('#critical-count').textContent=counts.critical;$('#warning-count').textContent=counts.warning;$('#notice-count').textContent=counts.notice;$('#result-title').textContent=result.title;$('#result-subtitle').textContent=`${result.findings.length} finding${result.findings.length===1?'':'s'} · ${result.images} image${result.images===1?'':'s'} · ${result.links} links · source parsed locally`;
  $('#finding-count').textContent=`${result.findings.length} TOTAL`;
  $('#finding-list').innerHTML=result.findings.length?result.findings.map(f=>`<article class="finding ${f.severity}"><div class="finding-top"><span class="severity">${f.severity.toUpperCase()}</span><code>${safeText(f.rule)}</code></div><h4>${safeText(f.title)}</h4><p>${safeText(f.message)}</p><div class="fix"><b>FIX</b>${safeText(f.fix)}</div></article>`).join(''):'<div class="empty">No findings for this page. Keep those good habits.</div>';
  const canonical=result.doc.querySelector('link[rel~="canonical"]')?.href||'Not set';const snapshot=[['DOCUMENT LANGUAGE',result.doc.documentElement.lang||'Not set'],['PAGE TITLE',result.title],['META DESCRIPTION',result.doc.querySelector('meta[name="description"]')?.content||'Not set'],['HEADINGS',result.doc.querySelectorAll('h1,h2,h3,h4,h5,h6').length],['FORM FIELDS',result.doc.querySelectorAll('input,select,textarea').length],['CANONICAL',canonical]];$('#snapshot').innerHTML=`<div class="snap">${snapshot.map(([key,val])=>`<div><span>${safeText(key)}</span><b>${safeText(val)}</b></div>`).join('')}</div>`;$('#results').hidden=false;$('#status').textContent=`Audit complete · ${result.findings.length} finding${result.findings.length===1?'':'s'} to review.`;$('#status').classList.remove('error');result.score=value;$('#results').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});}
let latest=null;
function scan(){const source=$('#html-input').value;if(!source.trim()){$('#status').textContent='Paste HTML or choose a sample before scanning.';$('#status').classList.add('error');return;}latest=audit(source);render(latest);}
$('#sample-select').addEventListener('change',event=>{$('#html-input').value=event.target.value==='studio'?studio:garden;updateCount();$('#results').hidden=true;$('#status').textContent='Sample loaded. Run the scan when you’re ready.';});
$('#html-input').value=garden;function updateCount(){$('#char-count').textContent=`${$('#html-input').value.length.toLocaleString()} CHARS`;}$('#html-input').addEventListener('input',updateCount);updateCount();
$('#file-input').addEventListener('change',async event=>{const file=event.target.files?.[0];if(!file)return;try{$('#html-input').value=await file.text();$('#sample-select').value='';updateCount();$('#results').hidden=true;$('#status').textContent=`Loaded ${file.name} · file remains in this browser tab.`;}catch{$('#status').textContent='Could not read that file.';$('#status').classList.add('error');}});
$('#scan-button').addEventListener('click',scan);
function download(name,type,data){const blob=new Blob([data],{type});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();URL.revokeObjectURL(a.href);}
$('#download-json').addEventListener('click',()=>{if(!latest)return;download('sitesentry-report.json','application/json',JSON.stringify({title:latest.title,score:latest.score,findings:latest.findings,summary:{images:latest.images,links:latest.links,forms:latest.forms}},null,2));});
$('#download-html').addEventListener('click',()=>{if(!latest)return;const findingHtml=latest.findings.map(f=>`<article><p><b>${safeText(f.severity.toUpperCase())} · ${safeText(f.rule)}</b></p><h2>${safeText(f.title)}</h2><p>${safeText(f.message)}</p><p><strong>Fix:</strong> ${safeText(f.fix)}</p></article>`).join('')||'<p>No findings.</p>';const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>SiteSentry report · ${safeText(latest.title)}</title><style>body{max-width:760px;margin:45px auto;padding:0 18px;background:#101411;color:#edf1e8;font:15px/1.6 system-ui}h1{color:#c2ef66}article{padding:16px;margin:12px 0;background:#171e18;border-left:3px solid #f0bd68}article:first-child{border-color:#f18b7f}article p{color:#abb7a6}small{color:#97a393}</style><h1>SiteSentry · ${safeText(latest.title)}</h1><p>Baseline score: ${latest.score} / 100 · generated from local HTML</p><small>Scores are triage signals, not compliance certification.</small>${findingHtml}</html>`;download('sitesentry-report.html','text/html',html);});
