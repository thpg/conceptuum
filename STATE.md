# Maintainer state

Update this file at the end of each content session. Continue from the first
unfinished item in [PLAN.md](PLAN.md), using the current snapshot below.

**Publication policy:** Q10–Q39 are included in the Q39 repository and site
publication requested on 2026-10-09. Continue further filling locally unless
publication is requested. Experiments remain local.

## Current position

- **Published concept algebra (2026-10-09):** Python package, CLI and
  [web workspace](https://conceptuum.su/algebra?lang=en), with typed set expressions,
  context-scoped graph operations, four property states and edge-level explanations.
  Nine demos, comparison counterexamples, arbitrary record inspection and
  browser-local question–answer collections with JSONL export support LLM
  training-data preparation and evaluation. Interface revision `2026-10-09.2`;
  data remains Q39. Validation: 51 Python checks, nine JavaScript collection
  checks and eleven desktop/mobile browser checks.
  See the [language guide](docs/concept-algebra.md). Experiments remain local.

- **Published data — Q39 (2026-10-09):** 13,456 concepts, 17,350 accepted edges,
  and 37,825 terms. All six live tables match the reviewed snapshot with
  timestamps compared in UTC. The SQL export explicitly preserves
  `utf8_general_ci` for compatibility with the site's MariaDB 11.8.6.
  The data publication used interface `2026-10-08.4`; the algebra update above
  advances the interface without changing the database. See the
  [publication record](docs/quality/2026-10-09-q39.md#publication).

## Review history

The following entries record each original review session. Statements about
local-only work precede the combined Q39 repository and site publication.

- **Latest local data — Q39 (2026-10-09):** Added 41 concepts and 106 relations in U1, with ten assertion repairs, five label changes and ten term removals. Material and food-use families intersect without making all jars or bottles glass or food containers. Pastry brushes and bench scrapers gain broader genera; sweeping and storage scope are corrected. U1/U3 exclusion scans remain clear. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q39 report](docs/quality/2026-10-09-q39.md) and [active queue](PLAN.md).
- **Earlier local data — Q38 (2026-10-09):** Added 36 concepts and 64 relations in U3; corrected the relational-algebra genus and label. Namespaces, schema descriptions, query specifications, results, plans, execution and software remain distinct. Key column sets are linked to their separate constraints. U1/U3 scans remain clear, with no baseline term losses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q38 report](docs/quality/2026-10-09-q38.md) and [active queue](PLAN.md).
- **Earlier local data — Q37 (2026-10-09):** Added 35 concepts and 68 relations in U1; corrected one assertion and two labels. Motion processes, geometric paths and measured quantities remain distinct. Physical movement actions have explicit targets and resulting processes. Four malformed or mistagged terms are removed; U1/U3 exclusion scans remain clear. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q37 report](docs/quality/2026-10-09-q37.md) and [active queue](PLAN.md).
- **Earlier local data — Q36 (2026-10-09):** Added 37 concepts and 84 relations in U1; corrected 14 assertions and four labels. Predator roles, taxonomic membership, human hunting occupations, catching activities, traps and bait are distinct. Seven malformed or mistagged terms are removed. U1/U3 exclusion scans remain clear. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q36 report](docs/quality/2026-10-09-q36.md) and [active queue](PLAN.md).
- **Earlier local data — Q35 (2026-10-09):** Added 27 concepts and 49 relations in U3; corrected seven assertions and five labels. Database data, DBMS software, table structures, constraint rules and transaction operations now have distinct meanings. Six baseline and five transient language-tag errors are cleaned. U1/U3 exclusion scans remain clear. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q35 report](docs/quality/2026-10-09-q35.md) and [active queue](PLAN.md).
- **Earlier local data — Q34 (2026-10-09):** Added 30 concepts and 64 relations in U3; corrected two assertions and six labels. Jenkins is software, while inherited physical client/server roles retain their facts. Both U1 and U3 remain clear in the shared-descendant exclusion scan. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q34 report](docs/quality/2026-10-09-q34.md) and [active queue](PLAN.md).
- **Earlier local data — Q33 (2026-10-09):** Added 22 concepts and 39 relations; corrected 19 assertions, 10 labels and 16 term rows. The five remaining U1 shared-descendant exclusion candidates are resolved without deleting their upper exclusions. U1 and U3 each have zero candidates in this specific scan. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q33 report](docs/quality/2026-10-09-q33.md) and [active queue](PLAN.md).
- **Earlier local data — Q32 (2026-10-09):** Added 28 concepts and 51 relations; corrected seven assertions and two labels, and merged one archived synonym duplicate with all terms retained. Five U1 exclusion candidates remain; U3 has none in the shared-descendant scan. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q32 report](docs/quality/2026-10-09-q32.md) and [active queue](PLAN.md).
- **Earlier local data — Q31 (2026-10-09):** Added 30 concepts and 47 relations in U3. Rejected the mistaken rest/API attribute without changing either everyday rest sense. HTTP/REST API intersections, method semantics and resource identifiers now have explicit distinctions. Six U1 exclusion candidates remain; the U3 scan has none. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q31 report](docs/quality/2026-10-09-q31.md) and [active queue](PLAN.md).
- **Earlier local data — Q30 (2026-10-09):** Added 26 concepts and 61 relations; corrected four assertions, one label and six term rows. New food-tool purposes extend existing cookware and utensil families. Six pre-existing U1 exclusion conflict candidates remain, with no new pair or witness. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q30 report](docs/quality/2026-10-09-q30.md) and [active queue](PLAN.md).
- **Earlier local data — Q29 (2026-10-09):** Added 32 concepts and 67 relations; corrected 10 assertions and two labels. Merged one archived fishing leaf, preserving the rare Russian noun on the survivor. Fishing methods, purposes, equipment and roles are distinct, and six U1 exclusion conflict candidates remain. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q29 report](docs/quality/2026-10-09-q29.md) and [active queue](PLAN.md).
- **Earlier local data — Q28 (2026-10-09):** Added 27 concepts and 54 relations, corrected eight assertions and eight labels, and removed fourteen malformed or mistagged term rows. Motion types form reviewed intersections. Stopping is a transition, rest is a state, and vector/angular quantities retain their own meanings. Seven U1 conflict candidates remain. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q28 report](docs/quality/2026-10-09-q28.md) and [active queue](PLAN.md).
- **Earlier local data — Q27 (2026-10-09):** Added 26 concepts and 51 relations; corrected 13 assertions, qualified one label and removed or reassigned 10 term rows. Darkness is a lighting state, pale colours belong to hue and lightness families, and photometric quantities remain distinct from perception. Eight U1 exclusion conflict candidates remain. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q27 report](docs/quality/2026-10-09-q27.md) and [active queue](PLAN.md).
- **Earlier local data — Q26 (2026-10-09):** Added 32 concepts and 69 relations for family groups, household units and kinship roles. Corrected 28 assertions without merging concepts or removing terms. The family group no longer inherits relation; friendship no longer necessarily inherits kinship. U1 exclusion conflicts fall from 10 to 9, with no new conflicts or witnesses and no changed exclusion edges. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q26 report](docs/quality/2026-10-09-q26.md) and [active queue](PLAN.md).
- **Earlier local data — Q25 (2026-10-09):** Added 36 concepts and 85 relations for game activities, sports formats, exercise and equipment. Corrected 14 assertions and two canonical labels; moved one physical-object term off an activity. Sport/game and racket/ball intersections are represented without making every sport physical exercise. U1 exclusion conflicts fall from 12 to 10, with no new conflicts or witnesses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q25 report](docs/quality/2026-10-09-q25.md) and [active queue](PLAN.md).
- **Earlier local data — Q24 (2026-10-09):** Added 41 concepts and 83 relations for clothing uses, materials, construction and components. Corrected 18 assertions, one canonical label and two lexical errors. Footwear remains clothing; jeans now inherit from trousers and denim clothing. U1 exclusion conflicts fall from 13 to 12, with no new conflicts or witnesses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q24 report](docs/quality/2026-10-09-q24.md) and [active queue](PLAN.md).
- **Earlier local data — Q23 (2026-10-09):** Added 28 concepts and 57 relations for dwellings, buildings, parts and rooms. Corrected 21 assertions, two canonical labels and two lexical errors. The house/apartment exclusion is retained while its wrong genus witness is removed. Two universal room-use exclusions are rejected to admit combined uses. U1 exclusion conflicts fall from 14 to 13, with no new conflicts or witnesses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q23 report](docs/quality/2026-10-09-q23.md) and [active queue](PLAN.md).
- **Earlier local data — Q22 (2026-10-09):** Added 32 concepts and 70 relations for weather, precipitation, measured quantities and information products. Corrected six relations while retaining reviewed natural and physical-process ancestry. No terms were removed. U1 exclusion conflicts fall from 15 to 14 with no new conflicts or witnesses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q22 report](docs/quality/2026-10-09-q22.md) and [active queue](PLAN.md).
- **Earlier local data — Q21 (2026-10-09):** Added 28 concepts and 55 relations for forest types, tree foliage classes and vegetation. Corrected five relations and one English translation. Forest/grove and forest/taiga conflicts are resolved, and forest/jungle disjointness is also rejected. U1 exclusion conflicts fall from 17 to 15 with no new conflicts or witnesses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q21 report](docs/quality/2026-10-09-q21.md) and [active queue](PLAN.md).
- **Earlier local data — Q20 (2026-10-09):** Added 21 concepts and 42 relations for materials, solutions, dispersions, phase states and physical joining. Corrected nine relations, four labels and 14 lexical entries. Object/phenomenon and physical/mental-process conflicts are resolved through sense and genus corrections while their exclusions remain unchanged. U1 exclusion conflicts fall from 19 to 17, with no new conflicts or witnesses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q20 report](docs/quality/2026-10-09-q20.md) and [active queue](PLAN.md).
- **Earlier local data — Q19 (2026-10-09):** Added 28 concepts and 50 relations for calendars and scheduling. Corrected 17 relations, three labels and eight lexical entries. The Wednesday/environment split resolves the time/space contradiction without removing its exclusion. U1 exclusion conflicts fall from 20 to 19, with no new conflicts or witnesses. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q19 report](docs/quality/2026-10-09-q19.md) and [active queue](PLAN.md).
- **Earlier local data — Q18 (2026-10-09):** Added 38 concepts and 77 relations for fasteners, threads, washers, tool types and physical installation actions. Corrected 15 relations, three action labels and 12 lexical entries. Rejected false tool/dishware and action/process exclusions; U1 exclusion conflicts with positive genus witnesses fall from 22 to 20, with no new conflicts or witnesses. Remaining candidates need individual review. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q18 report](docs/quality/2026-10-09-q18.md) and [active queue](PLAN.md).
- **Earlier local data — Q17 (2026-10-09):** Added 35 concepts and 103 relations for cookware, kitchen tools, food processing and cleaning. Corrected 23 relations, qualified the food-peeling label, and removed 20 malformed or mistagged terms. Material claims are scoped to appropriate vessel subtypes; the toaster now has bread-toasting purpose and capability. All explicit negations and grammar rows are preserved. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q17 report](docs/quality/2026-10-09-q17.md) and [active queue](PLAN.md).
- **Earlier local data — Q16 (2026-10-09):** Added 27 concepts and 41 relations for money, income, pay, expenses, budgets and savings. Consolidated three price-evaluation duplicates; refined four genera and two labels. Corrected payment nonwords and misplaced or mistagged terms. All explicit negations and grammar rows are preserved. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q16 report](docs/quality/2026-10-09-q16.md) and [active queue](PLAN.md).
- **Earlier local data — Q15 (2026-10-09):** Added 28 concepts and 62 relations for plane geometry, lengths, and angle measurement. Refined six genera, qualified three existing labels, and replaced one misleading English disk translation. All 23 explicit negations and all grammar rows remain unchanged. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q15 report](docs/quality/2026-10-09-q15.md) and [active queue](PLAN.md).
- **Earlier local data — Q14 (2026-10-09):** Added 54 concepts and 79 relations for physical quantities, derived units, measurement processes, and instruments. Refined one existing genus and qualified resultant force. All old terms, 23 explicit negations, and all grammar rows are preserved. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q14 report](docs/quality/2026-10-09-q14.md) and [active queue](PLAN.md).
- **Earlier local data — Q13 (2026-10-09):** Added 41 concepts and 58 relations for fractions, ratios, percentages, decimal forms, equation notation, and calculation targets. Mathematical notation is separated from values and programming constructs. No old terms or edges were removed. All 23 explicit negations and all grammar rows are preserved. Local database, SQL, version metadata, and documentation are updated. No commit, push or deployment. See the [Q13 report](docs/quality/2026-10-09-q13.md) and [active queue](PLAN.md).
- **Earlier local data — Q12 (2026-10-09):** continued the pinned dictionary
  comparison with 37 concepts and 74 relations for humidity, motion
  measurement, dimensional tools, and timekeeping. Reviewed 22 existing
  records, qualified three labels, and withdrew eight relations. Acceleration
  and diameter now have separate qualified senses. Removed four reviewed bad
  terms; translation gaps decreased to 7,299. All 23 explicit negations,
  29 grammar rows, and home contexts are preserved. Local DB, SQL snapshot,
  version metadata, and documentation are updated; no commit, push or deployment.
  See the [Q12 report](docs/quality/2026-10-09-q12.md). Next: mathematical ratios,
  percentages and physical quantities, then the adjacent taxonomy queue.
  Private review files: `G:\Projects\conceptuum-backups\quality-q12-20261009`.
- **Earlier local data — Q11 (2026-10-09):** full lexical comparison with
  Open English WordNet 2025 (135,969 entries; 107,519 synsets), followed by
  the first reviewed measurement cohort. Added 59 concepts and 85 relations;
  reused 14 existing meanings and refined two genera. Unit names, instruments,
  measurement purposes and targets are connected. Dictionary homonyms and
  scientific inaccuracies are reviewed explicitly against BIPM sources.
  All old terms, 23 explicit negations, and 29 grammar rows are preserved.
  Local DB, SQL, and version metadata are updated; no commit, push or deployment.
  See the [Q11 report](docs/quality/2026-10-09-q11.md) and the active dictionary
  queue in [PLAN.md](PLAN.md). Raw dictionary and comparison inventory:
  `G:\Projects\conceptuum-backups\dictionary-oewn-2025-20261009`.
- **Earlier local data — Q10 (2026-10-09):** reviewed 30 existing records;
  added eight concepts, clarified 24 labels, rejected 21 genus assertions,
  and added 38 relations. Corrected type/value, character/string, numeric,
  address, and processing distinctions. Added string length and processing
  roles. The database, SQL snapshot, and local version metadata are updated.
  All 23 explicit negations and all 29 grammar rows are preserved.
  No commit, push, or deployment was made. See the
  [Q10 report](docs/quality/2026-10-09-q10.md).
  Its remaining queue: data-structure homonyms and misplaced children,
  encoding/code points, signedness/ranges, fraction/percent/ratio, and units.
- **Earlier publication — Q9 (2026-10-09):** mathematical sets, cardinality,
  set operations, and collection/runtime corrections are published to
  https://conceptuum.su and GitHub commit `a4b334b`.
  At deployment, all six live tables matched the Q9 snapshot. Q39 supersedes
  that snapshot. Interface revision remains `2026-10-08.4`.
  See the [Q9 report](docs/quality/2026-10-09-q9.md).
- **Earlier foundation work — Q8 (2026-10-09):** corrected model/language,
  array/list/index, number/type, measurement, and three adjective meanings.
  Added six concepts and merged one duplicate. See the
  [Q8 report](docs/quality/2026-10-09-q8.md).
- **Euler demos and catalog sets (2026-10-08):** published interface revision
  `2026-10-08.4` to https://conceptuum.su. Seven database-backed demos show
  cross-classification, three-way intersection, Boolean operations, scoped
  complement, empty intersection, equality, and inherited exclusion. Catalog
  mode exposes exact record counts, sampled members, and supporting paths while
  preserving the separate semantic interpretation. All 21 live browser tests,
  Go checks, and JavaScript checks passed; all six public assets match the build.
  Q7 and the live database checksum are unchanged. See the
  [research and deployment report](docs/quality/2026-10-08-euler-demos.md).
- **Complex Euler diagrams (2026-10-08):** published interface revision
  `2026-10-08.3` to https://conceptuum.su. Combined circles now support partial
  overlap and multiple inclusion; selecting siblings automatically adds their
  direct shared genus. Automatic genera track selection changes and context,
  with explicit unknown-relation markers and an expandable relationship list.
  All 17 live browser tests, 22 geometry checks, and Go tests passed. The live
  database checksum and Q7 export are unchanged. See the
  [deployment report](docs/quality/2026-10-08-euler-overlap.md).
- **Euler circles (2026-10-08):** published interface revision `2026-10-08.2`
  to https://conceptuum.su. Compare up to eight concepts; add from search or the
  current concept, remove individual chips, or clear the selection. Context-aware
  genus/equality/exclusion inference feeds combined circles or independent pair
  comparisons. Unknown and conflicting relations remain explicit. Selection,
  context, and layout are shareable; SVG export and mobile controls are supported.
  All 14 live browser tests and Go inference/validation tests passed. The server
  database checksum is identical before and after deployment; Q7 is unchanged.
  See the [Euler deployment report](docs/quality/2026-10-08-euler.md).
- **Live visualizer update (2026-10-08):** published the new concept explorer
  and reviewed Q7 data to https://conceptuum.su. Interface revision
  `2026-10-08.1`, code `0.1.0-dev`. Added separate hierarchy/relation views,
  zoom/pan, filters, ancestry expansion, pagination, sharing, SVG export,
  keyboard controls, and a vertical mobile layout. All eight browser checks
  passed against the live site; public assets match the local build and all
  six deployed tables match Q7 row for row. The previous application and data
  are backed up. See the [deployment report](docs/quality/2026-10-08-visualizer.md).
  No GitHub push, tag, or GitHub Release was created in this deployment.
- **Этап:** лексикон учебника Виноградова/Кузьмина 1954 представлен в базе:
  термины логики (U5) и полнозначная лексика книги (U1). Наличие тегов
  `ru`/`en` не означает проверенного двуязычного наполнения: Q3 выявил
  тысячи русских слов с тегом `en`.
- **Documentation/runtime update (2026-10-08):** English README and current
  setup/filling guides reviewed against published commit `38c3e36` and the
  working code. Added `VERSION` (`0.1.0-dev`), `CHANGELOG.md`, pinned Python
  dependencies, and Python connection environment variables. Fixed the legacy
  filler's dry-run writes and candidate genus insertion. Data remains Q7;
  no new release tag or publication was made. Verification details:
  [instruction audit](docs/quality/2026-10-08-docs-review.md) and
  `docs/quality/2026-10-08-docs-verification.json`.
- **Earlier data review:** Q7 — причинность, математические операции и роли
  в процессах (2026-10-08). Пять дублей объединены с явным переносом восьми
  исходных связей; их полные строки сохранены в пакете. Добавлены
  математическая функция, арифметическая операция, деление, числовой остаток
  и исследование сна. Исправлены «сложиение» и «умножиение»; операция Mod
  отделена от результата. Поведение перенесено в процессы. Сняты ошибочные
  роли сна и смерти и причинные стрелки от вдовы/сироты к смерти.
  Отклонены 10 связей, добавлена 21; восемь исходных связей дублей заменены
  по архиву, одна совпала с уже исправленным родом. Код 27 дополнен явлением
  как допустимым объектом действия; остальные правила и ограничение субъекта
  не менялись. Исправлено повторение рода в другом универсуме и видов
  в определениях. Проверены 114 новых и 1 860 прежних условий, пять новых
  и 74 прежние проверки объединения, восемь маршрутов связей и 36 тестов
  кода. Все 23 строки отрицаний сохранены; циклы и нарушения сигнатур — 0.
  Откат проверен по пяти таблицам; исходная область верхнего аудита сохранена.
  Повторный прогон не меняет наполнение; SQL и gzip обновлены. Копии до/после
  и контрольные суммы указаны в отчёте.
  Пакет: `tools/quality_20261008_q7.json`;
  [отчёт и оставшиеся задачи](docs/quality/2026-10-08-q7.md).
  До того: Q6 — разбор смешанной верхней ветви и свойств
  организмов (2026-10-08). Разобраны все 36 прежних детей «абстрактного
  понятия»: восемь изолированных дублей объединены, остальные роды
  исправлены по смыслу. Само абстрактное понятие отнесено к понятию.
  Уточнено 21 имя; добавлены численность и относительное свойство.
  Отклонены 48 ошибочных связей, добавлены 48. Уточнены роды позвоночных
  и человека; кровь, анатомическая кожа и сон сняты с общего организма.
  Кожа-материал отделена от органа, исправлены направления частей тела
  и назначение спальни. У 121 понятия ветви растений и 15 понятий ветви
  грибов проверено отсутствие наследования этих трёх общих утверждений.
  Словарные значения и источники сохранены в пакете.
  Пройдены 384 новых условия, восемь проверок объединения, 1 476 прежних
  условий и 66 прежних проверок объединения; все 23 отрицания сохранены.
  Грамматика не менялась; циклы и нарушения сигнатур — 0.
  Полный откат проверен по строкам; повторный прогон не меняет наполнение.
  SQL и gzip обновлены. Пакет: `tools/quality_20261008_q6.json`;
  [отчёт и оставшиеся задачи](docs/quality/2026-10-08-q6.md).
  До того: Q5 — ревизия верхних частей графа (2026-10-08).
  Аудит охватил 329 исходных верхних узлов и дополнительные связи их ветвей.
  Отклонены 77 ошибочных связей, добавлены 50 связей и пять понятий;
  три изолированных дубля объединены, уточнены шесть имён.
  Разделены материальные объекты и информационное содержание, знание
  и познание, мысль и мышление. Исправлены роды слова, науки, организма,
  физических величин; 24 свойства выведены из явлений. Обращены ложные
  направления связей частей тела; выделено тело человека. Система
  дополнена структурированностью и составом. Снято соподчинение рода
  и вида. Пройдены 302 новых условия, три проверки объединения,
  1 174 прежних условия, 63 прежние проверки объединения и 19 тестов.
  Все 23 отрицания и грамматика сохранены. Полный откат проверен по
  строкам; повторное применение не меняет наполнение. SQL и gzip обновлены.
  Пакет: `tools/quality_20261008_q5.json`;
  [ошибки, недостаточность и резервная копия](docs/quality/2026-10-08-q5.md).
  До того: Q4 — словарная ревизия восприятия и связанных
  ментальных процессов (2026-10-08): 63 дубля словоформ объединены с
  существующими понятиями, исходные строки сохранены в манифесте;
  уточнено 30 имён. Отклонены 57 связей, добавлены 65 связей и три
  отдельных значения: восстановление зрения, повторный просмотр, досмотр.
  Исправлены искусственные существительные и кириллические записи `en`.
  Все 36 понятий итоговой ветки восприятия имеют английские термины
  без кириллических записей `en`. «Завидеть» проверено по словарю:
  разговорное увидеть издали; каноническое «завидение» заменено.
  Пройдены 685 условий Q4, 63 проверки объединения, 489 прежних условий
  и 12 модульных тестов. Все 23 отрицания и грамматика сохранены;
  циклы и нарушения сигнатур — 0. Полный откат проверен сравнением строк,
  повторное применение не меняет наполнение. SQL и gzip обновлены.
  Пакет: `tools/quality_20261008_q4.json`;
  [отчёт и резервная копия](docs/quality/2026-10-08-q4.md).
  До того: Q3 — ревизия значений и предметных связей
  (2026-10-08): отклонены 135 старых связей, включая 49 родовых;
  добавлены 152 принятые связи и 36 понятий, уточнено 31 каноническое имя.
  Блюда отделены от еды-действия, инвентарь от спорта, произведения от
  исполнения, научные дисциплины от исследований. Разделены совет,
  организация, мир, градус, Великобритания; исправлены география,
  календарные длительности, функции инструментов и органов.
  Нарушения сигнатур: 75→0 без изменения грамматики. Пройдены 190 новых
  проверок, 299 проверок Q1/Q2 и 13 случаев языковой проверки; все
  23 явных отрицания сохранены. Подробности и резервная копия:
  [отчёт Q3](docs/quality/2026-10-08-q3.md),
  пакет `tools/quality_20261008_q3.json`.
  Повторный запуск не меняет наполнение. Пути, определения, SQL-дамп и
  gzip обновлены; прежние рабочие копии сохранены.
  До того: Q2 — ревизия IT и профессиональных ролей
  (2026-10-08): исправлены 232 старые связи, включая 125 родовых; добавлены
  211 принятых связей и 12 понятий, уточнены 9 канонических имён.
  93 понятия людей выведены из ветки профессии; роды врача, учителя,
  учёного и IT-специалистов уточнены. Отделены программные методы от
  способов работы, программный редактор от человека, криптографический
  ключ от физического, сетевой хост от хозяина, ветка VCS от оператора.
  Устранены два изолированных IT-якоря, ложные переводы и назначения.
  Нарушения сигнатур: 235→75; корень без рода теперь только «сущее».
  Пройдены 279 проверок Q2 и 20 прежних проверок, повторный запуск
  не меняет наполнение. Бэкап и дампы обновлены.
  Пакет: `tools/quality_20261008_q2.json`; [отчёт](docs/quality/2026-10-08-q2.md).
  До того: ревизия качества и наполнение бытовых свойств
  (2026-10-08): 154 старых ошибочных ребра отклонены с сохранением истории;
  160 новых принятых рёбер, +15 понятий, 3 канонических переименования.
  Разделены мышь/компьютерная мышь, небо/нёбо, молния/застёжка,
  кисть/кисть руки, таз-сосуд/таз-скелет; ручка-деталь использована из базы.
  Закрыты все 115 пропусков английских терминов. Уточнены роды частей
  обуви, этажа, кухонных инструментов; дополнены назначения бытовой техники.
  Ошибочных по сигнатурам принятых рёбер: 364→235; циклов/самопетель 0.
  Кэш определений собран из канонических имён, без выбора старых словоформ.
  Пакет: `tools/quality_20261008.json`; [отчёт](docs/quality/2026-10-08.md).
  До того: добор ближайшего рода после bulk-cleanup
  (2026-09-01): ~720 NEW с «физическое действие» разобраны по
  движению/общению/восприятию/ментальному/эмоции/состоянию/процессам/
  труду/лечению/игре… (основы ≥4, без коротких подстрок); сняты
  230 skip-genus рёбер «действие» и 27 ложных (растение, дёготь, зять…);
  12 синонимов (бежание/спание/продавание…) слиты в канон; 14
  инфинитивов → сущ.; *везтие/*цвестие/*лезтие починены. Самопетель 0.
  До того: ревизия массового fill: сняты 5797 самопетель рода; починена
  морфология; словоформы-прилагательные удалены (~5k); kod 82→22;
  адвокат — один узел, два рода. concepts 17916→12501→12469.
  До того: добиты термины. IT: 881 русских (файл, БД, ЯП…;
  имена собственные как заимствования, 21 шт.). Быт: 88 фразовых `to …`
  получили канон без to (беречь→care, ссылка→reference). Покрытие
  ru+en: 4557/4557, only-to=0.
  До того: следующий ярус до p=3: физическое/социальное
  действие, нравственность (добро 64 зло; честность, жадность),
  природные явления (гроза→молния/гром), рельеф/ландшафт, дни недели
  (омоним среды обойдён), комнаты, напитки, мышление (+обобщение).
  p3: 316→354. +давление.
  До того: остов сверху до p=3.
  До того: rank3+4 по `jnana2_rel5_rank.tsv`
  (`fill_from_rank3.py`, `fill_from_rank4.py`). Ещё +98 понятий,
  +170 терминов: делание (делать/сделать), ум, крик, семья/дед,
  будущее, смысл, адрес… Топ-1500 content: 1100→1207+ попаданий.
  До того: rank1+2 (+53 понятия).
  До того: массовое заполнение свойств (2026-08-31).
  План `docs/fill-properties.md`: свойства на высший род, вид — только
  отличие; без локальной модели (`tools/fill_props1.py`). Сигнатуры
  15/20/21/22/27 расширены на `явление`. +9 понятий (теплокровность,
  фотосинтез, съедобность…), +248 нетто рёбер после prune. kod 15:
  6→19. Определения: птица — теплокровность/перо/полёт; рыба —
  холоднокровность/плавник; пища — съедобность; мухомор — ядовитость
  и не-съедобность.
  До того: таксономия как DAG + абстракция слово→понятие
  (2026-08-30). Два рода на одном узле, универсум на ребре kod 14;
  `rebuild`/`in_subtree`/`define` ходят по DAG. Слиты 89 прилагательных
  в существительные-термины (`tools/merge_adj_terms.py`), 37 свалок
  принадлежность/происхождение удалены как изолированные; closed-bearer
  снят (судоходное→судоходство, водоём—[20]→судоходство 90). Слиты 84
  пары инфинитив/отглагольное сущ. (`tools/merge_verb_noun.py`: влиять→влияние).
  До того: ревизия рода-3 (fix_genus3.py): «действие» разобрано —
  241 переподчинение (осталось 201 прямой ребёнок); новый род «физическое
  действие»; структурные фиксы: действие→явление (было сущее), физический/
  ментальный/физиологический процесс→процесс. Раньше: РЕВИЗИЯ БЛИЖАЙШЕГО РОДА (tools/fix_genus.py,
  fix_genus2.py). Правило: род = ближайший род, без пропусков (январь → месяц
  → период времени; север → сторона света → направление). Новые роды:
  день недели, часть суток, сторона света; добавлены недостающие месяцы, юг,
  среда-день (омоним «среды»-environment); слиты столетие→век, время года→сезон.
  Грубые ошибки шкал: хищное/рогатое/жвачное → признак, больное/грязное/жидкое →
  состояние, деревянное/судоходное → свойство; врач/повар → профессия
  (ошибочное решение, исправлено в Q2),
  брат/жена → родственник. Откат ложных переименований сущ.: пожарный,
  подчинённый, окружающие, служащий, трудящийся.
  До того: РЕВИЗИЯ прилагательных (tools/neuter_adjectives.py):
  канон = средний род («тяжёлое»), муж./жен. формы — термины; 619
  переименований, 1 слияние (прошлый→прошлое). «Тяжёлая гиря» = вхождение
  «гиря» в общее «тяжёлое». До того: РЕВИЗИЯ глаголов (tools/merge_verbs.py):
  167 групп видовых/возвратных пар слиты в одно понятие (канон — отглагольное
  существительное или невозвратный несовершенный вид), −281 понятие,
  +562 термина. Пример: отклонить/отклонять/отклоняться → «отклонение».
  До того: fill_lex1–7 (существительные), fill_verb1–3 (глаголы),
  fill_adj (прилагательные); остаток 36 лексем — мусор OCR и местоимения
  (books/lex_*.tsv регенерируются tools/extract_lexemes.py).
- **Следующее действие:** продолжить смысловую ревизию верхних ветвей:
  ошибочные дети природного объекта (34), физических и ментальных
  свойств, времени; классификация простейших и отдельных групп животных.
  Проверить остальные ошибочные названия и роды физиологических процессов
  (202), включая «предлагание», «завопение», «процедение», «нацепение».
  Математические целые числа и целочисленный тип (1198), а также значение
  Map (903), ещё требуют разделения/уточнения. Не объединять программную
  функцию (446) с математической функцией (24476).
  Подробности и ID — в [отчёте Q7](docs/quality/2026-10-08-q7.md).
  Аудитор верхних узлов: `tools/audit_upper_graph.py`; при сравнении
  сохранять исходную область через `--scope-from`.
  Далее — английское наполнение и неестественные отглагольные имена:
  7 306 понятий без любого термина `en` с латиницей;
  7 437 понятий содержат кириллическую запись `en` без латинских букв.
  Это эвристика для проверки, а не оценка правильности остальных переводов.
  Использовать существующие русские узлы, не создавать дубли переводом.
  Сомнительные слова проверять по словарям, сохранять источник и смысл;
  совпадение основы не гарантирует синонимию или видовую пару.
  Следующие ветки — физическое действие и ментальный процесс.
  Далее — дубли между универсумами, ближайшие роды перегруженных веток и
  отличительные свойства сверху вниз. Нулевые нарушения сигнатур не
  подтверждают истинность всех фактов. Поиск длинных выражений всё ещё
  извлекает лишние понятия по отдельным словам.
  Подробные ID и термины: `docs/quality/2026-10-08-q7-after.json`.

## Current local database snapshot — 2026-10-09, Q39

```
concepts:     13456 (Everyday: 12049, IT: 1030, Legal: 160, Logic: 217)
edges:        18450 (accepted: 17350, rejected: 1100)
paths:        64683
terms:        37825 (RU/EN tags present; translation quality remains incomplete)
without_latin_en: 7251
signature-invalid: 0
processed:    1:11624  2:853  3:979
self-loops:   0
taxonomy cycles: 0
deprecated relation codes: 0
explicit negations preserved: 23
```

## Журнал этапов

| Дата | Этап | Что сделано | concepts | edges | paths |
|---|---|---|---|---|---|
| 2026-10-09 | Q39 local | Containers, brushes, and scraping tools; 41 additions, 106 new relations; local only | 13456 | 18450 | 64683 |
| 2026-10-09 | Q38 local | Database names, views, plans, and key columns; 36 additions, 64 new relations; local only | 13415 | 18344 | 64340 |
| 2026-10-09 | Q37 local | Motion paths, inertia, momentum, and work; 35 additions, 68 new relations; local only | 13379 | 18280 | 64131 |
| 2026-10-09 | Q36 local | Animal roles, hunting, catching, and bait; 37 additions, 84 new relations; local only | 13344 | 18212 | 63904 |
| 2026-10-09 | Q35 local | Database software, structures, constraints, and transactions; 27 additions, 49 new relations; local only | 13307 | 18128 | 63601 |
| 2026-10-09 | Q34 local | Client/server meanings, HTTP roles, and automation; 30 additions, 64 new relations; local only | 13280 | 18079 | 63450 |
| 2026-10-09 | Q33 local | States, sleep, mood, and vocal actions; 22 additions, 39 new relations; local only | 13250 | 18015 | 63238 |
| 2026-10-09 | Q32 local | Recognition, authorship, and information status; 28 additions, 51 new relations; local only | 13228 | 17976 | 63138 |
| 2026-10-09 | Q31 local | REST, HTTP, and resource identifiers; 30 additions, 47 new relations; local only | 13201 | 17926 | 62983 |
| 2026-10-09 | Q30 local | Bakeware, kitchen tools, and food actions; 26 additions, 61 new relations; local only | 13171 | 17879 | 62809 |
| 2026-10-09 | Q29 local | Fishing methods, equipment, and participant roles; 32 additions, 67 new relations; local only | 13145 | 17818 | 62599 |
| 2026-10-09 | Q28 local | Motion, quantities, and braking terminology; 27 additions, 54 new relations; local only | 13114 | 17752 | 62366 |
| 2026-10-09 | Q27 local | Light, perception, and photometric measurement; 26 additions, 51 new relations; local only | 13087 | 17698 | 62203 |
| 2026-10-09 | Q26 local | Family groups, household units, and kinship roles; 32 additions, 69 new relations; local only | 13061 | 17647 | 62045 |
| 2026-10-09 | Q25 local | Game activities, sports formats, and physical equipment; 36 additions, 85 new relations; local only | 13029 | 17578 | 61669 |
| 2026-10-09 | Q24 local | Clothing purposes, materials, components, and intersecting garment families; 41 additions, 83 new relations; local only | 12993 | 17493 | 61342 |
| 2026-10-09 | Q23 local | Dwellings, building components, and combined room uses; 28 additions, 57 new relations; local only | 12952 | 17410 | 61029 |
| 2026-10-09 | Q22 local | Weather, precipitation, quantities, and forecasts; 32 additions, 70 new relations; local only | 12924 | 17353 | 60808 |
| 2026-10-09 | Q21 local | Forest types, foliage classes, and vegetation; 28 additions, 55 new relations; local only | 12892 | 17283 | 60651 |
| 2026-10-09 | Q20 local | Material composition, phase states, and physical joining; 21 additions, 42 new relations; local only | 12864 | 17228 | 60422 |
| 2026-10-09 | Q19 local | Calendars, scheduling, and the Wednesday/environment split; 28 additions, 50 new relations; local only | 12843 | 17186 | 60307 |
| 2026-10-09 | Q18 local | Fasteners, gripping tools, and upper-graph exclusions; 38 additions, 77 new relations; local only | 12815 | 17136 | 60196 |
| 2026-10-09 | Q17 local | Kitchen tools, cookware, food preparation, and cleaning; 35 additions, 103 new relations; local only | 12777 | 17059 | 59924 |
| 2026-10-09 | Q16 local | Money vocabulary, budgets, savings, and payment repairs; 27 additions, 41 new relations; local only | 12742 | 16956 | 59653 |
| 2026-10-09 | Q15 local | Plane geometry, geometric lengths, and angle measurement; 28 additions, 62 new relations; local only | 12718 | 16918 | 59528 |
| 2026-10-09 | Q14 local | Physical quantities, derived units, and measurement instruments; 54 additions, 79 new relations; local only | 12690 | 16856 | 59328 |
| 2026-10-09 | Q13 local | Fractions, ratios, percentages, and mathematical notation; 41 additions, 58 new relations; local only | 12636 | 16777 | 59005 |
| 2026-10-09 | Q12 local | Humidity, motion measurement, dimensional tools, timekeeping; 37 additions, 8 withdrawn relations, 74 new relations; no publication | 12595 | 16719 | 58725 |
| 2026-10-09 | Q11 local | Dictionary comparison; 59 additions, 2 refined genera, 85 new relations; no publication | 12558 | 16645 | 58486 |
| 2026-10-09 | Q10 local | Types/values, text terminology, addresses, processing; 8 additions, 24 renames, 21 rejected genera, 38 added relations; no push or deployment | 12499 | 16560 | 58142 |
| 2026-10-09 | Q9 | Sets, cardinality, set operations, collection and runtime senses; 19 additions, 1 merge, 7 rejected relations, 50 added relations; live dataset updated | 12491 | 16522 | 58117 |
| 2026-10-09 | Q8 | Foundation pilot: model/language, array/list/index, number/type, measurement, adjectives; 6 additions, 1 merge, 11 rejected relations, 22 added relations; live dataset updated | 12473 | 16473 | 58000 |
| 2026-10-08 | Q7 | Пять дублей с зависимыми связями объединены; операции отделены от результатов; поведение и роли процессов; 10 исправлений; уточнён код 27; 114 новых условий и 36 тестов | 12468 | 16452 | 57970 |
| 2026-10-08 | Q6 | 36 детей абстрактного понятия разобраны; восемь дублей объединены; 48 исправлений связей; позвоночные и свойства организмов; 384 новых условия и проверка наследования растений/грибов | 12468 | 16439 | 57948 |
| 2026-10-08 | Q5 | Верхние ветви: 77 исправлений, +50 связей, +5 понятий, три объединения; содержание/процесс/носитель, слово/знак, части тела; 302 новых условия; оставшиеся пробелы описаны | 12474 | 16399 | 57294 |
| 2026-10-08 | Q4 | 63 дубля объединены; 30 имён уточнены; 57 связей исправлены; три значения разделены; словарная ревизия восприятия; 685 условий и 63 проверки объединения | 12472 | 16353 | 54623 |
| 2026-10-08 | Q3 | 135 исправлений; +36 понятий; предметы/действия, география, время, науки; 190 новых проверок; нарушения сигнатур 75→0; выявлено ложное en-покрытие | 12532 | 16351 | 54830 |
| 2026-10-08 | Q2 | 232 исправления; люди/профессии, IT-роды и омонимы; +12 понятий; 279 проверок; нарушения сигнатур 235→75 | 12496 | 16199 | 54608 |
| 2026-10-08 | Q1 | 154 исправления; омонимы, часть/назначение/способность; +15 понятий; наличие тегов ru/en 100% (переводы переоценены, см. Q3); нарушения сигнатур 364→235 | 12484 | 15988 | 53826 |
| 2026-09-01 | FIX2 | leftover nearest-genus: 720 reparent с физ.действия; skip-genus/misfile; inf→noun; *тие | 12469 | 15826 | 53738 |
| 2026-09-01 | FIX | bulk-fill: самопетли, морфология, словоформы, 82→22, reparent | 12501 | 16101 | 53808 |
| 2026-08-31 | T2 | ярус 2: действия, нравственность, природа, быт; +зло/обобщение/давление; p3=354 | 4557 | 6790 | 19927 |
| 2026-08-31 | T1 | сверху вниз: уровни 1–3 на остове; +небытие/протяжённость/туловище; p3=316 | 4558 | 6710 | 19931 |
| 2026-08-31 | P0 | processed 0–3: 1 род/виды, 2 существенные/специфические, 3 параллельные; infer 1→2/3 | 4556 | 6575 | 19883 |
| 2026-08-31 | R2 | rank3+4: делание/ум/крик/семья/смысл… +98 узлов +170 терминов | 4556 | 6575 | 19883 |
| 2026-08-31 | R1 | частотный список jnana2: rank1+2, понятия не слова; +53 узла, +161 термин; пойти→ходьба, смерть | 4458 | 6467 | 19473 |
| 2026-08-31 | P1 | свойства на род: fill_props1 + сигнатуры явление; +9 понятий, +248 рёбер нетто (15: 6→19, 20: 282→366); prune 49 inherited | 4405 | 6404 | 19254 |
| 2026-08-30 | A9 | возвратные инфинитивы: канон = сущ. (согласиться→согласие, отказываться→отказ; 26 переименований + 17 слияний в уже существующие) | 4396 | 6156 | 19223 |
| 2026-08-30 | A8 | оставшиеся инфинитивы → существующие сущ. того же корня (48: анализировать→анализ, жить→жизнь, летать→полёт…); нет слова в базе — не трогали (~414) | 4413 | 6173 | 19283 |
| 2026-08-30 | A7 | ISA=DAG (два рода + универсум на ребре); merge_concepts; 89 adj→термин, 37 dump-drop, 84 inf→noun; closed-bearer снят; fill_llm коды 20–27 | 4461 | 6221 | 19476 |
| 2026-08-30 | A6 | аудит «отношение» (68→61): воздействие/влияние (+инфинитивы)→действие, взаимодействие→процесс, разница→различие, логический закон→правило; реляционные прилагательные (враждебное, соподчинённое…) оставлены — их носитель и есть отношение; создан docs/ontology-rules.md — все правила и журнал ошибок, ссылка из README | 4671 | 6435 | 19906 |
| 2026-08-30 | A5 | фикс закрытых носителей (fix_bearer.py): 20 прилагательных получили родом класс носителя (хищное/рогатое/позвоночное/жвачное/ластоногое→животное, цветковое→растение, перелётное→птица, больное/убитое/одноклеточное/высокоорганизованное→организм, жилое→помещение, отопительное/втяжное→устройство, гусеничное→транспортное средство, удушливое→воздух, грязное/чистое→чистота); свойства — отдельными рёбрами 20/21/70/71 со strength; +4 пары 63/64; новая шкала «чистота»→состояние | 4671 | 6435 | 19876 |
| 2026-08-30 | A4 | судоходное/несудоходное: род → водоём (носитель закрыт), свойство → edge 20 к судоходству (90 / 0), пара 64; правило «род прилагательного = класс носителя, если носитель закрыт» записано в README | 4670 | 6415 | 19858 |
| 2026-08-29 | A3 | ревизия рода-4 (fix_genus4.py): разбор «свойство» — 448 переподчинений (489→42 прямых ребёнка, только логико-аналитика + шкалы); новые роды: длительность, модальность, способность, масштаб, связь, тождество, преимущество, частота, состав, положение-пространственное (омоним к 3301-тезису); значения→шкалы (истинное→истинность…), -ое→тематические роды | 4670 | 6412 | 19864 |
| 2026-08-29 | A2 | новый род «агрегатное состояние»→состояние; жидкое/газообразное/застывшее туда (фикс рассогласования: жидкое было в состоянии, газообразное в свойстве) | 4660 | 6402 | 19140 |
| 2026-08-29 | H | ревизия рода-3 (fix_genus3.py): разбор «действие» — 241 переподчинение (442→201 прямых детей); новый род «физическое действие»; действие→явление; физ./ментальный/физиологический процесс→процесс | 4659 | 6401 | 19127 |
| 2026-08-29 | G | ревизия ближайшего рода (fix_genus.py, fix_genus2.py): +10 понятий-родов/членов шкал, ~60 переподчинений, 2 слияния синонимов, откат 5 ложных переименований | 4658 | 6400 | 17815 |
| 2026-08-29 | N | ревизия прилагательных (neuter_adjectives.py): канон = средний род («тяжёлое»), 619 переименований + 1 слияние (прошлый→прошлое); принцип записан в README | 4648 | 6390 | 17783 |
| 2026-08-29 | M | ревизия глаголов (merge_verbs.py): 167 групп слияния, −281 понятие, +562 термина; отклонить/отклонять/отклоняться → «отклонение» | 4649 | 6391 | 17785 |
| 2026-08-29 | X | лексикон книги целиком: +87 якорных родов, ~1030 существительных, 825 глаголов, 497 прилагательных (ru+en, роды из существующего дерева) | 4930 | 6672 | 18485 |
| 2026-08-29 | L | универсум «логика» (U5): 7 проходов по учебнику Виноградова/Кузьмина 1954 — понятие, определение/деление, суждение, законы логики, силлогизм, индукция/аналогия/гипотеза, доказательство/опровержение; +211 понятий U5, 0 отказов после фиксов сигнатур (74 для связей форм) | 2556 | 4298 | 11512 |
| 2026-08-28 | R | RELATE по всему бытовому: 4 прохода, +32 понятия, +445 связей (61/63/70/72/74/80/81/82/83/21/23/25), unprocessed=0 | 2027 | 3277 | 9038 |
| 2026-08-28 | E | второй слой: семья/родственники (62-пары), профессии (70→действия), город, торговля, школа | 2076 | 3372 | 9274 |
| 2026-08-28 | F | болезни, спорт, музыка/инструменты, искусство, праздники | 2122 | 3460 | 9471 |
| 2026-08-28 | G1 | еда вглубь: напитки/блюда/сладости; расширение фруктов/ягод/грибов/рыб/птиц/диких животных | 2221 | 3643 | 10022 |
| 2026-08-28 | G2 | одежда/обувь/мебель/транспорт/инструменты/части тела/дом/посуда; сезонность через 73 | 2305 | 3833 | 10452 |
| 2026-08-28 | — | план создан | 1144 | 1396 | 5154 |
| 2026-08-28 | 0 | аудит: остов чист, сирот нет; человек→животное ок | — | — | — |
| 2026-08-28 | 1 | вещества: твёрдые/камни/материалы/жидкости/газы/металлы/пища; процессы (таяние, горение…); связи 81/70/83/21 | 1232 | 1529 | 5507 |
| 2026-08-28 | 9 | ревизия: 0 циклов, 0 мульти-родителей, 0 сирот; verify-пробы прошли; дамп обновлён | 1838 | 2470 | 8265 |
| 2026-08-28 | 8 | связывание: функции артефактов (80), свойства предметов (21/23), агенты (82), каusalные (70/71/74) | 1838 | 2472 | 8369 |
| 2026-08-28 | 7 | пространственные/социальные отношения, семейные роли, детали объектов; часть-целое для деревьев/книг/мебели/часов/лестниц | 1826 | 2381 | 8323 |
| 2026-08-28 | 6 | действия: бытовые/ручные операции/кухня/движение/восприятие/ментальные/эмоции/социальные/физиология; пациенсы, агенты профессий, антонимы действий | 1781 | 2297 | 8129 |
| 2026-08-28 | 5 | шкалы: цвета/вкусы/запахи/тактильные/размер/форма/температура/ментальные/оценочные; +34 антонима (63) | 1697 | 2173 | 7803 |
| 2026-08-28 | 4 | природа: водоёмы/рельеф/ландшафты/небесные тела/явления/время и сезоны; каusalные цепочки (гроза→молния→гром), временные ряды (утро→день→вечер→ночь) | 1617 | 2059 | 7490 |
| 2026-08-28 | 3 | артефакты: мебель/инструменты/одежда/посуда/сооружения/транспорт/быттехника/канцелярия/игрушки; функции(80), материалы(81), части(21); merge мотор→двигатель | 1542 | 1945 | 7169 |
| 2026-08-28 | 2 | организмы: классы животных, ~70 видов, овощи/фрукты/злаки/деревья/цветы, роли человека, 37 частей тела; связи часть-целое и продукты (пчела→мёд 95%) | 1414 | 1750 | 6569 |

## Рабочие заметки

- 2026-08-30: уточнение таксономии. (1) Перекрёсток научных и бытовых
  родов (физическое явление / видимое) — **одно понятие, два kod 14,
  универсум на ребре**; омонимы (среда) по-прежнему разные узлы.
  (2) Прилагательные и инфинитивы — термины, не виды; судоходное =
  судоходство, влиять = влияние; форма слова = отношение из `relevant`.
  Правило closed-bearer (судоходное → водоём) снято. Движок ещё
  деревообразный: второй род пишется в `edge`, но `rebuild`/`parent`
  оставляют последний. Подробно: docs/ontology-rules.md.

- Движок: `tools/jnana_engine.py` (копия `jnana_engine.py` из корня;
  при расхождении корень — источник истины). Этап 4: +resolve_all (омонимы между универсумами), метки универсума в ask.py.
- Подключение: MariaDB 5.5, 127.0.0.1:3306, БД `jnana3`, root/123.
- Скрипты наполнения кладутся в `tools/fill_<этап>.py`, исполняются,
  затем rebuild/define/stats — и строка в журнал выше.
- 2026-08-28: починен `in_subtree` — теперь ходит по живой цепочке
  parent из edges, а не по устаревающему concept_path (иначе валидация
  новых понятий до rebuild() ложно падала).
