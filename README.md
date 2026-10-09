# conceptuum

A concept graph with typed relations, multilingual terms, and definitions generated from the graph.

conceptuum represents meanings as nodes and connects them through relations such as genus, purpose, material, opposition, and cause. It combines a MariaDB snapshot, a Python engine for querying and reviewing the graph, and a Go web visualizer. An optional retrieval demo supplies graph context to a local language model.

**Development version:** [0.1.0-dev](VERSION) · **Data snapshot:** [Q39, 2026-10-09](docs/quality/2026-10-09-q39.md) · **Published site data:** Q39 · **[Changelog](CHANGELOG.md)** · **[Live demo](https://conceptuum.su)**

## Euler diagrams from the concept graph

Explore how concepts overlap, exclude one another, coincide, or fit inside a
shared genus. Add or remove concepts, let sibling concepts bring in their common
genus automatically, and highlight intersections, unions, differences, and complements.

[![Euler circles showing affirmative, negative, universal, and particular judgments inside their shared genus, with region counts and a highlighted intersection](docs/visualizer/euler-circles.png)](https://conceptuum.su/?demo=judgment-grid&lang=en)

*Affirmative/negative and universal/particular judgments form overlapping
classifications. The highlighted intersection contains the universal affirmative
judgment. The outer circle is their automatically added genus.*

Try the seven live demos: [cross-classification](https://conceptuum.su/?demo=judgment-grid&lang=en),
[three-way intersection](https://conceptuum.su/?demo=shared-intersection&lang=en),
[union and difference](https://conceptuum.su/?demo=judgment-union&lang=en),
[complement](https://conceptuum.su/?demo=judgment-complement&lang=en),
[empty intersection](https://conceptuum.su/?demo=empty-intersection&lang=en),
[equality](https://conceptuum.su/?demo=language-equality&lang=en), and
[inherited exclusion](https://conceptuum.su/?demo=inherited-exclusion&lang=en).

Catalog mode compares sets of stored concept records, with exact region counts
and inspectable member samples. Share a selection by URL or export the diagram as SVG.

New in Q9: compare [finite and nonempty sets](https://conceptuum.su/?concept=24488&view=euler&sets=24488,24489&context=1&basis=catalog&op=intersection&a=24488&b=24489&lang=en), or
[commutative and associative operations](https://conceptuum.su/?concept=635&view=euler&sets=635,567&context=1&basis=catalog&op=intersection&a=635&b=567&lang=en). The first shares the singleton-set
record; the second shares the union and intersection records.

**Topics:** `knowledge-graph` · `ontology` · `euler-diagrams` · `set-visualization`

## What you can do

- Search English and Russian terms and inspect different meanings of a word.
- Explore separate hierarchy and relation views with zoom, filters, full ancestry,
  shareable links, and SVG export. The graph adapts to desktop and mobile screens.
- Compare concepts with [Euler diagrams](#euler-diagrams-from-the-concept-graph),
  using stored relations or catalog membership. Unknown semantic relationships
  remain explicitly marked.
- Retrieve stored facts from Python or the command line without an LLM.
- Review proposed changes against relation signatures, hierarchy checks, and explicit regression conditions.

The graph is experimental and still being reviewed. Structural validation catches some category errors; it does not establish whether a statement or translation is true.

## How the graph works

Open the [live concept explorer](https://conceptuum.su/?concept=2698&lang=en),
or read the [visualizer controls and browser checks](visualizer/README.md).

Synonyms share a concept. Homonyms have separate concepts. A concept can have multiple genus links, each carrying its discourse context, or **universe**.

```mermaid
graph BT
  subtraction["subtraction"] -->|"14: genus"| arithmetic["arithmetic operation"]
  modulo["remainder operation"] -->|"14: genus"| arithmetic
  arithmetic -->|"14: genus"| operation["mathematical operation"]
  operation -->|"14: genus"| fn["mathematical function"]
  fn -->|"14: genus"| object["mathematical object"]
  remainder["division remainder"] -->|"14: genus"| number["number"]
  number -->|"14: genus"| object
```

An operation and its numerical result are different meanings. The `defin` field is a generated cache: change the reviewed relations, then rebuild the definition. An edge's `strength=0` records explicit negation; an unspecified strength means no degree has been asserted.

## Versions and requirements

| Component | Version / requirement |
|---|---|
| Project | **0.1.0-dev**, an unreleased development version |
| Bundled and live data | **2026-10-09 / Q39** |
| Python | **3.9+**; checked with **3.9.13** |
| PyMySQL | **1.2.0**, pinned in [requirements.txt](requirements.txt) |
| pymorphy3 | **2.0.6**, pinned for Russian morphological matching |
| Go | **1.26.1+**, required by [visualizer/go.mod](visualizer/go.mod); only needed for the visualizer |
| MariaDB | Local setup checked on **5.5.42**; live Q39 import and visualizer checked on **11.8.6** |

The MariaDB version records the existing test environment. Compatibility with other server versions, including MySQL, needs separate verification. Python direct dependencies are pinned; Go dependencies are recorded in `go.mod` and `go.sum`.

## Run locally

### 1. Get the project and install Python dependencies

```bash
git clone https://github.com/thpg/conceptuum.git
cd conceptuum
python -m venv .venv
```

Activate the environment for your shell, then install the dependencies:

| Shell | Activation command |
|---|---|
| Bash / Zsh | `source .venv/bin/activate` |
| PowerShell | `.\.venv\Scripts\Activate.ps1` |

```bash
python -m pip install -r requirements.txt
```

Use `python3` to create the environment if that is your Python command. If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` in place of `python`; changing the machine's execution policy is unnecessary.

### 2. Import the database snapshot

Start MariaDB and open its client from the repository root:

```bash
mariadb --user=root --password --default-character-set=utf8mb4
```

At the database prompt:

```sql
SOURCE jnana3_dump.sql;
QUIT;
```

Use `mysql` if that is the installed client's name. This also works from PowerShell because `SOURCE` runs inside the database client.

**The dump creates/uses `jnana3` and replaces its six tables. Import into a fresh instance, or back up an existing `jnana3` first.** Selecting another database on the client command line does not redirect the dump's `USE jnana3` statement.

### 3. Configure Python and retrieve facts

Set these variables in the same shell where you run Python, using an account that can read the imported database.

<details>
<summary>Bash / Zsh</summary>

```bash
export JNANA_HOST=127.0.0.1
export JNANA_PORT=3306
export JNANA_DATABASE=jnana3
export JNANA_USER=your_database_user
export JNANA_PASSWORD='your_database_password'
```

</details>

<details>
<summary>PowerShell</summary>

```powershell
$env:JNANA_HOST = '127.0.0.1'
$env:JNANA_PORT = '3306'
$env:JNANA_DATABASE = 'jnana3'
$env:JNANA_USER = 'your_database_user'
$env:JNANA_PASSWORD = 'your_database_password'
$env:PYTHONIOENCODING = 'utf-8'
```

</details>

```bash
python ask.py "How are ice and water related?" --no-llm
```

This prints retrieved `FACTS` and one-hop `RELATED` context without contacting a model. Cached definitions are mostly Russian; `--lang en` selects lookup/display preferences and does not translate the stored definition cache.

See [setup details and troubleshooting](docs/setup.md) for database access, configuration precedence, and connection errors.

### 4. Start the visualizer (optional)

The Go application uses **`JNANA_DSN`**, independently of the Python settings. Set it with your own database account:

```bash
# Bash / Zsh
export JNANA_DSN='your_database_user:your_database_password@tcp(127.0.0.1:3306)/jnana3?charset=utf8mb4'
```

```powershell
# PowerShell
$env:JNANA_DSN = 'your_database_user:your_database_password@tcp(127.0.0.1:3306)/jnana3?charset=utf8mb4'
```

Then run:

```bash
cd visualizer
go run .
```

Open **http://127.0.0.1:7100/**. Run from `visualizer/` so the server can find `static/index.html`. `LISTEN` overrides the bind address. The interface chooses English or Russian from the browser locale; the hosted demo and bundled snapshot are updated independently.

## Use the Python engine

Run from the repository root with the Python database variables configured:

```python
from jnana_engine import JnanaEngine

eng = JnanaEngine(pref_lang="en")
try:
    print(eng.resolve_all("ice", lang="en"))
    print(eng.verify("ice", "freezing"))
    print(eng.stats())
finally:
    eng.close()
```

`resolve_all()` returns possible senses. `verify()` reports a stored path or relation; a positive result is not an independent fact check. Use concept IDs after selecting a meaning for edits.

`rebuild()` and `define()` **write to the database**. They are maintenance operations, not prerequisites for reading an imported snapshot. Reviewed changes use the [transactional batch workflow](docs/fill-properties.md).

## Optional LLM retrieval demo

Start a compatible local chat server, load a model, and pass its actual model identifier:

```bash
python ask.py "How are ice and water related?" --endpoint http://localhost:11434/v1 --model YOUR_LOADED_MODEL
```

The server must accept `/chat/completions`; `ask.py` does not start a server or download a model. The model receives retrieved graph context, which may contain incomplete or incorrect claims. `interleave.py` is a separate experiment that uses llama.cpp's native `/completion` endpoint.

## Check the graph and code

From the repository root:

```bash
python -m unittest discover -s tools -p "test_*.py"
python tools/audit_quality.py --output quality.json
python tools/audit_upper_graph.py --output upper.json
```

The unit tests need no database or model. The audits read the configured database and write JSON reports. For a before/after comparison, save the first upper-graph report and pass its path with `--scope-from` on the second run; this keeps reparented nodes in scope.

## Data snapshot and limits

The published **Q39** snapshot contains **13,456 concepts**, **17,350 accepted edges**, **1,100 rejected edges**, **64,683 genus paths**, and **37,825 terms** across everyday, IT, legal, and logic universes. Compared with Q9, the combined Q10–Q39 reviews add a net **965 concepts**, **1,633 accepted edges**, and **2,777 terms**.

Q11–Q39 use Open English WordNet 2025 to guide reviewed additions. Q39 adds 41 concepts and 106 relations for physical containers, material/use intersections, bristled tools, applicators, cleaning tools and scrapers. Ten inherited assertions, five labels and ten malformed or incorrectly tagged terms are corrected.

GitHub and the hosted demo include Q39. All six deployed tables match the reviewed snapshot, with timestamps compared in UTC. The SQL dump explicitly retains the source database's `utf8_general_ci` collation so newer MariaDB defaults do not merge distinct term keys during import. The local audit detected no signature violations, hierarchy cycles, or self-loops; all 23 explicit negations survived the reviews. These checks establish structural consistency, not complete or verified knowledge. **7,251 concepts still lack an English-tagged term containing Latin letters**, and even Latin-script terms need translation review.

The [coverage review and filling plan](PLAN.md) prioritizes remaining work. Sources and exact changes are recorded in the [Q39 review](docs/quality/2026-10-09-q39.md) and its [batch manifest](tools/quality_20261009_q39.json). The [Q11 review](docs/quality/2026-10-09-q11.md) retains the pinned dictionary comparison and source notices. The [changelog](CHANGELOG.md) separates code versions from data revisions; older entries in the [maintainer state](STATE.md) include Russian text.

## Documentation

| Document | Purpose |
|---|---|
| [Setup](docs/setup.md) | Connection settings, import behavior, and troubleshooting |
| [Ontology rules](docs/ontology-rules.md) | Concept identity, genera, relation meanings, and review constraints |
| [Property review](docs/fill-properties.md) | Preparing, previewing, and applying a reviewed batch |
| [Filling algorithm](FILL_ALGORITHM.md) | Candidate generation, semantic review, and implementation limits |
| [Roadmap](PLAN.md) | Remaining content and engine work |
| [Versions](CHANGELOG.md) | Development version and content revision history |
| [Instruction audit](docs/quality/2026-10-08-docs-review.md) | Published-document findings and setup verification |

The six storage tables are `concept`, `concept_term`, `edge`, `relevant`, `universum`, and `concept_path`. The relation grammar is data in `relevant`; the root [jnana_engine.py](jnana_engine.py) is the Python implementation. Older scripts in `tools/` preserve development history and are not an installation sequence.

## License

[MIT](LICENSE) for project code and original contributions. Q11–Q39 contain reviewed adaptations from Open English WordNet 2025, derived from Princeton WordNet, and BIPM unit information. Their attribution and source license notices are retained in the [Q11 source notice](docs/quality/2026-10-09-q11.md#sources-and-reuse).
