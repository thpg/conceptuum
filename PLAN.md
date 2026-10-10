# Roadmap and coverage review

Current baseline: [code 0.1.0-dev](VERSION), [data Q40](docs/quality/2026-10-10-q40.md).
Q10–Q40 and the QA generator are published to GitHub and the site at the user's request.
Continue further filling locally unless publication is requested.
This is the active work plan. Earlier expansion totals and relation-code
instructions remain available in Git history; they do not describe the
current graph or a sequence of scripts to rerun.

## Immediate quality queue after Q40

1. Review the 25 legacy records that merge different source verbs, such as
   dying/measuring or singing/drinking. Recover each sense and its genera
   before splitting records; selecting a single replacement word would lose meaning.
2. Review the 4,379 deferred generated labels for usage and sense. This queue
   includes valid productive or rare nouns. Dictionary absence is a search
   signal, not a deletion rule. Keep attested words, including the Russian
   word for detention, and remove only demonstrated spelling or derivation errors.
3. Resolve the semantic assertions excluded by
   [the QA policy](concept_algebra/qa_policy.json), including ant flight,
   lentil classification and grammatical case. Q40 does not change relations.
4. Expand reviewed translations and distinguishing properties in the branches
   below. The QA generator currently requires an English term containing Latin
   letters even for Russian output, so the legacy untranslated branch is excluded.
5. Review larger QA samples and separate related concept families across
   training and evaluation splits. The current 400-example pilot verifies
   derivability, not a demonstrated improvement in a trained model.

The generator and Q40 snapshot are published. Source manifests and the
[adequacy review](docs/quality/2026-10-10-qa-review.md) record the completed checks.

Coverage reviewed on **2026-10-09**, using a read-only snapshot of the local
database at 00:02 Asia/Yekaterinburg. The inventory matches Q7's 12,468 concepts,
15,665 accepted edges, and 34,950 terms. The tables below retain that Q7
baseline; subsequent filling progress is recorded separately below.

## What is missing

The largest deficit is information beyond classification. **10,181 of 12,468
concepts (81.7%) have a genus but no directly recorded non-taxonomic relation,
incoming or outgoing.** Of these, 9,895 are leaves. All concepts have a cached
definition, so counting nonempty definitions conceals this gap.

Of the 15,665 accepted edges, 12,578 (80.3%) are genus links. The remaining
3,087 include 812 co-hyponym links: being listed beside a sibling often still
leaves a concept's distinguishing meaning unexplained. Only 22 accepted edges
use the essential-attribute code 15, although other relation codes can also
express useful distinctions.

**7,306 concepts (58.6%) lack an English-tagged term containing Latin letters.**
All are in the Everyday home context. This is a discoverability indicator;
Latin text alone does not establish a correct translation. Some translated
concepts also have misleading aliases, as the examples below show.

| Home context | Concepts | Genus-only concepts | Share | Missing Latin-script English term |
|---|---:|---:|---:|---:|
| Everyday | 11,196 | 9,388 | 83.9% | 7,306 |
| IT | 895 | 710 | 79.3% | 0 |
| Legal | 160 | 37 | 23.1% | 0 |
| Logic | 217 | 46 | 21.2% | 0 |

These context totals use each concept's home context and inspect its accepted
relations across all contexts. The Scientific context (U2) has no concepts or
accepted edges. Scientific subjects still exist under Everyday and IT; an
empty U2 does not mean that the database contains no scientific knowledge.

### Branches needing attention

Branch counts below include the anchor and its descendants through accepted,
positive or unspecified-strength genus links **within the stated context**.
Genus-only status is also evaluated within that context. Multiple classification
means branches overlap; their sizes must not be added together.

| Branch / anchor | Context | Concepts | Genus-only | Missing English | Main gap |
|---|---|---:|---:|---:|---|
| Physical action (5017) | U1 | 4,090 | 4,058 | 3,974 | 4,086 direct children; very little intermediate classification or role information |
| Motion (55) | U1 | 728 | 695 | 655 | 724 direct children; separate kinds of movement, agents, paths, and conditions |
| Communication (64) | U1 | 721 | 694 | 624 | 696 direct children, including misplaced physical processes |
| Physiological process (202) | U1 | 442 | 402 | 373 | Mixed processes, states, and doubtful generated word forms |
| Color (2) | U1 | 133 | 113 | 104 | Non-color adjectives and word-form variants mixed into the taxonomy |
| Age (2810) | U1 | 122 | 118 | 117 | Non-age adjectives; many entries need meaning review before enrichment |
| Mathematical object (2698) | U1 | 43 | 43 | 0 | Classification without directly recorded distinctions or other non-taxonomic relations |
| Collection / set (2636) | U1 | 56 | 49 | 0 | Mathematical, collective, and everyday senses need separation |
| Data type (363) | U3 | 26 | 26 | 0 | Missing distinctions between types and their values or mathematical counterparts |
| Data structure (364) | U3 | 23 | 16 | 0 | Inconsistent aliases, mixed children, few defining characteristics |
| Algorithm (368) | U3 | 9 | 8 | 0 | Very small connected classification; operations and properties need clearer scope |
| Database (267) | U3 | 8 | 6 | 0 | Sparse hierarchy and few links to transactions, queries, and storage concepts |
| Tool (30) | U1 | 96 | 38 | 0 | Existing base for linking purpose, material, target, and practical tasks |
| Food (101) | U1 | 95 | 35 | 0 | Existing base for classification and links to preparation processes |
| Cooking (256) | U1 | 38 | 27 | 27 | Review generated variants and connect methods, utensils, and targets |
| Contract (1979) | U4 | 14 | 5 | 0 | Types exist, but only one outgoing specific-role/property edge in the branch |
| Judgment (2424) | U5 | 35 | 6 | 0 | Relatively connected; enrich selected distinctions and teaching examples |

Small subtree sizes do not measure an entire subject's coverage. For example,
Transaction (1156) exists outside the database subtree, and networking concepts
are scattered across several parents. Missing connections and misplaced
concepts should be repaired before creating replacements.

### Concrete review candidates

| Existing IDs | Recorded problem | Required review |
|---|---|---|
| 880 → 354, edge 1462 | Large language model is a programming language | Correct the model/language distinction and supply the missing model hierarchy |
| 468 | The array concept also carries `index`, `list`, and `vector` as English synonyms | Separate meanings and retain aliases only where they denote the same concept |
| 364 | Data structure has the English alias `data types` | Separate data structures from types in lookup and definitions |
| 1198 → 363, edge 1793 | Whole number / “целое число” is classified only as a data type | Review mathematical number versus programming type, including the English/Russian sense mismatch |
| 1909 → 64, edge 18033 | Weighing is classified as communication | Review the physical operation and any genuinely distinct figurative sense |
| 14535 and 14885 → 2, edges 28634 and 28640 | “всероссийское” and “нобелевское” appear under color | Review their meanings and remove the color classifications through a reviewed batch |
| 7072 → 2810, edge 28503 | “резиновое” appears under age | Review material-related meaning and its appropriate representation |
| 2636 and its children | Set includes society, stock, inheritance, and other collective meanings | Define a mathematical-set sense without silently rewriting every everyday collection |

These are observed rows and review tasks, not an estimate of the percentage of
incorrect concepts. Genus-only concepts can inherit useful information, and
some meanings need no extra direct property. Conversely, a structurally valid
edge or a high `processed` flag does not make a classification true.

Exact name and term probes also found useful search gaps:

- No exact EN/RU match for HTTP, authentication, authorization, artificial
  intelligence, machine learning, or embedding in the chosen aliases. LLM
  (880) and a backpropagation network (578) already exist, so this is partly
  a missing-hierarchy problem.
- No exact match for fraction, percent, ratio, statistics, set intersection,
  or set complement. Related records already exist: fractional (4824),
  average (3516), subset (859), and probability (2600). Review their senses
  and aliases before adding a node.
- No exact match for expense, budget, interest rate, inflation, credit, tax,
  or salary in the chosen aliases. Money, price, employment contract, and
  insurance do have records, providing starting points.
- An exact `RAG` probe finds the everyday rag/cloth concept (5187), and
  `index` finds array (468). A spelling match is not coverage of the intended
  technical meaning.

The probes used canonical names and all stored terms, case-folded with
whitespace normalization and Russian `ё`/`е` normalization. They identify
lookup and sense-review work; a failed exact probe does not prove absence.

## Likely demand and filling priority

Demand here is a **planning estimate**, not measured conceptuum traffic.
No project search logs or user-query sample were analyzed. The ranking combines
likely questions, the observed gaps, the project's graph/Euler capabilities,
and the cost of reviewing assertions.

Two external signals support the choice of initial subjects:

- The 2026 Stack Overflow survey reports that 69.9% of respondents to its
  answer-finding question ask an AI agent. This supports a developer-facing
  pilot around programming concepts and traceable explanations; it does not
  establish demand for this particular database.
  [Stack Overflow Developer Survey 2026](https://survey.stackoverflow.co/2026).
- The consumer ChatGPT usage study covering 2024–2025 found that practical
  guidance, information seeking, and writing together accounted for about
  77% of conversations; tutoring/teaching accounted for 10.2% of messages.
  This supports everyday explanations and educational concepts alongside IT.
  [How People Use ChatGPT, sections 5.2–5.3](https://cdn.openai.com/pdf/a253471f-8260-40c6-a2cc-aa93fe9f142e/economic-research-chatgpt-usage-paper.pdf).

| Priority | Area | Likely demand / project value | First useful scope |
|---|---|---|---|
| P0 | Shared taxonomy and terminology | Required for useful answers in every subject | Correct high-impact parents and ambiguous terms in the initial cohorts; review common meanings before the long tail |
| P1 | Mathematics, sets, and selected logic | Educational questions; strongest fit for explaining Euler diagrams | Numbers versus types, fraction/percent/ratio, sets and membership, operations versus results, quantity versus unit |
| P1 | Programming, data, and AI foundations | Strong fit for likely GitHub users and graph-grounded technical questions | Types and structures, algorithms, database concepts, HTTP/API, authentication versus authorization, model versus language |
| P1 | Everyday tasks and tools | Broad practical use; connects existing objects to actions | Cooking, cleaning, repair, storage, heating/cooling, measuring; tool–purpose–target and material distinctions |
| P2 | Communication, work, and learning | Useful for explaining requests, promises, decisions, roles, and documents | Repair the communication branch; separate activity, practitioner, state, result, and information content |
| P2 | Basic money and economic vocabulary | Useful everyday terms with substantial lookup gaps | Income/expense, price/cost, budget, saving/borrowing, nominal amount versus rate; start with concepts rather than current financial advice |
| P2 | Biology and health vocabulary | Potentially broad interest, but substantial semantic review effort | Organism/body/process/state distinctions, basic physiology and symptoms; definitions require appropriate domain sources |
| P3 | Law and contracts | Useful focused applications once the intended jurisdiction is chosen | Contract roles, rights/obligations, action/event, property and liability; record jurisdiction before extending legal rules |
| Later | Rare word forms and exhaustive species/product lists | Lower initial value for the proposed pilot | Extend only when a user question or a justified classification requires them |

For a broad public audience, everyday questions and basic mathematics should
receive more weight. For a developer audience, IT should receive more weight.
The default plan starts with mathematical/Euler explanations and core IT,
then uses practical tasks to extend the repaired common vocabulary.

## Filling plan

### Active direction — dictionary-guided filling, Q11–Q39 (2026-10-09)

The user requested a large English dictionary as the comparison source.
Use **Open English WordNet 2025, base edition**, pinned by the download hash
in the [Q11 manifest](tools/quality_20261009_q11.json). It contains 135,969
lexical entries, 185,129 senses, and 107,519 synsets. The complete normalized
English comparison is a candidate inventory; no English match does not mean
that the Russian database lacks the concept.

Q11 applies the first reviewed cohort locally: **59 additions**, 14 existing
meanings reused, two genera refined, and 85 new relations, including 21 purpose
or patient relations. All seven SI base-unit names are now represented.
Instrument/unit and programming-language/unit homonyms remain distinct.
The existing cohort's direct non-taxonomic coverage changes from
9/14 to 10/14; 22/59 new concepts have such a relation.
All new concepts have Russian and English terms. These are coverage counts,
not a claim that unit definitions or the dictionary are fully represented.

Q12 continues locally with **37 additions and 74 new relations**, including
26 non-taxonomic links. It reviews humidity, wind/rotation measurement,
acceleration, the caliper family, clocks, and levels. Three labels are qualified,
eight relations withdrawn, and four malformed or mistagged terms removed.
The 22-record existing cohort changes from 13/22 to 17/22 with direct
non-taxonomic relations; 30/37 additions have such a relation. Missing
Latin-script English terms decrease from 7,302 to 7,299. See the
[Q12 report](docs/quality/2026-10-09-q12.md) for exact scope and source decisions.

Q13 adds **41 concepts and 58 relations**, including 13 component or process-target links. Written fractions, decimals, and equations remain distinct from numbers and relations; programming homonyms retain their U3 meanings. All old records and terms are preserved. The ambiguous fractional record 4824 remains pending. See the [Q13 report](docs/quality/2026-10-09-q13.md).

Q14 adds **54 concepts and 79 relations**, including 22 instrument-purpose or process-target links. It fills density, force, area, volume, electrical power and energy, related unit families, and laboratory volume instruments. One resultant-force genus is refined. See the [Q14 report](docs/quality/2026-10-09-q14.md).

Q15 adds **28 concepts and 62 relations**. It distinguishes circle boundaries from filled disks, finite segments from complete lines, and geometric objects from lengths and angle quantities. Six genera are refined and the disk's misleading English circle term is replaced. See the [Q15 report](docs/quality/2026-10-09-q15.md).

Q16 adds **27 concepts and 41 relations**, while consolidating three duplicate price evaluations. Payment action 7752 receives a correct name and social-action genus; payment amount 3268 and price 3643 gain a monetary-amount genus. Budget plans, funds, savings and saving processes stay distinct. See the [Q16 report](docs/quality/2026-10-09-q16.md).

Q17 adds **35 concepts and 103 relations**, correcting 23 inherited assertions and 20 malformed or mistagged terms. It reuses existing utensils, adds cookware and measuring-tool families, separates food and general physical actions, and repairs the toaster and food-peeling relations. See the [Q17 report](docs/quality/2026-10-09-q17.md).

Q18 adds **38 concepts and 77 relations**, correcting 15 inherited assertions and 12 lexical entries. Screws and nails gain fastener genera; their tools gain qualified purposes. Two false upper-graph exclusions are rejected, while 20 other U1 conflict candidates remain queued. See the [Q18 report](docs/quality/2026-10-09-q18.md).

Q19 adds **28 concepts and 50 relations**, correcting 17 assertions and eight lexical entries. Wednesday and environment now have distinct records; calendar rules, labels, periods and planned events stay separate. One upper-graph conflict is resolved by the sense split; 19 candidates remain queued. See the [Q19 report](docs/quality/2026-10-09-q19.md).

Q20 adds **21 concepts and 42 relations**, correcting nine assertions and 14 lexical entries. Chemical compound and physical joining now have distinct records; material composition and phase state stay separate. Reviewed solution intersections add useful shared genera for Euler diagrams. Seventeen U1 conflict candidates remain queued. See the [Q20 report](docs/quality/2026-10-09-q20.md).

Q21 adds **28 concepts and 55 relations**, separating broadleaf from deciduous trees and forest landscape from collective vegetation. Deciduous conifers and temperate rainforests now provide explicit shared subtypes for Euler diagrams. Fifteen U1 conflict candidates remain queued. See the [Q21 report](docs/quality/2026-10-09-q21.md).

Q22 adds **32 concepts and 70 relations** for weather, precipitation, measurements, observations and forecasts. Natural phenomenon now admits conditions without making them processes. Rainy/windy weather supplies a reviewed intersection; the rain/snow mixture uses component relations. Fourteen U1 conflict candidates remain queued. See the [Q22 report](docs/quality/2026-10-09-q22.md).

Q23 adds **28 concepts and 57 relations**, correcting 21 assertions. Apartments, attics and basements are no longer kinds of whole houses. Optional features have restricted subjects; combined rooms and houseboats supply meaningful intersections. Thirteen U1 conflict candidates remain queued. See the [Q23 report](docs/quality/2026-10-09-q23.md).

Q24 adds **41 concepts and 83 relations**, correcting 18 assertions. Optional materials and fasteners now have restricted subjects. Jeans combine trouser form with denim material; hooded rain jackets combine garment form, component and intended use. Twelve U1 conflict candidates remain queued. See the [Q24 report](docs/quality/2026-10-09-q24.md).

Q25 adds **36 concepts and 85 relations**, correcting 14 assertions. Cards as a game are separate from physical playing cards; board games are separate from game boards. Tennis and table tennis share racket and ball classifications, while badminton uses a shuttlecock. Ten U1 conflict candidates remain queued. See the [Q25 report](docs/quality/2026-10-09-q25.md).

Q26 adds **32 concepts and 69 relations**, correcting 28 assertions. Family groups, kinship relations and relatives as people are kept distinct. Household and family have a restricted intersection; half-sibling and maternal/paternal classifications form further intersections. Nine U1 conflict candidates remain queued. See the [Q26 report](docs/quality/2026-10-09-q26.md).

Q27 adds **26 concepts and 51 relations**, correcting 13 assertions. Lighting state, lighting action, visible radiation, perceived brightness and physical measurement now have distinct meanings. Eight U1 conflict candidates remain queued. See the [Q27 report](docs/quality/2026-10-09-q27.md).

Q28 adds **27 concepts and 54 relations**, correcting eight assertions and four malformed braking records. The batch separates physical quantities from motion processes and adds useful path/speed intersections. Seven U1 conflict candidates remain queued. See the [Q28 report](docs/quality/2026-10-09-q28.md).

Q29 adds **32 concepts and 67 relations**, corrects 10 assertions and merges one archived duplicate. Recreational/method/location intersections and gear purposes expand practical graph coverage. Six U1 conflict candidates remain queued. See the [Q29 report](docs/quality/2026-10-09-q29.md).

Q30 adds **26 concepts and 61 relations**, corrects four assertions and cleans six term rows. Round springform moulds and combined openers demonstrate supported intersections. Six U1 conflict candidates remain queued. See the [Q30 report](docs/quality/2026-10-09-q30.md).

Q31 adds **30 IT concepts and 47 relations** and rejects the rest/API homonym error. HTTP methods, request messages, URI/URL families and software roles are distinguished. Six U1 exclusion candidates remain, with no U3 conflict introduced. See the [Q31 report](docs/quality/2026-10-09-q31.md).

Q32 adds **28 concepts and 51 relations**, corrects seven assertions and merges one isolated duplicate. Authorship, recognition and information-status intersections extend the graph. Five U1 exclusion candidates remain. See the [Q32 report](docs/quality/2026-10-09-q32.md).

Q33 adds **22 concepts and 39 relations**, corrects 19 assertions and separates state, process, property and vocal-action senses. The five remaining U1 shared-descendant exclusion candidates are resolved; broader semantic review is still needed. See the [Q33 report](docs/quality/2026-10-09-q33.md).

Q34 adds **30 concepts and 64 relations** in U3, repairs Jenkins's parent and separates hardware, software, HTTP roles and caching. Both U1 and U3 shared-descendant exclusion scans remain clear. See the [Q34 report](docs/quality/2026-10-09-q34.md).

Q35 adds **27 concepts and 49 relations**, reuses the DBMS record, corrects SQLite/table/foreign-key/transaction classifications, and cleans known rename-generated language errors. Both U1 and U3 shared-descendant exclusion scans remain clear. See the [Q35 report](docs/quality/2026-10-09-q35.md).

Q36 adds **37 concepts and 84 relations**, repairs predator and hunter genera, separates catching from capture, and confines six named-fish targets to specific fishing concepts. U1/U3 shared-descendant exclusion scans remain clear. See the [Q36 report](docs/quality/2026-10-09-q36.md).

Q37 adds **35 concepts and 68 relations**, separates motion paths from quantities, and adds translation, rolling, momentum, torque, kinetic energy and work. Both U1/U3 shared-descendant exclusion scans remain clear. See the [Q37 report](docs/quality/2026-10-09-q37.md).

Q38 adds **36 concepts and 64 relations** for database namespaces, views, plans, scans, join algorithms and key column sets. Relational algebra now has a query-language genus. U1/U3 shared-descendant exclusion scans remain clear. See the [Q38 report](docs/quality/2026-10-09-q38.md).

Q39 adds **41 concepts and 106 relations** for containers, material/use intersections, brushes and scraping tools. It corrects glass overgeneralizations, storage and sweeping scope, and ten malformed or incorrectly tagged terms. U1/U3 shared-descendant exclusion scans remain clear. See the [Q39 report](docs/quality/2026-10-09-q39.md).

**Continue locally in this order:**

1. Continue IT with relational-algebra operators and relation/tuple semantics, dataflow, Pipeline, protocol/standard links and broad versus programming identifiers. Review computer/home-appliance ancestry and virtual hosts before expanding hardware genera.
2. Continue household materials and actions: knife materials, cutting dependencies, inherited food patients, storage/wiping/drawing probabilities, container closures and action sequences. Review scraping-off synonym records and generated painting/dyeing aliases before merging.
3. Continue mechanics with reference frames, collisions, units for new quantities, potential energy and the inherited motion-to-sound probability. Review generated movement aliases individually.
4. Continue animal and activity review: bear/panda taxonomy, fox/fox synonym records, foraging, broader scavenging, hunting capabilities, protection subtypes and physical versus mental catch meanings.
5. Continue targeted review of emotion, sound, state, sleep/fatigue probabilities and knowledge branches: reputation, credibility, secrecy, lighting, family, calendar, money and geometry. Preserve upper distinctions and explicit negations.

For each cohort, record reuse/add/defer decisions with stable dictionary
sense IDs and a selected meaning. Review synonyms individually; OEWN's
resistance, mole, and candela entries demonstrate why its wording and parents
cannot be copied automatically. Unit conversions need a suitable data model;
never substitute a genus or a generic attribute edge for a scale factor.
Raw dictionary downloads and exploratory reports stay outside the repository.

This direction expands the earlier pilot's scope at the user's request.
The previous 25/33-concept estimates below are historical estimates, not a
limit on dictionary-guided filling. Q10–Q39 were subsequently published at
the user's request; the progress entries below retain their original review status.

### Local progress — 2026-10-09, Q10

Applied locally and exported: 30 existing records reviewed, eight new concepts,
24 clarified labels, 21 rejected genus links, and 38 new relations. No records
were merged. Types are separated from character/string values and mathematical
numbers; address and processing genera are repaired. String length, regex
purpose, and processing targets add explanatory facts beyond taxonomy.
See the [Q10 report](docs/quality/2026-10-09-q10.md).

Direct non-taxonomic relation coverage in the fixed cohort changed from
0/30 to 2/30; 3/8 new concepts have a direct non-taxonomic relation.
All reviewed and new records have Latin-script English terms. These remain
coverage measures, not completeness scores.

Revise the pilot's new-meaning estimate from 25 to 33: two type/value splits
and six missing shared concepts were needed for the reviewed distinctions.
Existing records were reused for real numbers, sequences, addresses, and
processing specializations. Q10 overlaps earlier cohorts, so their counts must
not simply be added. The approximately 100-meaning pilot remains in progress.

**Earlier IT queue, still pending:** review Map and heap senses, event listeners, mutex,
nonexecutable statements, program listings, variable-length fields, and
Z-buffering. Then review encoding/code-point distinctions, signedness and
numeric range properties, and fraction/percent/ratio vocabulary. Continue
source review before selecting language-specific meanings for `void` or
wide characters.

### Progress — 2026-10-09, Q9

The second foundation increment reviews 12 existing records, merges one
duplicate, and adds 19 meanings. Mathematical sets now have cardinality
properties and scoped empty/nonempty and finite/infinite oppositions. The
existing subset meaning and commutative and associative operation classes
are reused; JRE moves to runtime environment. See the
[Q9 report](docs/quality/2026-10-09-q9.md).

Within the fixed cohort, records with direct non-taxonomic relations changed
from 2/12 to 5/11 surviving. All already had Latin-script
English terms. Of the 19 new meanings, 13 have a direct non-taxonomic relation.
This measures relation coverage, not semantic completeness.

Together Q8 and Q9 review 28 distinct existing records, merge two duplicates,
and introduce 25 meanings. The pilot has reached its initial new-meaning
estimate; prioritize reuse and enrichment of existing concepts in the next
increment. Review that estimate explicitly if another missing genus is needed.
The roughly 100-meaning pilot remains in progress.

**Follow-up:** Q10 addresses selected type, structure, and model children
locally; the next unresolved groups are listed in the Q10 progress entry.
The legacy collection branch, general idempotence, and parser associativity
remain separate review tasks. The two new Euler examples are documented as
shared selections; arbitrary membership facts and a symbolic set solver are
outside Q9's scope.

### Progress — 2026-10-09, Q8

The first foundation increment is applied. It reviews 16 existing records,
merges one duplicate, and adds six missing meanings. Corrected areas include
the LLM/model hierarchy, array/list/index terminology, whole numbers versus
integer types, measurement/weighing, and the three misplaced adjectives.
The exact cohort, source interpretations, and remaining limitations are in
the [Q8 report](docs/quality/2026-10-09-q8.md).

On that fixed cohort, Latin-script English gaps fell from four to zero among
the 15 surviving records; three received translations and one duplicate was
merged. Records with a direct non-taxonomic relation changed from 4/16 to
5/15. Of the six new concepts, one has such a relation. These are coverage
indicators, not a claim that all reviewed meanings are fully filled.

Q9 continues the collection/set, subset/JRE, and set-operation work from
this increment. The original coverage tables above remain the Q7 baseline;
neither batch marks the whole foundation or pilot complete.

### First pilot: approximately 100 reviewed meanings

Use four batches of roughly 25 meanings. These are review targets, **not quotas
for new nodes**. Reuse existing concepts, move true synonyms into terms, and
create a new concept only after resolving its meaning against existing records.
Keep doubtful word forms pending until dictionaries establish the form and sense.

| Batch | Scope and starting IDs | Intended result |
|---|---|---|
| 1: correct the foundation | 880, 468, 364, 1198, 1909, 14535, 14885, 7072, 2636; inspect their parents and affected siblings | Resolve the concrete errors above and record the exact cohort, senses, sources, and context of every changed assertion |
| 2: mathematics and Euler | 2698, 2699, 24476, 918, 24477, 24478, 24479, 2636, 859, 4824, 3516, 2600, 2651 | Distinguish number/type and operation/result; review missing set operations, fraction/percent/ratio, and quantity/unit vocabulary |
| 3: core IT | 363, 364, 468, 368, 803, 267, 270, 271, 272, 1156, 299, 312, 1101, 340, 329, 327, 880, 578 | Explain type/structure, array/index, database/transaction, API/protocol, authentication/authorization, and model/language distinctions |
| 4: practical questions | 30, 9, 101, 256, 1799–1806, 1774, 1776, 1778, 254, 1304, 1305, 1908, 1909 | Connect reviewed everyday actions to tools, targets, materials, and justified conditions; repair both RU and EN terminology |

The tables list starting records, including dependencies shared between batches.
Deduplicate the pilot's reviewed-concept count; shared roots do not count as
newly completed meanings in every batch. Plan for at most about 25 new meanings
in the pilot, revising that estimate after the first batch's sense review.

Before adding formal mathematics or scientific classifications, document the
intended use of U1 versus the currently empty U2. Preserve the existing Everyday
view and keep each traversal within its chosen context.

### Expansion after the pilot

| Wave | Approximate review volume | Deliverable |
|---|---:|---|
| Mathematics and teaching | 80–120 meanings | Coherent number/set/measurement explanations plus a small set of sourced Euler examples |
| IT and data | 120–180 meanings | Connected foundations for types, structures, algorithms, databases, networking, security, and AI models |
| Practical tasks | 120–160 meanings | Useful object–action–purpose–target chains for common household and work tasks |
| Communication and learning | 60–100 meanings | Clean speech-act, learning, work-role, and decision vocabulary |
| Money, biology, or law | Select one 40–60 meaning pilot | Expand the subject with the strongest observed demand and available domain review |

Volumes are working estimates and can overlap earlier cohorts. Track reviewed
existing meanings, newly added meanings, merges, and unresolved cases separately.
Do not promise a completion date until the pilot establishes review effort.

For Euler teaching, a useful next example is **odd versus prime numbers**:
both inside a clearly defined natural-number universe, with examples in the
intersection and on each side. Add it only after the mathematical concepts and
membership evidence are reviewed. Keep catalog-record counts separate from
claims about the full mathematical extensions; never add an overlap merely to
obtain an attractive layout.

### What counts as filled

For each selected meaning, record a checked canonical label, useful RU/EN
terms, the nearest justified genus in the chosen context, and a sourced
distinction from its closest confusable concepts. Add appropriate relations
where evidence supports them; some valid definitions require no extra property.
Explain that exception instead of manufacturing an assertion to meet a count.

Use a fixed cohort and a short list of user questions to review each batch:

- Is a large language model a programming language?
- How do an array, a list, and an index differ in the stated programming context?
- How does a mathematical integer differ from an integer data type?
- How do a database and a transaction relate?
- How do authentication and authorization differ?
- How do a union, an intersection, and a complement depend on the chosen universe?
- How do boiling, frying, and baking differ, and which tools serve each process?
- Is weighing a kind of communication?

Set the pilot target at **at least 80 of its approximately 100 meanings having
a reviewed, non-circular explanation that answers an intended distinction**.
Every accepted new or changed assertion needs a source and scope; every chosen
meaning needs reviewed RU/EN terms or a recorded language exception. Count
unresolved items as unfinished, regardless of their `processed` value.

Report before/after coverage on that same cohort, including direct useful
relations, translation gaps, and wrong-sense matches. Global node totals alone
will barely reflect a 100-meaning pilot. After each wave, reprioritize using
actual requested questions and aggregate search misses when those data exist.

Existing follow-up work remains in scope: misplaced natural-object children,
protozoan/animal genera, Map (903), relative properties, time, and family-role
facts removed in Q7. Take them into a batch when they affect its selected meanings.

## Engine and retrieval work

- Improve sense selection for long queries without discarding valid homonyms.
- Separate the language of stored definition caches from display preferences.
- Add checked distinctions for operation inputs/results without misusing causality.
- Keep the root engine and the compatibility copy in `tools/` consistent until
  imports are consolidated.
- Extend verification beyond the current Python/MariaDB/Go test environment.
- Replace remaining direct-write historical workflows with reviewed changes.

## Review rules

Use the [property workflow](docs/fill-properties.md) and
[ontology rules](docs/ontology-rules.md). Preserve the nearest genus, justified
multiple classifications, discourse context, and explicit negations.
Signatures check structure; semantic review establishes whether a proposed
claim belongs in the graph. Do not assign invented percentages or broaden
a rule only to make an edge pass.

Current role codes include **20** for attributes/components, **21** for
purpose, **22** for capability/bearer, **23** for material, and **27** for
the target of an action. Earlier references to purpose 80, material 81,
agent 82, patient 83, or part-whole 21 are obsolete.

## Completion criteria for a review

Record reviewed IDs and evidence; preview with rollback; preserve prior
conditions and negations; apply with a backup; verify through a new
connection; rebuild and export; update the review report, maintainer state,
and [changelog](CHANGELOG.md). Structural counts and `processed` values are
progress indicators rather than proof of semantic completeness.

For public releases, keep the code version in [VERSION](VERSION), document
the data revision separately, and publish a tested commit with all referenced
dependencies, snapshot files, and reports.
