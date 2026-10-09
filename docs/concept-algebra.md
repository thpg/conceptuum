# Concept algebra

`concept_algebra` parses expressions into an AST, resolves their terms to
concept IDs, and evaluates them against a read-only database snapshot.
It needs Python 3.9 or newer. Parsing and JSON snapshot evaluation use only
the standard library; MariaDB access uses the project's existing PyMySQL
dependency and `JNANA_*` connection settings.

Use the [web workspace](https://conceptuum.su/algebra?lang=en), Python API or CLI.
All three use the same parser and evaluator. The interface is English; concept
terms can be English or Russian. Language version: **1**.

## Web workspace

Open **Algebra** in the explorer header. Choose one of nine database demos or
enter an expression, select its relation context and optionally specify a
**Within** domain. Search for a term to insert its exact ID at the editor cursor.
Ambiguous terms offer explicit sense choices without guessing. Press **Evaluate**
or Ctrl/Cmd+Enter, then **Explain** beside a result to inspect source edges.

**Copy query link** preserves the expression, domain, context, language and
inspected record. **Inspect any record** checks a concept ID even when the
record is outside the result; it also traces operands of counts and comparisons.
**Download JSON** exports schema `conceptuum.algebra.example.v1`: the original
request and result, resolved AST, all matching IDs, selected member evidence,
data revision and snapshot SHA-256. Labels are paginated, but the `ids` array is
complete. Boolean and integer results have a `value` instead of member IDs.
See [LLM training data and evaluation](../README.md#llm-training-data-and-evaluation)
for a suggested dataset workflow.

### Comparison evidence

Set comparisons and `disjoint(A, B)` return a `diagnostics` object with operand
sizes and three exact regions: `left_only`, `intersection`, and `right_only`.
Each region includes up to five labeled `items`, a `truncated` flag, and a
`counterexamples` flag when its records falsify the comparison. Equal sets
explain a failed proper-subset comparison through equality, without inventing
a counterexample. `count(A)` and `empty(A)` show the counted set; comparisons
such as `count(A) > count(B)` retain the evaluated integer operands.

Click a diagnostic sample to inspect its membership paths in both operands.
For example:

```console
python -m concept_algebra '#25439 <= #25446' --json --explain 25439
python -m concept_algebra 'count(#24488 & #24489)' --json --explain 24492
```

Set explanations retain `member`. Scalar explanation nodes use `kind` and
`value`, with recursively typed `operands`. A record's operand membership
illustrates the computation; it does not replace the complete-set comparison.
All diagnostics use the selected finite domain and remain statements about
catalog records, including when a missing path supplies a counterexample.

### Collecting examples

Enter an optional **Question** and use **Add current example** to save the
evaluated query, answer, version metadata, and currently selected explanation.
The **LLM example collection** supports individual removal, replay and JSONL
download. Every JSONL line is a `conceptuum.algebra.example.v1` object, with an
optional top-level `question` string. Newlines inside questions are JSON-escaped.
Repeated saves of the same question, query, inspected record, answer and source
revision do not duplicate an example just because its displayed page changed.

The collection uses browser storage, with a 50-example / 4 MiB limit; it is
not uploaded. Questions are also omitted from evaluation requests and shared
URLs. If browser storage is unavailable or full, the interface identifies the
session-only collection and still allows JSONL export. Replaying an example
reevaluates the query against current data without overwriting its saved answer.
Separate graph revisions and reviewed/unreviewed examples in your own pipeline.

### HTTP API

The read-only HTTP endpoint is `POST /api/algebra` with `Content-Type: application/json`:

```json
{"expression":"#25439 & #25446","context":1,"lang":"en","within":null,"limit":25,"offset":0,"explain":25447}
```

`context` defaults to 1; `lang` is `en`, `ru`, or null. `limit` is 1–100 and
`offset` is 0–1,000,000. Omit `explain` or use a concept ID to inspect result
membership or operands of a scalar expression. Errors contain a message, with source positions and candidate IDs
when applicable; `field` identifies `expression` or `within`. Offsets count
Unicode code points. The web API limits combined expression/domain size to 256
AST nodes and 12 property selectors, with a 96 KiB request-body limit.

The Go server proxies to a Python worker on loopback. The worker caches at most
two relation contexts and reloads when `data_revision` or `source_dump_sha256`
changes in `version.json`. Update version metadata when publishing database
changes. See [worker setup](../visualizer/README.md#concept-algebra-worker).

## Start with the Q39 database

Import the bundled database using the [setup guide](setup.md), then run these
commands from the repository root. The expressions below work in PowerShell
and Bash without changing their quoting.

```console
python -m concept_algebra '#25439 & #25446' --context 1 --lang en
python -m concept_algebra '#25439 & #25446' --json --explain 25447
python -m concept_algebra 'parents(exact(#25447))' --lang en
python -m concept_algebra '#3500 & has(material, #90)' --lang en
python -m concept_algebra 'count(#24488 & #24489)'
```

Verified Q39 results:

| Expression | Result |
|---|---|
| `#25439 & #25446` | `#25447`, glass food storage jar |
| `#25439 - #25446` | `#25439`, the general glass-jar record |
| `#25447 <= #25439` | `true`, catalog inclusion |
| `parents(exact(#25447))` | `#25439` and `#25446` |
| `#3500 & has(material, #90)` | Four vessel records with an unopposed recorded glass-material assertion, including inherited assertions |
| `#24488 & #24489` | `#24492`, the singleton-set record |
| `count(#24488 & #24489)` | `1` stored record |

`--explain 25447` returns the real edge IDs supporting membership. In the first
intersection, these are genus edges **37656** and **37734**. The material query
inherits glass from edge **37716**, owned by glass jar `#25439`, through genus
edge **37656**. That more specific assertion supersedes edge **37723** on the
broader glass-vessel concept.

## What a set contains

A reference such as `#25439` denotes the concept record itself and all records
that reach it through accepted, positive genus edges (`14`) or coextension
edges (`30`). Coextension is traversed in both directions. A concept with
several genera can belong to several sets, producing partial intersections.

The members are **stored concept records**. They are not physical objects or
elements of the mathematical sets named by those records. For example, the
empty-set concept has one database record; referring to it does not produce
the empty catalog set. Use `EMPTY` or `∅` for that.

Set comparisons and `disjoint()` describe this finite catalog. An empty
intersection means that no matching record is stored. It does not prove that
the corresponding real-world classes cannot overlap. Overlap, exclusion,
opposition and causal edges do not fabricate catalog members or remove
existing membership paths.

Only edges from the selected `--context` participate. The evaluator reads
their actual graph rather than the unscoped `concept_path` cache or a single
home parent. Concept identities remain global: an ID can participate in several
contexts even when its home context differs. With no `--within`, `U` contains
every concept record in the snapshot, including records with no edges in the
selected context.

Use an explicit domain for a useful complement:

```console
python -m concept_algebra '~#25439' --within '#1531' --lang en
```

This returns stored jar records outside the glass-jar catalog set. `--within`
is evaluated once against the full catalog, then defines `U` for the main
expression. Each set-valued operation is clipped to this domain. It limits
the output without cutting inheritance paths through genera outside the domain.

## References and operators

| Syntax | Meaning |
|---|---|
| `#25439` | Concept by stable ID, including its catalog descendants |
| `"glass jar"`, `'glass jar'` | Exact term or canonical name |
| `bird` | An unquoted single-word term |
| `en:"glass jar"`, `ru:"стеклянная банка"` | Exact term in an explicit language |
| `exact(#25439)` | Only that record, without descendants or coextension aliases |
| `U`, `EMPTY`, `∅` | Current finite domain or empty set |
| `A \| B`, `A + B`, `A ∪ B`, `A or B` | Union |
| `A & B`, `A * B`, `A ∩ B`, `A and B` | Intersection |
| `A - B`, `A \ B`, `A ∖ B` | Difference |
| `A ^ B`, `A △ B`, `A ⊕ B`, `A xor B` | Symmetric difference |
| `~A`, `!A`, `¬A`, `not A` | Complement relative to `U` |
| `A <= B`, `A ⊆ B` | Catalog subset, allowing equality |
| `A < B`, `A ⊂ B` | Proper catalog subset |
| `>=`, `>`, `⊇`, `⊃` | Corresponding superset comparisons |
| `A == B`, `A = B`, `A != B`, `A ≠ B` | Equality or inequality |

`A` and `B` in this table stand for expressions, not variable declarations.
Precedence, from strongest to weakest: parentheses and function calls;
unary complement; intersection and difference; symmetric difference; union;
comparison. Binary set operations at the same precedence associate to the
left. In particular, `A - B & C` means `(A - B) & C`.

Comparisons cannot be chained. Keywords and function names are case-sensitive.
Quote reserved terms such as `"U"` or `"and"` to look them up as concepts.
Quoted terms support escaped quotes, backslashes, `\n`, `\r`, `\t`, and
four-digit `\u` escapes; supplementary Unicode characters can be written literally.

Term lookup normalizes Unicode to NFC, folds case, and normalizes whitespace.
It performs no stemming, fuzzy matching or automatic translation. Multiple
matching senses produce an error with all candidate IDs and labels. For
example, Q39's `en:"glass"` matches both material `#90` and drinking vessel
`#1532`; `has(material, #90)` selects the material explicitly.

`--lang en` restricts unqualified term lookup and chooses English display
terms when available. An explicit `ru:` or `en:` overrides that lookup language.
Without `--lang`, terms from all languages and canonical labels are searched.

## Graph operations

| Function | Result |
|---|---|
| `parents(S)` | Direct genera of each member of S |
| `children(S)` | Direct species of each member of S |
| `ancestors(S)` | All proper genus ancestors of each member of S |
| `descendants(S)` | All proper genus descendants of each member of S |
| `related(code, S)` | Targets of direct accepted positive edges from S |
| `subjects(code, T)` | Subjects of direct accepted positive edges into T |
| `count(S)` | Number of stored records in S |
| `empty(S)` | Whether S contains no records |
| `disjoint(A, B)` | Whether the two catalog sets share no record |

The four navigation functions follow only genus edges, not coextension.
They operate on every supplied member, so use `exact(...)` when starting from
one record. If several seeds are supplied, a seed may itself be an ancestor
of another seed and therefore appear in `ancestors(S)`.

Direct projections respect the relation's stored symmetry flag. They do not
inherit properties or apply generic transitive inference to arbitrary relations.
Candidates, rejected edges and `strength=0` assertions do not form positive
projection or membership edges.

Numbers are scalar literals, not implicit concept IDs. `count(A) >= 2` is a
numeric comparison; `≤` and `≥` are supported aliases. `#2` refers to a concept. Set operators require sets,
and comparisons require matching operand types. Booleans support only equality
and inequality.

## Properties, inheritance and explicit negatives

Four selectors evaluate one exact property target:

| Selector | Included records |
|---|---|
| `has(code, reference)` | An unopposed positive assertion applies |
| `lacks(code, reference)` | An unopposed explicit negative assertion applies |
| `unknown(code, reference)` | No applicable assertion is recorded |
| `conflicts(code, reference)` | Positive and negative assertions both apply |

These four sets partition the domain. In Q39, the following select the penguin
record and produce an empty set, respectively:

```console
python -m concept_algebra 'exact(#1354) & lacks(action, #209)' --explain 1354
python -m concept_algebra 'exact(#1354) & has(action, #209)'
```

Only property codes **15 and 20–27** participate in this inheritance rule.
All accepted assertions for the selected code and exact target are considered
on the subject and every genus ancestor in the selected context. A more
specific owner supersedes an ancestor owner, even if a shortcut makes the
ancestor closer by path length. A local positive assertion can supersede an
inherited negative one, and a local negative can supersede an inherited positive.
Incomparable owners are retained together; disagreement becomes `conflict`.

`strength=0` is an explicit negative. `NULL` or a value greater than zero is a
positive recorded assertion. Numeric strengths are retained in the evidence;
they are not converted into probabilities or treated as independently verified
universal truths.

The target in these four selectors is an **exact concept identity**, even though
the same reference elsewhere denotes a catalog set. No target-subtype or
coextension-based property inference is performed. Combine several property
selectors with set operators when several target meanings are wanted.

Complement is different from explicit denial: `~has(action, #209)` also
contains unknown and conflicting records. It must not be read as proof that
all those concepts lack flight. Neither missing facts nor unrecorded genus
paths are automatically converted into negative facts.

All stored relation codes are available to `related` and `subjects`. The
following convenience aliases are also supported:

| Alias | Code | Alias | Code |
|---|---:|---|---:|
| `genus` | 14 | `essential` | 15 |
| `attribute` | 20 | `purpose` | 21 |
| `action` | 22 | `material` | 23 |
| `content` | 24 | `product` | 25 |
| `agent` | 26 | `patient` | 27 |
| `coextension` | 30 | | |

An unambiguous stored relation name can be used as a quoted first argument.
Unknown codes and unsupported inheritance codes produce errors.

## Python API and JSON

```python
from concept_algebra import ConceptAlgebra, parse

ast = parse('#25439 & #25446')       # no database required
print(ast.to_dict())

algebra = ConceptAlgebra.from_database(context=1, language="en")
result = algebra.evaluate('#25439 & #25446', explain=25447)
assert result.ids == (25447,)
print(result.to_dict(limit=20, include_ast=True))

print(algebra.evaluate('count(#25439 & #25446)').value)  # 1
print(algebra.graph.explain_fact(25447, "23", 90))
```

The database connection closes as soon as a consistent snapshot has been
loaded. Reuse the algebra object for multiple expressions; reload it to see
subsequent database changes. The evaluator does not call maintenance methods,
rebuild closures, write derived definitions, or create concepts for expression
results. Results are virtual selections.

`result.value` is a `frozenset` of IDs, a boolean, or an integer. `result.ids`
returns all set members in ascending ID order. `to_dict(limit=..., offset=...)` limits
displayed records while retaining the full count, `has_more` and `truncated` flags;
`limit=None` returns all. In the CLI, `--limit 0` means all records. JSON results
include the selected context, domain size, result type, and a resolved
expression containing IDs instead of ambiguous words.

Pass `include_ids=True` to include the full sorted ID list independently of
pagination, and `include_ast=True` to include the resolved syntax tree.

For a frozen JSON export, use:

```python
from concept_algebra import ConceptAlgebra, ConceptGraph

algebra = ConceptAlgebra.from_json("snapshot.json", context=1)
# Or supply an already loaded mapping:
# algebra = ConceptAlgebra(ConceptGraph(snapshot, context=1))
```

The JSON object needs these table-shaped lists:

| Key | Required row fields |
|---|---|
| `concept` | `dharma`, `nama`, `universum_id` |
| `concept_term` | `concept_id`, `term`, `lang` |
| `edge` | `id`, `dh1`, `kod`, `dh2`, `universum_id`, `status`; optional `strength` |
| `relevant` | `kod`; optional `long_name`, `is_symmetric` |
| `universum` | `id`, `nama` |

Additional columns are ignored. A supplied `concept_path` table is also
ignored because it does not carry the selected relation context. The SQL dump
is imported through MariaDB; it is not interpreted as a JSON snapshot.

`--snapshot snapshot.json` uses that export from the CLI. `--ast` parses only,
without database access. An expression argument of `-` reads an expression
from standard input. Syntax errors include line and column positions; ambiguous
term errors include candidate records. `--json` emits structured errors to
stderr and returns exit code 2.

Expressions are limited to 8,192 characters, 2,048 tokens, 1,024 AST nodes and
64 nesting/tree levels. They cannot execute Python or SQL, access files, define
functions, or assign variables. Cycles in a supplied graph terminate through
visited-node traversal; this does not certify that such cycles are semantically
valid.

## Verification

```console
python -m unittest discover -s tools -p "test_concept_algebra*.py" -v
```

The 51 focused checks cover partial overlap, operator precedence, De Morgan
identities, finite complements, typed comparisons, context isolation, homonyms,
negative exceptions, conflicting multiple inheritance, owner specificity,
cycles, evidence paths, read-only loading and CLI errors. They use a synthetic
graph and do not need a database or model. Q39 examples above were additionally
checked against the real database without modifying it. HTTP tests also cover
pagination with complete ID exports, error spans, cache invalidation, request
limits, comparison counterexamples and typed scalar explanations. See the
[browser checks](../visualizer/README.md#browser-checks) for eleven Q39 desktop/mobile
scenarios and nine JavaScript collection checks.
