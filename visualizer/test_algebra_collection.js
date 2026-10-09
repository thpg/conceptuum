const assert = require('assert').strict;
function test(name, fn) {
  try { fn(); console.log('PASS ' + name); }
  catch (error) { console.error('FAIL ' + name); throw error; }
}
const {Collection, KEY, MAX_BYTES, validate} = require('./static/algebra-collection.js');

function example(expression = '#1', question = '') {
  return {schema: 'conceptuum.algebra.example.v1', question,
    request: {expression, context: 1, lang: 'en', within: null, explain: null, limit: 1, offset: 0},
    result: {basis: 'catalog', expression, context: 1, kind: 'set', count: 3, ids: [1, 2, 3],
      items: [{id: 1, name: 'entity'}], ast: {kind: 'ref', value: {id: 1}}, language_version: '1',
      source: {data_revision: 'Q39', interface_revision: '2026-10-09.2', source_dump_sha256: 'abc'}}};
}
function storage() {
  const map = new Map();
  return {getItem: key => map.get(key) ?? null, setItem: (key, value) => map.set(key, value)};
}

test('snapshot copies keep full IDs and questions on one JSONL line', () => {
  const collection = new Collection(storage());
  const source = example('#1', 'Line one\n"quoted" <script> and русский текст');
  assert.equal(collection.add(source), true);
  source.result.ids.push(4);
  const lines = collection.jsonl().trim().split('\n');
  assert.equal(lines.length, 1);
  const saved = JSON.parse(lines[0]);
  assert.deepEqual(saved.result.ids, [1, 2, 3]);
  assert.equal(saved.question, source.question);
});

test('pagination does not duplicate an example, while another question or inspection does', () => {
  const collection = new Collection(storage());
  const source = example();
  collection.add(source);
  source.request.offset = 1;
  source.result.items = [{id: 2, name: 'next record'}];
  assert.equal(collection.add(source), false);
  source.question = 'Another wording';
  assert.equal(collection.add(source), true);
  source.request.explain = 2;
  assert.equal(collection.add(source), true);
  source.result.source.data_revision = 'Q40';
  assert.equal(collection.add(source), true);
  assert.equal(collection.entries.length, 4);
});

test('reload, cross-tab addition and removal preserve unrelated saved examples', () => {
  const shared = storage();
  const one = new Collection(shared), two = new Collection(shared);
  one.add(example('#1'));
  two.add(example('#2'));
  one.remove(1);
  assert.equal(one.entries.length, 1);
  assert.equal(one.entries[0].example.request.expression, '#2');
  const reloaded = new Collection(shared);
  assert.equal(reloaded.entries.length, 1);
});

test('scalar false and zero retain their types', () => {
  const collection = new Collection();
  for (const [kind, value] of [['boolean', false], ['integer', 0]]) {
    const source = example(kind);
    source.result.kind = kind;
    source.result.value = value;
    delete source.result.ids;
    collection.add(source);
  }
  assert.deepEqual(collection.entries.map(x => x.example.result.value), [false, 0]);
});

test('incomplete ID lists and mismatched request/answer pairs are rejected', () => {
  const partial = example(); partial.result.ids = [1];
  assert.throws(() => validate(partial), /every matching ID/);
  const repeated = example(); repeated.result.ids = [1, 1, 3];
  assert.throws(() => validate(repeated), /sorted order/);
  const mismatch = example(); mismatch.result.expression = '#2';
  assert.throws(() => validate(mismatch), /incomplete/);
  const scalar = example(); scalar.result.kind = 'boolean'; scalar.result.value = 'false';
  assert.throws(() => validate(scalar), /invalid answer/);
});

test('entry and byte limits leave existing examples intact', () => {
  const collection = new Collection(storage());
  for (let i = 1; i <= 50; i++) collection.add(example('#' + i));
  assert.throws(() => collection.add(example('#51')), /limit reached/);
  assert.equal(collection.entries.length, 50);
  const large = new Collection(storage());
  large.add(example());
  const oversized = example('#2'); oversized.result.extra = 'x'.repeat(MAX_BYTES);
  assert.throws(() => large.add(oversized), /limit reached/);
  assert.equal(large.entries.length, 1);
});

test('unavailable storage keeps a session collection that can still be exported', () => {
  const denied = {getItem() {throw Error('denied');}, setItem() {throw Error('denied');}};
  const collection = new Collection(denied);
  collection.add(example());
  assert.equal(collection.persistent, false);
  assert.match(collection.notice, /page session/);
  assert.equal(JSON.parse(collection.jsonl()).result.count, 3);
});

test('quota failure preserves existing snapshots and the newest in-memory example', () => {
  const full = storage();
  const collection = new Collection(full);
  collection.add(example());
  full.setItem = () => { throw Error('quota'); };
  collection.add(example('#2'));
  assert.equal(collection.persistent, false);
  assert.equal(collection.entries.length, 2);
  assert.equal(collection.jsonl().trim().split('\n').length, 2);
});

test('malformed stored data never replaces a valid in-memory collection', () => {
  const store = storage();
  const collection = new Collection(store);
  collection.add(example());
  store.setItem(KEY, '{broken');
  collection.reload();
  assert.equal(collection.entries.length, 1);
  assert.equal(collection.persistent, false);
});
