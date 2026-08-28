# LLM base-filling algorithm — maximum yield per token

Goal: fill a universe (concepts + validated relations) with an LLM at the
lowest possible token cost, without sacrificing graph quality.

Core principle: **the engine does everything deterministic; the LLM only
produces what the engine cannot** — candidate concepts and candidate
relations. The cheapest token is the one never sent.

## 1. Division of labour

| Task | Who | Cost |
|---|---|---|
| Term dedup, homonym detection | engine (`resolve_fuzzy`, lemma index) | 0 tokens |
| Relation validation (signatures, cycles, symmetry) | engine (`propose/validate`) | 0 tokens |
| Canonical definitions | engine (`define()` — genus + differentia) | 0 tokens |
| Transitive closure, inheritance | engine (`rebuild()`, `concept_path`) | 0 tokens |
| Verification of existing facts | engine (`verify()`) | 0 tokens |
| New concepts, terms, synonyms | LLM | tokens |
| New relations between concepts | LLM | tokens |
| Repair of rejected items | LLM (one batched pass) | tokens |

Never ask the LLM to: write definitions, check what is already in the base,
reformat output — all of that is local code.

## 2. The loop

```
frontier = priority_queue(seed_roots(universe))   # ordered by expected yield
known    = all_terms(universe)                     # local lemma index

while frontier and budget_left:
    anchor = frontier.pop()
    ctx    = children_terms(anchor)                # compact "already known" list

    # ---- call 1: EXPAND (breadth) --------------------------------------
    resp  = llm(expand_prompt(anchor, known_children=ctx, n=30))
    items = parse_lines(resp)                      # line format, see §3
    new, dup = partition(items, known, by=resolve_fuzzy)
    for c in new: engine.add_concept(c, parent=anchor, auto=True)

    # ---- call 2: RELATE (depth) — only if enough new material ----------
    if len(new) >= 8:
        pool  = new + ctx                          # concept terms only
        edges = parse_lines(llm(relate_prompt(pool, kod_menu)))
        for e in edges: engine.propose(e, auto=True)

    # ---- bookkeeping ----------------------------------------------------
    rejected -> repair_queue                       # with validation messages
    frontier.push(children_of(anchor), priority=expected_yield)
    known.update(new)
    if yield(anchor) < MIN_YIELD: prune_subtree(anchor)

# ---- final: one batched repair pass --------------------------------------
if repair_queue:
    resp = llm(repair_prompt(repair_queue))        # errors fed back verbatim
    for e in parse_lines(resp): engine.propose(e, auto=True)

engine.rebuild(); engine.define()                  # free, deterministic
```

### Frontier selection (where the savings come from)

Expansion anchors are chosen by the engine from local statistics, not by
asking the LLM "what is missing":

1. genus nodes with **few children** (thin branches of the tree);
2. concepts with a **weak defin** (no non-isa relations) — `define()`
   already returns them;
3. universe roots, then BFS downwards — general before specific.

A subtree is pruned when the last call's yield (new concepts / returned
items) drops below `MIN_YIELD ≈ 0.3` — the model is repeating what we
already have, so deeper expansion there is a token sink.

## 3. Wire format (token-lean)

No pretty JSON. One line per item, tab-separated, kods numeric:

```
# EXPAND response:  en_term <TAB> ru_term <TAB> parent_en [ <TAB> note ]
contract	law of obligations	legal act
# RELATE response:  subject_en <TAB> kod <TAB> object_en [ <TAB> strength ]
crime	70	criminal liability	95
plaintiff	62	defendant
```

Savings vs JSON: ~35–45% fewer output tokens (no keys, braces, quoting).
Parse errors are cheaper than the JSON overhead at this scale.

## 4. Prompt design

Three prompt types, all with an **invariant system prefix** (relation grammar,
kod menu, format rules, universe description) — this prefix is identical
across calls, so prompt caching (OpenAI/Anthropic automatic, llama.cpp
`cache_prompt`) makes its marginal cost near zero. Only the payload varies.

**EXPAND** (breadth-first skeleton):
```
System: [cached grammar + format rules]
Payload: "List up to 30 direct species of '<anchor>' in the <universe>
universe. Already known — do NOT repeat: <children terms, comma-separated>.
Format: en<TAB>ru<TAB>parent_en"
```

**RELATE** (non-isa edges among a pool):
```
Payload: "Concepts: <pool, comma-separated terms>.
List typed relations among them using only kods: 15 essential attribute,
21 inherent part, 61 coordinate, 62 converses, 63 contrary, 70 produces,
71 hinders, 72 precedes, 74 depends on, 80 purpose, 81 material,
82 agent, 83 patient. Format: subject<TAB>kod<TAB>object[<TAB>strength]"
```

**REPAIR** (batched, once at the end):
```
Payload: "These relations were rejected. Fix or drop each.
<item> — <validation error verbatim from engine.validate()>"
```

## 5. Rules that keep tokens down

1. **Dedupe before the call.** The "already known" children list prevents
   the model from re-generating existing concepts — the single biggest
   waste source. Without it, 30–60% of expansion output is duplicates.
2. **Never send the full base.** Context per call = one anchor + its
   children + (for RELATE) one pool of ≤ 40 terms.
3. **Batch, but not infinitely.** Sweet spot is 25–40 items per call:
   below that, prompt overhead dominates; above that, model quality and
   yield degrade and repair costs grow.
4. **RELATE only when there is material.** Skip the call if fewer than
   ~8 new concepts appeared.
5. **One repair pass, batched.** Feeding `validate()` messages back fixes
   most rejections; doing it per-item would multiply calls.
6. **Definitions are never generated by the LLM.** `define()` builds them
   canonically from the graph — genus + specific relations + species.
7. **Status discipline.** Auto-filled edges carry `source="llm:fill"`;
   anything the repair pass could not fix stays `candidate` for human or
   later strong-model review — do not burn tokens on it now.
8. **Source texts in one pass.** When filling from a dictionary article,
   extract everything in a single call: genus, both-language terms,
   synonyms, all relations. No per-aspect re-reads.

## 6. Token budget estimate

Assumptions: batch 30, line format, cached system prefix (~600 tokens,
counted once per session at providers with prompt caching; ~10% surcharge
at llama.cpp with `cache_prompt`).

Per call (EXPAND):
- in: payload ≈ 150–250 tok (anchor + ≤ 40 known children)
- out: 30 lines × ~12 tok ≈ 400 tok

Per universe of ~150 concepts (legal universe measured):
- EXPAND: ~6 calls ≈ 1.5k in + 2.4k out
- RELATE: ~4 calls ≈ 2k in + 2k out
- REPAIR: 1 call ≈ 1k in + 0.5k out
- **Total ≈ 9–10k tokens ≈ 60–70 tokens per stored concept**

For comparison: naive one-concept-per-call filling costs
~500–800 tokens per concept (definition + relations + repeats), and
produces worse definitions than the free `define()`.

## 7. Quality gates (engine-side, free)

- `propose()` rejects signature violations, duplicates, hierarchy cycles;
- after `rebuild()`: zero multi-parent, zero isa cycles (checked in the
  stage-9 revision);
- `define()` returns weak concepts → they become the next frontier;
- acceptance rate per call is logged; if it falls below ~70%, the prompt
  or batch size is adjusted before more tokens are spent.

## 8. What is deliberately NOT done

- No LLM-written definitions (engine does it deterministically).
- No LLM self-verification passes (engine `verify()` is exact and free).
- No chatty multi-turn dialogue — every call is one-shot stateless.
- No re-asking "what do you know about X" — the base itself is the
  record of what is known.
