# Complex Euler diagrams — 2026-10-08

Published interface revision **2026-10-08.3** to [conceptuum.su](https://conceptuum.su/?concept=26&lang=en&view=euler&sets=26,27&context=1).
Code version **0.1.0-dev**; data revision **Q7**, unchanged.

## Shared genera

Selecting **plant** and **animal** now automatically adds **organism**, with both
species inside its circle. Selecting **mammal**, **bird**, and **fish** adds
**vertebrate**. Automatic genera have an **auto** label and do not use the eight
selection slots. They disappear when fewer than two selected siblings need them.

The API discovers direct shared genera within the selected context. It handles
equality aliases, avoids duplicates and cycles, omits redundant broader genera,
and supports multiple shared genera. It does not add a distant common ancestor
to unrelated selections. Up to eight automatic genera are included; the UI
reports any further omissions. An explicitly selected genus remains a single
circle and can revert to an automatic circle when removed from the selection.

Screenshots from the deployed site:
[desktop](../visualizer/euler-shared-genus-desktop.png),
[mobile](../visualizer/euler-shared-genus-mobile.png).

## Partial overlaps

Combined diagrams now support partial overlaps, overlap chains, and species
inside the intersection of two genera. A bounded, deterministic circle solver
checks every known pair constraint before publishing its geometry. A hierarchy
uses direct packing when possible; larger sibling groups are arranged in rows.
The viewer falls back to pair comparisons if it cannot find a valid circle layout.
This fallback alone does not establish that the data is inconsistent.

Unknown sibling relationships use dashed outlines while preserving the known
enclosing genus. Spacing does not assert disjointness or overlap. The expandable
relationship list identifies recorded, derived, unspecified, and conflicting
pairs. Multi-set intersection regions illustrate one possible layout; binary
overlap does not determine a three-way intersection. Circle areas remain
illustrative. Labels adapt to the viewport, and SVG exports preserve the labels,
automatic-genus markers, and uncertainty notes.

## Verification

- All **17 browser tests** passed locally and against the deployed HTTPS site in
  Chrome 154.0.8037.58. Coverage includes genus addition/removal, context changes,
  deduplication, sharing, multiple inclusion, overlap geometry, mobile fitting,
  label readability, SVG export, and the previous graph workflows.
- **22 JavaScript geometry checks** passed, including overlap chains, equality
  aliases, multiple genera, unknown siblings, impossible constraints, larger
  selections, and six five-circle configurations.
- Go tests passed: 17 relationship cases, 13 shared-genus cases, selection
  validation, and HTTP validation. `go vet`, JavaScript syntax checks, and both
  Windows and Linux builds passed.
- Desktop and mobile screenshots were visually inspected. Mobile has no
  horizontal page overflow; a touch pinch changed zoom from 53% to 119%.
- Q7 has no accepted code-40 overlap records. Overlap scenarios use isolated
  test fixtures; no demonstration facts were written to the graph.
- All five public assets match the local files byte for byte. Seven live API
  examples passed and the service is active.
- Database dumps before and after deployment have the same SHA-256:
  `4940d7bbb50f0fd4e161c7010fb0a86ae33792d8e136849521e73c0819a93701`.
  The local Q7 SQL export is also unchanged.

See the [machine-readable verification record](2026-10-08-euler-overlap-verification.json).
The server backup is `/var/backups/conceptuum/20261008-euler-overlap`.
Local backups and deployment receipts are in
`G:/Projects/conceptuum-backups/euler-overlap-20261008`.
No GitHub push, tag, or release was created. Other browser engines and physical
mobile devices were not tested in this pass.
