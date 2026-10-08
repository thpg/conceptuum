# Filling and reviewing the concept graph

Applies to development version [0.1.0-dev](VERSION) and data revision Q7.
For running the project, start with the [README](README.md). For changing
data, use the [reviewed batch workflow](docs/fill-properties.md).

## Responsibilities

| Step | What can be checked mechanically | What still needs semantic review |
|---|---|---|
| Term lookup | Exact, normalized, and morphological matches | Whether the matches have the same meaning |
| Genus selection | Missing endpoints, cycles, redundant ancestors | The nearest appropriate genus and discourse |
| Relation validation | Signature, duplicate, and direction constraints encoded in `relevant` | Whether the statement is true and uses the right relation |
| Definitions | Generate a summary from accepted edges | Whether the underlying edges are sufficient and correct |
| Verification | Find stored paths or links with `verify()` | Confirm the claim independently of the graph |
| Inheritance | Traverse accepted genus edges | Scope, exceptions, and whether a property applies to descendants |

`resolve_fuzzy()` proposes matches; it does not decide identity. `verify()`
does not fact-check a claim against external evidence. Stronger models can
help draft candidates, but model choice is not an acceptance criterion.

## Recommended review loop

1. **Inventory an anchor and its surroundings.** Read its genera, children,
   incoming and outgoing links, terms, and explicit negations. Keep the
   original review cohort when comparing before and after.
2. **Generate candidate corrections or additions.** Start from known gaps,
   not a target number of concepts. Prefer existing meanings where they fit.
3. **Resolve meaning before identity.** Check homonyms and discourse-specific
   classifications. Verify doubtful words and senses in dictionaries; a
   plausible suffix or shared stem is insufficient.
4. **Review each assertion.** Check its nearest genus, relation code,
   direction, scope, and source. Leave strength unspecified without evidence
   for a degree. A structural pass does not replace this step.
5. **Prepare an explicit batch.** Record IDs, old values, reasons, term
   changes, and postconditions. Merges require full archives and explicit
   treatment of incoming links, children, context, and negations.
6. **Preview with rollback.** Validate all new relations, rebuild paths and
   definitions inside the transaction, then check semantics and preservation.
7. **Apply and verify.** Create a complete backup, save the same reviewed
   batch, verify through a new connection, check repeatability, and export
   the snapshot. Record results in the review report and changelog.

Batch related concepts where context can be shared. Batch size, acceptance
rate, and token cost are measurements to collect; the repository does not
establish a universal token-saving percentage or a fixed optimal batch size.

## Choosing the next area

Use the read-only auditors and the [roadmap](PLAN.md). Sparse hubs, weak leaf
definitions, missing translations, and suspicious genus assignments are
review candidates. A low count of properties does not by itself justify a
new assertion, and a high count does not show completeness.

`processed` is a historical fill level: 0 none, 1 taxonomy, 2 specific
properties, 3 parallel relations. It is neither an acceptance certificate
nor a lock against later review. `unprocessed(universum_id, below=...)`
filters this flag. `define()` returns leaves with genera but no listed
specific relations or species, and also writes the definition cache;
use an auditor for read-only inventory.

## Relation choices

Read the current `relevant` rows and [ontology rules](docs/ontology-rules.md).
The following distinctions prevent common filling errors:

| Code | Meaning | Direction / qualification |
|---|---|---|
| 14 | Genus | Species to nearest genus; keep the edge's universe |
| 15 | Essential attribute | Differentia, with an appropriate property object |
| 20 | Attribute or component | Whole/bearer to property or component |
| 21 | Purpose | Object to the activity it is for |
| 22 | Capability / bearer | Bearer to action or process |
| 23 | Material | Product/object to material |
| 24 | Intended content | Container/object to content |
| 25 | Application | Tool/object to what it acts upon |
| 26 | Intended user | Object to its user |
| 27 | Object of an action | Action/process to target object, property, or phenomenon |
| 30 / 40 / 60 | Equal scope / overlap / incompatibility | Check the rule's declared properties |
| 61 / 62 | Co-hyponyms / converse roles | Different relations; neither means causal cooperation |
| 63 / 64 | Contrary / contradictory | An intermediate value may exist only for contraries |
| 70 / 71 | Produces / hinders | Cause/preventer to effect; not a generic output-value link |
| 72 / 73 / 74 | Precedes / simultaneous / depends on | Preserve the intended relation and direction |

Only genus closure is materialized in `concept_path`. Do not assume other
codes are transitively inferred. `strength=0` is explicit negation, not a
low-confidence proposal. Adjectives, infinitives, and nouns are word forms;
their grammatical category does not determine whether a separate node is needed.

## Legacy LLM filler

[`fill_llm.py`](fill_llm.py) is a prototype rather than the reviewed-batch
pipeline above. Inspect prompts without a model call or database writes:

```bash
python fill_llm.py --universe 1 --max-anchors 3 --dry-run
```

This still needs a readable database connection. If no anchors have a
`processed` value below 1, there may be no prompts to print.

For experiments on a separate database, `--candidate` makes newly inserted
genus links and other relation edges candidates. It **still creates concepts
and terms, updates progress, and commits**; it is not a rollback mode.
Without `--candidate`, the prototype can accept generated data immediately.
The documented flags do not provide a semantic review or a complete backup.

The prototype does not implement every step described here. Its fuzzy
deduplication can conflate homonyms; it commits incrementally and uses
historical prompts. It should not be replayed over the reviewed snapshot as
routine maintenance. The separate batch runner provides explicit archives,
preconditions, rollback preview, and preservation checks.

## Completion evidence

- No new cycles, self-loops, missing endpoints, or signature violations.
- Correct and forbidden ancestry/relations checked for the changed meanings.
- Terms checked after a full reload, including language and database collation.
- Original explicit negations and required discourse contexts preserved.
- Backup, applied batch, before/after reports, and export checksum recorded.
- Remaining uncertainty recorded as follow-up work rather than filled with
  invented names, degrees, or relations.
