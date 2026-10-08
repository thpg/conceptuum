# Euler demos and catalog sets — 2026-10-08

Interface revision **2026-10-08.4**, code **0.1.0-dev**, data **Q7**.
Published to **https://conceptuum.su** on 2026-10-08.
Start with the [cross-classification demo](https://conceptuum.su/?demo=judgment-grid&lang=en).

## Research and design

Euler diagrams can express intersection, exclusion, equality, and combinations
of these relationships, as well as inclusion. Contours divide the diagram into
membership regions. Region selection provides a natural way to explore Boolean
set operations. [University of Kent: Euler diagrams overview](https://www.cs.kent.ac.uk/events/conf/2004/euler/eulerdiagrams.html).

Euler/Venn extensions add empty-region shading and explicit member markers.
Formal spider diagrams can make existential assertions, but a concept record
alone does not establish a real-world instance. This viewer therefore uses
counts and inspectable **catalog records**, without introducing existential
claims about the world. [Howse et al., Euler Diagram-based Notations](https://www.cs.kent.ac.uk/pubs/2006/2972/content.pdf).

Preserving membership regions matters beyond satisfying pairwise circle
relationships. A diagram should not silently drop a populated intersection or
present an extra geometric region as populated. The implementation checks for
visible points in every nonempty catalog region, hatches empty regions, and
falls back to pair comparisons when it cannot represent all occupied regions.
This is our implementation choice, informed by the emphasis on preserving set
semantics in [SpEuler](https://arxiv.org/abs/2108.03529); it does not implement
that paper's layout algorithm.

## Database findings

Q7 has seven accepted coextension edges and nineteen accepted contradictory
edges, but no accepted partial-overlap (40) or incompatibility (60) edges.
Multiple genus links provide concrete cross-classifications. For example:

- Universal affirmative judgment (2510) has genus links to affirmative judgment
  (2505) and universal judgment (2509), through edges 4631 and 4593.
- Particular affirmative judgment (2512) belongs to affirmative and particular
  judgment; the negative forms supply the other two quality/quantity combinations.
- Judgment (2424), concept (2423), and inference (2425) have genus links to both
  thought content (2415) and logical form (2420) in the Logic context.
- Machine language (370) and first-generation language (401) have an accepted
  coextension edge in the IT context, with usable genus paths above them.
- Mammal (104) is below vertebrate (4519), which contradicts invertebrate (4783).
  This supplies a real example of inherited exclusion.

Exploratory queries also found multiple classifications in broad everyday
process/action/state branches. Several sample members were unsuitable as
teaching examples, so those candidate selections were not included in the demo
library. The local audit is preserved with the deployment artifacts. No graph
facts were edited to manufacture examples.

## Implemented capabilities

The existing **Stored relations** basis retains its semantic interpretation.
The new **Catalog sets** basis represents each selected root and all concept
records reachable beneath it using accepted, positive or unspecified-strength
genus/equality links within one context. Equality is traversed in both directions.
Cycles terminate; dangling endpoints cannot create phantom members.

The finite universe U is the union of the displayed sets, including automatically
added genera. Counts refer to distinct record IDs. Absence of a membership path
is not a semantic exclusion, and calculated overlaps do not create code-40 edges.
Each sampled member has a path of original edge IDs to every containing set.
Samples are bounded at six per region and twelve per displayed operation result;
counts include every record, including those omitted from the sample.

The interface adds intersection, union, directed difference, symmetric
difference, scoped complement, and intersection across all selected sets.
Selecting a region shows its exact count and sample members. Empty intersections
return zero explicitly. Full legends and shaded regions survive SVG export.
Demo, context, basis, operands, operation, and selected region survive sharing
and browser history. Selection and reading controls can collapse to make room
for complex diagrams on small screens.

| Demo | Basis | Verified result |
|---|---|---|
| [Cross-cutting classifications](https://conceptuum.su/?demo=judgment-grid&lang=en) | Catalog | Four quality/quantity intersections; 9 occupied regions including the automatic genus |
| [Three-way intersection](https://conceptuum.su/?demo=shared-intersection&lang=en) | Catalog | 35 shared records; 82 records in the displayed union |
| [Union and difference](https://conceptuum.su/?demo=judgment-union&lang=en) | Catalog | Union 5; intersection 1; directed difference 2 each way; symmetric difference 4 |
| [Complement](https://conceptuum.su/?demo=judgment-complement&lang=en) | Catalog | 32 records outside the affirmative set within the 35-record judgment universe |
| [Empty intersection](https://conceptuum.su/?demo=empty-intersection&lang=en) | Catalog | No recorded member of both affirmative and negative sets |
| [Equality](https://conceptuum.su/?demo=language-equality&lang=en) | Stored relations | Coincident language categories inside two enclosing genera |
| [Inherited exclusion](https://conceptuum.su/?demo=inherited-exclusion&lang=en) | Stored relations | Two exclusion relationships plus four inclusions |

## Verification

Local checks passed: 21 browser scenarios, all Go tests and `go vet`, 22 existing
geometry checks, and 13 JavaScript catalog check groups. New Go cases cover
multi-set regions, evidence paths, equality, cycles, missing records, exact
counts despite sample limits, and sixteen displayed circles. Browser checks use
the actual database for every demo and validate member paths, context changes,
Boolean counts, history, sharing, keyboard interaction, mobile fit, and SVG masks.
Existing semantic overlap regression tests continue to use isolated fixtures.

Windows and Linux builds and syntax checks for all three JavaScript files pass.
Desktop and mobile previews were visually inspected. The selected demo examples
use actual API responses; no mocked data is supplied by the demo selector.

All **21 browser tests also passed against the live HTTPS site** in Chrome
154.0.8037.58. All six public assets match the local build byte for byte, all
seven demo selections were verified against the live API, and nine deployment
API checks passed. Desktop (1500 × 1000) and mobile (390 × 844) captures have no
JavaScript errors or horizontal mobile overflow. A touch pinch changed zoom
from 41% to 93%.

Screenshots: [cross-classification](../visualizer/euler-demos-desktop.png),
[three-way intersection](../visualizer/euler-demos-intersection.png),
[mobile](../visualizer/euler-demos-mobile.png).

Full database dumps before and after deployment have the same SHA-256:
`4940d7bbb50f0fd4e161c7010fb0a86ae33792d8e136849521e73c0819a93701`.
The Q7 SQL export is unchanged. See the
[verification record](2026-10-08-euler-demos-verification.json) for asset hashes,
demo counts, and source edge IDs. The server backup is
`/var/backups/conceptuum/20261008-euler-demos`; local backups, audits, and receipts
are in `G:/Projects/conceptuum-backups/euler-demos-20261008`.
No GitHub push, tag, or release was created. Physical mobile devices and other
browser engines were not tested in this pass.
