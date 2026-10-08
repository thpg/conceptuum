# Ontology rules

Rules of thumb for filling and maintaining the concept base, distilled from
build sessions and audit fixes. Each rule comes with the error that motivated
it. Examples are Russian because the base content is Russian.

## 1. Concept identity

- **A concept is not a word.** Synonyms are one concept with several terms in
  `concept_term` (мотор / двигатель → one node, two terms). Never create two
  concepts for the same meaning. Abstract from the word to the concept:
  part of speech, gender, aspect, noun vs adjective vs infinitive are
  surface forms of Russian (or English), not taxonomic facts.
- **Verb forms share a concept when their meanings match.** Infinitive and
  deverbal noun can denote the same meaning (влиять / влияние,
  замерзать / замерзание). Aspect or reflexive morphology alone does not
  establish identity: review the selected senses before merging. Canonical
  name: the deverbal noun when it exists, otherwise the non-reflexive
  imperfective infinitive. Other forms live as terms. Word class must not
  pick the genus (infinitive → «действие», noun → «процесс»).
  *Error found:* 167 verb groups had been entered as separate concepts —
  merged by `tools/merge_verbs.py` (−281 concepts, +562 terms). Residual
  infinitive/noun twins under the same parent are the same debt.
- **Adjectives do not change the taxonomy.** An adjective is a Russian
  word form, not a node type. For the abstract concept there is no
  difference between «судоходное» and «судоходство»: the form of the word
  *denotes a relation*, and relations already live in `relevant`. Gender
  and number forms are terms of that same concept. Do not hang
  «кошачье», «июльское», «зимнее» as species of «принадлежность» /
  «месяц» / «сезон» — those are not kinds, they are edges (водоём —[20]→
  судоходство; пальто —[20]→ зима).
  *Error found:* 619 gender forms renamed by `tools/neuter_adjectives.py`
  (right direction: one node). `tools/fix_bearer.py` then made the
  adjective a *species of the bearer* (судоходное → водоём) — that was
  the wrong next step: it let a word form rewrite the tree.
- **Homonyms are separate concepts.** One term, several *meanings* — one
  concept per meaning (среда = environment vs Wednesday; положение =
  thesis vs spatial position; desktop = writing desk vs GUI). A term
  lookup must return **all** senses. This is not the same as one meaning
  classified two ways (see two genera below).
- **Language tags do not validate translations.** `ДОБЫВАТЬ` with `lang=en`
  is still Russian. Audit script content as well as language-tag presence.
  Latin letters are a useful screening criterion, not proof of a correct
  translation. Check existing senses before creating a replacement node:
  a missing English label can hide an existing Russian concept.
- **Verify doubtful words and their senses in dictionaries.** Morphological
  plausibility and a shared substring are not evidence for either existence
  or meaning. Do not manufacture a noun by replacing an infinitive ending.
  Prefer an established noun or a clear phrase for the canonical label;
  keep verified colloquial/bookish forms as search terms. Record the source
  and selected sense in the reviewed batch. For example, dictionary
  `завидеть` means seeing from a distance, `завидовать` concerns envy, and
  `перезреть` concerns ripening. A missing dictionary entry alone does not
  prove that a productive phrase is invalid.

## 2. Taxonomy (genus, kod 14)

- **Nearest genus, no skipping.** The genus is the *immediate* broader class:
  январь → месяц → период времени; север → сторона света → направление.
  Never январь → период времени directly.
- **Two genera when the senses of classification diverge.** Naive
  scientific taxonomy and everyday phenomenological taxonomy often place
  the same concept in different trees («физическое явление» vs
  «видимое»). That is still *one* concept: two kod-14 edges, each with
  its `universum_id`. Do not split the node. True homonyms (different
  meanings) stay two concepts; two views of one meaning stay one
  concept. The engine must treat isa as a DAG filtered by universum,
  not as a single-parent tree. The same direct genus can appear in two
  universes; preserve both contexts but list the child once. `rebuild` and
  `define` handle the DAG; the legacy `parent` cache selects a home genus.
- **Definitions follow the classical rule:** genus of the definiendum first,
  then its specific properties; species may be listed additionally. With
  two genera the definition is universum-relative. The `defin` column is
  **derived data** — never hand-edit it; fix edges instead.
- **Instance vs class is still is-a.** There is no "instance-of" relation
  between concepts: Лондон — столица is a species-of relation (Лондон is one
  of the set of столиц), kod 14 like any вид→род link.
- **«свойство» is logical analytics, not a taxonomic genus.** "Свойство" is
  not the genus of every property. Property *values* (real concepts, not
  adjective leftovers) go to their scale (красное → цвет, истинное →
  истинность); only terms of logic itself (качество, количество,
  распределённость термина, модальность, шкалы суждений) stay under
  «свойство». Same for «действие» and «отношение»: they are not dumping
  grounds. *Error found:* 489 direct children under «свойство» —
  dissolved by `tools/fix_genus4.py` (448 reparentings); 442 under
  «действие» — dissolved by `tools/fix_genus3.py`.
- **No closed-bearer-as-genus.** A property bound to one typical bearer
  is still the property, not a species of the bearer. Водоём —[20]→
  судоходство; животное —[20]→ хищность / охота. The adjective form
  does not make «судоходное» a kind of водоём.
- **A thing can be viewed as a property of its whole.** Колесо–автомобиль:
  колесо is a component-property of автомобиль (kod 20), not only a separate
  object node.
- **An occupation is not its practitioner.** Врач → медик → специалист →
  человек; профессия → труд. A professional performs an action (22):
  врач → лечение. A person's profession is not the genus of that person.
  Keep ремесло in the activity branch. Preserve other discourse-specific
  genera, for example the legal classification of адвокат.
- **Domain homonyms need a sense check before inheritance.** An object
  method is a function; a development method is a way of working. Neither
  spelling nor a matching English term justifies sharing their genus.
  Likewise a library can be a binary software component, so its genus
  must not require it to be source code.
- **Separate content, its carrier, and the process producing it.** Knowledge
  is informational content; cognition is a process that can produce knowledge.
  A thought as content is distinct from thinking. Physical attributes of a
  book do not become attributes of its information. Attach mass and spatial
  extension to the material branch, not to every object of discourse.
- **Coordinate concepts cannot be ancestor and descendant.** A word is a
  kind of sign; the two are not co-hyponyms. A part and its element subtype
  likewise cannot be connected by 61. Review both the genus and the parallel
  relation when reparenting an upper node.
- **Relational vs agentive is a distinction of concepts, not of word
  class.** Predicates that *express* relations (равняться, зависеть,
  принадлежать, предшествовать — and their nouns) stay under
  «отношение»; agentive actions (воздействовать / влияние) under
  «действие»; mutual processes (взаимодействие) under «процесс». The
  infinitive and the noun of the same concept follow that one genus.

## 3. Property attachment

- **Essential attribute (kod 15) is the differentia.** Object ⊂ «свойство»
  (теплокровность, съедобность); subject ⊂ предмет or явление. Do not use
  15 for parts or actions — those are 20/22. Process/state subjects are
  allowed because действие ⊂ явление (signature `sig_subject2=2535`).
- **Attach a property at the highest applicable genus.** Check that the
  claim holds for the intended descendants before moving it upwards.
  Porcelain is a material of some tableware; that does not make every cup
  porcelain. A species edge may record a justified exception, a supported
  degree difference, or a more specific target (птица—полёт vs
  животное—движение). There is no universal percentage threshold for keeping
  an override. Historical pruning scripts need review before reuse.
- **Negation is strength = 0.** An attribute edge with strength 0 is an
  explicit negative fact that overrides genus inheritance:
  пингвин —[22]→ полёт (0), змея —[20]→ лапа (0). Use it for essential
  negative properties too (несудоходное —[20]→ судоходство 0).
- **Degree is data, not code.** Frequency/intensity lives in
  `edge.strength` (0–100), not in relation codes.
- **material (23) ≠ content (24) ≠ component (20).** Чашка—фарфор (made of),
  чашка—кофе (for holding), чашка—ручка (has part) share similar signatures;
  only the code tells them apart. part-of ≠ made-of: a part is localized and
  detachable, a material is the substrate of the whole.
- **Whole-to-part facts need the right direction and scope.** Человек —[20]→
  тело человека; тело человека —[20]→ голова. Neither direction may be
  reversed. Human anatomy must not be inherited by every physical body.
- **Biological traits need an applicable bearer and a complete genus path.**
  Кровь and anatomical кожа belong with reviewed animal groups, not every
  организм. Млекопитающее → позвоночное → животное must be present before
  expecting vertebrate traits to reach mammals. Removing a broad claim does
  not create a negative fact for every unreviewed group. Кожа as an organ
  and кожа as leather are different meanings.
- **Ternary facts are virtual.** "Кофейная чашка — для питья — кофе" is two
  binary edges (purpose + patient); no ternary relation nodes.
- **An action's target differs from its bearer.** Code 27 can target a
  physical object, property or phenomenon: psychological research studies
  behavior; sleep research studies sleep. The sleeping animal is the bearer
  of sleep (22), not what sleep is directed at (27). An object of study does
  not become a property merely to fit the grammar. Signature changes require
  a meaning-based rationale, an exact reviewed rule delta, and checks of both
  accepted and refused examples; never relax a rule just to silence an audit.
- **Separate a mathematical operation, its result and its implementation.**
  Addition is an operation; a sum is a number. Mod is an operation, while
  «остаток от деления» names its numerical result. A mathematical function
  and a programming function have different genera. Code 70 expresses
  causation; do not use it as a general function-result relation.

## 4. Relations between concepts

- **Converses are mutually implying (62).** "Конверсионные" pairs are exactly
  "предполагающие друг друга": муж — жена, купить — продать. One code, not
  two.
- **63 (contrary) vs 64 (contradictory):** белый — чёрный have a middle
  (63); живой — мёртвый exhaust the domain (64). Use 64 for A / не-A pairs
  (судоходное — несудоходное, позвоночное — беспозвоночное).
- Negative relation nouns are first-class too: неравенство,
  непринадлежность under «отношение».

## 5. Universums

- **Universum = base discourse context**, not "the most general notion":
  бытовой, научный, биология, медицина, IT, юриспруденция, логика. The same
  pair may have different links per universum (томат — овощ in everyday,
  ягода in biology). When the *genus itself* differs by discourse, keep
  one concept and put the universum on the kod-14 edge, not on a second
  node. `concept.universum_id` is the home discourse (where the node was
  first entered), not a second identity. Special terms coined inside a
  domain still start there (термины логики → U5) unless they are the
  same meaning as an everyday node — then attach a second genus instead
  of cloning.
- Fill order: **from the more general to the more specific**, universum by
  universum; the everyday (бытовой) universum is the backbone.

- **`processed` is a fill level, not a lock.** 0 none; 1 genus and species;
  2 essential and specific properties (kod 15, 20–27); 3 parallel
  relations (coordinate 61, converses 62, contrary 63, contradictory 64,
  overlap 30/40, causal/temporal 70–74). Setting a level does not forbid
  later edges. `set_processed(cid, 2)` / `unprocessed(below=2)`.

## 6. Workflow rules

- **A strong model fills the base; small models consume it.** Do not use a
  small local LLM for real filling — quality of genus choice is the whole
  point. The base is the precomputed "thinking" that a small model grounds
  on at query time. Model strength does not replace evidence and semantic
  review; do not accept a generated assertion solely because of the model
  that produced it.
- **No lexeme corpus table.** It was designed as a manual-entry aid; now that
  LLMs do the filling, it is dead weight.
- After every change: `engine.rebuild()`, `engine.define()`, check
  `engine.stats()`; dump the DB (`jnana3_dump.sql`), log a row in
  `STATE.md`, commit locally.
- Fill scripts live in `tools/fill_*.py`, fix scripts in `tools/fix_*.py` —
  they are the audit trail; keep them in git.
- Track fill progress in `STATE.md` so a later session can resume.
- `rebuild()` and `define()` write and commit in the base engine. Use
  read-only auditors for inspection; the reviewed batch runner controls
  these writes within its transaction. Preserve canonical cache labels
  with `JnanaEngine()` unless changing the persisted definition language
  is an explicitly reviewed part of the task.

## 7. Error log (anti-patterns actually found)

| Error | Fix |
|---|---|
| Verb aspect/reflexive forms as separate concepts | merge_verbs.py: one concept, canonical noun |
| Masculine adjectives as concepts | neuter_adjectives.py: neuter canonical form |
| «свойство» as genus of 489 values/classes | fix_genus4.py: values→scales, adjectives→thematic genera |
| «действие» as genus of 442 heterogeneous verbs | fix_genus3.py: split by nearest genus |
| Skipped genus levels (январь → период времени) | fix_genus.py/2: nearest genus |
| Closed-bearer: adjective as species of bearer (судоходное → водоём) | Retracted: one concept судоходство/судоходное; relation in relevant, not isa |
| жидкое in «состояние» vs газообразное in «свойство» (inconsistent) | new genus «агрегатное состояние» |
| логический закон under «отношение» | → правило |
| воздействие/влияние under «отношение» | → действие; взаимодействие → процесс |
| Part → whole entered as purpose (21): подошва → обувь | Whole → part uses 20; a part is not a species of its whole |
| User's action entered as an artifact's ability: кровать → сон (22) | Purpose (21); the bed does not perform the sleeper's action |
| Homonyms resolved to the first matching term: небо → рот, мышь → компьютер | Select the intended concept by ID; create a separate sense only if absent |
| Material direction reversed: фарфор → посуда (23) | Product → material: посуда → фарфор |
| People under профессия: врач, учитель, программист | Human genera; professional actions use 22 |
| Every method under the programming function method | Separate ways of working from object methods |
| for → «для»; Pop = Post Office Protocol; IDE = drive interface | Check the term's domain sense; remove false translations and expansions |
| A missing genus makes an entire IT branch fail signatures | Repair the anchor, then review each existing relation semantically |
| Pizza under eating; skates under sport | Food and equipment are objects; eating and skating are activities |
| A song is produced by every performance of it | Separate the authored work from its vocal performance and resulting sound |
| Cities have countries as their purpose | Country → city is a whole-to-part attribute; reverse the direction |
| A second precedes a minute | Unit size does not imply temporal ordering; use quantities and duration |
| Science has an organism as its patient | A discipline includes research; the research process studies organisms |
| мир-world is opposite to war | Separate world from peace; use the existing peace-state concept |

## 8. Reviewing existing fill batches

`python tools/audit_quality.py --output report.json` is read-only. It checks
accepted edges for relation signatures, cycles, self-loops, dangling endpoints,
deprecated codes, invalid strengths, and missing Russian/English terms. Multiple
meanings of a term and multiple discourse-specific genera are not errors by
themselves. Passing these structural checks does not establish semantic truth.

The audit also lists `cyrillic_only_en` terms and concepts `without_latin_en`.
These are review heuristics: technical notation, mixed scripts, and proper
names need interpretation. Neither a language tag nor Latin script establishes
translation quality. The batch runner rejects newly introduced missing-language
flags and Cyrillic-only English labels, while retaining the existing review
backlog in its reports.

Reviewed corrections are recorded as explicit concept/edge IDs with expected
old values, explanations, and replacement relations. The 2026-10-08 batch is
`tools/quality_20261008.json`; run it with
`python tools/apply_quality_batch.py tools/quality_20261008.json` for a rollback
preview, or add `--apply` to save it after a SQL backup. The runner validates all
new relations with `propose`, rebuilds paths and definitions in the same
transaction, and refuses new structural/signature errors. Incorrect old edges
remain in the audit trail with `status='rejected'`.

The IT/profession continuation is `tools/quality_20261008_q2.json`. It also
checks required and forbidden ancestry and term senses. Additional genus
links for isolated anchors are validated before their descendant relations.
Reparenting preserves the original edge's discourse. During edge-only changes
the runner refreshes the live DAG; it compares that cache with a full engine
reload before rebuilding definitions and saving.

The Q3 continuation is `tools/quality_20261008_q3.json`; its rationale and
sources are in [the Q3 review](quality/2026-10-08-q3.md). Renames refresh lexical
indexes once per batch. A newly created concept is fully loaded before its
temporary candidate genus is replaced; that replacement refreshes only the DAG.
No relation signature is relaxed to make old edges pass.

The Q4 continuation is `tools/quality_20261008_q4.json`; see
[the lexical review](quality/2026-10-08-q4.md). It includes explicit
`leaf_merges` only for reviewed duplicates with no incoming links, children,
non-genus facts, negations, or rejected history. Each source's complete
concept, term, and edge rows are archived in the manifest and matched under
row locks before removal. Only listed valid terms move to the surviving
concept. Merge chains are forbidden. The full SQL backup remains mandatory;
`propose`, closure rebuilding, definition rebuilding, and rollback preview
use the same transaction. Other kinds of merges need a separate review.
Guard tests: `python -m unittest discover -s tools -p test_quality_guards.py`.

The Q5 continuation is `tools/quality_20261008_q5.json`; see
[the upper-graph review](quality/2026-10-08-q5.md). The read-only command
`python tools/audit_upper_graph.py --output upper.json` inspects the first two
genus steps from the root plus named anchors. It reports ancestor/co-hyponym
conflicts, skipped genera, property/phenomenon overlap, inherited physical
claims on abstract branches, and hubs with few explicit facts. These are
review candidates, not a semantic completeness score. Multiple discourse
genera can be valid. For a before/after comparison, retain the original cohort:
`python tools/audit_upper_graph.py --scope-from docs/quality/2026-10-08-q5-upper-before.json --output upper.json`.
Reparenting a node below the depth threshold must not hide it from the review.
Tests: `python -m unittest discover -s tools -p test_upper_graph_audit.py`.

The Q6 continuation is `tools/quality_20261008_q6.json`; see
[the mixed-branch and organism review](quality/2026-10-08-q6.md). It reviews
all 36 former children of «абстрактное понятие», with explicit selected senses,
eight archived leaf merges, and English terms for all surviving concepts.
Relative properties are classified by their dependence on another entity or
context; they are not species of that entity or a grammatical part-of-speech
class. For example, вычислительное is not a kind of computation, and
целлофановое is not a kind of abstract concept. Do not invent a noun just to
replace an established adjective.

Validate terms after reloading the actual database: its collation can treat
case or е/ё variants as equal in the unique index. A Python-only preview must
not claim that two distinct spellings will both be stored.

Do not replay historical mass-fill scripts merely because they ran before:
several wrote directly to `edge` and confused the relation codes above. New
properties need a checked sense, a suitable genus, and a relation with the right
direction. Leave `strength` unspecified when no defensible degree is available.

The Q7 continuation is `tools/quality_20261008_q7.json`; see
[the causality, arithmetic and role review](quality/2026-10-08-q7.md).
`reviewed_merges` extends the archive procedure to nodes with children or
incoming/outgoing facts. Every archived edge needs exactly one explicit
`merge_routes` entry, including an edge shared by two merge sources. Code,
strength and universe are preserved. Changing a genus target requires its
own reviewed reason. An existing destination edge is reusable only with the
same accepted status and degree. Missing routes, changed snapshots, chains,
self-loops, unaccepted history and explicit negations block this procedure.
The simpler `leaf_merges` restrictions remain unchanged.

Q7 changes only the description, examples and fourth object-signature anchor
of code 27 (`sig_object4=2535`, phenomenon). All other rule rows and its subject
signature remain unchanged. The grammar correction, merges, closure and
definitions share the transaction and rollback. Checks cover an action aimed
at a process/state and reject an artifact or a mathematical operation acting
as the subject. Genus assertions in another universe no longer fail as cycles;
reverse cycles, self-loops, duplicates within one universe and ancestor
shortcuts are still refused. Run `python -m unittest discover -s tools -p "test_*.py"`.

Known open issues (spotted, not yet fixed):
- Relative properties reviewed in Q6 still need richer representation of
  their reference objects and contexts. Their genus alone does not encode
  a particular material, purpose or textual reference for an actual bearer.
- Map (903) still needs a sense review; Whole number (1198) is under data type.
  Do not merge a mathematical function with a collection operation, or a
  mathematical integer with a machine integer type just because labels overlap.
- Arithmetic genera added in Q7 still need checked distinguishing properties.
  Genus coverage is not a complete mathematical definition.
- Other children of physiological process include implausible generated nouns
  and wrong genera. Check their dictionary meanings and existing senses before
  renaming or merging; no automatic suffix replacement.
- Heterogeneous children of natural object, time, physical and mental
  properties remain review priorities. Q6 fixes the blood/skin/sleep claims
  on all organisms and several animal parts; other biological classifications
  and legacy percentages still need review. Existing percentages are not
  evidence for a claim.
- структура under «отношение» — defensible as "система связей", but arguably
  belongs near «состав»; left as is pending a decision.
- Engine ISA is a DAG (`parents`, `rebuild`, `in_subtree`, `define`).
  `self.parent` remains the home-universum parent for old callers.
- Relational adjectives: 89 merged to nouns, dump-parents cleaned
  (`tools/merge_adj_terms.py`). Leftovers: национальность ⊂ принадлежность,
  естественность ⊂ происхождение; some -ое with no noun in the base
  were dropped as isolated.
- Infinitive/noun: 84 pairs merged (`tools/merge_verb_noun.py`). Residual
  infinitives under «действие» have no deverbal noun in the base yet.
