# Reviewing and filling properties

Current workflow for [0.1.0-dev](../VERSION), using the Q10 data review as an example.
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

## Use dictionaries as sense inventories

[Q11](quality/2026-10-09-q11.md) demonstrates dictionary-guided filling with
Open English WordNet 2025. Download a fixed edition from the official source,
record its checksum and license, and compare normalized English terms across
the complete inventory. Treat matches as review candidates, not equivalence.
Search existing Russian terms and inspect parents before deciding a concept
is absent. Keep raw downloads and exploratory candidates outside the repository.

Retain stable synset IDs and explicit reuse/add/defer decisions in the reviewed
manifest. Check every proposed synonym and genus: a dictionary can conflate
resistance and resistivity or preserve obsolete unit definitions. Use primary
subject sources where needed. Mark composed measurement phrases as ontology
adaptations, without claiming that they are standalone dictionary entries.
Preserve attribution when distributing dictionary-derived data.

[Q12](quality/2026-10-09-q12.md) continues the same source comparison and
distinguishes acceleration as a process from a physical quantity, and diameter
as a geometric segment from its length. A nearer genus can supersede an earlier
direct genus condition: document that change explicitly, preserve the broader
ancestor and applicable purpose relations, and check the remaining conditions.
Qualified labels can share ambiguous lookup terms without merging meanings.

[Q13](quality/2026-10-09-q13.md) separates numerical values from their written representations. A fraction's numerator, denominator, and bar can be components of its notation without being components of the abstract number. Record source corrections such as the equality boundary of improper fractions, and leave unsupported arithmetic predicates in review metadata.

[Q14](quality/2026-10-09-q14.md) checks dictionary instrument descriptions against quantity definitions and manufacturer evidence. Watt-hours measure energy; a wattmeter targets power. General pipettes transfer liquid, while calibrated subtypes also serve volume measurement. Record source restrictions and excluded synonyms explicitly.

[Q15](quality/2026-10-09-q15.md) separates geometric objects from their quantities and distinguishes component links from genus links. A disk includes a circle as its boundary; it is not a subtype of that circle. A chord is a finite segment, and a radius segment has a length. Preserve legitimate homonyms with qualified labels and record source hierarchy corrections.

[Q16](quality/2026-10-09-q16.md) distinguishes monetary resources, numerical amounts, actions, and plans. A payment action has an amount; the amount is not the action or the cash. Before adding dictionary labels, inspect existing action/quantity homonyms and archive any reviewed duplicate consolidation, including shared hierarchy edges and retained terms.

[Q17](quality/2026-10-09-q17.md) separates food preparation from heat cooking and general physical processes from their food-specific subtypes. Check inherited purposes and materials before adding a child: a measuring spoon must not inherit a mandatory eating purpose or steel construction. Manufacturer examples can refute a material restriction, but they do not establish population percentages. Keep tools, units, materials, actions and action products distinct.

[Q18](quality/2026-10-09-q18.md) checks positive genus witnesses against U1 exclusions as well as relation signatures. A shared descendant can reveal a false disjointness claim even when every edge passes the relation grammar. Review endpoint senses before changing the hierarchy; keep both legitimate parents of an intersection. A tool, its fastener, its physical thread feature and the installation action remain distinct concepts.

[Q19](quality/2026-10-09-q19.md) demonstrates resolving an exclusion conflict by splitting a mixed sense. Wednesday and environment need separate concepts; deleting the time/space exclusion would leave the actual error in place. Keep calendar systems, date representations, civil periods and scheduled events distinct, and qualify calendar-dependent assumptions.

[Q20](quality/2026-10-09-q20.md) separates material composition, physical state and action. A solution is not necessarily liquid, a state is not the substance in that state, and physical joining does not necessarily synthesize a chemical compound. Use qualified component roles and source-supported multiple genera; check exclusion witnesses before applying the batch.

[Q21](quality/2026-10-09-q21.md) separates leaf form, seasonal foliage and forest climate. Broadleaf does not mean deciduous, and rainforest does not mean tropical. Encode source-supported intersections with multiple genera; use component relations for mixed stands rather than claiming that both components dominate.

[Q22](quality/2026-10-09-q22.md) distinguishes conditions, processes, materials, quantities and information. Weather is a condition; falling precipitation is a process; precipitation depth is a quantity. A forecast is produced by forecasting, which does not produce the predicted weather. Qualify regional terms such as sleet and retain separate snow-depth and water-equivalent meanings.

[Q23](quality/2026-10-09-q23.md) separates a dwelling's purpose, a building's form and its components. A basement belongs to a building; it is not a kind of house. Give optional features to restricted subtypes. Room functions can overlap: a combined living room/bedroom and a bathroom with toilet facilities invalidate blanket exclusions.

[Q24](quality/2026-10-09-q24.md) classifies garments independently by purpose, material, form and components. Jeans are trousers and denim clothing; a rain jacket can also have a hood or zipper. Do not attach optional components to every garment, turn its material into its genus, or infer a protection rating from intended use.

[Q25](quality/2026-10-09-q25.md) keeps activities separate from their equipment: a card game is not a playing card, and a board game is not a game board. A racket has a sporting purpose; it does not perform the game. Classifications can overlap: tennis is both a ball sport and a racket sport, but badminton is not a ball sport. Social and physical action also describe compatible aspects.

[Q26](quality/2026-10-09-q26.md) distinguishes a group, a relation and a participant role: family is a group, kinship is a relation, and a relative is a person. Brother/sister are co-roles rather than converse roles; grandparent/grandchild are converses within the same relationship. Keep the reference person fixed when comparing genealogical degrees, and independently check suspect dictionary synonym sets.

[Q27](quality/2026-10-09-q27.md) separates visible radiation, environmental lighting state, illumination activity, perceived brightness and physical luminance. Use technical primary sources when a general dictionary combines these meanings. Classify quantities, units, measurements and meters separately; colour adjectives are not lighting processes.

[Q28](quality/2026-10-09-q28.md) keeps transitions, states, motion types and measured quantities distinct. Constant scalar speed does not imply constant vector velocity. Search Russian stems as well as English labels before adding a concept: generated braking records needed spelling and genus repairs, not duplicate entries.

[Q29](quality/2026-10-09-q29.md) separates fishing method, purpose, location, equipment and participant role. A fisher need not be a worker, and a generic net need not be fishing gear. Merge only fully archived, unconnected duplicates; preserve attested uncommon words instead of treating rarity as a spelling error.

[Q30](quality/2026-10-09-q30.md) extends existing bakeware and utensil families. Shape, construction and purpose are distinct axes; round springform moulds and combined openers have supported multiple genera. Review tool-versus-patient direction, spelling and broad/narrow synonym scope before importing a dictionary cluster.

[Q31](quality/2026-10-09-q31.md) keeps technical additions and assertions in U3. Case-insensitive dictionary matching must not merge physiological rest with REST architecture. Distinguish protocols, architectural styles, API restrictions, message types and software roles; verify context placement independently of general genus checks.

[Q32](quality/2026-10-09-q32.md) distinguishes public fame, familiarity and whether information is known. Qualified information objects can intersect by access, authorship and verification without being synonyms. Archive isolated duplicate records completely and preserve valid terms at the survivor.

[Q33](quality/2026-10-09-q33.md) separates states, processes, properties and emitted sounds. Reuse existing records where the sense is clear, archive mixed-sense terms before splitting, and preserve upper exclusions instead of deleting them to hide contradictions.

[Q34](quality/2026-10-09-q34.md) distinguishes physical hosts, software roles, components and operations. Client/server roles may overlap. Qualify a reverse proxy before inferring HTTP on both sides, and use a component relation instead of treating a caching proxy as a cache.

[Q35](quality/2026-10-09-q35.md) distinguishes managed data, software, structures, rules and operations. Reuse a Russian СУБД record before adding an English DBMS synonym. Check rename-generated aliases for wrong language tags, and preserve the correctly tagged source term.

[Q36](quality/2026-10-09-q36.md) separates roles from taxonomy, actions from results, and participant roles from occupations. A dictionary genus can be too narrow: predators are not necessarily mammals, hunters are not necessarily workers, and bait is not necessarily a manufactured device.

[Q37](quality/2026-10-09-q37.md) checks dictionary physics against domain sources. Pure translation can follow curved paths; angular momentum is distinct from linear momentum; torque is distinct from force. Preserve the difference between an action causing motion, the motion itself, its geometric path and its measured quantities.

[Q38](quality/2026-10-09-q38.md) uses technical sources when ordinary dictionary senses do not cover database meanings. Keep schema namespaces separate from descriptions, algorithms separate from execution, and constraint rules separate from the column sets they govern. Reuse the existing general plan across contexts instead of duplicating it.

[Q39](quality/2026-10-09-q39.md) separates container form, body material and intended use. Put universal material claims on explicit subtypes, distinguish a tool from its use, and review Russian infinitives before merging similar generated nouns. Dictionary construction details need counterexample checks against real tools.

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

Use [the Q10 manifest](../tools/quality_20261009_q10.json) as a concrete example
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
python tools/apply_quality_batch.py tools/quality_20261009_q10.json --report preview.json
```

Without `--apply`, the runner rolls back. It validates new edges through
`propose`, rebuilds paths and definitions, and checks the batch's outcomes.
Confirm that the preview matches the intended changes and preserves existing
negations. A historical batch's old-value preconditions may reject a newer
snapshot; prepare a new reviewed batch instead of bypassing the checks.

To save a new reviewed batch (replace the historical example path with your batch):

```bash
python tools/apply_quality_batch.py tools/quality_20261009_q10.json --apply --report applied.json
```

`--apply` requires `mariadb-dump` or `mysqldump`, and creates a full backup in
the `conceptuum-backups` directory next to the repository. The batch,
grammar changes, paths, and generated definitions share one transaction.
The runner writes the requested JSON report; updating the repository's SQL
export and changelog is a separate maintenance step.

After saving, use a fresh connection for the read-only audits:

```bash
python tools/audit_quality.py --output after.json
python tools/audit_upper_graph.py --output upper.json
```

For a fixed before/after scope, keep the first upper-graph report and pass it
with `--scope-from` when auditing the later snapshot.

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
