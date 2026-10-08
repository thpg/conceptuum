"""Read-only review of upper genera, inherited claims and thinly described hubs.

Flags are review candidates, not proof of semantic errors or incompleteness.
Multiple genera and different discourse classifications remain legitimate.
"""
import argparse
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jnana_engine import JnanaEngine
from audit_quality import english_script_flags

ANCHORS = (1, 6, 19, 25, 29, 34, 42, 47, 51, 58, 60, 265, 1853, 2414, 2415, 2416,
           2631, 2633, 2639, 2653, 2698, 2847, 5766)


def audit_upper(eng, root=16, depth_limit=2, include_ids=()):
    accepted = [e for e in eng.edges if e[4] == 'ok']
    up, down, outgoing = defaultdict(set), defaultdict(set), defaultdict(list)
    for a, b, k, strength, status, eid in accepted:
        outgoing[a].append((b, k, strength, eid))
        if k == '14':
            up[a].add(b)
            down[b].add(a)
    depths, pending = {root: 0}, deque([root])
    while pending:
        cid = pending.popleft()
        for child in down[cid]:
            if child not in depths:
                depths[child] = depths[cid] + 1
                pending.append(child)
    ancestry, descendants = {}, defaultdict(set)
    for cid in eng.names:
        seen, pending = set(), list(up[cid])
        while pending:
            parent = pending.pop()
            if parent not in seen:
                seen.add(parent)
                pending.extend(up[parent] - seen)
        ancestry[cid] = seen
        for parent in seen:
            descendants[parent].add(cid)
    top = {cid for cid, d in depths.items() if d <= depth_limit}
    scope = top | ((set(ANCHORS) | set(include_ids)) & set(eng.names))

    def node(cid):
        return dict(id=cid, name=eng.names.get(cid))

    def relation(a, b, k, strength, eid):
        return dict(id=eid, subject_id=a, subject=eng.names.get(a), kod=k,
                    object_id=b, object=eng.names.get(b), strength=strength)

    nodes = []
    thin = []
    for cid in sorted(scope, key=lambda i: (depths.get(i, 999), i)):
        properties = [relation(cid,b,k,s,eid) for b,k,s,eid in outgoing[cid] if k != '14']
        flagged, has_latin = english_script_flags(eng.terms_of.get(cid, []))
        row = dict(**node(cid), depth=depths.get(cid),
                   parents=[node(p) for p in sorted(up[cid])],
                   children=[node(c) for c in sorted(down[cid])],
                   descendant_count=len(descendants[cid]), facts=properties,
                   cyrillic_only_en=flagged, has_latin_en=has_latin)
        nodes.append(row)
        if len(descendants[cid]) >= 3 and not any(p['kod'] not in ('61','63','64') for p in properties):
            thin.append(dict(**node(cid), descendant_count=len(descendants[cid])))
    coordination, shortcuts, mixed = [], [], []
    for a, b, k, s, status, eid in accepted:
        if k == '61' and (a in scope or b in scope) and (a in ancestry[b] or b in ancestry[a]):
            coordination.append(relation(a,b,k,s,eid))
        if k == '14' and a in scope and any(b in ancestry[p] for p in up[a] if p != b):
            shortcuts.append(relation(a,b,k,s,eid))
    for cid in sorted(scope):
        if 18 in ancestry[cid] and 2535 in ancestry[cid]:
            mixed.append(dict(**node(cid), parents=[node(p) for p in sorted(up[cid])]))
    physical_inheritance = []
    for anchor in [265, 2698, 2430]:
        if anchor not in eng.names:
            continue
        # Inspect the nearest declarations for each physical attribute. An
        # explicit nearer negation overrides a broad inherited default.
        levels, pending = {anchor: 0}, deque([anchor])
        while pending:
            cid = pending.popleft()
            for parent in up[cid]:
                if parent not in levels:
                    levels[parent] = levels[cid] + 1
                    pending.append(parent)
        candidates = defaultdict(list)
        for a, distance in levels.items():
            for b,k,s,eid in outgoing[a]:
                if k == '20' and b in {45,3081,5192}:
                    candidates[b].append((distance, relation(a,b,k,s,eid)))
        bad = []
        for matches in candidates.values():
            closest = min(d for d,row in matches)
            rows = [row for d,row in matches if d == closest]
            if not any(row['strength'] == 0 for row in rows):
                bad.extend(rows)
        if bad:
            physical_inheritance.append(dict(**node(anchor),
                affected_descendants=len(descendants[anchor]), inherited_claims=bad))
    return dict(
        scope=dict(root=root, depth_limit=depth_limit, shortest_depth_nodes=len(top),
                   inspected_nodes=len(scope), additional_anchors=sorted(scope-top),
                   depth_counts=dict(sorted(Counter(depths.values()).items()))),
        review_flags=dict(coordinate_with_ancestor=coordination, genus_shortcuts=shortcuts,
                          property_and_phenomenon=mixed,
                          physical_claims_on_abstract_branches=physical_inheritance,
                          thin_hubs=thin),
        nodes=nodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=int, default=16)
    parser.add_argument('--depth', type=int, default=2)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scope-from', type=Path,
                        help='Retain previously reviewed nodes even if reparented below the depth limit')
    args = parser.parse_args()
    eng = JnanaEngine()
    try:
        prior = json.loads(args.scope_from.read_text(encoding='utf-8')) if args.scope_from else {}
        report = audit_upper(eng, args.root, args.depth, [n['id'] for n in prior.get('nodes',[])])
    finally:
        eng.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(scope=report['scope'], flags={k:len(v) for k,v in report['review_flags'].items()}),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
