"""Fail-closed planning for archived merges that have children or facts.

No automatic deduplication: every incident edge needs an explicit route.
The caller applies the routes transactionally through the engine grammar.
Negations and unaccepted history require a separate review and are refused.
"""


def validate_reviewed_archive(item, concept, terms, edges):
    src = item['source_id']
    if src == item['target_id'] or concept.get('dharma') != src:
        raise ValueError('Invalid reviewed merge identity')
    order = lambda rows: sorted(rows, key=lambda row: repr(sorted(row.items())))
    archive = item['archive']
    for label, actual in [('concept', concept), ('terms', order(terms)), ('edges', order(edges))]:
        expected = archive[label] if label == 'concept' else order(archive[label])
        if actual != expected:
            raise ValueError('Reviewed merge ' + label + ' changed: ' + str(src))
    if not edges or any(e['status'] != 'ok' or e['strength'] == 0 or
                        src not in (e['dh1'], e['dh2']) for e in edges):
        raise ValueError('Merge needs a separate history/negation review: ' + str(src))


def plan_merge_routes(items, routes, resolve, rules):
    mapping = {m['source_id']: m['target_id'] for m in items}
    if len(mapping) != len(items) or set(mapping) & set(mapping.values()):
        raise ValueError('Reviewed merges require unique sources and no chains')
    archived = {}
    for m in items:
        for e in m['archive']['edges']:
            if e['id'] in archived and archived[e['id']] != e:
                raise ValueError('Conflicting archives of a shared edge')
            archived[e['id']] = e
    if len({r['edge_id'] for r in routes}) != len(routes) or set(archived) != {r['edge_id'] for r in routes}:
        raise ValueError('Every archived edge requires exactly one route')
    result = []
    for r in routes:
        if set(r) - {'edge_id', 'subject', 'object', 'genus_reason'}:
            raise ValueError('Route cannot change relation, degree or universe')
        old = archived[r['edge_id']]
        a, b = resolve(r['subject']), resolve(r['object'])
        expected_a, expected_b = (mapping.get(old[key], old[key]) for key in ['dh1', 'dh2'])
        if a != expected_a or (b != expected_b and
                              not (old['kod'] == '14' and r.get('genus_reason'))):
            raise ValueError('Route changes an unreviewed endpoint: ' + str(old['id']))
        if a == b or a in mapping or b in mapping:
            raise ValueError('Route creates a self-loop or references a removed source')
        if old['status'] != 'ok' or old['strength'] == 0:
            raise ValueError('Route needs a separate history/negation review')
        if rules[old['kod']]['sym'] and a > b:
            a, b = b, a
        result.append(dict(old=old, subject=a, object=b, kod=old['kod'],
                           universum_id=old['universum_id'], strength=old['strength'],
                           reason=r.get('genus_reason', 'Reviewed duplicate: preserve incident relation.')))
    return sorted(result, key=lambda r: (r['kod'] != '14', r['old']['id']))


def validate_edge_reuse(existing, strength):
    if existing[1] != 'ok':
        raise ValueError('Replacement collides with an unaccepted edge: ' + str(existing))
    if existing[2] != strength:
        raise ValueError('Replacement changes an existing degree/negation: ' + str(existing))


def grammar_changes(before, after):
    if set(before) != set(after) or before['kod'] != after['kod']:
        raise ValueError('Grammar repair must retain the full row and relation identity')
    allowed = {'long_name', 'description', 'sample'} | {
        prefix + suffix for prefix in ['sig_subject', 'sig_object'] for suffix in ['', '2', '3', '4']}
    changes = {k: v for k, v in after.items() if before[k] != v}
    if not changes or not set(changes) <= allowed:
        raise ValueError('Unsupported or empty grammar repair')
    return changes
