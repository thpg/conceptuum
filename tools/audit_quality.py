"""Read-only quality audit of the active concept graph.

Run from any directory: python tools/audit_quality.py --output report.json
Ambiguous terms are legitimate homonyms, so they are not counted as errors.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jnana_engine import JnanaEngine


def english_script_flags(terms):
    """Heuristics for review, not a claim that Latin text is a translation.

    An English language tag alone says nothing about the term's content.
    Mixed-script technical names and names in other scripts need human review.
    """
    english = [term for term, lang in terms if lang == "en"]
    cyrillic_only = [term for term in english
                     if re.search(r"[\u0400-\u052f]", term)
                     and not re.search(r"[A-Za-z]", term)]
    return cyrillic_only, bool(any(re.search(r"[A-Za-z]", term) for term in english))


def audit(eng):
    accepted = [e for e in eng.edges if e[4] == "ok"]
    up = defaultdict(set)
    for a, b, kod, strength, status, eid in accepted:
        if kod == "14":
            up[a].add(b)
    ancestry = {}
    for cid in eng.names:
        seen, pending = set(), list(up[cid])
        while pending:
            node = pending.pop()
            if node not in seen:
                seen.add(node)
                pending.extend(up[node] - seen)
        ancestry[cid] = seen

    issues = defaultdict(list)
    specific, parallel = set(), set()
    for a, b, kod, strength, status, eid in accepted:
        item = dict(id=eid, subject_id=a, subject=eng.names.get(a),
                    kod=kod, object_id=b, object=eng.names.get(b), strength=strength)
        if a == b:
            issues["self_loops"].append(item)
        if a not in eng.names or b not in eng.names:
            issues["dangling_edges"].append(item)
            continue
        rule = eng.rules.get(kod)
        if not rule:
            issues["unknown_codes"].append(item)
            continue
        if "deprecated" in rule["name"]:
            issues["deprecated_codes"].append(item)
        if strength is not None and not 0 <= strength <= 100:
            issues["invalid_strength"].append(item)
        if kod == "14" and a in ancestry[b] | {b}:
            issues["taxonomy_cycles"].append(item)
        for side, keys, cid in (
            ("subject", ("ss", "ss2", "ss3", "ss4"), a),
            ("object", ("so", "so2", "so3", "so4"), b),
        ):
            anchors = {rule[k] for k in keys if rule.get(k) is not None}
            if anchors and not anchors & (ancestry[cid] | {cid}):
                issues["signature_violations"].append(dict(item, side=side))
        if kod in eng.PROC_SPEC:
            specific.add(a)
        if kod in eng.PROC_PARA:
            parallel.add(a)

    for cid, name in sorted(eng.names.items()):
        langs = {lang for term, lang in eng.terms_of[cid]}
        for lang in ("ru", "en"):
            if lang not in langs:
                issues["missing_" + lang].append(dict(id=cid, name=name))
        suspect, has_latin_en = english_script_flags(eng.terms_of[cid])
        if suspect:
            issues["cyrillic_only_en"].append(dict(id=cid, name=name, terms=suspect))
        if not has_latin_en:
            issues["without_latin_en"].append(dict(id=cid, name=name))
        if not up[cid]:
            issues["roots"].append(dict(id=cid, name=name))

    signature_ids = {row["id"] for row in issues["signature_violations"]}
    metrics = dict(
        concepts=len(eng.names), edges=len(eng.edges), accepted_edges=len(accepted),
        terms=sum(map(len, eng.terms_of.values())),
        signature_invalid_edges=len(signature_ids),
        signature_violations=len(issues["signature_violations"]),
        self_loops=len(issues["self_loops"]),
        taxonomy_cycle_edges=len(issues["taxonomy_cycles"]),
        dangling_edges=len(issues["dangling_edges"]),
        deprecated_edges=len(issues["deprecated_codes"]),
        missing_ru=len(issues["missing_ru"]), missing_en=len(issues["missing_en"]),
        concepts_with_cyrillic_only_en=len(issues["cyrillic_only_en"]),
        cyrillic_only_en_terms=sum(len(row["terms"]) for row in issues["cyrillic_only_en"]),
        concepts_without_latin_en=len(issues["without_latin_en"]),
        concepts_with_specific_properties=len(specific),
        concepts_with_parallel_relations=len(parallel),
        concepts_without_non_isa=len(set(eng.names) - specific - parallel),
        accepted_by_code=dict(sorted(Counter(e[2] for e in accepted).items())),
    )
    return dict(metrics=metrics, issues=dict(issues))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    eng = JnanaEngine(pref_lang="ru")
    try:
        report = audit(eng)
    finally:
        eng.close()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
