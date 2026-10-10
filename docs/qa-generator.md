# Question–answer generator

Open the [online generator](https://conceptuum.su/training), or start the
[local viewer and Python worker](../README.md#4-start-the-visualizer-optional)
and open `/training`. It creates questions,
answers and the facts needed to derive each answer. Choose English or Russian,
a graph context, a seed, question types and an optional focus concept. Review
the cards, uncheck unwanted examples, then download training JSONL or annotated
JSONL with evidence. The selection lasts for the current page session.

The generator uses graph algorithms and controlled templates. It requires no
LLM server and does not send questions to an external model.

The published site and bundled snapshot use Q40 and interface revision
2026-10-10.1. See the [publication record](quality/2026-10-10-q40.md#publication).

## Command line

Install the [project requirements and database](setup.md), then run from the
repository root:

```sh
python -m concept_algebra.qa --count 200 --seed 42 --lang en --output qa-en.jsonl --messages-output qa-en-sft.jsonl --report qa-en-report.json
python -m concept_algebra.qa --count 200 --seed 42 --lang ru --output qa-ru.jsonl --messages-output qa-ru-sft.jsonl --report qa-ru-report.json
```

Use `--root 105 --tasks ancestry property inference` to focus on birds and their
recorded capabilities. Focus selects starting concepts from the root's catalog
set; their ancestors, related comparison sets and evidence may lie outside it.
`--context` selects one relation context, from 1 to 5. Contexts are never mixed.
`--snapshot graph.json` uses the same frozen graph format as
[concept algebra](concept-algebra.md). Output files must be distinct; existing
files require `--force`. Snapshot and version input files cannot be overwritten.

CLI batches allow 1–2,000 examples; the website allows 1–50. Exit status is 0
for a complete batch, 3 when too few suitable examples exist, and 2 for invalid
input or an export error. A short batch is saved with `complete: false`; it is
never padded with duplicate questions. The same graph, policy, options and
generator version reproduce the same batch.

## Question types

| Task | What the model learns |
|---|---|
| `parents` | Read all directly recorded genera, including multiple parents |
| `ancestry` | Follow a transitive chain and recognize an unsupported reverse direction |
| `shared_genus` | Find common **direct** genera of two concepts |
| `intersection` | Find shared catalog members, including multiple inheritance |
| `difference` | Select catalog members belonging to one set but not the other |
| `count` | Count a union once per record, with irrelevant domain records present |
| `property` | Separate positive, negative, unknown and conflicting knowledge; apply overrides |
| `inference` | Distinguish supported common membership from unsupported disjointness or converse inclusion |

Question types are sampled in rotation, with separate positive/negative/unknown/
conflict property pools. Intersection candidates mix empty and witnessed results.
The report records the actual distribution; quotas are not guaranteed when
source evidence or suitable labels are missing. Conflicts are emitted only when
present in the source graph; synthetic regression fixtures are not mixed into
real training exports.

## Training format

`--messages-output` and **Training JSONL** produce one object per line:

```json
{"messages":[{"role":"system","content":"Rules for interpreting the supplied graph facts…"},{"role":"user","content":"Question, concept IDs, source facts and any finite catalog domain…"},{"role":"assistant","content":"Computed answer and supporting edge IDs where applicable…"}]}
```

This is an illustrative schema, not a literal training example. Each real row
contains complete strings. Keep the system instructions and the user evidence
with the answer: training on the bare question alone changes the task into
memorizing an incomplete graph. Apply your model's chat template in your own
training pipeline. Train the assistant response with your trainer's appropriate
loss masking; no tokenizer or model-specific special tokens are inserted here.

Annotated output uses schema `conceptuum.qa.v1` and additionally contains:

- `question`, `answer`, `task`, `language`, `context` and machine-readable `spec`;
- `grounding`: exact concept IDs and stored labels, source-edge IDs and strengths,
  the finite domain and the scope of the supplied premises;
- `expected`: the typed result and effective/overridden property evidence;
- `algebra`: a reproducible query and domain, where applicable;
- `source`: data and interface revisions, declared SQL hash, actual graph hash,
  policy hash and generator version;
- `id`, `group_id`, `messages` and automatic-check results in `quality`.

The actual graph hash covers concepts, terms, accepted edges and relation codes
in the selected context. The SQL hash is version-file metadata, not a runtime
proof that a database was imported from that exact dump. A missing version file
does not invent a revision: actual graph and policy fingerprints are still
present. Changing policy or graph content changes example IDs.

## Adequacy checks and limits

Every generated answer is recomputed by a separate solver that reads only the
facts included in that example. Source edges and labels are checked against the
loaded graph. Catalog and property answers are also cross-checked with concept
algebra; logical sufficiency questions use explicit inference rules instead.
Property evidence must match the complete graph, including overridden assertions.

The generator rejects missing or unsuitable labels, cyclic supplied genus
premises, oversized evidence, duplicate questions and known problematic source
assertions. Each example is limited to 36 facts, 24 domain records and 24 KiB
of annotated JSON. See the versioned [selection policy](../concept_algebra/qa_policy.json).

The default policy also requires a usable English term for every referenced
concept, including Russian examples. This conservative coverage filter excludes
many legacy records whose English column contains a Cyrillic source verb. It is
not a spelling dictionary and can omit valid untranslated concepts. Russian
canonical names and selected reviewed English terms are preferred over shorter
aliases that change the part of speech or suggest another sense.

An automatic pass means consistency with supplied records, **not independently
certified world knowledge**. Source strengths are not probabilities or universal
quantifiers. An empty catalog intersection does not establish real-world
disjointness, and no applicable property assertion means unknown rather than
negative. The [adequacy review](quality/2026-10-10-qa-review.md) describes the
pilot, detected issues and the scope of semantic inspection.

Keep `group_id` together when splitting training and evaluation data, including
language variants. Shared ancestors, targets and evidence can still cross groups;
inspect those overlaps before claiming held-out concepts. Templates and task
families also repeat. A large generated batch is not automatically a diverse
benchmark, and no model improvement is established merely by generating it.

## Python and HTTP

```python
from concept_algebra import ConceptGraph
from concept_algebra.qa import QuestionGenerator
from concept_algebra.qa_check import verify_record

graph = ConceptGraph.from_database(context=1)
batch = QuestionGenerator(graph, language="en").generate(count=200, seed=42)
assert all(not verify_record(record, graph) for record in batch["records"])
```

`verify_record` recomputes answers, checks wording and chat messages, and, when
given a graph, checks source fidelity and completeness for catalog/property/
direct-genus queries. It does not certify record hashes, review policy or world
facts when independently inspecting an arbitrary imported record.

The Go site proxies `POST /api/qa/generate` to the existing loopback Python
worker's `/generate` endpoint. Both the generator and algebra use the same worker
and graph cache. The JSON request accepts only `count`, `seed`, `lang`, `context`,
`root` and `tasks`; the response contains `records` and a batch quality `report`.
See the [visualizer setup](../visualizer/README.md). Generation only reads data.
