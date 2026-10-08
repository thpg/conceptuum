/* Conceptuum explorer. No runtime dependencies or external assets. */
'use strict';
(() => {
  const $ = selector => document.querySelector(selector);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const storage = {
    get(key) { try { return localStorage.getItem(key); } catch (_) { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch (_) { /* Private mode remains usable. */ } }
  };
  const domains = {1:'Everyday',2:'Scientific',3:'Information technology',4:'Legal',5:'Logic'};
  const domain = id => domains[id] || 'Concept';
  const validID = id => Number.isSafeInteger(Number(id)) && Number(id) > 0;
  const list = value => Array.isArray(value) ? value : [];
  const params = new URLSearchParams(location.search);
  const Euler = window.ConceptuumEuler;
  const Catalog = window.ConceptuumEulerCatalog;
  const state = {
    id: validID(params.get('concept')) ? Number(params.get('concept')) : 2698,
    lang: (params.get('lang') || storage.get('conceptuum-lang')) === 'ru' ? 'ru' : 'en',
    view: ['relations','euler'].includes(params.get('view')) ? params.get('view') : 'hierarchy',
    full: params.get('ancestry') === 'full', filter: 'all', page: 0,
    tab: 'overview', data: null, nodes: [], links: [], rows: [], historyIndex: 0,
    searchController: null, conceptController: null, searchVersion: 0, conceptVersion: 0,
    transform: {x:0,y:0,k:1}, bounds: null, pending: false,
    eulerIDs: params.has('sets') ? Euler.parseSelection(params.get('sets')) : null,
    eulerContext: /^[1-5]$/.test(params.get('context')) ? Number(params.get('context')) : null,
    eulerMode: params.get('layout') === 'pairs' ? 'pairs' : 'auto',
    eulerBasis:params.get('basis')==='catalog'?'catalog':'relations',
    eulerDemo:params.get('demo')||'',
    eulerOperation:Catalog.operations.includes(params.get('op'))?params.get('op'):'none',
    eulerA:Number(params.get('a'))||0,eulerB:Number(params.get('b'))||0,eulerRegion:Number(params.get('region'))||0,
    eulerData: null, eulerKey: null, eulerPending: false, eulerError: '',
    eulerController: null, eulerVersion: 0, conceptNames: new Map()
  };
  const initialDemo=Catalog.demos.find(d=>d.id===state.eulerDemo);
  if(initialDemo&&!params.has('sets'))Object.assign(state,{id:initialDemo.ids[0],view:'euler',eulerIDs:[...initialDemo.ids],eulerContext:initialDemo.context,eulerBasis:initialDemo.basis,eulerOperation:initialDemo.op,eulerA:initialDemo.a||initialDemo.ids[0],eulerB:initialDemo.b||initialDemo.ids[1]});
  const starters = [
    {id:2698,nama:'Mathematical object',uni:1,icon:'∑',ru:'Математический объект'},
    {id:87,nama:'Ice',uni:1,icon:'◇',ru:'Лёд'},
    {id:25,nama:'Organism',uni:1,icon:'♧',ru:'Организм'},
    {id:218,nama:'Emotion',uni:1,icon:'○',ru:'Эмоция'},
    {id:16,nama:'Entity',uni:1,icon:'⌘',ru:'Сущее'}
  ];
  const NW = 212, NH = 80, COL = 310, ROW = 100;
  const compact = () => graph.clientWidth < 540;
  const pageSize = () => compact() ? 3 : 8;
  const graph = $('#graph'), viewport = $('#graph-viewport'), results = $('#search-results');
  const measure = document.createElement('canvas').getContext('2d');
  measure.font = '550 13px "Segoe UI", sans-serif';
  let searchTimer, toastTimer, resizeTimer, pointerStart = null, moved = false, pinch = null;
  const pointers = new Map();

  async function request(path, signal) {
    const response = await fetch(`${path}${path.includes('?') ? '&' : '?'}lang=${state.lang}`, {signal});
    if (!response.ok) throw new Error(response.status === 404 ? 'This concept could not be found.' : 'The knowledge map is temporarily unavailable.');
    return response.json();
  }
  function toast(message) {
    clearTimeout(toastTimer); $('#toast').textContent = message; $('#toast').hidden = false;
    toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3200);
  }
  function showMessage(title, description, retry = false) {
    $('#graph-message').innerHTML = `<strong>${esc(title)}</strong>${esc(description)}${retry ? '<button class="retry-button" id="retry-concept">Try again</button>' : ''}`;
    $('#graph-message').hidden = false;
    if (retry) $('#retry-concept').onclick = () => selectConcept(state.id, {history:'replace'});
  }
  function updateURL(mode = 'replace') {
    const url = new URL(location.href);
    url.search = '';
    url.searchParams.set('concept', state.id);
    url.searchParams.set('lang', state.lang);
    if (state.view !== 'hierarchy') url.searchParams.set('view', state.view);
    if (state.full) url.searchParams.set('ancestry', 'full');
    if (state.view === 'euler') {
      if (state.eulerIDs !== null) url.searchParams.set('sets', state.eulerIDs.join(','));
      if (state.eulerContext !== null) url.searchParams.set('context', state.eulerContext);
      if (state.eulerMode === 'pairs') url.searchParams.set('layout', 'pairs');
      if (state.eulerDemo) url.searchParams.set('demo',state.eulerDemo);
      if (state.eulerBasis==='catalog') {
        url.searchParams.set('basis','catalog');url.searchParams.set('op',state.eulerOperation);
        if(state.eulerA)url.searchParams.set('a',state.eulerA);
        if(state.eulerB)url.searchParams.set('b',state.eulerB);
        if(state.eulerOperation==='region')url.searchParams.set('region',state.eulerRegion);
      }
    }
    if (mode === 'push') state.historyIndex++;
    history[mode === 'push' ? 'pushState' : 'replaceState']({conceptuum:true,index:state.historyIndex}, '', url);
    $('#go-back').disabled = state.historyIndex <= 0;
  }
  function updateSelection() {
    results.querySelectorAll('[data-concept]').forEach(button => {
      const selected = Number(button.dataset.concept) === state.id;
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-current', selected ? 'true' : 'false');
    });
  }
  function renderResults(rows, isStarter = false) {
    state.rows = rows;
    state.rowsAreStarters = isStarter;
    results.innerHTML = rows.map(c => {
      const name = isStarter && state.lang === 'ru' ? c.ru : c.nama;
      state.conceptNames.set(`${state.lang}:${c.id}`,name);
      const button = `<button class="result" data-concept="${Number(c.id)}"><span class="result-icon" aria-hidden="true">${esc(c.icon || '◇')}</span><span class="result-body"><span class="result-name">${esc(name)}</span><span class="result-domain">${esc(domain(c.uni))}</span></span><span class="result-arrow" aria-hidden="true">↗</span></button>`;
      if (state.view !== 'euler') return button;
      const added = (state.eulerIDs || []).includes(Number(c.id)), full = (state.eulerIDs || []).length >= Euler.maxConcepts;
      return `<div class="euler-result-row">${button}<button class="result-add" data-euler-add="${Number(c.id)}" aria-label="${esc(added ? `${name} is in the diagram` : `Add ${name} to circles`)}" title="${added ? 'Already added' : full ? 'Remove a concept before adding another' : 'Add to Euler circles'}" ${added || full ? 'disabled' : ''}>${added ? '✓' : '+'}</button></div>`;
    }).join('');
    updateSelection();
  }
  function starterList() {
    results.removeAttribute('aria-busy');
    $('#search-heading').textContent = 'START EXPLORING'; $('#result-count').textContent = '';
    $('#search-status').textContent = 'Suggested starting points'; renderResults(starters, true);
  }
  async function search(query) {
    state.searchController?.abort();
    const version = ++state.searchVersion;
    const q = query.trim();
    if (!q) { starterList(); return; }
    const controller = state.searchController = new AbortController();
    $('#search-heading').textContent = 'SEARCH RESULTS'; $('#result-count').textContent = '…';
    $('#search-status').textContent = 'Searching';
    results.setAttribute('aria-busy', 'true');
    try {
      const rows = list(await request(`/api/search?q=${encodeURIComponent(q)}`, controller.signal));
      if (version !== state.searchVersion) return;
      renderResults(rows.filter(c => validID(c.id)));
      $('#result-count').textContent = rows.length >= 100 ? '100+' : String(rows.length);
      $('#search-status').textContent = `${rows.length} matching concepts`;
      if (!rows.length) results.innerHTML = '<div class="empty-state"><strong>No concepts found</strong>Try a shorter word, a synonym, or another language.</div>';
    } catch (error) {
      if (error.name === 'AbortError' || version !== state.searchVersion) return;
      state.rows = []; $('#result-count').textContent = '';
      $('#search-status').textContent = 'Search failed. Try again.';
      results.innerHTML = '<div class="empty-state"><strong>Search is unavailable</strong>Please try again.<button class="retry-button" id="retry-search">Retry search</button></div>';
      $('#retry-search').onclick = () => search($('#search').value);
    } finally { if (version === state.searchVersion) results.removeAttribute('aria-busy'); }
  }

  async function selectConcept(id, options = {}) {
    if (!validID(id)) return;
    const previousID = state.id;
    state.id = Number(id); state.page = 0;
    state.conceptController?.abort();
    const version = ++state.conceptVersion;
    const controller = state.conceptController = new AbortController();
    state.pending = true; $('#loading').hidden = false;
    $('#graph-message').hidden = true; graph.setAttribute('aria-busy', 'true');
    updateSelection(); closePanels();
    updateURL(options.history || (previousID === state.id ? 'replace' : 'push'));
    try {
      // One descendant level keeps large hubs usable; select a child to explore further.
      const data = await request(`/api/tree?id=${state.id}&depth=1`, controller.signal);
      if (version !== state.conceptVersion) return;
      if (!data.center || !validID(data.center.id) || !data.up) throw new Error('The graph response is incomplete.');
      state.data = data;
      state.conceptNames.set(`${state.lang}:${data.center.id}`,data.center.nama);
      list(data.center.parents).forEach(c => state.conceptNames.set(`${state.lang}:${c.id}`,c.nama));
      document.title = `${data.center.nama} — Conceptuum`;
      $('#current-name').textContent = data.center.nama;
      $('#relation-count').textContent = list(data.center.rels).length;
      renderInspector(); renderGraph();
    } catch (error) {
      if (error.name === 'AbortError' || version !== state.conceptVersion) return;
      state.data = null; state.nodes = []; state.links = []; state.bounds = null;
      viewport.replaceChildren();
      $('#concept-heading').innerHTML = '<span class="domain-badge">Concept unavailable</span><h2>Try another connection</h2>';
      $('#detail-content').replaceChildren(); $('#current-name').textContent = `Concept #${state.id}`;
      $('#graph-summary').textContent = 'Unable to load concept'; $('#pagination').hidden = true;
      $('#relation-count').textContent = '0';
      showMessage('Unable to open this concept', error.message || 'Check your connection and try again.', true);
    } finally {
      if (version === state.conceptVersion) { state.pending = false; $('#loading').hidden = true; graph.removeAttribute('aria-busy'); }
    }
  }

  function conceptButton(c, parent = false) {
    return `<button class="concept-link${parent ? ' parent-link' : ''}" data-concept="${Number(c.id)}"><span>${esc(c.nama)}</span><span aria-hidden="true">↗</span></button>`;
  }
  function relationText(r) {
    const negated = r.strength === 0;
    return `${negated ? 'NOT ' : ''}${r.name || r.kod}`;
  }
  function symmetric(r) {
    return r.symmetric === true;
  }
  function relationDirection(r) {
    const center = state.data.center.nama;
    if (symmetric(r)) return `${center} ↔ ${r.other.nama}`;
    return r.dir === 'in' ? `${r.other.nama} → ${center}` : `${center} → ${r.other.nama}`;
  }
  function relationRow(r) {
    const badge = r.strength === 0 ? 'Negated' : r.strength != null ? `${r.strength}%` : '';
    return `<div class="detail-relation"><div class="relation-label${r.strength === 0 ? ' negative' : ''}"><span>${esc(relationText(r))}</span>${badge ? `<span class="strength" title="Stored relation strength, not a probability">${badge}</span>` : ''}</div>${conceptButton(r.other)}<p class="relation-direction">${esc(relationDirection(r))}</p></div>`;
  }
  function renderInspector() {
    if (!state.data) return;
    const c = state.data.center;
    const coverage = ['Not yet classified','Taxonomy recorded','Properties recorded','Relations recorded'][Math.max(0, Math.min(3, Number(c.processed) || 0))];
    $('#concept-heading').innerHTML = `<span class="domain-badge">${esc(domain(c.uni))}</span><h2>${esc(c.nama)}</h2><div class="concept-id"><span>#${Number(c.id)}</span><i class="coverage-dot"></i><span title="Recorded processing stage; not a quality score">${coverage}</span></div>`;
    renderDetailTab();
  }
  function renderDetailTab() {
    document.querySelectorAll('[data-tab]').forEach(button => {
      const active = button.dataset.tab === state.tab;
      button.setAttribute('aria-selected', active); button.tabIndex = active ? 0 : -1;
    });
    $('#detail-content').setAttribute('aria-labelledby', `tab-${state.tab}`);
    if (!state.data) return;
    const c = state.data.center, parents = list(c.parents), children = list(c.children), rels = list(c.rels), terms = list(c.terms);
    let html = '';
    if (state.tab === 'overview') {
      html += `<section class="detail-section"><h3 class="section-title">BROADER CONCEPTS <span>${parents.length}</span></h3>${parents.length ? parents.map(p => conceptButton(p, true)).join('') : '<p class="inline-empty">No broader concept is recorded.</p>'}</section>`;
      html += `<section class="detail-section"><h3 class="section-title">NARROWER CONCEPTS <span>${children.length}</span></h3>${children.length ? children.slice(0,20).map(c => conceptButton(c)).join('') : '<p class="inline-empty">No narrower concepts are recorded yet.</p>'}${children.length > 20 ? `<details><summary class="inline-empty">Show ${children.length - 20} more</summary>${children.slice(20).map(c => conceptButton(c)).join('')}</details>` : ''}</section>`;
      if (c.genDefin) html += `<section class="detail-section"><h3 class="section-title">FROM THE KNOWLEDGE MAP</h3><details class="summary-box"><summary>Read the generated description</summary><p>${esc(c.genDefin)}</p></details></section>`;
    } else if (state.tab === 'relations') {
      html = rels.length ? `<p class="inline-empty" style="margin-bottom:18px">Arrows show the stored direction. Percentages are relation strengths, not probabilities.</p>${rels.map(relationRow).join('')}` : '<p class="inline-empty">No additional relations are recorded for this concept. Explore its hierarchy to find related ideas.</p>';
    } else {
      for (const language of [...new Set(terms.map(t => t.lang))].sort()) {
        const values = [...new Set(terms.filter(t => t.lang === language).map(t => t.term))];
        html += `<section class="detail-section"><h3 class="section-title">${esc(({en:'ENGLISH',ru:'RUSSIAN'})[language] || language.toUpperCase())} <span>${values.length}</span></h3><div class="terms-list">${values.map(term => `<button class="term-chip" data-term="${esc(term)}">${esc(term)}</button>`).join('')}</div></section>`;
      }
      if (!terms.length) html = '<p class="inline-empty">No alternative terms are recorded.</p>';
      if (state.lang === 'en' && /[А-Яа-яЁё]/.test(c.nama)) html += '<p class="inline-empty" style="margin-top:20px">An English label is not available yet; the original label is shown.</p>';
    }
    $('#detail-content').innerHTML = html; $('#detail-content').scrollTop = 0;
  }

  function wrappedLabel(text) {
    const chars = Array.from(String(text)); const lines = []; let line = '';
    for (const char of chars) {
      if (measure.measureText(line + char).width > NW - 42 && line) {
        lines.push(line.trim()); line = char;
      } else line += char;
    }
    if (line) lines.push(line.trim());
    if (lines.length > 2) {
      let last = lines[1];
      while (measure.measureText(last + '…').width > NW - 42) last = last.slice(0,-1);
      return [lines[0], last + '…'];
    }
    return lines.length ? lines : ['Unnamed concept'];
  }
  function graphNode(c, x, y, kind, key = String(c.id), meta = '') {
    return {key,id:Number(c.id),name:c.nama,x,y,kind,meta:meta || domain(c.uni)};
  }
  function filteredRelations() {
    return list(state.data?.center.rels).filter(r => {
      if (!r.other || !validID(r.other.id)) return false;
      const code = Number(r.kod);
      return state.filter === 'all' || (state.filter === 'negative' && r.strength === 0) ||
        (state.filter === 'attributes' && code >= 15 && code <= 27) ||
        (state.filter === 'logical' && code >= 30 && code <= 64) ||
        (state.filter === 'causal' && code >= 70 && code <= 74);
    });
  }
  function makeHierarchy() {
    const c = state.data.center, nodes = new Map(), links = new Map(), levels = new Map();
    nodes.set(String(c.id), graphNode(c, 0, 0, 'center', String(c.id), 'SELECTED · ' + domain(c.uni)));
    function visit(node, depth, path) {
      if (depth > (state.full ? 10 : 1)) return;
      for (const parent of list(node.parents)) {
        if (!validID(parent.id) || path.has(parent.id)) continue;
        const key = String(parent.id);
        levels.set(key, Math.max(levels.get(key) || 0, depth));
        nodes.set(key, graphNode(parent, -COL * depth, 0, 'parent', key, domain(parent.edgeUni || parent.uni)));
        links.set(`${node.id}:${parent.id}`, {from:String(node.id),to:key,kind:'taxonomy',label:`${node.nama} is a kind of ${parent.nama}`});
        if (state.full) visit(parent, depth + 1, new Set([...path, parent.id]));
      }
    }
    visit(state.data.up, 1, new Set([c.id]));
    const groups = new Map();
    for (const [key, level] of levels) {
      if (!groups.has(level)) groups.set(level, []);
      groups.get(level).push(nodes.get(key));
    }
    for (const [level, group] of groups) group.forEach((node, i) => { node.x = -COL * level; node.y = (i - (group.length - 1) / 2) * ROW; });
    // ConceptInfo contains all direct children; the old tree endpoint caps its down array at 200.
    const children = list(c.children).filter(child => validID(child.id));
    const size = pageSize(), totalPages = Math.max(1, Math.ceil(children.length / size));
    state.page = Math.min(state.page, totalPages - 1);
    const current = children.slice(state.page * size, (state.page + 1) * size);
    current.forEach((child, i) => {
      const key = `child-${child.id}`;
      nodes.set(key, graphNode(child, COL, (i - (current.length - 1) / 2) * ROW, 'child', key, domain(child.uni)));
      links.set(`${key}:${c.id}`, {from:key,to:String(c.id),kind:'taxonomy',label:`${child.nama} is a kind of ${c.nama}`});
    });
    if (compact()) {
      const ancestors = [...levels.entries()].sort((a,b) => a[1]-b[1]);
      ancestors.forEach(([key],i) => { const n=nodes.get(key); n.x=0; n.y=-(i+1)*ROW-15; });
      current.forEach((child,i) => { const n=nodes.get(`child-${child.id}`); n.x=0; n.y=(i+1)*ROW+15; });
    }
    return {nodes:[...nodes.values()],links:[...links.values()],total:children.length,totalPages,count:current.length,unit:'narrower concepts'};
  }
  function makeRelations() {
    const c = state.data.center, nodes = [graphNode(c,0,0,'center',String(c.id),'SELECTED · ' + domain(c.uni))], links = [];
    const rels = filteredRelations();
    const size = pageSize(), totalPages = Math.max(1, Math.ceil(rels.length / size));
    state.page = Math.min(state.page, totalPages - 1);
    const current = rels.slice(state.page * size,(state.page + 1) * size);
    for (const side of ['in','out']) {
      const group = current.map((r,i) => ({r,i})).filter(({r}) => (r.dir === 'in' ? 'in' : 'out') === side);
      group.forEach(({r,i}, j) => {
        const key = `rel-${i}`, isIn = side === 'in';
        const arrow = symmetric(r) ? 'Mutual ·' : isIn ? 'Incoming ·' : 'Outgoing ·';
        const strength = r.strength != null && r.strength !== 0 ? ` · ${r.strength}%` : '';
        const x = compact() ? 0 : isIn ? -COL : COL;
        const y = compact() ? (isIn ? -1 : 1)*((j+1)*ROW+15) : (j - (group.length - 1) / 2) * ROW;
        nodes.push(graphNode(r.other,x,y,`relation${r.strength === 0 ? ' negative' : ''}`,key,`${arrow} ${relationText(r)}${strength}`));
        links.push({from:isIn ? key : String(c.id),to:isIn ? String(c.id) : key,kind:`relation${r.strength === 0 ? ' negative' : ''}`,symmetric:symmetric(r),label:`${relationText(r)}: ${relationDirection(r)}`});
      });
    }
    return {nodes,links,total:rels.length,totalPages,count:current.length,unit:'relations'};
  }
  function renderGraph() {
    updateViewControls();
    if (state.view === 'euler') { renderEuler(); return; }
    $('#focus-selected').disabled = false;
    if (!state.data) return;
    $('#graph-message').hidden = true;
    const model = state.view === 'hierarchy' ? makeHierarchy() : makeRelations();
    state.nodes = model.nodes; state.links = model.links;
    graph.querySelector('defs').innerHTML = '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#97ad9d" stroke-width="1.4"/></marker><marker id="relation-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#a188b4" stroke-width="1.4"/></marker>';
    const byKey = new Map(state.nodes.map(n => [n.key,n]));
    let html = '';
    state.links.forEach(link => {
      const from = byKey.get(link.from), to = byKey.get(link.to); if (!from || !to) return;
      const direction = to.x >= from.x ? 1 : -1;
      const x1 = from.x + direction * NW / 2, x2 = to.x - direction * (NW / 2 + 5);
      const middle = (x1 + x2) / 2, marker = link.kind.includes('relation') ? 'relation-arrow' : 'arrow';
      const path = compact()
        ? `M${from.x-NW/2},${from.y} C${-NW/2-65},${from.y} ${-NW/2-65},${to.y} ${to.x-NW/2-5},${to.y}`
        : `M${x1},${from.y} C${middle},${from.y} ${middle},${to.y} ${x2},${to.y}`;
      html += `<path class="graph-edge ${link.kind}" data-from="${esc(link.from)}" data-to="${esc(link.to)}" d="${path}" marker-end="url(#${marker})"${link.symmetric ? ` marker-start="url(#${marker})"` : ''}><title>${esc(link.label)}</title></path>`;
    });
    for (const n of state.nodes) {
      const lines = wrappedLabel(n.name), start = lines.length === 1 ? -7 : -14;
      let meta = n.meta;
      measure.font = '10px "Segoe UI", sans-serif';
      while (measure.measureText(meta).width > NW - 38 && meta.length > 1) meta = meta.slice(0,-2) + '…';
      measure.font = '550 13px "Segoe UI", sans-serif';
      html += `<g class="graph-node ${n.kind}" data-key="${esc(n.key)}" data-concept="${n.id}" transform="translate(${n.x},${n.y})" role="button" tabindex="0" aria-label="${esc(n.name + '. ' + n.meta + '. Open concept.')}" aria-current="${n.kind === 'center' ? 'true' : 'false'}"><title>${esc(n.name + '\n' + n.meta)}</title><rect class="node-box" x="${-NW/2}" y="${-NH/2}" width="${NW}" height="${NH}" rx="9"/><rect class="node-accent" x="${-NW/2+13}" y="${-NH/2+16}" width="3" height="19" rx="1.5"/>${lines.map((line,i) => `<text class="node-title" x="${-NW/2+25}" y="${start+i*16}">${esc(line)}</text>`).join('')}<text class="node-meta" x="${-NW/2+25}" y="24">${esc(meta)}</text><path class="node-icon" d="M${NW/2-22},-23 h7 v7 m-7,0 7,-7"/></g>`;
    }
    viewport.innerHTML = html;
    state.bounds = {minX:Math.min(...state.nodes.map(n => n.x)) - NW/2-20,maxX:Math.max(...state.nodes.map(n => n.x)) + NW/2+20,minY:Math.min(...state.nodes.map(n => n.y))-NH/2-20,maxY:Math.max(...state.nodes.map(n => n.y))+NH/2+20};
    if (compact()) state.bounds.minX -= 45;
    const size = pageSize(), first = model.total ? state.page * size + 1 : 0, last = state.page * size + model.count;
    $('#graph-summary').textContent = model.total > size ? `${first}–${last} of ${model.total} ${model.unit}` : `${state.nodes.length} ${state.nodes.length === 1 ? 'concept' : 'concepts'} · ${state.links.length} connections`;
    $('#pagination').hidden = model.totalPages <= 1;
    $('#page-label').textContent = `${state.page + 1} / ${model.totalPages}`;
    $('#page-prev').disabled = state.page === 0; $('#page-next').disabled = state.page >= model.totalPages - 1;
    if (state.view === 'relations' && !model.total) {
      viewport.replaceChildren();
      showMessage(state.filter === 'all' ? 'No additional relations yet' : 'No matching relations', state.filter === 'all' ? 'Switch to Hierarchy to explore broader and narrower concepts.' : 'Choose another filter to see more connections.');
    }
    fitGraph();
  }
  function updateViewControls() {
    document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', button.dataset.view === state.view));
    $('#ancestry-control').hidden = state.view !== 'hierarchy'; $('#relation-filter-control').hidden = state.view !== 'relations';
    $('#euler-controls').hidden = state.view !== 'euler';
    $('#graph-direction').hidden = state.view === 'euler';
    $('#full-ancestry').checked = state.full;
    $('#graph-direction').innerHTML = state.view === 'hierarchy' ? `<span><i class="dot parent-dot"></i>Broader${compact() ? ' ↑' : ''}</span><span><i class="dot focus-dot"></i>Selected concept</span><span><i class="dot child-dot"></i>Narrower${compact() ? ' ↓' : ''}</span>` : '<span>Incoming / mutual</span><span><i class="dot focus-dot"></i>Selected concept</span><span>Outgoing / mutual</span>';
    $('.graph-legend > span').innerHTML = `<i class="legend-line"></i>${state.view === 'hierarchy' ? 'is a kind of' : 'stored relation direction'}`;
    if (state.view === 'euler') $('.graph-legend > span').innerHTML = '<i class="euler-legend-circle"></i>concept extension';
  }

  function seedEuler() {
    if (state.eulerIDs !== null || !state.data) return;
    const c = state.data.center;
    if (state.eulerContext === null) state.eulerContext = c.uni >= 1 && c.uni <= 5 ? c.uni : 1;
    const parent = list(c.parents).find(p => (p.edgeUni || p.uni) === state.eulerContext);
    state.eulerIDs = parent ? [c.id,parent.id] : [c.id];
    updateURL();
  }
  function renderEulerSelection() {
    const ids = state.eulerIDs || [];
    const fresh = state.eulerKey === `${state.lang}:${state.eulerContext || 1}:${state.eulerBasis}:${ids.join(',')}` && !state.eulerPending;
    const data = fresh ? state.eulerData : null, automatic = list(data?.automatic);
    const demo=Catalog.demos.find(d=>d.id===state.eulerDemo&&d.basis===state.eulerBasis&&d.context===(state.eulerContext||1)&&d.ids.join(',')===ids.join(','));
    $('#euler-demo').value=demo?.id||'';
    $('#euler-demo-description').hidden=!demo;
    $('#euler-demo-description').textContent=demo?.description||'';
    $('#euler-basis').value=state.eulerBasis;
    $('#euler-settings-summary').textContent=`${ids.length} selected · ${state.eulerBasis==='catalog'?'Catalog sets':'Stored relations'} · Selection & display options`;
    $('#euler-basis-help').textContent=state.eulerBasis==='catalog'?'Sets of stored concepts; an absent classification is not a semantic exclusion.':'Circles describe recorded concept relationships.';
    $('#euler-controls').classList.toggle('catalog-active',state.eulerBasis==='catalog');
    $('#euler-count').textContent = `${ids.length} / ${Euler.maxConcepts}`;
    $('#euler-context').value = state.eulerContext || 1;
    $('#euler-layout').value = state.eulerMode;
    $('#euler-clear').disabled = ids.length === 0;
    $('#euler-add-current').disabled = ids.includes(state.id) || ids.length >= Euler.maxConcepts || !state.data;
    $('#euler-selection').innerHTML = ids.map(id => {
      const name = state.conceptNames.get(`${state.lang}:${id}`) || `Concept #${id}`;
      const missing = list(data?.missing).includes(id);
      const set=list(data?.catalog?.sets).find(c=>c.id===id),prefix=set?`${String.fromCharCode(65+data.concepts.findIndex(c=>c.id===id))} · `:'';
      return `<span class="euler-chip${missing ? ' missing' : ''}" style="--circle-color:${Euler.color(id,ids)}"><button class="euler-chip-name" data-euler-inspect="${id}" title="Inspect ${esc(name)}${set?` (${set.count} stored concepts)`:''}"><i aria-hidden="true"></i>${prefix}${esc(name)}${missing ? ' (unavailable)' : ''}</button><button class="euler-remove" data-euler-remove="${id}" aria-label="Remove ${esc(name)} from diagram">×</button></span>`;
    }).join('');
    $('#euler-automatic').hidden = !automatic.length;
    $('#euler-automatic').innerHTML = automatic.length ? `<span>Shared ${automatic.length===1?'genus':'genera'} · auto</span>` + automatic.map(g => {
      const name = state.conceptNames.get(`${state.lang}:${g.id}`) || `Concept #${g.id}`;
      return `<button class="euler-auto-chip" style="color:${Euler.color(g.id,ids)}" data-euler-inspect="${g.id}" title="Added for selected sibling concepts; does not use a selection slot. Inspect ${esc(name)}">${esc(name)}</button>`;
    }).join('') : '';
    const pairs = list(data?.pairs), byID = new Map(list(data?.concepts).map(c=>[c.id,c]));
    $('#euler-relationships').hidden = !pairs.length;
    const unknown = pairs.filter(p=>p.kind==='unknown').length;
    $('#euler-relationships-summary').textContent = `Relationships (${pairs.length})${unknown ? ` · ${unknown} unspecified` : ''}`;
    $('#euler-relationships-list').innerHTML = pairs.map(p=>`<li data-kind="${esc(p.kind)}"><span>${esc(Euler.relationDescription(p,byID))}${data?.catalog?' (catalog sets)':''}</span><small>${data?.catalog?'Calculated':p.kind==='unknown'?'Unspecified':p.kind==='conflict'?'Review needed':p.inferred?'Derived':'Recorded'}</small></li>`).join('');
    renderCatalogControls(data);
  }
  function catalogOptions() {
    return {ids:state.eulerIDs||[],op:state.eulerOperation,a:state.eulerA,b:state.eulerB,region:state.eulerRegion,compact:compact(),page:state.page,mode:state.eulerMode,width:graph.clientWidth,height:graph.clientHeight};
  }
  function renderCatalogControls(data) {
    $('#euler-catalog-controls').hidden=!data?.catalog;
    if(!data?.catalog)return;
    const concepts=data.concepts;
    if(!concepts.some(c=>c.id===state.eulerA))state.eulerA=concepts[0].id;
    if(!concepts.some(c=>c.id===state.eulerB))state.eulerB=(concepts[1]||concepts[0]).id;
    if(state.eulerOperation==='region'&&!data.catalog.regions.some(r=>r.mask===state.eulerRegion))state.eulerOperation='none';
    const options=concepts.map((c,i)=>`<option value="${c.id}">${String.fromCharCode(65+i)} · ${esc(c.nama)}</option>`).join('');
    for(const selector of ['#euler-operand-a','#euler-operand-b'])if($(selector).innerHTML!==options)$(selector).innerHTML=options;
    $('#euler-operand-a').value=state.eulerA;$('#euler-operand-b').value=state.eulerB;
    $('#euler-operation').value=state.eulerOperation;
    $('#euler-operation option[value=region]').disabled=!data.catalog.regions.some(r=>r.mask===state.eulerRegion);
    $('#euler-operand-a').disabled=['none','all','region'].includes(state.eulerOperation);
    $('#euler-operand-b').disabled=['none','all','region','complement'].includes(state.eulerOperation);
    const evaluated=Catalog.evaluate(data,catalogOptions());
    $('#euler-operation-result').textContent=`${evaluated.formula} = ${evaluated.count} stored ${evaluated.count===1?'concept':'concepts'}${evaluated.count===0?' · empty result':''}`;
    $('#euler-region-list').innerHTML=data.catalog.regions.map(r=>`<button data-euler-zone="${r.mask}" title="${esc(Catalog.regionDescription(data,r.mask))}" aria-pressed="${state.eulerOperation==='region'&&state.eulerRegion===r.mask}">${Catalog.regionName(data,r.mask)} <b>${r.count}</b></button>`).join('');
    $('#euler-member-list').innerHTML=evaluated.samples.map(c=>`<button data-euler-inspect="${c.id}" title="Membership supported by ${c.paths.map(p=>p.edges.length).join('/')} accepted links to the containing sets">${esc(c.nama)}</button>`).join('');
    $('#euler-member-note').textContent=evaluated.count?`Showing ${evaluated.samples.length} sample records of ${evaluated.count}. Select a member to inspect it. Each set includes its root; U includes automatic genera.`:'No catalog records match this expression. This does not assert that the corresponding real-world set is empty.';
    updateURL();
  }
  function selectEulerRegion(mask) {
    if(!state.eulerData?.catalog?.regions.some(r=>r.mask===Number(mask)))return;
    state.eulerRegion=Number(mask);state.eulerOperation='region';
    $('#euler-region-details').open=true;updateURL();renderGraph();
    $('#euler-region-details').scrollIntoView({block:'nearest'});
  }
  function loadEulerDemo(id) {
    const demo=Catalog.demos.find(d=>d.id===id);if(!demo)return;
    state.eulerDemo=demo.id;state.eulerIDs=[...demo.ids];state.eulerContext=demo.context;state.eulerBasis=demo.basis;
    state.eulerOperation=demo.op;state.eulerA=demo.a||demo.ids[0];state.eulerB=demo.b||demo.ids[1];state.eulerRegion=0;
    state.eulerMode='auto';state.view='euler';state.page=0;$('#euler-region-details').open=false;
    $('#euler-settings').open=demo.basis!=='catalog';
    $('#euler-guide').open=demo.basis!=='catalog';
    state.id=demo.ids[0];updateURL('push');renderResults(state.rows,state.rowsAreStarters);renderGraph();selectConcept(demo.ids[0],{history:'replace'});
  }
  function changeEulerSelection(ids) {
    state.eulerIDs = Euler.parseSelection(ids.join(',')); state.page = 0;state.eulerDemo='';state.eulerRegion=0;
    if (state.eulerContext === null) state.eulerContext = state.data?.center.uni || 1;
    updateURL(); renderEulerSelection();
    renderResults(state.rows,state.rowsAreStarters); renderGraph();
  }
  function addEuler(id) {
    id = Number(id);
    if (!validID(id) || (state.eulerIDs || []).includes(id)) return;
    if ((state.eulerIDs || []).length >= Euler.maxConcepts) { toast('Up to 8 concepts fit in a comparison. Remove one to add another.'); return; }
    changeEulerSelection([...(state.eulerIDs || []),id]);
    toast('Concept added to the Euler diagram.');
  }
  async function loadEuler(key) {
    state.eulerController?.abort();
    const controller = state.eulerController = new AbortController(), version = ++state.eulerVersion, requestLang = state.lang;
    state.eulerKey = key; state.eulerData = null; state.eulerError = ''; state.eulerPending = true;
    state.bounds = null; state.nodes = []; state.links = []; viewport.replaceChildren();
    $('#pagination').hidden = true;
    showMessage('Loading circles…','Checking relationships in the selected context.');
    $('#graph-summary').textContent = 'Loading set relationships…';
    try {
      const response = await request(`/api/euler?ids=${state.eulerIDs.join(',')}&context=${state.eulerContext || 1}&basis=${state.eulerBasis}`,controller.signal);
      if (version !== state.eulerVersion) return;
      if (!Array.isArray(response.concepts) || !Array.isArray(response.pairs)) throw new Error('The set relationship response is incomplete.');
      if(state.eulerBasis==='catalog'&&response.concepts.length&&(!Array.isArray(response.catalog?.sets)||!Array.isArray(response.catalog?.regions)))throw new Error('The catalog membership response is incomplete.');
      state.eulerData = response;
      response.concepts.forEach(c => state.conceptNames.set(`${requestLang}:${c.id}`,c.nama));
    } catch(error) {
      if (error.name === 'AbortError' || version !== state.eulerVersion) return;
      state.eulerError = error.message || 'Check your connection and try again.';
    } finally {
      if (version === state.eulerVersion) {
        state.eulerPending = false;
        if (state.view === 'euler') renderGraph();
      }
    }
  }
  function renderEuler() {
    seedEuler(); renderEulerSelection();
    if (state.eulerIDs === null) return;
    const key = `${state.lang}:${state.eulerContext || 1}:${state.eulerBasis}:${state.eulerIDs.join(',')}`;
    if (state.eulerKey !== key) { loadEuler(key); return; }
    if (state.eulerPending) return;
    $('#graph-message').hidden = true; graph.querySelector('defs').replaceChildren();
    $('#pagination').hidden = true; state.links = [];
    if (state.eulerError) {
      showMessage('Unable to load Euler circles',state.eulerError);
      const retry = document.createElement('button');retry.id='retry-euler';retry.className='retry-button';retry.textContent='Try again';
      retry.onclick = () => {state.eulerKey=null;renderGraph();};$('#graph-message').appendChild(retry);
      $('#graph-summary').textContent = 'Set relationships unavailable'; return;
    }
    if (!state.eulerData?.concepts.length) {
      state.bounds=null;state.nodes=[];viewport.replaceChildren();
      const empty = state.eulerIDs.length === 0;
      showMessage(empty ? 'Build your Euler diagram' : 'These concepts are unavailable',empty ? 'Find concepts with search, then use + to add them. You can compare up to 8 concepts.' : 'Remove unavailable concepts and choose another selection.');
      $('#euler-notice').textContent = 'Use + in search results to add a concept. Remove it with × on its chip.';
      $('#graph-summary').textContent = 'No concepts to display';$('#focus-selected').disabled=true;return;
    }
    const options=catalogOptions();
    const model = Catalog.decorate(state.eulerData,Euler.render(state.eulerData,options),options);
    viewport.innerHTML = model.html;
    state.nodes = model.nodes;state.bounds = model.bounds;state.page=model.page;
    $('#euler-notice').textContent = model.notice + (list(state.eulerData.missing).length ? ' Some selected concepts are unavailable.' : '');
    $('#graph-summary').textContent = model.summary;
    $('#pagination').hidden = model.totalPages <= 1;
    $('#page-label').textContent = `${model.page+1} / ${model.totalPages}`;
    $('#page-prev').disabled = model.page === 0;$('#page-next').disabled = model.page >= model.totalPages-1;
    $('#focus-selected').disabled = !state.nodes.some(n=>n.id===state.id);
    fitGraph();
  }
  function transform() {
    const t = state.transform;
    viewport.setAttribute('transform', `translate(${t.x},${t.y}) scale(${t.k})`);
    $('#zoom-label').textContent = `${Math.round(t.k * 100)}%`;
    $('#zoom-out').disabled = t.k <= .1201; $('#zoom-in').disabled = t.k >= 2.999;
  }
  function fitGraph() {
    if (!state.bounds) return;
    const b = state.bounds, width = graph.clientWidth, height = graph.clientHeight;
    if (!width || !height) return;
    const scale = Math.max(.12, Math.min(1.1,(width-40)/(b.maxX-b.minX),(height-(state.view==='euler'?75:130))/(b.maxY-b.minY)));
    state.transform = {k:scale,x:width/2 - (b.minX+b.maxX)/2*scale,y:height/2 - (b.minY+b.maxY)/2*scale - 7};
    transform();
  }
  function zoom(factor, x = graph.clientWidth/2, y = graph.clientHeight/2) {
    const t = state.transform, k = Math.max(.12,Math.min(3,t.k*factor)), ratio = k/t.k;
    state.transform = {k,x:x-(x-t.x)*ratio,y:y-(y-t.y)*ratio}; transform();
  }
  function highlight(key) {
    const connected = new Set([key]);
    state.links.forEach(link => { if (link.from === key || link.to === key) { connected.add(link.from); connected.add(link.to); } });
    viewport.querySelectorAll('.graph-node').forEach(node => node.classList.toggle('faded', Boolean(key) && !connected.has(node.dataset.key)));
    viewport.querySelectorAll('.graph-edge').forEach(edge => {
      const active = edge.dataset.from === key || edge.dataset.to === key;
      edge.classList.toggle('faded', Boolean(key) && !active); edge.classList.toggle('highlight', Boolean(key) && active);
    });
  }

  function closePanels() {
    $('#sidebar').classList.remove('open'); $('#inspector').classList.remove('open');
    $('#mobile-backdrop').hidden = true; $('#toggle-details').setAttribute('aria-expanded', 'false');
  }
  function openPanel(selector) {
    closePanels(); $(selector).classList.add('open'); $('#mobile-backdrop').hidden = false;
    if (selector === '#sidebar') $('#search').focus();
    else { $('#toggle-details').setAttribute('aria-expanded','true'); $('#close-details').focus(); }
  }

  $('#search').addEventListener('input', event => {
    clearTimeout(searchTimer);
    // Invalidate immediately, even while the next request is still debounced.
    state.searchController?.abort(); ++state.searchVersion;
    state.rows = []; results.setAttribute('aria-busy', 'true');
    searchTimer = setTimeout(() => search(event.target.value), 180);
  });
  $('#search').addEventListener('keydown', event => {
    if (event.key === 'ArrowDown') { event.preventDefault(); results.querySelector('button[data-concept]')?.focus(); }
    if (event.key === 'Enter' && state.rows.length && !results.hasAttribute('aria-busy')) {
      if (state.view === 'euler') addEuler(state.rows[0].id); else selectConcept(state.rows[0].id);
    }
    if (event.key === 'Escape') { $('#search').value = ''; clearTimeout(searchTimer); search(''); }
  });
  results.addEventListener('keydown', event => {
    const buttons = [...results.querySelectorAll('button[data-concept]')], index = buttons.indexOf(document.activeElement);
    if (event.key === 'ArrowDown' && index >= 0) { event.preventDefault(); buttons[Math.min(index+1,buttons.length-1)].focus(); }
    if (event.key === 'ArrowUp' && index >= 0) { event.preventDefault(); (index > 0 ? buttons[index-1] : $('#search')).focus(); }
    if (event.key === 'Escape') $('#search').focus();
  });
  document.addEventListener('click', event => {
    const zone=event.target.closest('[data-euler-zone]');
    if(zone&&(!zone.closest('#graph')||!moved)) {selectEulerRegion(zone.dataset.eulerZone);return;}
    const add = event.target.closest('[data-euler-add]');
    if (add) { addEuler(add.dataset.eulerAdd);return; }
    const remove = event.target.closest('[data-euler-remove]');
    if (remove) { changeEulerSelection(state.eulerIDs.filter(id=>id!==Number(remove.dataset.eulerRemove)));return; }
    const inspect = event.target.closest('[data-euler-inspect]');
    if (inspect && (!inspect.closest('#graph') || !moved)) { selectConcept(inspect.dataset.eulerInspect);return; }
    const node = event.target.closest('[data-concept]');
    if (node && !moved) selectConcept(node.dataset.concept);
    const term = event.target.closest('[data-term]');
    if (term) { $('#search').value = term.dataset.term; search(term.dataset.term); if (innerWidth <= 700) openPanel('#sidebar'); else $('#search').focus(); }
  });
  document.querySelectorAll('[data-tab]').forEach(button => {
    button.onclick = () => { state.tab = button.dataset.tab; renderDetailTab(); };
    button.onkeydown = event => {
      const buttons = [...document.querySelectorAll('[data-tab]')]; let index = buttons.indexOf(button);
      if (event.key === 'ArrowRight') index = (index+1)%buttons.length;
      else if (event.key === 'ArrowLeft') index = (index+buttons.length-1)%buttons.length;
      else if (event.key === 'Home') index = 0;
      else if (event.key === 'End') index = buttons.length-1;
      else return;
      event.preventDefault(); buttons[index].click(); buttons[index].focus();
    };
  });
  document.querySelectorAll('[data-view]').forEach(button => { button.onclick = () => {
    state.view = button.dataset.view; state.page = 0;
    if (state.view === 'euler') seedEuler();
    updateURL(); renderResults(state.rows,state.rowsAreStarters); renderGraph();
  }; });
  $('#euler-add-current').onclick = () => addEuler(state.id);
  $('#euler-clear').onclick = () => changeEulerSelection([]);
  $('#euler-find').onclick = () => { if (innerWidth <= 700) openPanel('#sidebar'); $('#search').focus(); };
  $('#euler-context').onchange = () => { state.eulerContext = Number($('#euler-context').value);state.page=0;state.eulerDemo='';state.eulerRegion=0;updateURL();renderGraph(); };
  $('#euler-layout').onchange = () => { state.eulerMode = $('#euler-layout').value;state.page=0;updateURL();renderGraph(); };
  $('#euler-basis').onchange=()=>{state.eulerBasis=$('#euler-basis').value;state.eulerDemo='';state.eulerRegion=0;state.page=0;$('#euler-settings').open=state.eulerBasis!=='catalog';$('#euler-guide').open=state.eulerBasis!=='catalog';updateURL();renderGraph();};
  $('#euler-demo').innerHTML='<option value="">Choose a database example…</option>'+Catalog.demos.map(d=>`<option value="${d.id}">${esc(d.title)}</option>`).join('');
  $('#euler-demo').onchange=()=>loadEulerDemo($('#euler-demo').value);
  $('#euler-operation').onchange=()=>{state.eulerOperation=$('#euler-operation').value;updateURL();renderGraph();};
  $('#euler-operand-a').onchange=()=>{state.eulerA=Number($('#euler-operand-a').value);updateURL();renderGraph();};
  $('#euler-operand-b').onchange=()=>{state.eulerB=Number($('#euler-operand-b').value);updateURL();renderGraph();};
  $('#language').value = state.lang;
  $('#language').onchange = () => {
    state.lang = $('#language').value; storage.set('conceptuum-lang',state.lang);
    clearTimeout(searchTimer); search($('#search').value); selectConcept(state.id,{history:'replace'});
  };
  $('#full-ancestry').onchange = () => { state.full = $('#full-ancestry').checked; updateURL(); renderGraph(); };
  $('#relation-filter').onchange = () => { state.filter = $('#relation-filter').value; state.page = 0; renderGraph(); };
  $('#page-prev').onclick = () => { state.page = Math.max(0,state.page-1); renderGraph(); };
  $('#page-next').onclick = () => { state.page++; renderGraph(); };
  $('#go-back').onclick = () => history.back();
  window.addEventListener('popstate', event => {
    const query = new URLSearchParams(location.search), id = query.get('concept');
    state.historyIndex = event.state?.index || 0;
    state.lang = query.get('lang') === 'ru' ? 'ru' : 'en'; $('#language').value = state.lang;
    state.view = ['relations','euler'].includes(query.get('view')) ? query.get('view') : 'hierarchy'; state.full = query.get('ancestry') === 'full';
    state.eulerIDs = query.has('sets') ? Euler.parseSelection(query.get('sets')) : null;
    state.eulerContext = /^[1-5]$/.test(query.get('context')) ? Number(query.get('context')) : null;
    state.eulerMode = query.get('layout') === 'pairs' ? 'pairs' : 'auto';
    state.eulerBasis=query.get('basis')==='catalog'?'catalog':'relations';state.eulerDemo=query.get('demo')||'';
    $('#euler-settings').open=state.eulerBasis!=='catalog';
    $('#euler-guide').open=state.eulerBasis!=='catalog';
    state.eulerOperation=Catalog.operations.includes(query.get('op'))?query.get('op'):'none';
    state.eulerA=Number(query.get('a'))||0;state.eulerB=Number(query.get('b'))||0;state.eulerRegion=Number(query.get('region'))||0;
    search($('#search').value); selectConcept(validID(id) ? id : 2698,{history:'replace'});
  });
  $('#open-search').onclick = () => openPanel('#sidebar');
  $('#close-search').onclick = () => { closePanels(); $('#open-search').focus(); };
  $('#toggle-details').onclick = () => $('#inspector').classList.contains('open') ? closePanels() : openPanel('#inspector');
  $('#close-details').onclick = () => { closePanels(); $('#toggle-details').focus(); };
  $('#mobile-backdrop').onclick = closePanels;
  document.addEventListener('keydown', event => {
    const editing = event.target.matches('input,textarea,select,[contenteditable=true]');
    if (event.key === '/' && !editing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault(); if (innerWidth <= 700) openPanel('#sidebar'); $('#search').focus();
    }
    if (event.key === 'Escape' && !editing) { closePanels(); graph.focus(); }
  });
  $('#zoom-in').onclick = () => zoom(1.2); $('#zoom-out').onclick = () => zoom(1/1.2); $('#fit').onclick = fitGraph;
  $('#focus-selected').onclick = () => {
    if (!state.data) return;
    const node = state.view === 'euler' ? state.nodes.find(n=>n.id===state.id) : {x:0,y:0};
    if (!node) return;
    state.transform = {k:1,x:graph.clientWidth/2-node.x,y:graph.clientHeight/2-node.y}; transform(); graph.focus();
  };
  graph.addEventListener('keydown', event => {
    const zone=event.target.closest('[data-euler-zone]');
    if(zone&&(event.key==='Enter'||event.key===' ')) {event.preventDefault();selectEulerRegion(zone.dataset.eulerZone);return;}
    const circle = event.target.closest('[data-euler-inspect]');
    if (circle && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault();selectConcept(circle.dataset.eulerInspect);return; }
    const node = event.target.closest('.graph-node');
    if (node && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); selectConcept(node.dataset.concept); return; }
    if (event.key.toLowerCase() === 'f') { event.preventDefault(); fitGraph(); }
    if (event.key === '+' || event.key === '=') { event.preventDefault(); zoom(1.2); }
    if (event.key === '-') { event.preventDefault(); zoom(1/1.2); }
    const pan = {ArrowLeft:[35,0],ArrowRight:[-35,0],ArrowUp:[0,35],ArrowDown:[0,-35]}[event.key];
    if (pan && !node) { event.preventDefault(); state.transform.x += pan[0]; state.transform.y += pan[1]; transform(); }
  });
  graph.addEventListener('wheel', event => { event.preventDefault(); const r = graph.getBoundingClientRect(); zoom(Math.exp(-event.deltaY*.0015), event.clientX-r.left,event.clientY-r.top); }, {passive:false});
  graph.addEventListener('pointerdown', event => {
    if (event.button !== 0 && event.pointerType === 'mouse') return;
    moved = false; pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
    pointerStart = {x:event.clientX,y:event.clientY,tx:state.transform.x,ty:state.transform.y};
    if (!event.target.closest('.graph-node,.euler-region,.catalog-region-count,.catalog-set-key')) graph.setPointerCapture(event.pointerId);
    if (pointers.size === 2) {
      const [a,b] = [...pointers.values()]; pinch = {distance:Math.hypot(a.x-b.x,a.y-b.y)};
    }
  });
  graph.addEventListener('pointermove', event => {
    if (!pointers.has(event.pointerId)) return;
    pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
    if (pointers.size === 2 && pinch) {
      const [a,b] = [...pointers.values()], distance = Math.hypot(a.x-b.x,a.y-b.y), rect = graph.getBoundingClientRect();
      if (pinch.distance > 0) zoom(distance/pinch.distance,(a.x+b.x)/2-rect.left,(a.y+b.y)/2-rect.top);
      pinch.distance = distance; moved = true; return;
    }
    if (!pointerStart) return;
    const dx = event.clientX-pointerStart.x, dy = event.clientY-pointerStart.y;
    if (Math.hypot(dx,dy)>5) moved = true;
    if (moved) { graph.classList.add('panning'); graph.setPointerCapture(event.pointerId); state.transform.x=pointerStart.tx+dx; state.transform.y=pointerStart.ty+dy; transform(); }
  });
  function endPointer(event) {
    pointers.delete(event.pointerId); pinch = null; pointerStart = null; graph.classList.remove('panning');
    if (graph.hasPointerCapture(event.pointerId)) graph.releasePointerCapture(event.pointerId);
    if (pointers.size === 1) { const p = [...pointers.values()][0]; pointerStart = {x:p.x,y:p.y,tx:state.transform.x,ty:state.transform.y}; }
    setTimeout(() => { if (!pointers.size) moved = false; }, 0);
  }
  graph.addEventListener('pointerup',endPointer); graph.addEventListener('pointercancel',endPointer);
  graph.addEventListener('pointerover', event => { if (!pointers.size) highlight(event.target.closest('.graph-node')?.dataset.key); });
  graph.addEventListener('pointerleave', () => highlight(null));
  graph.addEventListener('focusin', event => highlight(event.target.closest('.graph-node')?.dataset.key));
  graph.addEventListener('focusout', () => highlight(null));
  let wasCompact;
  new ResizeObserver(() => {
    clearTimeout(resizeTimer); resizeTimer = setTimeout(() => {
      if (wasCompact !== compact()) { wasCompact=compact(); state.page=0; renderGraph(); }
      else if (state.view === 'euler') renderGraph();
      else fitGraph();
    },100);
  }).observe($('#graph-stage'));
  window.addEventListener('resize', () => { if (innerWidth > 1200) closePanels(); });

  $('#share').onclick = async () => {
    updateURL();
    try { await navigator.clipboard.writeText(location.href); toast('Link copied. This view is ready to share.'); }
    catch (_) { window.prompt('Copy this link to share the concept:', location.href); }
  };
  $('#export').onclick = () => {
    if (!state.bounds || !viewport.childElementCount) { toast('Open a graph before exporting.'); return; }
    const svg = graph.cloneNode(true), group = svg.querySelector('#graph-viewport'), b = state.bounds;
    svg.removeAttribute('id'); svg.removeAttribute('tabindex'); svg.removeAttribute('style');
    svg.setAttribute('viewBox',`${b.minX} ${b.minY} ${b.maxX-b.minX} ${b.maxY-b.minY}`);
    svg.setAttribute('width',b.maxX-b.minX); svg.setAttribute('height',b.maxY-b.minY);
    group.removeAttribute('transform');
    const originals = graph.querySelectorAll('*'), copies = svg.querySelectorAll('*');
    originals.forEach((el,index) => {
      const style = getComputedStyle(el);
      for (const prop of ['fill','fill-opacity','stroke','stroke-opacity','stroke-width','stroke-dasharray','stroke-dashoffset','opacity','font-family','font-size','font-weight','filter','paint-order','stroke-linejoin']) copies[index].style.setProperty(prop,style.getPropertyValue(prop));
      copies[index].removeAttribute('tabindex'); copies[index].classList.remove('faded','highlight');
    });
    const background = document.createElementNS('http://www.w3.org/2000/svg','rect');
    background.setAttribute('x',b.minX); background.setAttribute('y',b.minY); background.setAttribute('width',b.maxX-b.minX); background.setAttribute('height',b.maxY-b.minY); background.setAttribute('fill','#f5f7f4');
    svg.insertBefore(background,group);
    const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'}));
    const anchor = document.createElement('a'); anchor.href=url; anchor.download=`conceptuum-${state.id}-${state.view}.svg`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
    toast('Graph exported as SVG.');
  };
  $('#euler-settings').open=state.eulerBasis!=='catalog';
  $('#euler-guide').open=state.eulerBasis!=='catalog';
  starterList(); updateViewControls(); selectConcept(state.id,{history:'replace'});
})();
