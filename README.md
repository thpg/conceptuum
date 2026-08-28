# conceptuum

A relational knowledge base of **logical relations between concepts** — genus–species,
part–whole, cause–effect, opposition, purpose — across domain universes
(everyday, scientific, IT). Designed as a **grounding layer for LLMs**:
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

## Relation kinds

The grammar distinguishes several families of logical relations:

- **Taxonomic** (14 — *genus / is-a*): the backbone hierarchy.
  `dog is-a mammal`. Transitive; a closure table makes ancestor and
  descendant queries O(1) lookups. Every concept has exactly one genus
  (single inheritance keeps the tree navigable).
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
| `universum` | Domain contexts (everyday / scientific / IT) |
| `concept` | Concepts: id (`dharma`), label (`nama`), cached definition (`defin`), universum, property passport |
| `concept_term` | Multilingual terms per concept (`lang` codes) — real names live here |
| `relevant` | Grammar of relation types: signatures (allowed subject/object subtrees), symmetry, transitivity, inverse codes |
| `edge` | Typed relations between concepts: `dh1 —[kod]→ dh2`, strength, status, source, rationale |
| `concept_path` | Transitive closure of the genus relation (kod 14) |

## Relation codes (table `relevant`)

| Code | Relation | Properties |
|---|---|---|
| 11 | universe (discourse context) | |
| 12 | domain-related | |
| 14 | genus (is-a) | transitive; closure table `concept_path` |
| 15 | essential attribute | |
| 21 / 23 / 25 / 27 | inherent / frequent / occasional / rare attribute | part-whole spectrum |
| 30 | coextensive (equal scope) | |
| 43 / 45 / 47 / 48 | strong / equal / slight / possible overlap | |
| 60 | incompatible | |
| 61 | coordinate (co-hyponyms) | symmetric |
| 62 | mutually implying (converses) | symmetric |
| 63 / 64 | contrary / contradictory | symmetric |
| 70 / 71 | causal (produces) / hindrance | |
| 72 / 73 | temporal precedence / simultaneity | 73 symmetric |
| 74 | dependence | |
| 80 / 81 / 82 / 83 | function (purpose) / material / agent / patient | |

Deprecated codes kept for history: 10, 13, 20, 40, 41, 49.

## Engine

`jnana_engine.py` — class `JnanaEngine`:

- `resolve(term, lang=None)` / `add_concept(nama, parent, …)`
- `verify(t1, t2)` — check a statement against the graph (incl. inheritance
  and 2-hop indirect paths)
- `propose(t1, kod, t2, …, auto=True)` — grammar-validated relation insert
- `rebuild()` — rebuild transitive closure
- `define()` — regenerate canonical definitions
- `stats()` — base statistics

`JnanaEngine(pref_lang="en")` renders definitions in the chosen language
whenever terms in that language exist in `concept_term`.

Requires: Python 3.8+, `pymysql`, a running MariaDB/MySQL with the loaded dump.

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
eng.cur.execute("SELECT defin FROM concept WHERE nama='Java'")
# Java — object-oriented programming language; coordinate with: Python
```

Definitions and the relation grammar are in English; concept terms are
multilingual (`concept_term.lang` — currently ru+en for the everyday universe,
en for IT).

## Demo: grounded QA (`ask.py`)

```bash
python ask.py "Why does water turn into ice when it is cold?" --no-llm
# - water — liquid; object of: freezing
# - ice — solid; inherent: cold (95%); produced by: freezing
# - cold — temperature; coordinate with: warm; opposite: hot
```

With a local model running (Ollama / llama.cpp / LM Studio):

```bash
python ask.py "Why does water turn into ice?" --model qwen3:4b
```

The script finds concepts in the question, injects their verified definitions
as a FACTS block, and the small model answers from them — the
"built once by a strong model, used by small ones" workflow in action.

## Current state

~1150 concepts, ~1400 relations, ~5000 closure paths.
Universes: everyday (ru+en), IT (en, auto-filled from the Computer Hope
dictionary with a subsequent LLM revision pass).

## Status

Experimental research project. The filling engine is LLM-driven; auto-extracted
relations are marked by `source` and are meant to be revisable.
