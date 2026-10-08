# Documentation and setup review — 2026-10-08

Scope: improve the English GitHub README, verify published instructions,
and add explicit versions. Code version: **0.1.0-dev**. Data remains **Q7**.

The published baseline was
[commit 38c3e36](https://github.com/thpg/conceptuum/tree/38c3e3634fe1714f55a6fc74080a61f30e6dcac0).
README, filling algorithm, property guide, ontology rules, roadmap, and Go
module requirements were compared with the local implementation. Public
tags and releases were empty at review time; the new version is explicitly
marked as development rather than presented as an existing release.

## Findings and corrections

| Finding | Correction |
|---|---|
| Published README reported an old 4,560-concept snapshot | Documented Q7 counts with links to the recorded evidence |
| Python 3.8+ was listed without an installation file | Pinned tested dependencies and documented Python 3.9+ |
| Python CLI connection settings were hardcoded | Added environment overrides and documented their precedence |
| Go and Python used different configuration conventions without enough explanation | Listed the separate Python variables, Go DSN, and listen address |
| Dump import instructions omitted replacement behavior and were shell-specific | Used the client's `SOURCE` command and described its database selection and table replacement |
| A read example called `define()`, which writes and commits | Replaced it with lookup, verification, and statistics examples |
| `verify()` and model strength were described as stronger guarantees than they provide | Distinguished stored claims, structural checks, and semantic evidence |
| Property guide recommended widening signatures and replaying an old bulk script | Replaced it with the reviewed, backed, transactional workflow |
| Roadmap still used obsolete purpose/material/agent/patient and part-whole codes | Replaced it with current priorities and role meanings |
| Fill algorithm included an incorrect translation example and unsupported universal token-cost claims | Replaced them with concrete review steps and implementation limits |
| `fill_llm.py --dry-run` could update progress on leaf groups | Prevented those writes and added tests for all frontier shapes |
| `--candidate` did not apply to new genus edges | Passed the flag through to concept creation and tested genus and non-genus cases |
| A baseline from before Q7 omitted its new nodes in a fresh upper audit | Used Q7's after-scope for current instructions, retaining all 389 reviewed nodes |

## Verification

- Installed the pinned dependencies in a new virtual environment.
- Passed **43 Python unit tests**, without a database or model.
- Imported a copy of the SQL dump using the MariaDB client's `SOURCE` command
  into a new, isolated schema. Only its database selector was redirected.
- Executed the README retrieval and Python API examples against that schema
  using the documented environment variables.
- Ran both read-only audits; metrics matched Q7 and the upper scope contained
  389 nodes. Ran the filler preview without a model request.
- Ran `go test ./...` (there are no Go test files), built the visualizer, and
  checked its HTML page plus search, concept, and tree API responses.
- Compared all six source-table fingerprints before and after: unchanged.
  Stopped the temporary server and removed the temporary schema.
- Checked local Markdown links, code fences, English prose in the rewritten
  guides, engine-copy parity, and the unchanged SQL export checksum.

The tested server identified itself as **5.5.42-MariaDB**; the runtime versions
are recorded in the [verification results](2026-10-08-docs-verification.json).
LLM-backed generation and browser rendering were not exercised. Other server
versions are not claimed as tested.

These changes are in the local working tree. This review did not push a
commit, create a release tag, or publish a GitHub Release.
