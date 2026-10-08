# Changelog

The project version is stored in [VERSION](VERSION). Code versions and data
revisions are tracked separately: **Q1–Q7 are content reviews, not software
release numbers**. The first explicitly versioned working tree is
**0.1.0-dev**. No release tag or GitHub Release was created by this update.

## 0.1.0-dev — Unreleased

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
