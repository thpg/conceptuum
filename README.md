# conceptuum

A relational knowledge base of **logical relations between concepts** — genus–species,
part–whole, cause–effect, opposition, purpose — across domain universes
(everyday, scientific, IT, legal). Designed as a **grounding layer for LLMs**:
machine-readable definitions, a validated relation grammar, and an LLM-driven
filling engine.

## Idea

Every concept is defined by the classical rule *genus + differentia*:
its parent genus, its specific relations, and its species (children).
Relations follow a formal grammar — typed signatures, symmetry, transitivity,
inverse pairs — validated at insert time. A transitive-closure table
(`concept_path`) gives instant ancestor/descendant queries.

An LLM uses the engine to:

- **verify** facts against the graph (e.g. "is ice really a result of freezing water?")
- **propose** new relations — validated automatically against the grammar
- **define** any concept canonically: `genus; specific relations. Species: …`
- **fill the base** from dictionaries or its own knowledge, at scale

This reduces hallucinations and gives the model a structured, inspectable
long-term memory of a domain.

### Built once by a strong model, used everywhere by small ones

The base is designed for an asymmetric workflow:

- **Preparation (offline, expensive):** a powerful LLM fills and revises the
  base — extracting concepts and relations from dictionaries and corpora,
  resolving synonyms, validating against the grammar, fixing misplacements.
  This happens once per domain and costs frontier-model tokens.
- **Usage (runtime, cheap):** a small local model (or a plain rules engine, or
  no model at all) queries the result — `verify()`, `define()`, ancestor
  lookups are plain SQL over `concept_path`. A 1–3B parameter model augmented
  with canonical definitions and verified relations can answer with the
  factual reliability that would otherwise require a much larger model.

In other words: **pay the intelligence cost once, at build time** — then serve
structured, deterministic knowledge to any number of cheap runtimes.

The full set of filling/maintenance rules, with the error log that motivated
them, lives in [docs/ontology-rules.md](docs/ontology-rules.md).

## Relation kinds

The grammar distinguishes several families of logical relations:

- **Taxonomic** (14 — *genus / is-a*): the backbone hierarchy.
  `dog is-a mammal`. Transitive; a closure table makes ancestor and
  descendant queries O(1) lookups. One meaning is one concept; when
  scientific and everyday classifications diverge, the same concept
  has two genera, each tagged with a universum (физическое явление /
  видимое). True homonyms (different meanings) stay separate nodes.
- **Attributive / part-whole spectrum** (15, 21–27): from *essential
  attribute* (without which the concept is not itself) through *inherent*
  (inseparable part or phase — "wheel of a car", "parsing phase of
  compilation") down to *frequent / occasional / rare* attributes.
  The same kod family covers both physical parts and process phases.
- **Compatibility** (30, 43–48, 60): coextensive concepts, graded overlap,
  incompatibility.
- **Logical opposition** (61–64): *coordinate* (co-hyponyms under one genus),
  *converses* (mutually implying — "buy/sell"), *contrary* (hot/cold),
  *contradictory* (true/false).
- **Causal & temporal** (70–74): *produces*, *hinders*, *precedes*,
  *simultaneous with*, *depends on*.
- **Functional** (80–83): *purpose* ("hammer → hammering"), *material*
  ("table ← wood"), *agent*, *patient* (object of action).
- **Contextual** (11–12): universe (discourse context) and domain membership.

Symmetric relations (61–64, 73) are stored once and queried both ways.
Each relation type declares a **signature** — which subtrees its subject and
object must belong to — so the engine rejects category errors at insert time
(e.g. only an action can *produce* something).

## Schema (MariaDB)

| Table | Purpose |
|---|---|
| `universum` | Domain contexts (everyday / scientific / IT / legal) |
| `concept` | Concepts: id (`dharma`), label (`nama`), cached definition (`defin`), universum, property passport, `processed` flag (genus + general properties + species specified; additions and side relations still possible) |
| `concept_term` | Multilingual terms per concept (`lang` codes) — real names live here |
| `relevant` | Grammar of relation types: signatures (up to 4 allowed subject/object subtrees), symmetry, transitivity, inverse codes |
| `edge` | Typed relations between concepts: `dh1 —[kod]→ dh2`, strength, status, source, rationale |
| `concept_path` | Transitive closure of the genus relation (kod 14) |

## Relation codes (table `relevant`)

| Code | Relation | Properties |
|---|---|---|
| 11 | universe (discourse context) | |
| 12 | domain-related | |
| 14 | genus (is-a) | transitive; closure table `concept_path` |
| 15 | essential attribute | |
| 20 | attribute (quality / component / capability) | degree lives in `edge.strength` (0–100), not in the code; attribute kind is derived from the object's root |
| 21 / 22 | function (purpose) / agent (capable of) | both artifact → action |
| 23 | material | artifact → substance |
| 24 / 25 / 26 | telic: content (чашка—кофе) / application (открывалка—бутылка) / user (будка—собака) | |
| 27 | patient (object of action) | action → object |
| 30 | coextensive (equal scope) | |
| 40 | overlap | symmetric; degree in `strength` (70 strong / 50 half / 5 slight / NULL possible) |
| 60 | incompatible | |
| 61 | coordinate (co-hyponyms) | symmetric |
| 62 | mutually implying (converses) | symmetric |
| 63 / 64 | contrary / contradictory | symmetric |
| 70 / 71 | causal (produces) / hindrance | |
| 72 / 73 | temporal precedence / simultaneity | 73 symmetric |
| 74 | dependence | |

Deprecated codes kept for history: 10, 13, 41, 43, 45, 47, 48, 49, 80, 81, 82, 83
(the 8X series moved into 2X on 2026-08-28; degree codes 21/23/25/27 of the
old scheme merged into 20 and overlap baskets 43–48 merged into 40, with the
degree stored in `edge.strength`).

### Design notes (why the code set looks like this)

- **Degree is data, not code.** Frequency ("always / usually / sometimes /
  rarely") is a property of the individual edge, so it lives in
  `edge.strength` (0–100). Rendering maps it back to words.
- **Derivable distinctions are not coded.** Attribute kinds (quality vs
  component vs capability) are read from the object's subtree root
  (property / artifact / action), and property classes (physical,
  measurable, evaluative, mental, state) are modeled as taxonomy nodes,
  not relation codes.
- **A code exists only where the same signature pair carries two different
  semantics.** That's why material (23) and content (24) are separate:
  "чашка — фарфор" (made of) vs "чашка — кофе" (for holding) share the
  artifact→substance signature, and only the code tells them apart.
  Same for application (25) and user (26) vs plain components.
- **part-of ≠ made-of.** A part is localized and detachable (чашка с
  ручкой); a material is the substrate of the whole (чашка фарфоровая).
  Mixing them breaks transitive inference.
- **Ternary facts are virtual.** "чашка — для питья — кофе" is stored as
  two binary edges (purpose + patient) and rendered as a phrase; the verb
  stays a first-class concept with its own relations.
- **Attach properties at the highest applicable genus.** "Фарфоровая
  чашка" inherits material from посуда; a species-level edge repeating the
  genus property is redundant and gets pruned. Redundancy requires the
  **same relation code and the exact same object** on an ancestor: a
  species edge whose object is a *subtype* of the genus's object is a
  specialization, not a duplicate (птица—полёт stays even though
  животное—движение exists, since полёт isa движение). Exception that
  keeps even an exact duplicate: the species frequency deviates
  noticeably (≈25+ points) from the genus value — e.g. пчела—полёт 95%
  is kept against насекомое—полёт 60%.
  `validate()` warns about inherited duplicates at insert time;
  `tools/prune_inherited.py` cleans exact duplicates,
  `tools/restore_prune.py` rolls back over-pruning.
- **Negation is strength = 0.** An attribute edge with strength 0 is an
  explicit exception/negative fact that overrides genus inheritance:
  пингвин —[22]→ полёт (0) renders as "not capable of: полёт" and cancels
  the inherited "птица — capable of: полёт (95%)". Works for essential
  negative properties too: змея —[20]→ лапа (0) renders "no: лапа".
  Negated edges are not flagged as redundant and are skipped in the
  incoming direction (a negation says something about the subject, not
  about the object).
- **Terms do not change the taxonomy.** Adjective / noun / infinitive /
  gender are Russian surface forms of one concept, stored in
  `concept_term`. «Судоходное» and «судоходство» are the same node; the
  word form names a relation already coded in `relevant` (водоём —[20]→
  судоходство), it does not make a species of водоём. Same for verbs:
  aspect pairs, reflexives, and the deverbal noun (отклонить / отклонять /
  отклоняться / отклонение; влиять / влияние) are one concept. Canonical
  label: deverbal noun when it exists. Maintenance: `tools/merge_verbs.py`,
  `tools/neuter_adjectives.py`. The closed-bearer reparenting
  (`судоходное` → водоём) was a mistaken next step and is retracted;
  see [docs/ontology-rules.md](docs/ontology-rules.md).

## Engine

`jnana_engine.py` — class `JnanaEngine`:

- `resolve(term, lang=None)` / `resolve_all(term, lang=None)` — term lookup,
  all homonyms across universes
- `resolve_fuzzy(token, lang=None)` / `resolve_phrase_fuzzy(phrase, lang=None)` —
  morphological lookup: pymorphy3 lemma index (ru) + prefix/skeleton fallback
- `add_concept(nama, parent, …, terms=[(term, lang), …])`
- `verify(t1, t2)` — check a statement against the graph (incl. inheritance
  and 2-hop indirect paths)
- `propose(t1, kod, t2, …, auto=True)` — grammar-validated relation insert
- `rebuild()` — rebuild transitive closure
- `define()` — regenerate canonical definitions
- `stats()` — base statistics

`JnanaEngine(pref_lang="en")` renders definitions in the chosen language
whenever terms in that language exist in `concept_term`.

Requires: Python 3.8+, `pymysql`, `pymorphy3` (optional — Russian morphology;
without it matching falls back to exact + prefix), a running MariaDB/MySQL
with the loaded dump.

## Quick start

```sql
CREATE DATABASE jnana3 CHARACTER SET utf8mb4;
```

```bash
mysql -u root -p jnana3 < jnana3_dump.sql
```

```python
from jnana_engine import JnanaEngine
eng = JnanaEngine(pref_lang="en")
eng.verify("ice", "freezing")
# ('yes', 'ice <-[causal (produces)] freezing', [])
eng.resolve_fuzzy("камня", lang="ru")   # -> [камень] via pymorphy3 lemma
```

Definitions and the relation grammar are in English; concept terms are
multilingual (`concept_term.lang` — ru+en for the everyday and legal
universes, en for IT).

## Demo: grounded QA (`ask.py`)

```bash
python ask.py "Why does water turn into ice?" --no-llm
```

With a local model running (Ollama / llama.cpp / LM Studio — any
OpenAI-compatible endpoint):

```bash
python ask.py "Что порождает юридическую ответственность?" \
    --endpoint http://localhost:8090/v1 --model local
```

### Retrieval pipeline

1. **Term extraction** — 1–3-word n-grams from the question are looked up in
   `concept_term`. The question's language (auto-detected, `--lang`
   overrides) is searched first; other languages are a fallback.
2. **Morphological normalization** — three levels: exact match → lemma index
   (`pymorphy3` for Russian: *камня → камень*, *юридическую ответственность*
   hits the term *юридическая ответственность*) → prefix/consonant-skeleton
   match (English inflection and vowel-drop roots).
3. **Homonym filter** — of the matched concepts, only the largest cluster
   connected by graph edges (direct or via a shared neighbour) is kept;
   isolated matches are dropped as noise (*"turn" → поворот* in a question
   about ice). Homonyms across universes are all returned — the LLM picks
   the one fitting its context.
4. **RELATED block (1 hop)** — grounding is extended with one-step
   neighbours: non-isa relations in both directions and the isa parent.
   This covers transitive inference (*кража → преступление → produces:
   наказание*) and "who/what is related to X" questions (*обвинение* pulls
   in *прокурор — purpose: обвинение*).
5. **Grounded generation** — the FACTS + RELATED blocks are injected into
   the prompt; the small model is instructed to answer only from them and
   to say plainly when facts are insufficient.

Real grounded answers (Qwen3-4B, llama.cpp):

> **Q: Что порождает кража?** — Кража — преступление. Преступление
> порождает наказание и уголовную ответственность. Следовательно, кража
> порождает наказание и уголовную ответственность.

> **Q: Can I drink what ice becomes when it melts?** — Yes. Melting
> produces water (таяние produces вода, 80%), drinking is directed at
> water (питьё directed at вода, 90%) — so the water from melted ice can
> be drunk.

## Experiment: in-stream fact injection (`interleave.py`)

An alternative to prompt-time grounding: word-by-word generation where
every model word matching a known concept gets a base fact injected
in square brackets, and generation continues with the extended context.
Two modes:

- `--think` (default) — facts are injected into a `<think>…</think>`
  reasoning block; the final answer after `</think>` is written clean.
  This avoids format mimicry (the model copying the bracket/percentage
  style of injections into the visible answer).
- `--no-think` — facts directly in the answer stream.

```bash
python interleave.py "Почему вода превращается в лёд?" --endpoint http://localhost:8090
```

Findings: injection works mechanically and small models do use injected
facts, but in-stream injection pollutes the context (homonym noise,
format mimicry); the think-block variant fixes the visible answer.

## Visualizer (Go)

`visualizer/` — a small self-contained web viewer for the base:

- searchable concept list (ru/en terms, exact match first)
- click a concept → dependency tree: all genera upward (DAG — two
  discourses of the same concept show as two parent branches, labelled
  by universum), species tree downward (tidy SVG layout, click any node
  to re-center)
- concept card: canonical definition (genus + differentia + species),
  terms by language, all typed relations with direction and strength

Run:

```bash
cd visualizer
go run .        # or: go build -o conceptuum-viz.exe . && ./conceptuum-viz.exe
# opens http://localhost:7100/
```

DB connection defaults to `root:123@tcp(127.0.0.1:3306)/jnana3`,
override with the `JNANA_DSN` environment variable.

## Current state

~1980 concepts, ~2650 relations, ~8800 closure paths.
Universes: everyday (956, ru+en), IT (882, en — auto-filled from the
Computer Hope dictionary with an LLM revision pass), legal (139, ru+en —
general theory of law: norms, sources, legal relations, offenses,
liability, judiciary).

## Status

Experimental research project. The filling engine is LLM-driven; auto-extracted
relations are marked by `source` and are meant to be revisable.
