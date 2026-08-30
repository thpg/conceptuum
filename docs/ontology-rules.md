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
- **Verb pairs are one concept.** Aspect and reflexive variants (отклонить /
  отклонять / отклоняться) are a single concept; so are the infinitive and
  the deverbal noun (влиять / влияние, замерзать / замерзание). Canonical
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
  not as a single-parent tree (`rebuild` / `parent` / `define` are
  still tree-shaped — known gap).
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
- **Relational vs agentive is a distinction of concepts, not of word
  class.** Predicates that *express* relations (равняться, зависеть,
  принадлежать, предшествовать — and their nouns) stay under
  «отношение»; agentive actions (воздействовать / влияние) under
  «действие»; mutual processes (взаимодействие) under «процесс». The
  infinitive and the noun of the same concept follow that one genus.

## 3. Property attachment

- **Attach a property at the highest applicable genus.** Фарфор is a material
  of посуда as a whole; a чашка—фарфор edge is redundant *unless* the species
  frequency deviates noticeably (≈25+ points) from the genus value
  (пчела—полёт 95% is kept against насекомое—полёт 60%). A species edge is
  also kept when its object is a *subtype* of the genus's object
  (птица—полёт vs животное—движение). `tools/prune_inherited.py` cleans
  exact duplicates.
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
- **Ternary facts are virtual.** "Кофейная чашка — для питья — кофе" is two
  binary edges (purpose + patient); no ternary relation nodes.

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

## 6. Workflow rules

- **A strong model fills the base; small models consume it.** Do not use a
  small local LLM for real filling — quality of genus choice is the whole
  point. The base is the precomputed "thinking" that a small model grounds
  on at query time.
- **No lexeme corpus table.** It was designed as a manual-entry aid; now that
  LLMs do the filling, it is dead weight.
- After every change: `engine.rebuild()`, `engine.define()`, check
  `engine.stats()`; dump the DB (`jnana3_dump.sql`), log a row in
  `STATE.md`, commit locally.
- Fill scripts live in `tools/fill_*.py`, fix scripts in `tools/fix_*.py` —
  they are the audit trail; keep them in git.
- Track fill progress in `STATE.md` so a later session can resume.

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

Known open issues (spotted, not yet fixed):
- цель → знание → ментальный процесс — a цель is not знание; chain needs a
  proper genus (намерение? отдельный узел).
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
