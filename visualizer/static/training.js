(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const types = {parents:'Direct genera', ancestry:'Ancestry chains', shared_genus:'Shared genera', intersection:'Intersections', difference:'Differences', count:'Counting', property:'Inherited properties', inference:'Valid and invalid inferences'};
  let batch = null;
  const excluded = new Set();
  function node(tag, text, className) {
    const item = document.createElement(tag);
    if (text !== undefined) item.textContent = text;
    if (className) item.className = className;
    return item;
  }
  for (const [value, label] of Object.entries(types)) {
    const wrapper = node('label'), input = node('input');
    input.type = 'checkbox'; input.value = value; input.checked = true;
    wrapper.append(input, document.createTextNode(label)); $('qa-tasks').append(wrapper);
  }
  const selected = () => batch ? batch.records.filter(record => !excluded.has(record.id)) : [];
  function updateSelection() {
    const count = selected().length;
    $('qa-selected').textContent = batch ? `${count} of ${batch.records.length} selected` : '';
    $('qa-chat').disabled = $('qa-annotated').disabled = count === 0;
    $('qa-report-download').disabled = !batch;
  }
  function render() {
    const report = batch.report;
    $('qa-snapshot').textContent = `${report.source.data_revision || 'Graph snapshot'} · ${report.source.interface_revision || 'QA generator'}`;
    $('qa-status').textContent = report.complete ? `${report.generated} examples generated and automatically checked.` : `Only ${report.generated} of ${report.requested} requested examples passed the checks for these options. No duplicates were added to fill the batch.`;
    const area = $('qa-report'); area.replaceChildren(); area.hidden = false;
    const summary = node('div', undefined, 'qa-summary');
    for (const [key, value] of Object.entries(report.tasks)) summary.append(node('span', `${types[key]} · ${value}`, 'qa-tag'));
    area.append(summary, node('p', 'Checked against source facts; world-fact review remains necessary.'));
    if (report.property_states && report.tasks.property) area.append(node('p', `Properties: ${Object.entries(report.property_states).map(([key,value]) => `${key} ${value}`).join(' · ')}. Conflict examples appear only when present in the source.`));
    for (const record of batch.records) {
      const card = node('article', undefined, 'qa-example'); card.lang = record.language;
      const top = node('div', undefined, 'qa-example-top'), include = node('label'), checkbox = node('input');
      checkbox.type = 'checkbox'; checkbox.checked = true; checkbox.setAttribute('aria-label', `Include example ${record.id}`);
      checkbox.addEventListener('change', () => { if (checkbox.checked) excluded.delete(record.id); else excluded.add(record.id); card.classList.toggle('excluded', !checkbox.checked); updateSelection(); });
      include.append(checkbox, document.createTextNode('Include'));
      top.append(node('span', types[record.task], 'qa-tag'), include);
      const details = node('details'), prompt = record.messages.slice(0,2).map(message => `${message.role.toUpperCase()}\n${message.content}`).join('\n\n');
      details.append(node('summary', `${record.grounding.facts.length} source edges · inspect training prompt`), node('pre', prompt));
      if (record.algebra) {
        const link = node('a', 'Inspect in concept algebra ↗');
        const query = new URLSearchParams({expr:record.algebra.expression, context:String(record.context), lang:record.language});
        if (record.algebra.within) query.set('within', record.algebra.within);
        link.href = `/algebra?${query}`; link.target = '_blank'; link.rel = 'noopener noreferrer'; details.append(link);
      }
      details.append(node('p', `Example ${record.id} · graph ${record.source.graph_sha256.slice(0,12)} · policy ${record.source.qa_policy_sha256.slice(0,12)}`));
      card.append(top, node('h3', record.question, 'qa-question'), node('p', record.answer, 'qa-answer'), details);
      $('qa-items').append(card);
    }
    updateSelection();
  }
  async function generate(event) {
    if (event) event.preventDefault();
    if (!$('qa-form').reportValidity()) return;
    const tasks = Array.from($('qa-tasks').querySelectorAll('input:checked'), input => input.value);
    if (!tasks.length) { $('qa-error').textContent = 'Choose at least one question type.'; $('qa-error').hidden = false; return; }
    batch = null; excluded.clear(); updateSelection();
    $('qa-items').replaceChildren(); $('qa-report').hidden = true; $('qa-error').hidden = true;
    $('qa-run').disabled = true; $('qa-results').setAttribute('aria-busy', 'true'); $('qa-status').textContent = 'Generating questions and checking their evidence…';
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 25000);
    try {
      const response = await fetch('/api/qa/generate', {method:'POST', headers:{'Content-Type':'application/json'}, signal:controller.signal,
        body:JSON.stringify({count:Number($('qa-count').value), seed:Number($('qa-seed').value), context:Number($('qa-context').value), lang:$('qa-language').value, root:$('qa-root').value ? Number($('qa-root').value) : null, tasks})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error && result.error.message || 'Generation failed. Please try again.');
      if (result.schema !== 'conceptuum.qa.batch.v1' || !Array.isArray(result.records) || !result.report) throw new Error('The server returned an incomplete batch.');
      batch = result; render();
    } catch (error) {
      batch = null; updateSelection(); $('qa-status').textContent = 'No batch is ready to export.';
      $('qa-error').textContent = error.name === 'AbortError' ? 'Generation timed out. Try a smaller batch.' : error.message; $('qa-error').hidden = false;
    } finally { clearTimeout(timer); $('qa-run').disabled = false; $('qa-results').setAttribute('aria-busy', 'false'); }
  }
  function download(mode) {
    if (!batch) return;
    const records = selected();
    const body = mode === 'report' ? JSON.stringify({...batch.report, exported:records.length, excluded_ids:Array.from(excluded), exported_ids:records.map(r=>r.id)}, null, 2) + '\n' : records.map(record => JSON.stringify(mode === 'chat' ? {messages:record.messages} : record)).join('\n') + '\n';
    const url = URL.createObjectURL(new Blob([body], {type:mode === 'report' ? 'application/json;charset=utf-8' : 'application/x-ndjson;charset=utf-8'}));
    const link = node('a'); link.href = url; link.download = `conceptuum-qa-${batch.report.language}-${batch.report.seed}-${mode}.${mode === 'report' ? 'json' : 'jsonl'}`;
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  $('qa-form').addEventListener('submit', generate);
  for (const [id, mode] of [['qa-chat','chat'],['qa-annotated','annotated'],['qa-report-download','report']]) $(id).addEventListener('click', () => download(mode));
  $('qa-preset').addEventListener('change', () => {
    const preset = $('qa-preset').value;
    $('qa-root').value = preset === 'flight' ? '105' : preset === 'containers' ? '3500' : '';
    $('qa-context').value = '1';
    const focus = preset === 'flight' ? ['parents','ancestry','property','inference'] : Object.keys(types);
    $('qa-tasks').querySelectorAll('input').forEach(input => { input.checked = focus.includes(input.value); });
  });
  if (new URLSearchParams(location.search).get('lang') === 'ru') $('qa-language').value = 'ru';
  generate();
})();
