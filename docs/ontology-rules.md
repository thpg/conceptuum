# Ontology rules

Rules of thumb for filling and maintaining the concept base, distilled from
build sessions and audit fixes. Each rule comes with the error that motivated
it. Examples are Russian because the base content is Russian.

## 1. Concept identity

- **A concept is not a word.** Synonyms are one concept with several terms in
  `concept_term` (мотор / двигатель → one node, two terms). Never create two
  concepts for the same meaning.
- **Verb pairs are one concept.** Aspect and reflexive variants (отклонить /
  отклонять / отклоняться) are a single concept. Canonical name: the deverbal
  noun when it exists (отклонение), otherwise the non-reflexive imperfective
  infinitive. Other forms live as terms.
  *Error found:* 167 verb groups had been entered as separate concepts —
  merged by `tools/merge_verbs.py` (−281 concepts, +562 terms).
- **Adjectives are not autonomous concepts.** An adjective is the result of a
  bearer→property relation. Where a general class is needed, the canonical
  name is the **neuter form** (тяжёлое, красное); gender/number forms are
  terms. "Тяжёлая гиря" = the inclusion of гиря in the general class тяжёлое.
  *Error found:* 619 masculine/feminine forms renamed to neuter by
  `tools/neuter_adjectives.py`.
- **Homonyms are separate concepts.** One term, several concepts — one per
  sense, usually per universum (desktop = writing desk in the everyday
  universum vs desktop in the IT universum; среда = environment vs
  Wednesday; положение = thesis vs spatial position). A term lookup must
  return **all** senses; the consuming LLM picks by context.

## 2. Taxonomy (genus, kod 14)

- **Nearest genus, no skipping.** The genus is the *immediate* broader class:
  январь → месяц → период времени; север → сторона света → направление.
  Never январь → период времени directly.
- **Definitions follow the classical rule:** genus of the definiendum first,
  then its specific properties; species may be listed additionally. The
  generated definition (`defin`, rebuilt by `engine.define()`) must read
  exactly like that. The `defin` column is **derived data** — never hand-edit
  it; fix edges instead.
- **Instance vs class is still is-a.** There is no "instance-of" relation
  between concepts: Лондон — столица is a species-of relation (Лондон is one
  of the set of столиц), kod 14 like any вид→род link.
- **«свойство» is logical analytics, not a taxonomic genus.** "Свойство" is
  not the genus of every property. Property *values* go to their scale
  (красное → цвет, истинное → истинность, зимнее → сезон); only terms of
  logic itself (качество, количество, распределённость термина, модальность,
  шкалы суждений) stay under «свойство». Same for «действие» and «отношение»:
  they are not dumping grounds. *Error found:* 489 direct children under
  «свойство» — dissolved by `tools/fix_genus4.py` (448 reparentings);
  442 under «действие» — dissolved by `tools/fix_genus3.py`.
- **Closed-bearer rule.** When a property is bound to one typical bearer
  class, the adjective-concept is a *species of that bearer*, and the
  property becomes a separate attribute edge:
  судоходное —[14]→ водоём plus судоходное —[20]→ судоходство (90%);
  хищное —[14]→ животное plus хищное —[20]→ охота (90%).
  When the bearer class is open (anything can be heavy), the genus stays the
  property scale: тяжёлое → вес. Implemented in `tools/fix_bearer.py`.
- **A thing can be viewed as a property of its whole.** Колесо–автомобиль:
  колесо is a component-property of автомобиль (kod 20), not only a separate
  object node.
- **Verbs that *express* relations** (равняться, зависеть, принадлежать,
  предшествовать…) stay under «отношение» as relational predicates; verbs
  that *are* agentive actions (воздействовать, влиять) go to «действие»,
  mutual processes (взаимодействие) to «процесс».

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
  ягода in biology). Special terms of a domain get that domain's universum
  (термины логики → U5).
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
| Property bound to one bearer filed under the scale (судоходное → пригодность) | fix_bearer.py: genus = bearer class |
| хищное / рогатое / больное as "физическое свойство" | → животное / организм (bearer) |
| жидкое in «состояние» vs газообразное in «свойство» (inconsistent) | new genus «агрегатное состояние» |
| логический закон under «отношение» | → правило |
| воздействие/влияние under «отношение» | → действие; взаимодействие → процесс |

Known open issues (spotted, not yet fixed):
- цель → знание → ментальный процесс — a цель is not знание; chain needs a
  proper genus (намерение? отдельный узел).
- структура under «отношение» — defensible as "система связей", but arguably
  belongs near «состав»; left as is pending a decision.
