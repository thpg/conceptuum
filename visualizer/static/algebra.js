(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const demos = [
    {id: 'intersection', name: 'Two overlapping classes', expression: '#25439 & #25446', description: 'Glass jars ∩ food storage jars: a glass food storage jar belongs to both classes.'},
    {id: 'material', name: 'An inherited material', expression: '#3500 & has(material, #90)', description: 'Find vessels with a recorded glass material. Explain a member to follow the property through its genus chain.'},
    {id: 'exception', name: 'An explicit exception', expression: 'exact(#1354) & lacks(action, #209)', description: 'The penguin has an explicit negative flight assertion that overrides the inherited bird property.'},
    {id: 'parents', name: 'More than one genus', expression: 'parents(exact(#25447))', description: 'The glass food storage jar has two direct genera: glass jar and food storage jar.'},
    {id: 'subset', name: 'A subset comparison', expression: '#25447 <= #25439', description: 'Is every stored member of the glass food storage jar class also in the glass jar class?'},
    {id: 'counterexample', name: 'Find a counterexample', expression: '#25439 <= #25446', description: 'The glass jar catalog is not a subset of food storage jars. Inspect the record in Only in A to see why the comparison is false.'},
    {id: 'unknown', name: 'Unknown is not negative', expression: 'exact(#1354) & unknown(material, #90)', description: 'No applicable glass-material assertion is recorded for the penguin. Unknown does not mean an explicit negative assertion.'},
    {id: 'complement', name: 'A bounded complement', expression: '~#25439', within: '#1531', description: 'Within the jar catalog, return records outside the glass jar set. This is catalog difference, not a negative material assertion.'},
    {id: 'count', name: 'Count an intersection', expression: 'count(#24488 & #24489)', description: 'Finite sets ∩ nonempty sets: count the stored records shared by these two classes.'}
  ];
  const contexts = {1: 'Everyday', 2: 'Scientific', 3: 'IT', 4: 'Legal', 5: 'Logic'};
  const relations = {14: 'genus', 15: 'essential property', 20: 'attribute', 21: 'purpose', 22: 'action', 23: 'material', 24: 'content', 25: 'product', 26: 'agent', 27: 'patient', 30: 'coextension'};
  let requestNumber = 0, controller, lastResult, lastRequest, exportData;
  let searchNumber = 0, searchController, searchTimer, toastTimer;
  let selection = [0, 0];
  const editor = $('expression');
  let storage;
  try { storage = window.localStorage; } catch (_) { /* Session-only collection remains available. */ }
  const collection = new window.ConceptuumAlgebraCollection.Collection(storage);
  for (const demo of demos) {
    const option = el('option', '', demo.name);
    option.value = demo.id;
    $('algebra-demo').append(option);
  }

  function toast(message) {
    $('algebra-toast').textContent = message;
    $('algebra-toast').hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { $('algebra-toast').hidden = true; }, 3500);
  }
  function query(offset = 0, explain = null) {
    return {expression: editor.value, context: Number($('algebra-context').value),
      lang: $('algebra-language').value, within: $('algebra-within').value.trim() || null,
      limit: 25, offset, explain};
  }
  function queryURL() {
    const url = new URL('/algebra', location.origin);
    const data = query();
    url.searchParams.set('expr', data.expression);
    url.searchParams.set('context', data.context);
    url.searchParams.set('lang', data.lang);
    if (data.within) url.searchParams.set('within', data.within);
    if (exportData && lastRequest && lastRequest.explain) url.searchParams.set('explain', lastRequest.explain);
    return url;
  }
  function busy(value) {
    $('algebra-results').setAttribute('aria-busy', String(value));
    $('algebra-run').disabled = value;
    $('algebra-download').disabled = value || !exportData;
    $('collection-add').disabled = value || !exportData;
  }
  function invalidate() {
    ++requestNumber;
    if (controller) controller.abort();
    lastResult = lastRequest = exportData = null;
    busy(false);
    $('result-content').hidden = true;
    $('algebra-error').hidden = true;
    $('algebra-explanation').hidden = true;
    $('inspect-status').textContent = '';
    $('algebra-status').textContent = 'Expression changed. Evaluate to see the current result.';
  }
  function matchDemo() {
    const match = demos.find(d => d.expression === editor.value && (d.within || '') === $('algebra-within').value && $('algebra-context').value === '1');
    $('algebra-demo').value = match ? match.id : '';
    $('demo-description').textContent = match ? match.description : '';
  }
  function loadURL() {
    const params = new URL(location.href).searchParams;
    const demo = demos.find(d => d.id === params.get('demo')) || demos[0];
    editor.value = params.has('expr') ? params.get('expr').slice(0, 8192) : demo.expression;
    $('algebra-within').value = params.has('within') ? params.get('within').slice(0, 8192) : params.has('expr') ? '' : demo.within || '';
    $('algebra-context').value = /^[1-5]$/.test(params.get('context')) ? params.get('context') : '1';
    let language = 'en';
    try { language = localStorage.getItem('conceptuum-lang') || 'en'; } catch (_) { /* Storage is optional. */ }
    if (params.has('lang')) language = params.get('lang');
    $('algebra-language').value = language === 'ru' ? 'ru' : 'en';
    selection = [editor.value.length, editor.value.length];
    matchDemo();
  }
  function conceptLink(id, label) {
    const a = el('a', '', label || `#${id}`);
    a.href = `/?concept=${encodeURIComponent(id)}&lang=${$('algebra-language').value}`;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    return a;
  }
  function edgeLine(edge, container) {
    const p = el('p', 'evidence-line');
    p.append(`Edge #${edge.id}: `, conceptLink(edge.subject), ` → ${relations[edge.code] || `relation ${edge.code}`} → `, conceptLink(edge.target));
    if (edge.strength === 0) p.append(' · explicit negative');
    if (edge.traversal_from !== undefined && edge.traversal_from !== edge.subject) p.append(' · symmetric traversal');
    container.append(p);
  }
  function traceNode(trace) {
    const li = el('li', 'evidence-node');
    const scalar = trace.kind === 'boolean' || trace.kind === 'integer';
    const label = scalar ? String(trace.value) : trace.member ? 'included' : 'not included';
    const state = scalar ? (trace.value === false ? ' negative' : '') : trace.member ? '' : ' unknown';
    li.append(el('code', '', trace.expression), el('span', `evidence-state${state}`, label));
    if (trace.meaning) li.append(el('p', 'evidence-meaning', trace.meaning));
    if (Array.isArray(trace.path)) {
      if (!trace.path.length) li.append(el('p', 'evidence-line', 'The concept itself is the root of this set.'));
      trace.path.forEach(edge => edgeLine(edge, li));
    }
    if (trace.record_id) li.append(el('p', 'evidence-line', `Exact record #${trace.record_id}.`));
    (trace.edges || []).forEach(edge => edgeLine(edge, li));
    if (trace.fact) {
      const fact = trace.fact;
      const p = el('p', 'evidence-line');
      p.append(`${relations[fact.relation] || fact.relation} → #${fact.target}: `, el('span', `evidence-state ${fact.state}`, fact.state));
      li.append(p);
      for (const evidence of fact.evidence) {
        const box = el('div', 'evidence-owner');
        box.append(el('p', 'evidence-line', evidence.edge.subject === fact.subject ? 'Direct assertion' : `Inherited from #${evidence.edge.subject}`));
        edgeLine(evidence.edge, box);
        (evidence.genus_path || []).forEach(edge => edgeLine(edge, box));
        li.append(box);
      }
      if (fact.state === 'unknown') li.append(el('p', 'evidence-meaning', 'No applicable assertion is recorded. Unknown does not mean false.'));
      if (fact.state === 'conflict') li.append(el('p', 'evidence-meaning', 'Incomparable sources assert both positive and negative values.'));
      if (fact.overridden_edge_ids.length) li.append(el('p', 'evidence-meaning', `More general assertions overridden: ${fact.overridden_edge_ids.map(id => `#${id}`).join(', ')}.`));
    }
    if (trace.operands) {
      const list = el('ul', 'evidence-tree');
      trace.operands.forEach(operand => list.append(traceNode(operand)));
      li.append(list);
    }
    return li;
  }
  function renderExplanation(trace) {
    const scalar = trace.kind === 'boolean' || trace.kind === 'integer';
    $('explanation-title').textContent = `Inspect ${trace.concept.name}`;
    const meaning = scalar ? `Expression result: ${trace.value}. Follow this record through the operands below.` : trace.member ? 'Included in this result.' : 'Not included in this result.';
    const intro = el('p', 'explanation-intro', `#${trace.concept.id} · ${meaning}${trace.in_universe ? '' : ' Outside the selected domain.'}`);
    const tree = el('ul', 'evidence-tree');
    tree.append(traceNode(trace));
    $('explanation-content').replaceChildren(intro, tree);
    $('algebra-explanation').hidden = false;
    $('inspect-id').value = `#${trace.concept.id}`;
  }
  function inspectButton(item) {
    const button = el('button', 'diagnostic-sample', `#${item.id} ${item.name}`);
    button.type = 'button';
    button.setAttribute('aria-label', `Inspect ${item.name}`);
    button.addEventListener('click', () => evaluate(lastResult.offset || 0, item.id));
    return button;
  }
  function renderDiagnostics(data) {
    const container = $('algebra-diagnostics');
    container.replaceChildren();
    container.hidden = !data;
    if (!data) return;
    container.append(el('h3', '', 'Why this answer?'), el('p', 'diagnostic-rule', data.rule));
    const operands = el('div', 'diagnostic-operands');
    data.operands.forEach((operand, index) => {
      const line = el('div', 'diagnostic-operand');
      line.append(el('span', '', String.fromCharCode(65 + index)), el('code', '', operand.expression),
        el('strong', '', operand.kind === 'set' ? `${operand.count.toLocaleString()} records` : String(operand.value)));
      operands.append(line);
      if (operand.counted_set) {
        const samples = el('div', 'diagnostic-samples');
        operand.counted_set.items.forEach(item => samples.append(inspectButton(item)));
        if (operand.counted_set.truncated) samples.append(el('span', 'sample-note', `Sample of ${operand.counted_set.count} counted records`));
        operands.append(samples);
      }
    });
    container.append(operands);
    const regions = el('div', 'diagnostic-regions');
    data.regions.forEach(region => {
      const box = el('div', `diagnostic-region${region.counterexamples ? ' counterexamples' : ''}`);
      const heading = el('div', 'diagnostic-region-heading');
      heading.append(el('span', '', region.label), el('strong', '', region.count.toLocaleString()));
      box.append(heading);
      if (region.counterexamples) box.append(el('p', 'counterexample-label', 'Counterexamples'));
      const samples = el('div', 'diagnostic-samples');
      region.items.forEach(item => samples.append(inspectButton(item)));
      box.append(samples);
      if (region.truncated) box.append(el('p', 'sample-note', `Showing ${region.items.length} of ${region.count} records`));
      else if (!region.count) box.append(el('p', 'sample-note', 'No stored records'));
      regions.append(box);
    });
    container.append(regions);
    if (data.note) container.append(el('p', 'diagnostic-note', data.note));
  }
  function currentExample() {
    if (!exportData) return null;
    const data = {...exportData};
    const question = $('example-question').value.trim();
    if (question) data.question = question;
    return data;
  }
  function refreshJSON() {
    $('algebra-json').textContent = exportData ? JSON.stringify(currentExample(), null, 2) : '';
  }
  function renderResult(data, submitted) {
    lastResult = data;
    lastRequest = submitted;
    exportData = {schema: 'conceptuum.algebra.example.v1', request: submitted, result: data};
    refreshJSON();
    const summary = $('result-summary');
    const members = $('result-members');
    summary.replaceChildren();
    members.replaceChildren();
    summary.append(el('strong', '', data.kind === 'set' ? data.count.toLocaleString() : String(data.value)),
      el('span', '', data.kind === 'set' ? `stored concept${data.count === 1 ? '' : 's'}` : data.kind === 'boolean' ? 'catalog comparison' : 'catalog count'));
    $('resolved-expression').textContent = `${data.resolved_expression}${data.within === 'U' ? '' : ` · within ${data.within}`}`;
    renderDiagnostics(data.diagnostics);
    $('algebra-status').textContent = `${contexts[data.context]} relations · ${data.universe_count.toLocaleString()} records in domain${data.source.data_revision ? ` · ${data.source.data_revision}` : ''}`;
    for (const item of data.items || []) {
      const row = el('div', 'result-member');
      const body = el('div', 'member-body');
      body.append(conceptLink(item.id, item.name), el('span', '', `#${item.id} · home context: ${contexts[item.context] || item.context}`));
      const button = el('button', 'explain-button', 'Explain');
      button.type = 'button';
      button.setAttribute('aria-label', `Explain ${item.name}`);
      button.addEventListener('click', () => evaluate(data.offset, item.id));
      row.append(el('span', 'member-symbol', '∈'), body, button);
      members.append(row);
    }
    if (data.kind === 'set' && !data.count) members.append(el('p', 'evidence-meaning', 'No matching records in this domain. This is not proof of real-world incompatibility.'));
    $('algebra-pagination').hidden = data.kind !== 'set' || data.count <= submitted.limit;
    $('algebra-prev').disabled = !data.offset;
    $('algebra-next').disabled = !data.has_more;
    $('algebra-page-label').textContent = data.kind === 'set' ? `${data.returned ? data.offset + 1 : 0}–${data.offset + data.returned} of ${data.count}` : '';
    $('result-content').hidden = false;
    if (data.explanation) renderExplanation(data.explanation);
    else $('algebra-explanation').hidden = true;
  }
  function displayError(error) {
    const field = error.field === 'within' ? $('algebra-within') : editor;
    $('algebra-error').hidden = false;
    $('algebra-error-message').textContent = `${error.field === 'within' ? 'Within domain: ' : ''}${error.message || 'The request could not be completed.'}`;
    $('algebra-candidates').replaceChildren();
    const offset = value => Array.from(field.value).slice(0, value).join('').length;
    if (Number.isInteger(error.position)) {
      field.focus();
      field.setSelectionRange(offset(error.position), offset(error.end ?? error.position + 1));
    }
    for (const candidate of error.candidates || []) {
      const button = el('button', '', `#${candidate.id} · ${candidate.name} · ${contexts[candidate.context] || candidate.context}`);
      button.type = 'button';
      button.addEventListener('click', () => {
        if (!Number.isInteger(error.position) || !Number.isInteger(error.end)) return;
        field.setRangeText(`#${candidate.id}`, offset(error.position), offset(error.end), 'end');
        invalidate();
        matchDemo();
        evaluate();
      });
      $('algebra-candidates').append(button);
    }
  }
  async function evaluate(offset = 0, explain = null) {
    if (controller) controller.abort();
    controller = new AbortController();
    const serial = ++requestNumber;
    const submitted = query(offset, explain);
    exportData = null;
    $('collection-status').textContent = '';
    $('algebra-error').hidden = true;
    $('result-content').hidden = true;
    $('algebra-explanation').hidden = true;
    $('algebra-status').textContent = 'Evaluating against the concept graph…';
    busy(true);
    try {
      const response = await fetch('/api/algebra', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(submitted), signal: controller.signal});
      let data;
      try { data = await response.json(); } catch (_) { throw new Error('The server returned an unreadable response. Try again shortly.'); }
      if (serial !== requestNumber) return;
      if (!response.ok || data.error) {
        displayError(data.error || {message: `Request failed (${response.status}).`});
        $('algebra-status').textContent = 'No result. Check the message above.';
        return;
      }
      renderResult(data, submitted);
      const url = queryURL();
      if (url.href.length <= 7000) history.replaceState(null, '', url);
      if (explain !== null) $('algebra-explanation').scrollIntoView({block: 'nearest', behavior: 'instant'});
    } catch (error) {
      if (serial !== requestNumber || error.name === 'AbortError') return;
      displayError({message: error.message || 'Unable to reach the server. Try again shortly.'});
      $('algebra-status').textContent = 'No result. The query has been kept in the editor.';
    } finally {
      if (serial === requestNumber) busy(false);
    }
  }
  function renderCollection() {
    $('collection-count').textContent = String(collection.entries.length);
    $('collection-download').disabled = !collection.entries.length;
    $('collection-storage').textContent = collection.notice || (collection.persistent ?
      'Saved in this browser · up to 50 examples / 4 MiB. Export JSONL to keep a portable copy.' :
      'This collection lasts for this page session. Export JSONL to keep it.');
    const list = $('collection-items');
    list.replaceChildren();
    if (!collection.entries.length) list.append(el('p', 'collection-empty', 'Evaluate a query, optionally inspect a record, then add the example here.'));
    for (const entry of collection.entries) {
      const {example} = entry;
      const row = el('div', 'collection-item');
      const body = el('div', 'collection-item-body');
      const replay = el('button', 'collection-replay', example.question || example.request.expression);
      replay.type = 'button';
      replay.title = 'Load this example and evaluate it against the current graph';
      replay.addEventListener('click', () => {
        const request = example.request;
        invalidate();
        editor.value = request.expression;
        $('algebra-within').value = request.within || '';
        $('algebra-context').value = String(request.context);
        $('algebra-language').value = request.lang === 'ru' ? 'ru' : 'en';
        $('example-question').value = example.question || '';
        selection = [editor.value.length, editor.value.length];
        matchDemo();
        evaluate(0, request.explain);
        editor.scrollIntoView({block: 'center'});
        toast('Loaded query. Evaluating against the current graph; the saved example stays unchanged.');
      });
      const answer = example.result.kind === 'set' ? `${example.result.count} records` : String(example.result.value);
      body.append(replay, el('p', '', `${example.result.source.data_revision || 'Unversioned'} · ${contexts[example.request.context]} · ${answer}${example.request.explain ? ` · inspecting #${example.request.explain}` : ''}`));
      const remove = el('button', 'collection-remove', 'Remove');
      remove.type = 'button';
      remove.setAttribute('aria-label', `Remove example ${entry.id}`);
      remove.addEventListener('click', () => { collection.remove(entry.id); renderCollection(); $('collection-status').textContent = 'Example removed.'; });
      row.append(body, remove);
      list.append(row);
    }
  }
  function download(text, filename, type) {
    const url = URL.createObjectURL(new Blob([text], {type}));
    const a = el('a');
    a.href = url; a.download = filename;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function urlInspection() {
    const value = new URL(location.href).searchParams.get('explain');
    return /^[1-9][0-9]{0,9}$/.test(value) && Number(value) <= 2147483647 ? Number(value) : null;
  }
  function insert(text) {
    editor.focus();
    editor.setSelectionRange(...selection);
    editor.setRangeText(text, editor.selectionStart, editor.selectionEnd, 'end');
    if (text === '()') editor.setSelectionRange(editor.selectionStart - 1, editor.selectionStart - 1);
    selection = [editor.selectionStart, editor.selectionEnd];
    invalidate();
    matchDemo();
  }
  async function search() {
    const serial = ++searchNumber;
    if (searchController) searchController.abort();
    const term = $('algebra-search').value.trim();
    $('algebra-search-results').replaceChildren();
    if (!term) { $('algebra-search-status').textContent = ''; return; }
    searchController = new AbortController();
    $('algebra-search-status').textContent = 'Searching…';
    try {
      const params = new URLSearchParams({q: term, lang: $('algebra-language').value});
      const response = await fetch(`/api/search?${params}`, {signal: searchController.signal});
      if (!response.ok) throw new Error('Search is temporarily unavailable.');
      const items = await response.json();
      if (serial !== searchNumber) return;
      $('algebra-search-status').textContent = items.length ? `${Math.min(items.length, 8)} matches shown · click to insert` : 'No matching terms. Try a shorter word.';
      for (const item of items.slice(0, 8)) {
        const button = el('button', 'lookup-result');
        button.type = 'button';
        const body = el('span');
        body.append(el('strong', '', item.nama), el('small', '', `#${item.id} · ${contexts[item.uni] || 'Concept'}`));
        button.append(body, el('span', '', '+'));
        button.addEventListener('click', () => { insert(`#${item.id}`); toast(`Inserted #${item.id}`); });
        $('algebra-search-results').append(button);
      }
    } catch (error) {
      if (serial === searchNumber && error.name !== 'AbortError') $('algebra-search-status').textContent = error.message;
    }
  }
  $('algebra-form').addEventListener('submit', event => { event.preventDefault(); evaluate(); });
  for (const id of ['expression', 'algebra-within', 'algebra-context']) $(id).addEventListener('input', () => { invalidate(); matchDemo(); });
  for (const name of ['select', 'keyup', 'click', 'blur', 'input']) editor.addEventListener(name, () => { selection = [editor.selectionStart, editor.selectionEnd]; });
  $('algebra-form').addEventListener('keydown', event => { if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); evaluate(); } });
  document.querySelectorAll('[data-insert]').forEach(button => button.addEventListener('click', () => insert(button.dataset.insert)));
  $('algebra-clear').addEventListener('click', () => { editor.value = ''; selection = [0, 0]; invalidate(); matchDemo(); editor.focus(); });
  $('algebra-demo').addEventListener('change', () => {
    const demo = demos.find(d => d.id === $('algebra-demo').value);
    if (!demo) { $('demo-description').textContent = ''; return; }
    editor.value = demo.expression;
    $('algebra-within').value = demo.within || '';
    $('algebra-context').value = '1';
    selection = [editor.value.length, editor.value.length];
    invalidate(); matchDemo(); evaluate();
  });
  $('algebra-language').addEventListener('change', () => {
    try { localStorage.setItem('conceptuum-lang', $('algebra-language').value); } catch (_) { /* Storage is optional. */ }
    invalidate(); search(); evaluate();
  });
  $('algebra-prev').addEventListener('click', () => { if (lastResult && lastRequest) evaluate(Math.max(0, lastResult.offset - lastRequest.limit)); });
  $('algebra-next').addEventListener('click', () => { if (lastResult && lastRequest) evaluate(lastResult.offset + lastRequest.limit); });
  $('close-explanation').addEventListener('click', () => { $('algebra-explanation').hidden = true; });
  $('inspect-form').addEventListener('submit', event => {
    event.preventDefault();
    const raw = $('inspect-id').value.trim().replace(/^#/, '');
    if (!/^[1-9][0-9]*$/.test(raw) || Number(raw) > 2147483647) {
      $('inspect-status').textContent = 'Enter a valid concept ID, such as #1354.';
      return;
    }
    $('inspect-status').textContent = '';
    evaluate(lastResult.offset || 0, Number(raw));
  });
  $('example-question').addEventListener('input', refreshJSON);
  $('collection-add').addEventListener('click', () => {
    if (!exportData) return;
    try {
      const added = collection.add(currentExample());
      renderCollection();
      $('collection-status').textContent = added ? 'Example added.' : 'This example is already in the collection.';
    } catch (error) { $('collection-status').textContent = error.message; }
  });
  $('collection-download').addEventListener('click', () => {
    if (collection.entries.length) download(collection.jsonl(), 'conceptuum-algebra-examples.jsonl', 'application/x-ndjson');
  });
  window.addEventListener('storage', event => {
    if (event.key === window.ConceptuumAlgebraCollection.KEY || event.key === null) { collection.reload(); renderCollection(); }
  });
  $('algebra-search').addEventListener('input', () => { clearTimeout(searchTimer); ++searchNumber; if (searchController) searchController.abort(); searchTimer = setTimeout(search, 200); });
  $('algebra-share').addEventListener('click', async () => {
    const url = queryURL().href;
    if (url.length > 7000) { toast('This query is too long for a link. Evaluate and download its JSON.'); return; }
    try { await navigator.clipboard.writeText(url); toast('Query link copied.'); }
    catch (_) {
      const field = el('textarea');
      field.value = url;
      field.style.cssText = 'position:fixed;left:-9999px;top:0';
      document.body.append(field); field.select();
      const copied = document.execCommand('copy'); field.remove();
      toast(copied ? 'Query link copied.' : 'Copy the query URL from the address bar after evaluating.');
    }
  });
  $('algebra-download').addEventListener('click', () => {
    if (!exportData) return;
    download(JSON.stringify(currentExample(), null, 2) + '\n', 'conceptuum-algebra-example.json', 'application/json');
    toast('JSON includes all matching concept IDs.');
  });
  window.addEventListener('popstate', () => { invalidate(); loadURL(); evaluate(0, urlInspection()); });
  fetch('/static/version.json', {cache: 'no-cache'}).then(response => response.ok ? response.json() : null).then(version => {
    if (!version) return;
    $('algebra-snapshot').textContent = `${version.data_revision} · ${Number(version.concepts).toLocaleString()} concepts`;
    $('algebra-version').textContent = `v${version.code_version} · UI ${version.interface_revision} · ${version.data_revision}`;
  }).catch(() => {});
  loadURL();
  renderCollection();
  evaluate(0, urlInspection());
})();
