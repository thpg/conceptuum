# Visualizer update and live deployment — 2026-10-08

Published to [conceptuum.su](https://conceptuum.su/?concept=2698&lang=en).
Code version: **0.1.0-dev**. Interface revision: **2026-10-08.1**.
Data revision: **Q7**. The live [version record](https://conceptuum.su/static/version.json)
identifies the deployed snapshot. This was a site deployment; no GitHub push,
release tag, or GitHub Release was created.

## Interface changes

- Separate hierarchy and relation views replace the mixed, crowded graph.
- A search sidebar and dedicated details panel keep the graph visible.
- Graph cards wrap names; tooltips and details retain the full text.
- Zoom, pan, fit, locate, ancestry expansion, and pagination support large branches.
- Relation filters distinguish attributes, logical relations, causal relations,
  and explicit negations. Arrows follow stored direction; symmetry comes from
  the grammar. Strength percentages are not presented as probabilities.
- Shareable URLs preserve the concept, content language, view, and ancestry
  setting. Browser history supports returning to a previous concept.
- SVG export includes styles and needs no external assets to display.
- Small screens use a vertical graph with three children or relations per page,
  plus search and details drawers. Touch supports panning and pinch zoom.
- Keyboard navigation, loading states, retry controls, and cancellation protect
  against failed requests and stale search or concept responses.

The interface is English. The language selector changes the stored concept
and relation labels. An unavailable English translation can still display an
original Russian label. Coverage limitations in the Q7 report still apply.

Screenshots captured from the live site:
[desktop](../visualizer/desktop.png) and [mobile](../visualizer/mobile.png).
Controls and test instructions are in the [visualizer guide](../../visualizer/README.md).

## Data publication

Before deployment, all six live tables exactly matched the local backup taken
before Q1: 12,469 concepts and 15,826 edges. The comparison found no independent
server edits to preserve. The application and complete database were backed up
before any replacement; the deployment checked again that neither had changed.

The Q7 import now serves:

| Record | Count |
|---|---:|
| Concepts | 12,468 |
| All edges | 16,452 |
| Accepted edges | 15,665 |
| Terms | 34,950 |
| Paths | 57,970 |
| Accepted explicit negations | 23 |

The source dump SHA-256 is
`fb7beb0e5a2d523141196d4d5c85ec2c992b72e00f3d0b2938a94d74f8a169d9`.
The live database was exported again after deployment and compared with Q7 in
isolated local schemas. Every row in all six tables matches. For this comparison,
only newer MariaDB client directives and DDL charset/collation names were adapted
to the older local server; INSERT data was unchanged. Scratch schemas were removed.

## Verification

- Eight browser tests passed locally and against the deployed HTTPS site in
  Chrome 154.0.8037.58. They cover hierarchy/history, keyboard search and retry,
  pan/zoom/share/export, complete child pagination, negations/symmetry/escaping,
  stale-response races, mobile controls, and recovery with unavailable storage.
- Desktop at 1440 × 960 and mobile at 390 × 844 were visually inspected; no
  horizontal page overflow was observed on mobile. A touch pinch changed zoom
  from 87% to 196% while preserving the selected concept.
- `node --check static/explorer.js` passed. `go test ./...` passed; the Go module
  currently has no unit test files. Windows preview and Linux deployment builds
  completed with Go 1.26.1.
- Public HTML, CSS, JavaScript, and version metadata return HTTP 200 and match
  the local files byte for byte. The live service is active; search, concept,
  and tree APIs passed the browser checks.
- Live database: MariaDB 11.8.6. Local comparison database: MariaDB 5.5.42.
- No LLM calls were needed. Other browser engines and physical mobile devices
  have not been tested in this pass.

Machine-readable evidence: [verification record](2026-10-08-visualizer-verification.json).

The previous executable, HTML, and database are retained on the server in
`/var/backups/conceptuum/20261008-visualizer`. Local pre-change files, database
copies, comparisons, deployment tooling, and receipts are retained under
`G:/Projects/conceptuum-backups/visualizer-20261008`. The local project database
and Q7 export were not modified by this interface update.
