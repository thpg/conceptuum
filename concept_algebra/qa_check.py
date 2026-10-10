"""Recompute answers from supplied edges without using ConceptGraph's inference."""
from collections import defaultdict, deque

from .qa_format import TASKS, wording, messages


def reach(start, links):
    found = {start}
    pending = deque([start])
    while pending:
        for target in links.get(pending.popleft(), ()):
            if target not in found:
                found.add(target)
                pending.append(target)
    return found


def solve(task, spec, grounding):
    genus, sets = defaultdict(set), defaultdict(set)
    facts = grounding["facts"]
    for edge in facts:
        if edge["strength"] == 0:
            continue
        a, b = edge["subject"], edge["target"]
        if edge["relation"] == "14":
            genus[a].add(b)
            sets[a].add(b)
        elif edge["relation"] == "30":
            sets[a].add(b)
            sets[b].add(a)
    a = spec["a"]
    b = spec.get("b")
    if task == "parents":
        return {"kind": "set", "value": sorted(genus[a])}
    if task == "shared_genus":
        return {"kind": "set", "value": sorted(genus[a] & genus[b])}
    if task == "ancestry":
        path = spec["path"]
        if len(path) < 3 or len(set(path)) != len(path) or not all(y in genus[x] for x, y in zip(path, path[1:])):
            raise ValueError("Invalid ancestry path")
        if {a, b} != {path[0], path[-1]}:
            raise ValueError("Ancestry endpoints do not match")
        return {"kind": "boolean", "value": b in reach(a, genus)}
    if task in {"intersection", "difference", "count"}:
        left = {cid for cid in grounding["domain"] if a in reach(cid, sets)}
        right = {cid for cid in grounding["domain"] if b in reach(cid, sets)}
        if task == "count":
            return {"kind": "integer", "value": len(left | right)}
        return {"kind": "set", "value": sorted(left & right if task == "intersection" else left - right)}
    if task == "property":
        ancestry = reach(a, genus)
        assertions = [edge for edge in facts if edge["subject"] in ancestry and edge["relation"] == spec["relation"] and edge["target"] == spec["target"]]
        owners = {edge["subject"] for edge in assertions}
        closures = {owner: reach(owner, genus) for owner in owners}
        specific = {owner for owner in owners if not any(owner != other and owner in closures[other] and other not in closures[owner] for other in owners)}
        evidence = [edge for edge in assertions if edge["subject"] in specific]
        signs = {edge["strength"] != 0 for edge in evidence}
        state = "conflict" if len(signs) == 2 else "positive" if True in signs else "negative" if False in signs else "unknown"
        return {"kind": "property_state", "value": state, "evidence_ids": sorted(edge["id"] for edge in evidence),
                "overridden_ids": sorted(edge["id"] for edge in assertions if edge["subject"] not in specific)}
    if task == "inference":
        if any(edge["relation"] != "14" or edge["strength"] == 0 for edge in facts):
            raise ValueError("Invalid genus-only inference premises")
        if spec["inference"] == "shared_membership":
            if a == b or spec["parent"] not in genus[a] & genus[b]:
                raise ValueError("Missing shared-genus premises")
            return {"kind": "inference_state", "value": "entailed"}
        if spec["inference"] == "siblings_disjoint":
            if a == b or not genus[a] & genus[b]:
                raise ValueError("Missing shared-genus premises")
        elif spec["inference"] == "reverse_genus":
            if b not in genus[a] or a in reach(b, genus):
                raise ValueError("Invalid converse premises")
        else:
            raise ValueError("Unknown inference task")
        return {"kind": "inference_state", "value": "not_entailed"}
    raise ValueError("Unknown task")


def verify_record(record, graph=None):
    """Return reasons to reject; an empty list is not a world-truth certificate."""
    errors = []
    try:
        if record["schema"] != "conceptuum.qa.v1" or record["task"] not in TASKS or record["language"] not in ("en", "ru"):
            return ["invalid_schema"]
        grounding = record["grounding"]
        concepts = {item["id"]: item["name"] for item in grounding["concepts"]}
        if len(concepts) != len(grounding["concepts"]) or any(not isinstance(name, str) or not name.strip() for name in concepts.values()):
            errors.append("invalid_concepts")
        ids = set()
        for edge in grounding["facts"]:
            if (type(edge["id"]) is not int or edge["id"] <= 0 or edge["id"] in ids or
                    edge["subject"] not in concepts or edge["target"] not in concepts or
                    edge["relation"] not in {"14", "20", "21", "22", "23", "30"} or
                    edge["strength"] is not None and (type(edge["strength"]) is not int or not 0 <= edge["strength"] <= 100)):
                errors.append("invalid_fact")
            ids.add(edge["id"])
        if len(set(grounding["domain"])) != len(grounding["domain"]) or any(cid not in concepts for cid in grounding["domain"]):
            errors.append("invalid_domain")
        genus = defaultdict(set)
        for edge in grounding["facts"]:
            if edge["relation"] == "14" and edge["strength"] != 0:
                genus[edge["subject"]].add(edge["target"])
        if any(cid in reach(parent, genus) for cid in list(genus) for parent in genus[cid]):
            errors.append("cyclic_genus")
        actual = solve(record["task"], record["spec"], grounding)
        if actual != record["expected"]:
            errors.append("answer_mismatch")
        question, answer = wording(record["task"], record["spec"], actual, grounding["concepts"], record["language"])
        if question != record["question"] or answer != record["answer"]:
            errors.append("wording_mismatch")
        if messages(question, answer, grounding, record["language"]) != record["messages"]:
            errors.append("messages_mismatch")
        if graph is not None:
            if record["context"] != graph.context:
                errors.append("context_mismatch")
            source = {edge.id: edge for edge in graph.edges}
            for edge in grounding["facts"]:
                stored = source.get(edge["id"])
                if stored is None or (stored.subject, stored.code, stored.target, stored.strength) != (edge["subject"], edge["relation"], edge["target"], edge["strength"]):
                    errors.append("unsupported_fact")
            for cid, label in concepts.items():
                if cid not in graph.ids or label not in graph.terms(cid, record["language"]) and not (record["language"] == "ru" and label == graph.concepts[cid].name):
                    errors.append("unsupported_label")
            task, spec = record["task"], record["spec"]
            if task == "property":
                fact = graph.fact(spec["a"], spec["relation"], spec["target"])
                full = dict(kind="property_state", value=fact.state, evidence_ids=[e.id for e in fact.evidence], overridden_ids=[e.id for e in fact.overridden])
                if full != actual:
                    errors.append("incomplete_property_evidence")
            elif task in {"parents", "shared_genus"}:
                parents = lambda cid: {e.target for e in graph.edges if e.subject == cid and e.code == "14" and e.positive}
                full = parents(spec["a"])
                if task == "shared_genus":
                    full &= parents(spec["b"])
                if sorted(full) != actual["value"]:
                    errors.append("incomplete_genus_evidence")
            elif task in {"intersection", "difference", "count"}:
                domain = set(grounding["domain"])
                left, right = graph.extent(spec["a"]) & domain, graph.extent(spec["b"]) & domain
                full = len(left | right) if task == "count" else sorted(left & right if task == "intersection" else left - right)
                if full != actual["value"]:
                    errors.append("incomplete_catalog_evidence")
    except (KeyError, TypeError, ValueError, AttributeError):
        errors.append("malformed_record")
    return sorted(set(errors))
