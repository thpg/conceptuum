# Reviewing and filling properties

Current workflow for [0.1.0-dev](../VERSION), following the Q7 data review.
Read [ontology rules](ontology-rules.md) before editing meanings or relations.

## Start from a defined review area

Inventory the selected concepts, their direct genera, existing properties,
incoming links, and inherited assertions. Check whether a purported gap is
already represented under another term. Keep different meanings separate.

Attach a property to the broadest genus for which the reviewed claim holds.
Check descendants before doing so: a statement about a particular animal
group must not automatically become a statement about every organism.
An exception or a narrower target may require a species-level edge.
Preserve all existing `strength=0` negations. Leave the degree unspecified
unless its value has an evidence-based interpretation.

## Choose the relation by meaning

| Code | Role | Example pattern |
|---|---|---|
| 15 | Essential attribute | Concept to its distinguishing property |
| 20 | Attribute / component | Vehicle to wheel |
| 21 | Purpose | Bed to sleep |
| 22 | Capability / bearer | Mammal to sleep |
| 23 | Material | Product to its material |
| 24 | Intended content | Container to what it holds |
| 25 | Application | Tool to what it acts upon |
| 26 | Intended user | Object to the user it is designed for |
| 27 | Object of action | Sleep research to sleep |
| 70 / 71 / 74 | Produces / hinders / depends on | Review the exact causal or dependency claim |

The table describes roles; the current signature columns in `relevant`
determine permitted subject and object subtrees. In Q7, code 27 gained
phenomena as a possible object. A process's bearer and its target remain
different roles.

Do not expand a signature simply to get an existing edge accepted. First
check the meaning, genus, direction, and code. A legitimate grammar change
requires an exact before/after rule row, independent examples, rejected
counterexamples, and preservation checks for other rules.

## Prepare a reviewed batch

Use [the Q7 manifest](../tools/quality_20261008_q7.json) as a concrete example
of the format, not a list of changes to repeat on an unrelated database.

| Field | Purpose |
|---|---|
| `source` | Short revision identifier stored on new edges |
| `repairs` | Required list, possibly empty: edge IDs, expected old values, reasons, replacements |
| `edges` | Required list, possibly empty: explicitly reviewed additions |
| `concepts`, `renames`, `terms`, `remove_terms` | Reviewed concept and lexical changes |
| `checks`, `subtree_checks`, `term_checks` | Required/forbidden semantic outcomes |
| `leaf_merges` | Archived duplicates with only accepted positive outgoing genus links |
| `reviewed_merges`, `merge_routes` | Archived nodes with dependent links; one explicit route per old edge |
| `grammar_repairs` | Separately justified exact rule changes, if needed |

Use concept IDs after selecting their senses. New concepts use batch-local
keys until their IDs are assigned. Merge archives include full concept,
term, and edge rows. The runner refuses changed archives, lost routes,
unreviewed history, and negations in these merge procedures. Reusing a
destination edge requires the same accepted status and degree.

## Preview, apply, and verify

Configure a maintenance database account first. A rollback preview executes
writes inside a transaction and therefore needs write privileges.

```bash
python tools/apply_quality_batch.py tools/quality_20261008_q7.json --report preview.json
```

Without `--apply`, the runner rolls back. It validates new edges through
`propose`, rebuilds paths and definitions, and checks the batch's outcomes.
Confirm that the preview matches the intended changes and preserves existing
negations. A historical batch's old-value preconditions may reject a newer
snapshot; prepare a new reviewed batch instead of bypassing the checks.

To save a reviewed batch:

```bash
python tools/apply_quality_batch.py tools/quality_20261008_q7.json --apply --report applied.json
```

`--apply` requires `mariadb-dump` or `mysqldump`, and creates a full backup in
the `conceptuum-backups` directory next to the repository. The batch,
grammar changes, paths, and generated definitions share one transaction.
The runner writes the requested JSON report; updating the repository's SQL
export and changelog is a separate maintenance step.

After saving, use a fresh connection for the read-only audits:

```bash
python tools/audit_quality.py --output after.json
python tools/audit_upper_graph.py --scope-from docs/quality/2026-10-08-q7-upper-after.json --output upper.json
```

Also check changed definitions, search results, previous semantic conditions,
discourse context, and inherited assertions. Test a repeat preview for
unintended additions or losses. Export the database, compare the export with
its compressed copy if provided, and record checksums and backup locations.

## Historical scripts

`tools/fill_props1.py`, older `fill_*`/`fix_*` scripts, and automatic pruning
scripts describe earlier stages. Some directly changed signatures, attached
overbroad biological properties, or used superseded relation meanings.
They are not the current installation or maintenance instructions.

The former plan to widen several signatures and replay `fill_props1.py`
has been superseded by explicit review. Do not run old batches merely to
raise a fill count. Sparse but correctly scoped content remains preferable
to unsupported properties; track the missing facts for the next review.
