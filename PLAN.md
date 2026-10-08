# Roadmap

Current baseline: [code 0.1.0-dev](VERSION), [data Q7](docs/quality/2026-10-08-q7.md).
This is the active work plan. Earlier expansion totals and relation-code
instructions remain available in Git history; they do not describe the
current graph or a sequence of scripts to rerun.

## Content priorities

| Area | Review needed |
|---|---|
| Upper genera | Misplaced children of natural object (34), physical/mental properties, and time |
| Physiological processes (202) | Suspect generated word forms, incorrect genera, and roles |
| Biological classification | Protozoa and animal groups with overly broad or questionable parents |
| Mathematics | Mathematical integers versus integer data types (1198), the meaning of Map (903), and distinguishing properties of operations |
| Relative properties | Explicit reference objects and contexts beyond a generic parent |
| Family roles | Correctly scoped facts to replace the reversed causal claims removed in Q7 |
| English terminology | Missing translations, Cyrillic terms tagged as English, and ambiguous translations |

Review specific meanings before generating new nodes. Dictionary evidence
is needed for doubtful word forms. A high-level genus or a translated label
alone is not a complete definition.

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
