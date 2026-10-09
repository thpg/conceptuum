# Conceptuum visualizer

A Go HTTP server with a dependency-free HTML, CSS, and JavaScript explorer.
See the [project setup guide](../docs/setup.md) for database configuration.

Run `go run .` from this directory. Set `JNANA_DSN` to your database connection
string; `LISTEN` defaults to `127.0.0.1:7100`. The process reads the `static`
directory from its working directory.

## Exploring the graph

- Search by name or term. Press `/` to focus search, use arrow keys to move
  through results, and Enter to open a concept.
- The hierarchy shows broader and narrower concepts. Arrows point from a
  narrower concept to its genus. Select a node to continue exploring.
- Enable **Full ancestry** to see more context. Large child lists are paginated;
  the details panel also provides the complete list of direct children.
- The **Relations** view shows stored directions and symmetric relations,
  with filters for attributes, logical relations, causal relations, and
  explicit negations. Strength percentages are not probabilities.
- **Euler circles** compares up to eight concepts. Use **+ Find a concept**,
  then the **+** button beside a search result, or choose **+ Add current**.
  Remove a concept with **×** on its chip; **Clear** empties the selection.
  These controls only change the diagram, never the database.
- Drag to pan, scroll or pinch to zoom, and use **Fit** to restore the overview.
  With the graph focused, `+`, `-`, arrow keys, and `F` control the viewport.
- **Share** copies the concept, content language, view, and ancestry setting.
  In Euler mode it also preserves the comparison selection, context, and layout.
  **Download SVG** saves a standalone, styled copy of the displayed graph.
- Small screens use a vertical graph and fewer nodes per page. Search and
  details are available through the toolbar buttons.

The interface is English. The language selector changes concept and relation
labels; untranslated concepts retain their available label.

## Euler circles

The **Context** selector chooses which discourse universe supplies the
relationships. A path is followed only within that context. Nested circles
represent genus inclusion; coincident outlines represent equal extension.
Overlap and disjointness require recorded set relations. Sizes are illustrative,
not concept counts, probabilities, or measured set cardinalities.

The read-only `/api/euler?ids=16,25,26&context=1&lang=en` endpoint returns
concepts, pair relationships, and the edge evidence used to derive them:

| Code | Euler interpretation |
|---|---|
| 14 | Inclusion through the accepted genus chain |
| 30 | Equal extension, including chains of equality |
| 40 | Recorded partial overlap |
| 60, 64 | Incompatibility or contradiction; disjoint extensions |

Only accepted edges with a positive or unspecified strength are used.
Equality can carry inclusion across equivalent concepts. Disjointness descends
to narrower concepts. Siblings (61) and opposites (63) do not, by themselves,
establish disjointness. Negative relations are not converted into positive set
constraints.

Selecting two or more sibling concepts automatically adds their direct shared
genus and draws them inside it. For example, selecting **plant** and **animal**
adds **organism**. Automatic genera have muted colors and an **auto** label;
they do not use the eight selection slots. They disappear when no longer needed.
A genus explicitly included in the selection is drawn once. Removing it from
the selection leaves an automatic circle if the remaining siblings still need it.

Genus discovery stays within the selected context and follows equality aliases.
It does not add a distant common ancestor for unrelated selections. Redundant
broader genera are omitted; multiple distinct shared genera are supported, with
a maximum of eight automatic additions. The API returns these as `automatic`
entries containing `id` and `children`, plus `omitted_genera` if the limit is hit.
Pairs and their edge evidence cover both selected concepts and automatic genera.

**Auto diagram** supports nesting, equality, disjointness, partial overlap,
overlap chains, and species contained in the intersection of multiple genera.
Every recorded pair constraint is checked against the resulting geometry.
If a combined circle layout cannot satisfy those constraints, the viewer falls
back to independent pairs; this does not necessarily mean the data is wrong.
**Compare pairs** is also available manually, with one pair per page on mobile.

Unknown siblings can appear together inside their known genus, using dashed
outlines. Their spacing does not assert disjointness or overlap. Disconnected
unknown selections and conflicting records use pair comparisons. Expand
**Relationships** to see which pairs are recorded, derived, or unspecified.
Circle areas are illustrative. Pairwise overlap does not establish the existence
or size of a three-way intersection: multi-set regions show one possible layout.

Try [plant inside organism inside entity](https://conceptuum.su/?concept=25&lang=en&view=euler&sets=16,25,26&context=1).
Also try [plant and animal with an automatic organism circle](https://conceptuum.su/?concept=26&lang=en&view=euler&sets=26,27&context=1)
or [mammal, bird, and fish inside vertebrate](https://conceptuum.su/?concept=104&lang=en&view=euler&sets=104,105,106&context=1).

## Catalog sets and demos

Use **Explore a demo** in Euler circles to load a verified selection, context,
and interpretation. The [cross-classification demo](https://conceptuum.su/?demo=judgment-grid&lang=en)
is a useful starting point. Open **Selection & display options** to edit a
selection or switch its **Basis**. **Stored relations** keeps the semantic rules
described above. **Catalog sets** computes finite sets of concept records.

Each catalog circle contains its root concept and every record connected to it
by accepted genus/equality paths in the selected context. Equality links are
traversed in both directions; cycles terminate and invalid endpoints are ignored.
The finite universe **U** is the union of all displayed sets, including automatic
genera. Record IDs are counted once per set. Areas are not proportional to counts.

- Highlight intersection, union, directed difference, symmetric difference,
  complement within U, or the intersection of all selected sets.
- Region badges show exact counts. Select a badge, or open **Regions & members**,
  to inspect sample records. The response includes up to six samples per region;
  the combined result lists up to twelve. Totals include unsampled records.
- Hatching marks geometrically visible regions with no catalog members. If a
  nonempty region cannot be drawn, the viewer uses pair comparisons and retains
  exact results in the membership panel.
- Full set names appear in the diagram legend and SVG export. Shared links keep
  the demo, basis, operation, operands, region, selection, and context.

An absent catalog path is **not** a semantic exclusion. These counts concern
stored concept records, not people, objects, probabilities, or real-world
cardinalities. Catalog overlaps do not create code-40 edges in the database.

| Demo | What the current Q9 data demonstrates |
|---|---|
| [Cross-cutting classifications](https://conceptuum.su/?demo=judgment-grid&lang=en) | Judgment quality and quantity form four occupied cross-classification regions |
| [Three-way intersection](https://conceptuum.su/?demo=shared-intersection&lang=en) | 35 judgment records lie within both thought content and logical form |
| [Union and difference](https://conceptuum.su/?demo=judgment-union&lang=en) | Affirmative/universal sets: union 5, intersection 1, each directed difference 2, symmetric difference 4 |
| [Scoped complement](https://conceptuum.su/?demo=judgment-complement&lang=en) | 32 of the 35 judgment records lie outside the affirmative catalog set |
| [Empty intersection](https://conceptuum.su/?demo=empty-intersection&lang=en) | No recorded member belongs to both affirmative and negative judgment sets |
| [Equality](https://conceptuum.su/?demo=language-equality&lang=en) | Machine language and first-generation language share an extension inside the language hierarchy |
| [Inherited exclusion](https://conceptuum.su/?demo=inherited-exclusion&lang=en) | Vertebrate/invertebrate exclusion also applies to the narrower mammal concept |

The read-only endpoint accepts `basis=catalog`, for example
`/api/euler?ids=2505,2509&context=5&basis=catalog&lang=en`. Its `catalog` object
contains `universe_count`, per-set counts, and disjoint membership `regions`.
Region masks use the order of `concepts`, including automatic additions.
Samples contain accepted edge paths from each member to each containing set.
The default `basis=relations` keeps the semantic interpretation. Invalid basis
values are rejected. No database mutations are performed by either mode.

Q9 also provides two documented selections using the existing controls:

- [Finite and nonempty sets](https://conceptuum.su/?concept=24488&view=euler&sets=24488,24489&context=1&basis=catalog&op=intersection&a=24488&b=24489&lang=en): the singleton-set record is shared.
- [Commutative and associative operations](https://conceptuum.su/?concept=635&view=euler&sets=635,567&context=1&basis=catalog&op=intersection&a=635&b=567&lang=en): union and intersection are shared.

These compare catalog records. The empty-set record is itself a member of the
finite-set catalog; its mathematical cardinality zero does not mean that its
catalog circle contains zero records. No new menu preset or solver is introduced.

Research and verification: [Euler demos report](../docs/quality/2026-10-08-euler-demos.md).

## Browser checks

Run the server against the bundled dataset first. In a separate Python environment:

```sh
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python test_browser.py
```

Set `CONCEPTUUM_TEST_URL` to test a different address. Set
`CONCEPTUUM_BROWSER_CHANNEL=chrome` to use installed Chrome instead of downloading
Chromium. The twenty-one tests only read the database; overlap fixtures, failure,
stale-response, and escaping cases use intercepted browser responses. Q9 has no
accepted code-40 records. The catalog demos calculate overlaps from real
classification paths; the earlier semantic overlap tests use isolated fixtures.

Also run `go test ./...`, `node test_euler_layout.js`, `node test_euler_catalog.js`,
and syntax checks for all three JavaScript files in `static/`. Go tests
cover relation inference, shared genera, cycles, selection limits, and API
validation. The 22 geometry checks cover partial overlaps, multiple inclusion,
unknown siblings, inconsistent constraints, mobile layout, and safe labels.
Catalog checks cover Boolean operations, witnesses, empty regions, equality,
cycles, missing records, sample limits, and all sixteen possible displayed sets.
There is no frontend package build step.

## Deployment files

Deploy the Go executable together with **all** files in `static/`. Preserve the
working directory and the server's existing database environment configuration.
Update the asset revision in `index.html` when changing CSS or JavaScript.
Keep `static/version.json` aligned with the deployed code and data snapshot.
Back up the live application and database before publishing a data revision,
and verify the live API and browser after restarting the service.
