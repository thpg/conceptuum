/* Browser-local examples. Pure collection rules are also exercised by Node tests. */
((root, factory) => {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ConceptuumAlgebraCollection = api;
})(typeof globalThis === 'object' ? globalThis : this, () => {
  'use strict';
  const KEY = 'conceptuum-algebra-examples-v1';
  const MAX_EXAMPLES = 50;
  const MAX_BYTES = 4 * 1024 * 1024;
  const bytes = text => new TextEncoder().encode(text).length;

  function validate(example) {
    const request = example && example.request;
    const result = example && example.result;
    if (!example || example.schema !== 'conceptuum.algebra.example.v1' ||
        !request || typeof request.expression !== 'string' || !request.expression.length || request.expression.length > 8192 ||
        !Number.isInteger(request.context) || request.context < 1 || request.context > 5 ||
        !['en', 'ru', null].includes(request.lang) ||
        !(request.within === null || typeof request.within === 'string' && request.within.length <= 8192) ||
        !(request.explain === null || Number.isInteger(request.explain) && request.explain > 0) ||
        !result || result.basis !== 'catalog' || result.expression !== request.expression || result.context !== request.context ||
        !result.ast || !result.source || !['set', 'boolean', 'integer'].includes(result.kind) ||
        example.question !== undefined && (typeof example.question !== 'string' || example.question.length > 2000)) {
      throw new Error('This example is incomplete. Evaluate the expression again before saving.');
    }
    if (result.kind === 'set') {
      if (!Array.isArray(result.ids) || result.ids.length !== result.count ||
          result.ids.some((id, i) => !Number.isInteger(id) || id <= 0 || i > 0 && id <= result.ids[i - 1])) {
        throw new Error('A set example must contain every matching ID in sorted order.');
      }
    } else if (result.kind === 'boolean' ? typeof result.value !== 'boolean' : !Number.isInteger(result.value)) {
      throw new Error('This example has an invalid answer. Evaluate it again before saving.');
    }
  }

  function identity(example) {
    const {request, result} = example;
    return JSON.stringify([example.question || '', request.expression, request.context, request.lang,
      request.within, request.explain, result.source.code_version, result.source.interface_revision,
      result.source.data_revision, result.source.source_dump_sha256, result.language_version,
      result.kind, result.kind === 'set' ? result.ids : result.value]);
  }

  class Collection {
    constructor(storage) {
      this.storage = storage;
      this.entries = [];
      this.persistent = Boolean(storage);
      this.notice = '';
      this.reload();
    }

    reload() {
      if (!this.persistent) return;
      try {
        const text = this.storage.getItem(KEY);
        if (!text) { this.entries = []; return; }
        if (bytes(text) > MAX_BYTES) throw new Error('Collection exceeds the storage limit.');
        const data = JSON.parse(text);
        if (data.version !== 1 || !Array.isArray(data.entries) || data.entries.length > MAX_EXAMPLES) throw new Error('Invalid collection format.');
        const ids = new Set();
        for (const entry of data.entries) {
          if (!Number.isSafeInteger(entry.id) || entry.id <= 0 || ids.has(entry.id)) throw new Error('Invalid example ID.');
          ids.add(entry.id);
          validate(entry.example);
        }
        this.entries = data.entries;
      } catch (_) {
        this.persistent = false;
        this.notice = 'Browser storage is unavailable or unreadable. This collection lasts for this page session; export JSONL to keep it.';
      }
    }

    save(entries) {
      const text = JSON.stringify({version: 1, entries});
      if (entries.length > MAX_EXAMPLES || bytes(text) > MAX_BYTES) {
        throw new Error('Collection limit reached (50 examples or 4 MiB). Export JSONL, then remove examples to make room.');
      }
      this.entries = entries;
      if (!this.persistent) return;
      try { this.storage.setItem(KEY, text); }
      catch (_) {
        this.persistent = false;
        this.notice = 'Browser storage is full or unavailable. Current changes last for this page session; export JSONL to keep them.';
      }
    }

    add(example) {
      validate(example);
      this.reload();
      const key = identity(example);
      if (this.entries.some(entry => identity(entry.example) === key)) return false;
      const id = this.entries.reduce((maximum, entry) => Math.max(maximum, entry.id), 0) + 1;
      const copy = JSON.parse(JSON.stringify(example));
      this.save([...this.entries, {id, example: copy}]);
      return true;
    }

    remove(id) {
      this.reload();
      this.save(this.entries.filter(entry => entry.id !== id));
    }

    jsonl() {
      return this.entries.map(entry => JSON.stringify(entry.example)).join('\n') + (this.entries.length ? '\n' : '');
    }
  }
  return {Collection, KEY, MAX_EXAMPLES, MAX_BYTES, validate};
});
