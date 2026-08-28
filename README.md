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

## Schema (MariaDB)

| Table | Purpose |
|---|---|
| `universum` | Domain contexts (everyday / scientific / IT) |
| `concept` | Concepts: id (`dharma`), label (`nama`), cached definition (`defin`), universum, property passport |
| `concept_term` | Multilingual terms per concept (`lang` codes) — real names live here |
| `relevant` | Grammar of relation types: signatures (allowed subject/object subtrees), symmetry, transitivity, inverse codes |
| `edge` | Typed relations between concepts: `dh1 —[kod]→ dh2`, strength, status, source, rationale |
| `concept_path` | Transitive closure of the genus relation (kod 14) |

## Engine

`jnana_engine.py` — class `JnanaEngine`:

- `resolve(term)` / `add_concept(nama, parent, …)`
- `verify(t1, kod, t2)` — check a statement against the graph (incl. inheritance)
- `propose(t1, kod, t2, …, auto=True)` — grammar-validated relation insert
- `rebuild()` — rebuild transitive closure
- `define()` — regenerate canonical definitions
- `stats()` — base statistics

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
eng = JnanaEngine()
print(eng.define('Java'))
# Java — object-oriented programming language; соподчинено с: Python
```

## Current state

~1150 concepts, ~1400 relations, ~5000 closure paths.
Universes: everyday (ru), IT (en, auto-filled from the Computer Hope dictionary
with a subsequent LLM revision pass).

## Status

Experimental research project. The filling engine is LLM-driven; auto-extracted
relations are marked by `source` and are meant to be revisable.
