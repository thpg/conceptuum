# Changelog

The project version is stored in [VERSION](VERSION). Code versions and data
revisions are tracked separately: **Q1–Q39 are content reviews, not software
release numbers**. The first explicitly versioned working tree is
**0.1.0-dev**. No release tag or GitHub Release was created by this update.

## 0.1.0-dev — Unreleased

### Comparison evidence and LLM example collections — 2026-10-09

- Explain set comparisons with exact region counts, inspectable samples and
  counterexamples. Trace any record through comparison and count operands,
  including records outside a result; shared URLs retain the inspected ID.
- Add browser-local example collections with optional questions, replay,
  individual removal and JSONL export. Preserve complete set IDs and original
  source revisions; handle unavailable storage and exclude questions from API requests.
- Add counterexample and unknown-property demos, bringing the total to nine.
  Interface revision `2026-10-09.2`; data remains Q39.
- Verify 51 Python tests, nine JavaScript collection checks and eleven
  desktop/mobile browser scenarios. Update the README screenshot and guides.

### Concept algebra on the web — 2026-10-09

- Add a bounded expression parser, a read-only catalog evaluator, a Python
  API and `python -m concept_algebra` CLI. Support set operations, comparisons,
  genus navigation, direct relation projections and property selections.
- Resolve exact terms to all candidate senses before evaluation; keep each
  relation context separate. Preserve negative exceptions and conflicting
  multiple inheritance, with source-edge explanations.
- Publish the `/algebra` workspace with seven Q39 demos, concept search, context
  and domain controls, member explanations, pagination and shareable queries.
- Export versioned JSON examples with resolved ASTs, full member IDs, snapshot
  identity and selected evidence for LLM training-data preparation and evaluation.
- Add a bounded loopback Python worker and Go API proxy; queries only read the
  database. Interface revision is `2026-10-09.1`; data remains Q39.
- Verify 44 Python checks, Go proxy checks and six desktop/mobile browser checks.
  See the [language guide](docs/concept-algebra.md). Experiment files remain local.

### Repository and site publication — 2026-10-09, Q10–Q39

- Publish the combined Q10–Q39 filling work: 13,456 concepts, 17,350 accepted
  edges, and 37,825 terms. Relative to Q9, this is a net increase of 965
  concepts, 1,633 accepted edges, and 2,777 terms.
- Retain the source `utf8_general_ci` collation explicitly in the SQL dump
  so the same term keys import successfully on MariaDB 11.8.6.
- Update the live database and version metadata. All six tables match the
  reviewed data with timestamps compared in UTC; interface assets remain at
  revision `2026-10-08.4`. Experiments are excluded from publication.
- Earlier local-only statements below record the original review sessions.
  See the [Q39 publication record](docs/quality/2026-10-09-q39.md#publication).

### Local data — 2026-10-09, Q39

- Add 41 concepts and 106 relations in U1 for physical containers, vessel materials, food uses, can types, brushes, applicators, cleaning implements and scrapers.
- Replace universal jar/bottle glass claims with glass subtypes; separate physical vessels from dishware and software containers, and food storage from generic storage.
- Connect pastry brushes and bench scrapers to broader tool families; qualify drawing brushes, add paint-use intersections, correct sweeping ancestry and broom purpose, and clean ten malformed or incorrectly tagged terms.
- Export 13,456 concepts, 17,350 accepted edges, and 37,825 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q39 report](docs/quality/2026-10-09-q39.md) for sources, scope and verification.

### Local data — 2026-10-09, Q38

- Add 36 concepts and 64 relations in U3 for SQL namespaces and names, view definitions, ordinary/materialized views, query specifications, results, plans and execution.
- Reuse the general plan and nested-loop join records; add scan operations, optimizer software, hash/merge join algorithms and column-set/arity intersections linked to Q35 constraints.
- Correct relational algebra from data to query language, qualify its label and remove one transient English alias tagged as Russian; preserve all baseline term rows.
- Export 13,415 concepts, 17,254 accepted edges, and 37,725 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q38 report](docs/quality/2026-10-09-q38.md) for sources, scope and verification.

### Local data — 2026-10-09, Q37

- Add 35 concepts and 68 relations in U1 for motion paths, scalar/vector quantities, inertia, momentum, impulse, angular momentum, torque and axis-specific moment of inertia.
- Model straight and curved pure translation, rolling components, path length, kinetic energy and physical work. Preserve prior quantity genera and separate paths, processes, quantities and measurement targets.
- Qualify two existing transitive movement actions; correct one inherited assertion and remove four malformed or mistagged term rows.
- Export 13,379 concepts, 17,191 accepted edges, and 37,647 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q37 report](docs/quality/2026-10-09-q37.md) for sources, scope and verification.

### Local data — 2026-10-09, Q36

- Add 37 concepts and 84 relations in U1, separating ecological predators from Carnivora, hunting roles from occupations, and catching attempts from successful capture.
- Reuse herbivore, catching, pursuit and luring records; add role intersections, trap hunting, live bait and six fish-target restrictions. Preserve reviewed mammal ancestry and fishing genera.
- Correct 14 assertions and four labels; move named-fish targets off generic fishing, broaden protection, and remove seven malformed or mistagged terms.
- Export 13,344 concepts, 17,124 accepted edges, and 37,565 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q36 report](docs/quality/2026-10-09-q36.md) for sources, scope and verification.

### Local data — 2026-10-09, Q35

- Add 27 concepts and 49 relations in U3 for DBMS families, rows, columns, schema descriptions, indexes, integrity constraints and transaction operations.
- Reuse the existing СУБД record as software, classify SQLite as an embedded relational DBMS and library, and correct database-table, foreign-key and transaction genera.
- Model composite constraint intersections and partial rollback. Correct seven assertions and five labels; remove six mistagged baseline aliases and five temporary rename-generated copies.
- Export 13,307 concepts, 17,054 accepted edges, and 37,472 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q35 report](docs/quality/2026-10-09-q35.md) for sources, scope and verification.

### Local data — 2026-10-09, Q34

- Add 30 concepts and 64 relations in U3 for software clients and servers, service operations, file services, browsers, HTTP intermediaries, caches and automation.
- Move Jenkins from hardware server to automation server software. Qualify physical server/client and workstation meanings and the build process; reject one duplicated mutual-role assertion.
- Represent overlapping HTTP client/server roles, HTTP-to-HTTP reverse proxies and shared-cache forward proxies. Distinguish cache components from caching operations and client-server architecture from its style.
- Export 13,280 concepts, 17,012 accepted edges, and 37,408 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q34 report](docs/quality/2026-10-09-q34.md) for sources, scope and verification.

### Local data — 2026-10-09, Q33

- Add 22 concepts and 39 relations for mental and physiological states, sleep phases, moods, sleep duration and measurement, and vocal sounds.
- Separate sleeping as a process from the asleep state, vocal howling from its sound, and the conflated walking/raving verbs. Reuse mood, wakefulness, sleep onset and dozing.
- Correct 19 assertions, 10 labels and 16 term rows. Both U1 and U3 shared-descendant exclusion scans now have zero candidates; all upper exclusions and explicit negations remain intact.
- Export 13,250 concepts, 16,950 accepted edges, and 37,327 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q33 report](docs/quality/2026-10-09-q33.md) for sources, scope and verification.

### Local data — 2026-10-09, Q32

- Add 28 concepts and 51 relations for known/unknown distinctions, authorship restrictions and information status, including multiple-genus intersections.
- Repair the fame/unknown conflict and the familiar/unfamiliar knowledge genera. Merge the isolated famous duplicate into public fame, preserving all three terms.
- Correct seven assertions and two labels. Separate confidentiality from actual access, unverified from false, and pseudonymity from anonymity. U1 exclusion candidates fall from six to five.
- Export 13,228 concepts, 16,930 accepted edges, and 37,260 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q32 report](docs/quality/2026-10-09-q32.md) for sources, scope and verification.

### Local data — 2026-10-09, Q31

- Add 30 concepts and 47 relations in U3 for REST, HTTP, identifiers, message semantics and software client/server roles.
- Reject the mistaken physiological-rest/API attribute. Correct dictionary restrictions that make all HTTP TCP-based and all URLs web-page addresses.
- Keep method semantics distinct from request messages, software roles from hardware hosts, and architectural style from protocol choice. Preserve U1/U3 context boundaries and introduce no new exclusion conflicts.
- Export 13,201 concepts, 16,887 accepted edges, and 37,192 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q31 report](docs/quality/2026-10-09-q31.md) for sources, scope and verification.

### Local data — 2026-10-09, Q30

- Add 26 concepts and 61 relations for bakeware, specialised kitchen tools and coring, coating, piping and dough-cutting actions.
- Distinguish round shape from springform construction and broad bottle-opening tools from crown-cap openers. Add supported multiple-genus intersections.
- Correct four assertions, including opener exclusion, compulsory peeling before slicing and a reversed knife-patient link. Repair six malformed or mistagged terms; no new exclusion conflicts are introduced.
- Export 13,171 concepts, 16,841 accepted edges, and 37,118 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q30 report](docs/quality/2026-10-09-q30.md) for sources, scope and verification.

### Local data — 2026-10-09, Q29

- Add 32 concepts and 67 relations for fishing purposes, methods, locations, equipment and participant roles, including purpose/method intersections.
- Correct animal-capable hunting, the hunting/fishing exclusion, generic-net purpose and occupational-only fisher classification. Repair angling and fishing adjectives.
- Merge one fully archived fishing duplicate, preserving the attested rare noun while removing malformed and mistagged terms. U1 exclusion conflicts fall from 7 to 6.
- Export 13,145 concepts, 16,784 accepted edges, and 37,048 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q29 report](docs/quality/2026-10-09-q29.md) for sources, scope and verification.

### Local data — 2026-10-09, Q28

- Add 27 concepts and 54 relations for motion types, vector and angular quantities, units, measurements, oscillation and displacement amplitude.
- Separate stopping from rest, motion from its quantities, speed from velocity and rotational frequency from angular velocity. Repair four generated braking entries previously classified as communication.
- Add path/speed and oscillation/path intersections. U1 exclusion conflicts fall from 8 to 7, preserving the existing motion/rest contrary and earlier measurement assertions.
- Export 13,114 concepts, 16,728 accepted edges, and 36,960 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q28 report](docs/quality/2026-10-09-q28.md) for sources, scope and verification.

### Local data — 2026-10-09, Q27

- Add 26 concepts and 51 relations for lighting states, photometric quantities, units, measurement activities, meters and natural visible light.
- Correct darkness classified as light, six pale colours classified as lighting, and mixed physical/perceptual brightness. Remove malformed and mistagged terms.
- Use CIE and BIPM sources to correct mixed dictionary meanings and unit definitions. U1 exclusion conflicts fall from 9 to 8 without a new pair or shared witness.
- Export 13,087 concepts, 16,682 accepted edges, and 36,879 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q27 report](docs/quality/2026-10-09-q27.md) for sources, scope and verification.

### Local data — 2026-10-09, Q26

- Add 32 reviewed concepts and 69 relations for shared family-role genera, household composition, full/half siblings and great-grandparent/great-grandchild roles.
- Correct family/group versus kinship/relation and friendship classified as kinship. Refine existing family roles and replace false co-role implications with appropriate converse families.
- Reject nuclear-family and half/step-sibling errors in the source dictionary; keep household units distinct from family groups. U1 exclusion conflicts fall from 10 to 9 while the upper object/relation distinction is preserved.
- Export 13,061 concepts, 16,644 accepted edges, and 36,807 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q26 report](docs/quality/2026-10-09-q26.md) for sources, scope and verification.

### Local data — 2026-10-09, Q25

- Add 36 reviewed concepts and 85 relations for rule-governed games, racket and ball sports, singles/doubles formats, exercise and physical equipment.
- Separate card-game activity from playing cards; distinguish game boards, domino tiles, rackets, shuttlecocks and sport-specific balls from their activities.
- Refine existing sports and games, separate toy balls from the wider ball family, and remove false sport/play, gymnastics/sport and social/physical-action exclusions. U1 exclusion conflicts fall from 12 to 10.
- Export 13,029 concepts, 16,603 accepted edges, and 36,725 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q25 report](docs/quality/2026-10-09-q25.md) for sources, scope and verification.

### Local data — 2026-10-09, Q24

- Add 41 reviewed concepts and 83 relations for clothing purposes, materials, garment components, footwear and qualified combinations.
- Remove universal fabric, nylon, wool, fastener and heel assertions; attach reviewed materials and components to restricted families.
- Refine jeans, outerwear, knitwear, sleepwear, apron and pocket genera; keep cardigan distinct from the narrower Russian sweater sense. U1 exclusion conflicts fall from 13 to 12.
- Export 12,993 concepts, 16,532 accepted edges, and 36,629 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q24 report](docs/quality/2026-10-09-q24.md) for sources, scope and verification.

### Local data — 2026-10-09, Q23

- Add 28 reviewed concepts and 57 relations for housing forms, component-defined buildings, architectural spaces and rooms with combined uses.
- Correct apartments, attics and basements classified as houses; fix reversed containment and restrict optional house/building features to suitable subtypes.
- Reuse residential premises and residing; distinguish houseboat/dwelling intersections, two-unit buildings from two-level apartments, and bedroom count from total-room count. U1 exclusion conflicts fall from 14 to 13.
- Export 12,952 concepts, 16,467 accepted edges, and 36,535 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q23 report](docs/quality/2026-10-09-q23.md) for sources, scope and verification.

### Local data — 2026-10-09, Q22

- Add 32 reviewed concepts and 70 relations for atmospheric phenomena, precipitation, weather conditions, quantities, observing tools, forecasts and records.
- Separate weather states from precipitation processes, snow depth from water-equivalent precipitation depth, and forecast information from forecasting activity.
- Correct six relations, including natural phenomenon's process-only genus and weather/natural-phenomenon exclusion. U1 exclusion conflicts fall from 15 to 14.
- Export 12,924 concepts, 16,431 accepted edges, and 36,454 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q22 report](docs/quality/2026-10-09-q22.md) for sources, scope and verification.

### Local data — 2026-10-09, Q21

- Add 28 reviewed concepts and 55 relations for forest types, vegetation, evergreen and deciduous trees, with explicit shared subtypes for Euler intersections.
- Move deciduous tree from the broadleaf-tree record to its own meaning; place larch under deciduous conifers and true fir under evergreen conifers.
- Reject forest/grove, forest/taiga and forest/jungle exclusions. Preserve valid forest genera; U1 exclusion conflicts fall from 17 to 15.
- Export 12,892 concepts, 16,367 accepted edges, and 36,374 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q21 report](docs/quality/2026-10-09-q21.md) for sources, scope and verification.

### Local data — 2026-10-09, Q20

- Add 21 reviewed concepts and 42 relations for pure substances, mixtures, solution subtypes and roles, dispersed materials, solid state and physical joining.
- Separate chemical compound from joining; correct liquid state's substance genus, solution's liquid-only genus, smoke's gas genus, and stray drilling, regret, dissolution and color classifications.
- Add explicit aqueous/saturation intersections and retain correct upper-graph exclusions while resolving their mixed-sense witnesses. U1 exclusion conflicts fall from 19 to 17.
- Export 12,864 concepts, 16,317 accepted edges, and 36,300 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q20 report](docs/quality/2026-10-09-q20.md) for sources, scope and verification.

### Local data — 2026-10-09, Q19

- Add 28 reviewed concepts and 50 relations for calendar systems, dates, civil periods, deadlines, scheduling and planned meetings.
- Split Wednesday from spatial environment; move weekday relations and remove weekday ancestry from fifteen environment descendants while retaining the time/space exclusion.
- Correct Sunday spelling, schedule's physiological-process genus, general occurrence aliases on social meeting, and the nearest genus of twelve named calendar months.
- Export 12,843 concepts, 16,284 accepted edges, and 36,232 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q19 report](docs/quality/2026-10-09-q19.md) for sources, scope and verification.

### Local data — 2026-10-09, Q18

- Add 38 reviewed concepts and 77 relations for threaded fasteners, physical thread features, washers, rivets, wrenches, clamps and installation actions.
- Correct 15 inherited assertions, including screw/nail tool genera, broad material claims, the software-build homonym, and two upper-graph exclusions contradicted by shared subtypes.
- Correct three action labels and 12 lexical entries; distinguish general blind rivets from pull-mandrel rivets, fastening washers from sealing gaskets, and general unscrewing from hardware-specific removal.
- Export 12,815 concepts, 16,251 accepted edges, and 36,155 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q18 report](docs/quality/2026-10-09-q18.md) for sources, scope and verification.

### Local data — 2026-10-09, Q17

- Add 35 reviewed concepts and 103 relations for cookware, utensils, food-processing purposes, toast, and physical cleaning.
- Correct 23 existing relations, including unsupported material claims, misplaced action genera, spoon purposes, and shoe-cleaning facts attached to food peeling.
- Remove 20 obvious generated or mistagged terms; distinguish kitchen volume-measuring tools from laboratory ware and units, and toaster operation from frying.
- Export 12,777 concepts, 16,189 accepted edges, and 36,030 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q17 report](docs/quality/2026-10-09-q17.md) for sources, scope and verification.

### Local data — 2026-10-09, Q16

- Add 27 reviewed financial-vocabulary concepts and 41 relations; consolidate three redundant expensive/inexpensive records with full archives.
- Repair the generated payment nonword and its motion genus, separate payment amounts from actions, and move income lookup away from arrival.
- Distinguish budget plans from allocated funds, savings from saving actions, interest charges from interest rates, and net employee pay from business profit.
- Export 12,742 concepts, 16,109 accepted edges, and 35,919 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q16 report](docs/quality/2026-10-09-q16.md) for sources, scope and verification.

### Local data — 2026-10-09, Q15

- Add 28 reviewed geometry and angle-measurement meanings with 62 new relations; refine six existing genera.
- Correct the disk record's circle translation, preserve circle-boundary and circumference-length homonyms, and keep finite segments and rays distinct from complete straight lines.
- Connect geometric figures to their quantities and components, refine width as length, and add radians, arcminutes, arcseconds, and angle instruments.
- Export 12,718 concepts, 16,075 accepted edges, and 35,827 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q15 report](docs/quality/2026-10-09-q15.md) for sources, scope and verification.

### Local data — 2026-10-09, Q14

- Add 54 reviewed physical-quantity, unit, process, and instrument meanings with 79 new relations.
- Keep watt-hours under energy units, relative density separate from mass density, and force gauges separate from power-measuring dynamometers.
- Refine resultant force through the new force genus; retain its former label and every old term. Distinguish calibrated volumetric pipettes from general liquid-transfer tools.
- Export 12,690 concepts, 16,019 accepted edges, and 35,730 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q14 report](docs/quality/2026-10-09-q14.md) for sources, scope and verification.

### Local data — 2026-10-09, Q13

- Add 41 reviewed meanings for mathematical notation, fractions, decimals, ratios, percentages, equations, and calculation processes, with 58 new relations.
- Separate written representations from numerical values and U3 programming homonyms. Include the equality boundary for improper fractions and avoid the dictionary's inconsistent decimal hierarchy.
- Add precise English lookup terms to eight existing records; preserve every old concept, term, edge, home context, and explicit negation.
- Export 12,636 concepts, 15,941 accepted edges, and 35,543 terms locally. No commit, push or deployment; Q9 remains published.
- See the [Q13 report](docs/quality/2026-10-09-q13.md) for sources, scope and verification.

### Local data — 2026-10-09, Q12

- Continue the pinned English dictionary comparison with 37 new concepts for
  humidity, wind speed, rotational frequency, acceleration, dimensional tools,
  and timekeeping; add 74 relations, including 26 non-taxonomic links.
- Separate acceleration as process/quantity and diameter as segment/length.
  Refine measuring-instrument families, qualify three existing labels, and
  withdraw eight reviewed relations while preserving their historical rows.
- Remove one malformed Russian alias and three Russian terms mistagged as
  English. Existing translation gaps decrease from 7,302 to 7,299.
- Export 12,595 concepts, 15,883 accepted edges, and 35,406 terms
  locally. Preserve all 23 explicit negations and the relation grammar.
  No commit, push, or deployment; the published reference remains Q9.
- See the [Q12 report](docs/quality/2026-10-09-q12.md) for sense decisions,
  source corrections, verification, and remaining work.

### Local data — 2026-10-09, Q11

- Compare all 135,969 Open English WordNet 2025 lexical entries against the
  existing English terms, then review selected meanings against RU/EN labels
  and graph context. Preserve source sense IDs and explicit mapping decisions.
- Add 59 concepts: 13 unit families, 24 units, four measured quantities,
  nine measurement actions, and nine instruments including their shared genus.
  Reuse 14 existing meanings, refine two genera, and add 85 relations.
- Keep instrument/unit homonyms distinct and correct dictionary-derived
  traps involving mole, candela, resistance, and voltage using BIPM sources.
- Export 12,558 concepts, 15,817 accepted edges, and 35,290 terms locally.
  Preserve all previous terms, all 23 explicit negations, and all grammar rows.
  No commit, push, or deployment; Q9 remains published.
- See the [Q11 report](docs/quality/2026-10-09-q11.md) for source attribution,
  reviewed additions, verification, and the next dictionary cohorts.

### Local data — 2026-10-09, Q10

- Review 30 existing records. Add eight missing concepts, refine 24 canonical
  labels, replace 21 incorrect genus assertions, and add 38 relations.
- Separate character/string values from their data types; organize unsigned
  integer types and mathematical real/rational/integer values.
- Correct byte order, Java keywords, LF/CR escape spellings, computer addresses,
  and stream processing. Add string-length and processing-role facts.
- Export 12,499 concepts, 15,734 accepted edges, and 35,112 terms locally.
  Preserve all explicit negations and relation-grammar rows. No commit, push,
  or site deployment was made; the published reference remains Q9.
- Record sources and remaining limitations in the
  [Q10 report](docs/quality/2026-10-09-q10.md).

### Data — 2026-10-09, Q9

- Add 19 meanings covering mathematical sets, cardinality properties, and set
  operations. Classify union and intersection as both commutative and associative.
- Separate everyday collection from mathematical set; merge one archived
  duplicate. Correct subset/JRE, runtime, and concept-extension genera.
- Rename five records, reject seven relations, and add 50. Preserve all 23
  explicit negations and the existing relation grammar.
- Bundle 12,491 concepts, 15,717 accepted edges, and 35,048 terms;
  publish the data with interface revision `2026-10-08.4`.
- Add two shared Euler selections to the documentation. See the
  [Q9 report](docs/quality/2026-10-09-q9.md) for sources, scope, and remaining work.

### Data — 2026-10-09, Q8

- Start the foundation pilot from the coverage review: correct model/language,
  array/list/index, number/type, measurement, and selected adjective meanings.
- Add six concepts, merge one archived duplicate, rename three records,
  reject 11 relations, and add 22 reviewed relations. Preserve all 23 explicit
  negations and the existing relation grammar.
- Bundle 12,473 concepts, 15,675 accepted edges, and 34,981 terms; update the
  live dataset while keeping interface revision `2026-10-08.4`.
- Record the fixed cohort, sources, context policy, and unfinished set review
  in the [Q8 report](docs/quality/2026-10-09-q8.md) and [active plan](PLAN.md).

### Euler demos and catalog sets — 2026-10-08, interface revision 2026-10-08.4

- Add seven database-backed demos for cross-classification, multi-set
  intersection, union/difference, scoped complement, empty intersection,
  equality, and inherited exclusion.
- Compute finite catalog memberships from accepted genus/equality paths and
  return exact region counts with inspectable samples and edge evidence.
- Add Boolean region highlighting, empty-region hatching, full diagram legends,
  and shared URLs that preserve operations and operands.
- Keep catalog membership distinct from stored semantic relations. Demo
  calculations do not insert new relation facts into Q7.
- Add catalog inference/operation checks and four browser scenarios; improve
  compact controls and exported SVG legends for complex diagrams.

### Complex Euler diagrams — 2026-10-08, interface revision 2026-10-08.3

- Combine partial overlaps, overlap chains, and species inside the intersection
  of multiple genera. Validate all known pair constraints before showing a layout.
- Automatically add direct shared genera for selected siblings in the current
  context. Remove unnecessary automatic genera as the selection changes;
  handle equality aliases and multiple shared genera without duplicate circles.
- Mark unspecified relationships with dashed circles and a relationship list.
  Keep multi-set regions illustrative and retain pair comparisons as a fallback.
- Improve label readability, distinguish automatic genera, and pack larger
  sibling groups into rows. Include these details in shared views and SVG exports.
- Add 13 genus-discovery cases, 22 geometry checks, and three browser scenarios.

### Euler circles — 2026-10-08, interface revision 2026-10-08.2

- Added Euler diagrams with up to eight selected concepts, search-based adding,
  individual removal, clearing, context selection, sharing, and SVG export.
- Added a read-only set-relationship endpoint with genus/equality traversal,
  inherited exclusions, evidence records, and strict input limits.
- Use independent pair diagrams for unknown, conflicting, or overlapping
  selections instead of asserting unsupported multi-set intersections.
- Added Go inference/validation tests and six browser scenarios covering the
  new view. Existing hierarchy and relation workflows remain available.

### Visualizer — 2026-10-08

- Replaced the crowded graph with separate hierarchy and relation views,
  a searchable concept sidebar, and a dedicated details panel.
- Added pan and zoom, fit and locate controls, ancestry expansion, branch
  pagination, relation filters, shareable URLs, browser history, and SVG export.
- Added a vertical graph layout and search/details drawers for small screens.
- Added keyboard navigation, loading and retry states, request cancellation,
  and protection against stale search or concept responses.
- Read relation symmetry from the grammar and distinguish explicit negations
  from positive relations. Keep full labels available in tooltips and details.
- Added eight browser checks and machine-readable interface/data versions.

### Documentation and setup — 2026-10-08

- Reworked the English README around project purpose, local setup, versions,
  read-only examples, audits, and known data limitations.
- Added pinned Python dependencies and a platform-aware setup guide.
- Added Python database environment overrides while retaining existing local
  defaults and explicit constructor-argument precedence.
- Corrected the legacy filler's `--dry-run` to avoid progress writes, and
  made `--candidate` apply to newly created genus links as well as other edges.
- Replaced outdated bulk-fill instructions and retired relation codes with
  the current reviewed-batch workflow.
- Added regression checks for configuration and filler flags.

### Data and graph engine — 2026-10-08, Q7

- Consolidated five causality/arithmetic duplicates with explicit routes for
  dependent edges and preserved discourse context.
- Separated mathematical operations, numerical results, and program functions.
- Corrected behavior, process roles, and reversed causal assertions.
- Reviewed the object signature of code 27 for processes and states.
- Fixed genus validation across universes and repeated children in definitions.
- Bundled 12,468 concepts and 15,665 accepted edges. See the
  [Q7 report](docs/quality/2026-10-08-q7.md) for checks and remaining gaps.

## Content revision history

These rows describe reviewed data stages. Counts refer to their recorded
snapshots; they are not separate published software releases.

| Revision | Date | Main changes | Concepts | All edges |
|---|---|---|---:|---:|
| [Q39](docs/quality/2026-10-09-q39.md) | 2026-10-09 | Containers, brushes, and scraping tools | 13,456 | 18,450 |
| [Q38](docs/quality/2026-10-09-q38.md) | 2026-10-09 | Database names, views, plans, and key columns | 13,415 | 18,344 |
| [Q37](docs/quality/2026-10-09-q37.md) | 2026-10-09 | Motion paths, inertia, momentum, and work | 13,379 | 18,280 |
| [Q36](docs/quality/2026-10-09-q36.md) | 2026-10-09 | Animal roles, hunting, catching, and bait | 13,344 | 18,212 |
| [Q35](docs/quality/2026-10-09-q35.md) | 2026-10-09 | Database software, structures, constraints, and transactions | 13,307 | 18,128 |
| [Q34](docs/quality/2026-10-09-q34.md) | 2026-10-09 | Client/server meanings, HTTP roles, and automation | 13,280 | 18,079 |
| [Q33](docs/quality/2026-10-09-q33.md) | 2026-10-09 | States, sleep, mood, and vocal actions | 13,250 | 18,015 |
| [Q32](docs/quality/2026-10-09-q32.md) | 2026-10-09 | Recognition, authorship, and information status | 13,228 | 17,976 |
| [Q31](docs/quality/2026-10-09-q31.md) | 2026-10-09 | REST, HTTP, and resource identifiers | 13,201 | 17,926 |
| [Q30](docs/quality/2026-10-09-q30.md) | 2026-10-09 | Bakeware, kitchen tools, and food actions | 13,171 | 17,879 |
| [Q29](docs/quality/2026-10-09-q29.md) | 2026-10-09 | Fishing methods, equipment, and participant roles | 13,145 | 17,818 |
| [Q28](docs/quality/2026-10-09-q28.md) | 2026-10-09 | Motion, quantities, and braking terminology | 13,114 | 17,752 |
| [Q27](docs/quality/2026-10-09-q27.md) | 2026-10-09 | Light, perception, and photometric measurement | 13,087 | 17,698 |
| [Q26](docs/quality/2026-10-09-q26.md) | 2026-10-09 | Family groups, household units, and kinship roles | 13,061 | 17,647 |
| [Q25](docs/quality/2026-10-09-q25.md) | 2026-10-09 | Game activities, sports formats, and physical equipment | 13,029 | 17,578 |
| [Q24](docs/quality/2026-10-09-q24.md) | 2026-10-09 | Clothing purposes, materials, components, and intersecting garment families | 12,993 | 17,493 |
| [Q23](docs/quality/2026-10-09-q23.md) | 2026-10-09 | Dwellings, building components, and combined room uses | 12,952 | 17,410 |
| [Q22](docs/quality/2026-10-09-q22.md) | 2026-10-09 | Weather, precipitation, quantities, and forecasts | 12,924 | 17,353 |
| [Q21](docs/quality/2026-10-09-q21.md) | 2026-10-09 | Forest types, foliage classes, and vegetation | 12,892 | 17,283 |
| [Q20](docs/quality/2026-10-09-q20.md) | 2026-10-09 | Material composition, phase states, and physical joining | 12,864 | 17,228 |
| [Q19](docs/quality/2026-10-09-q19.md) | 2026-10-09 | Calendars, scheduling, and the Wednesday/environment split | 12,843 | 17,186 |
| [Q18](docs/quality/2026-10-09-q18.md) | 2026-10-09 | Fasteners, gripping tools, and upper-graph exclusions | 12,815 | 17,136 |
| [Q17](docs/quality/2026-10-09-q17.md) | 2026-10-09 | Kitchen tools, cookware, food preparation, and cleaning | 12,777 | 17,059 |
| [Q16](docs/quality/2026-10-09-q16.md) | 2026-10-09 | Money vocabulary, budgets, savings, and payment repairs | 12,742 | 16,956 |
| [Q15](docs/quality/2026-10-09-q15.md) | 2026-10-09 | Plane geometry, geometric lengths, and angle measurement | 12,718 | 16,918 |
| [Q14](docs/quality/2026-10-09-q14.md) | 2026-10-09 | Physical quantities, derived units, and measurement instruments | 12,690 | 16,856 |
| [Q13](docs/quality/2026-10-09-q13.md) | 2026-10-09 | Fractions, ratios, percentages, and mathematical notation | 12,636 | 16,777 |
| [Q12](docs/quality/2026-10-09-q12.md) | 2026-10-09 | Humidity and motion measurement, dimensional tools, timekeeping, sense repairs | 12,595 | 16,719 |
| [Q11](docs/quality/2026-10-09-q11.md) | 2026-10-09 | Dictionary reconciliation, units, instruments, and measurement roles | 12,558 | 16,645 |
| [Q10](docs/quality/2026-10-09-q10.md) | 2026-10-09 | Types and values, text terminology, addresses, processing roles | 12,499 | 16,560 |
| [Q9](docs/quality/2026-10-09-q9.md) | 2026-10-09 | Mathematical sets, cardinality, set operations, collection and runtime senses | 12,491 | 16,522 |
| [Q8](docs/quality/2026-10-09-q8.md) | 2026-10-09 | Foundation pilot: models, structures, values, measurement, terminology | 12,473 | 16,473 |
| [Q7](docs/quality/2026-10-08-q7.md) | 2026-10-08 | Causality, arithmetic, process roles, dependent merges | 12,468 | 16,452 |
| [Q6](docs/quality/2026-10-08-q6.md) | 2026-10-08 | Mixed abstract branch, vertebrate genera, biological properties | 12,468 | 16,439 |
| [Q5](docs/quality/2026-10-08-q5.md) | 2026-10-08 | Upper graph; material objects, information, mental processes | 12,474 | 16,399 |
| [Q4](docs/quality/2026-10-08-q4.md) | 2026-10-08 | Dictionary review and perception-related duplicates | 12,472 | 16,353 |
| [Q3](docs/quality/2026-10-08-q3.md) | 2026-10-08 | Objects/actions, geography, time, disciplines, language audit | 12,532 | 16,351 |
| [Q2](docs/quality/2026-10-08-q2.md) | 2026-10-08 | Professions, IT genera, homonyms | 12,496 | 16,199 |
| [Q1](docs/quality/2026-10-08.md) | 2026-10-08 | Initial signature, role, material, and homonym corrections | 12,484 | 15,988 |

## Version policy

- Use `MAJOR.MINOR.PATCH` for code releases; a `-dev` suffix marks development.
- Record interface or setup changes under the code version.
- Record content reviews with a date and revision ID, including snapshot
  counts, validation evidence, and export checksums in their reports.
- Before publishing a release, update `VERSION`, this changelog, and the
  README together, and include the referenced code, dependency files, and data
  reports. Tags should identify tested commits; a changelog entry alone is not
  a published release.
