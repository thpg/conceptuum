"""Deterministic, evidence-grounded QA generation and JSONL export."""
import argparse
from collections import Counter, defaultdict, deque
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import re
import sys

from . import AlgebraError, ConceptAlgebra, ConceptGraph
from .graph import normalize
from .qa_check import solve, verify_record
from .qa_format import TASKS, wording, messages

MAX_FACTS = 36
MAX_DOMAIN = 24
MAX_RECORD_BYTES = 24576
PROPERTY_CODES = {"20", "21", "22", "23"}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def graph_fingerprint(graph):
    return digest({"context": graph.context, "concepts": [asdict(graph.concepts[cid]) for cid in sorted(graph.ids)],
                   "terms": [[cid, lang, list(sorted(terms))] for (cid, lang), terms in sorted(graph._terms.items())],
                   "relations": sorted(graph.rules.items()), "edges": [asdict(edge) for edge in graph.edges]})


def checked_options(data, maximum=2000):
    allowed = {"count", "seed", "context", "lang", "root", "tasks"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise AlgebraError("Expected a QA request with count, seed, context, lang, root and/or tasks")
    output = dict(count=data.get("count", 20), seed=data.get("seed", 42), context=data.get("context", 1),
                  lang=data.get("lang", "en"), root=data.get("root"), tasks=data.get("tasks", list(TASKS)))
    for field, low, high in [("count", 1, maximum), ("seed", 0, 2**32-1), ("context", 1, 5)]:
        value = output[field]
        if type(value) is not int or not low <= value <= high:
            raise AlgebraError(f"{field} must be an integer from {low} to {high}")
    if output["lang"] not in ("en", "ru"):
        raise AlgebraError("lang must be en or ru")
    if output["root"] is not None and (type(output["root"]) is not int or output["root"] <= 0):
        raise AlgebraError("root must be a positive concept ID or null")
    tasks = output["tasks"]
    if not isinstance(tasks, list) or not tasks or len(tasks) > len(TASKS) or any(not isinstance(t, str) or t not in TASKS for t in tasks) or len(tasks) != len(set(tasks)):
        raise AlgebraError("tasks must be a nonempty list of distinct supported task names")
    return output


class Rejected(ValueError):
    pass


class QuestionGenerator:
    def __init__(self, graph, language="en", source=None, policy=None):
        if language not in ("en", "ru"):
            raise AlgebraError("Question language must be en or ru")
        self.graph, self.language = graph, language
        self.algebra = ConceptAlgebra(graph, language=language)
        self.policy = policy if policy is not None else json.loads(Path(__file__).with_name("qa_policy.json").read_text(encoding="utf-8"))
        self.source = {key: value for key, value in (source or {}).items() if key in {"data_revision", "source_dump_sha256", "code_version", "interface_revision"}}
        self.source.update(graph_sha256=graph_fingerprint(graph), qa_policy_sha256=digest(self.policy), generator_version="1")
        self.parents, self.children, self.up = defaultdict(list), defaultdict(list), defaultdict(list)
        self.properties = defaultdict(list)
        self.labels = {}
        for edge in graph.edges:
            if edge.code == "14" and edge.positive:
                self.parents[edge.subject].append(edge)
                self.children[edge.target].append(edge)
                self.up[edge.subject].append((edge.target, edge))
            elif edge.code == "30" and edge.positive:
                self.up[edge.subject].append((edge.target, edge))
                self.up[edge.target].append((edge.subject, edge))
            elif edge.code in PROPERTY_CODES:
                self.properties[edge.subject].append(edge)

    def label(self, cid):
        if cid in self.labels:
            if self.labels[cid] is None:
                raise Rejected("missing_or_unsuitable_label")
            return self.labels[cid]
        terms = list(self.graph.terms(cid, self.language))
        if self.policy.get("require_valid_english_label") and not any(
                re.search(r"[A-Za-z]", term) and not re.search(r"[А-Яа-яЁё]", term)
                for term in self.graph.terms(cid, "en")):
            # Legacy auto-derived Russian names often carry a Cyrillic verb in
            # the EN column. Exclude these unreviewed records in either language.
            self.labels[cid] = None
            raise Rejected("missing_or_unsuitable_label")
        if self.language == "ru" and not terms:
            terms = [self.graph.concepts[cid].name]
        def usable(term):
            if not term.strip() or len(term) > 90 or any(ord(char) < 32 for char in term) or "\ufffd" in term:
                return False
            if self.language == "en":
                return bool(re.search(r"[A-Za-z]", term)) and not re.search(r"[А-Яа-яЁё]", term) and not term.lower().startswith("to ")
            return bool(re.search(r"[А-Яа-яЁё]", term))
        terms = [term for term in terms if usable(term)]
        excluded = {item["id"] for item in self.policy.get("excluded_concepts", [])}
        if cid in excluded:
            raise Rejected("reviewed_concept_exclusion")
        preferred = self.policy.get("preferred_terms", {}).get(self.language, {}).get(str(cid))
        if preferred is None and self.language == "ru":
            preferred = self.graph.concepts[cid].name
        # Prefer an unambiguous stored term over a shorter homonym (flight vs fly).
        terms.sort(key=lambda term: (term != preferred if preferred else False,
                                     len(self.graph._lookup.get((self.language, normalize(term)), ())) != 1,
                                     len(term), term.casefold(), term))
        self.labels[cid] = terms[0] if terms else None
        if not terms:
            raise Rejected("missing_or_unsuitable_label")
        return terms[0]

    def closure(self, seeds, coextension=False):
        seen, facts = set(seeds), {}
        queue = deque(sorted(seeds))
        while queue:
            cid = queue.popleft()
            links = self.up[cid] if coextension else [(edge.target, edge) for edge in self.parents[cid]]
            for target, edge in links:
                facts[edge.id] = edge
                if len(facts) > MAX_FACTS:
                    raise Rejected("evidence_too_large")
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        return seen, list(facts.values())

    def blocked(self, edge):
        return any((edge.subject, edge.code, edge.target, edge.strength) ==
                   (item["subject"], item["relation"], item["target"], item.get("strength", edge.strength))
                   for item in self.policy.get("excluded_assertions", []))

    def candidates(self, options):
        rng = random.Random(options["seed"])
        domain = self.graph.extent(options["root"]) if options["root"] is not None else self.graph.ids
        subjects = sorted(cid for cid in domain if self.parents[cid])
        rng.shuffle(subjects)
        pools = defaultdict(list)
        pairs = set()
        for index, cid in enumerate(subjects):
            try:
                self.label(cid)
            except Rejected:
                continue
            parents = self.parents[cid]
            if len(parents) <= 4:
                pools["parents"].append(("parents", {"a": cid}, parents, []))
            choices = []
            queue = deque([(cid, [], [cid])])
            visited = {cid}
            while queue:
                current, edges, path = queue.popleft()
                if 2 <= len(edges) <= 4:
                    choices.append((edges, path))
                if len(edges) >= 4:
                    continue
                for edge in self.parents[current]:
                    if edge.target not in visited:
                        visited.add(edge.target)
                        queue.append((edge.target, edges + [edge], path + [edge.target]))
            if choices:
                edges, path = rng.choice(choices)
                a, b = (cid, path[-1]) if index % 2 else (path[-1], cid)
                pools["ancestry"].append(("ancestry", {"a": a, "b": b, "path": path}, edges, []))
            primary = rng.choice(parents)
            siblings = [edge for edge in self.children[primary.target] if edge.subject != cid and edge.subject in domain]
            if siblings:
                other = rng.choice(siblings)
                both = parents + self.parents[other.subject]
                if len(both) <= 8:
                    pools["shared_genus"].append(("shared_genus", {"a": cid, "b": other.subject}, both, []))
                if index % 3:
                    pools["inference"].append(("inference", {"a": cid, "b": other.subject, "inference": "siblings_disjoint"}, [primary, other], []))
                else:
                    pools["inference"].append(("inference", {"a": cid, "b": other.subject, "parent": primary.target, "inference": "shared_membership"}, [primary, other], []))
                pairs.add(tuple(sorted((cid, other.subject))))
            if not index % 2:
                pools["inference"].append(("inference", {"a": cid, "b": primary.target, "inference": "reverse_genus"}, [primary], []))
            if len(parents) > 1:
                for i, left in enumerate(parents):
                    for right in parents[i+1:]:
                        if left.target != right.target:
                            pairs.add(tuple(sorted((left.target, right.target))))
        for left, right in sorted(pairs):
            for task in ("intersection", "difference", "count"):
                pools[task].append((task, {"a": left, "b": right}, None, None))
        # Related concepts provide meaningful unknowns (e.g. a vessel need not inherit
        # the glass-material assertion of a narrower glass vessel).
        property_keys = set()
        for owner in sorted(self.properties):
            for edge in self.properties[owner]:
                related = [owner] + [e.subject for e in self.children[owner]][:5] + [e.target for e in self.parents[owner]]
                for cid in related:
                    key = (cid, edge.code, edge.target)
                    if cid not in domain or key in property_keys:
                        continue
                    property_keys.add(key)
                    state = self.graph.fact(cid, edge.code, edge.target).state
                    pools["property_" + state].append(("property", {"a": cid, "relation": edge.code, "target": edge.target,
                        "distractor_edge": edge.id if state == "unknown" else None}, None, []))
        for key in list(pools):
            if ("property" if key.startswith("property_") else key) not in options["tasks"]:
                del pools[key]
            else:
                rng.shuffle(pools[key])
        # Half the intersection attempts use witnessed overlap, rather than letting
        # the much larger pool of unrelated leaves dominate with empty answers.
        if "intersection" in pools:
            overlap, empty = [], []
            for candidate in pools["intersection"]:
                spec = candidate[1]
                left, right = self.graph.extent(spec["a"]), self.graph.extent(spec["b"])
                if 3 <= len(left | right) <= MAX_DOMAIN:
                    (overlap if left & right else empty).append(candidate)
            mixed = []
            while overlap or empty:
                for group in (empty, overlap):
                    if group:
                        mixed.append(group.pop())
            pools["intersection"] = list(reversed(mixed))
        return pools

    def make(self, candidate):
        task, original_spec, facts, domain = candidate
        spec = dict(original_spec)
        if task == "property":
            owners, facts = self.closure({spec["a"]})
            facts += [edge for owner in owners for edge in self.properties[owner]
                      if edge.code == spec["relation"] and edge.target == spec["target"]]
            distractor = spec.pop("distractor_edge", None)
            if distractor:
                edge = next(edge for edge in self.graph.edges if edge.id == distractor)
                facts.append(edge)
                facts += self.parents[edge.subject]
        elif task in {"intersection", "difference", "count"}:
            left, right = self.graph.extent(spec["a"]), self.graph.extent(spec["b"])
            domain = sorted(left | right)
            if not 3 <= len(domain) <= MAX_DOMAIN:
                raise Rejected("catalog_domain_size")
            if task == "count":
                ancestors, _ = self.closure({spec["a"], spec["b"]})
                distractors = sorted(ancestors - set(domain))[:2]
                if not distractors or len(domain) + len(distractors) > MAX_DOMAIN:
                    raise Rejected("uninformative_count_domain")
                domain = sorted(set(domain) | set(distractors))
            _, facts = self.closure(domain, coextension=True)
        facts = sorted({edge.id: edge for edge in facts}.values(), key=lambda edge: edge.id)
        if not facts or len(facts) > MAX_FACTS:
            raise Rejected("evidence_too_large")
        if any(self.blocked(edge) for edge in facts):
            raise Rejected("reviewed_assertion_exclusion")
        ids = {spec["a"]} | set(domain)
        if "b" in spec:
            ids.add(spec["b"])
        if "target" in spec:
            ids.add(spec["target"])
        for edge in facts:
            ids.update((edge.subject, edge.target))
        concepts = [{"id": cid, "name": self.label(cid)} for cid in sorted(ids)]
        grounding = {"concepts": concepts, "facts": [dict(id=edge.id, subject=edge.subject, relation=edge.code,
            target=edge.target, strength=edge.strength) for edge in facts], "domain": domain,
            "scope": "selected_premises" if task in {"inference", "ancestry"} else "complete_for_query"}
        expected = solve(task, spec, grounding)
        if task in {"parents", "shared_genus"} and not expected["value"]:
            raise Rejected("uninformative_answer")
        query = self.query(task, spec, domain, expected)
        if task == "property":
            actual = self.graph.fact(spec["a"], spec["relation"], spec["target"])
            if expected != dict(kind="property_state", value=actual.state, evidence_ids=[e.id for e in actual.evidence], overridden_ids=[e.id for e in actual.overridden]):
                raise Rejected("incomplete_property_evidence")
        if query:
            evaluated = self.algebra.evaluate(query["expression"], within=query["within"])
            value = list(evaluated.ids) if evaluated.kind == "set" else evaluated.value
            gold = [spec["a"]] if task == "property" else expected["value"]
            if type(value) is not type(gold) or value != gold:
                raise Rejected("independent_solver_disagreement")
        question, answer = wording(task, spec, expected, concepts, self.language)
        record = {"schema": "conceptuum.qa.v1", "id": digest([self.source, self.language, task, spec])[:24],
            "group_id": digest([self.graph.context, spec["a"]])[:16], "task": task, "language": self.language,
            "context": self.graph.context, "question": question, "answer": answer, "spec": spec,
            "grounding": grounding, "expected": expected, "algebra": query, "source": dict(self.source),
            "messages": messages(question, answer, grounding, self.language),
            "quality": {"status": "automatically_verified", "source_edges_checked": True,
                "answer_recomputed_from_input": True, "algebra_cross_checked": query is not None,
                "independent_world_fact_review": False}}
        errors = verify_record(record, self.graph)
        if errors:
            raise Rejected("verification:" + ",".join(errors))
        if len(json.dumps(record, ensure_ascii=False).encode("utf-8")) > MAX_RECORD_BYTES:
            raise Rejected("record_too_large")
        return record

    @staticmethod
    def query(task, spec, domain, expected):
        a, b = spec["a"], spec.get("b")
        expressions = {"parents": f"parents(exact(#{a}))", "ancestry": f"exact(#{a}) <= #{b}",
                       "shared_genus": f"parents(exact(#{a})) & parents(exact(#{b}))",
                       "intersection": f"#{a} & #{b}", "difference": f"#{a} - #{b}", "count": f"count(#{a} | #{b})"}
        if task == "inference":
            return None
        if task == "property":
            selector = {"positive": "has", "negative": "lacks", "unknown": "unknown", "conflict": "conflicts"}[expected["value"]]
            return {"expression": f"{selector}({spec['relation']}, #{spec['target']})", "within": f"exact(#{a})"}
        return {"expression": expressions[task], "within": " | ".join(f"exact(#{cid})" for cid in domain) if domain else None}

    def generate(self, count=20, seed=42, root=None, tasks=None):
        options = checked_options(dict(count=count, seed=seed, root=root, tasks=list(TASKS) if tasks is None else tasks,
                                       lang=self.language, context=self.graph.context))
        pools = self.candidates(options)
        records, seen = [], set()
        rejected = Counter()
        attempts = 0
        keys = [key for key in ("parents", "ancestry", "shared_genus", "intersection", "difference", "count",
                "property_positive", "property_negative", "property_unknown", "property_conflict", "inference") if key in pools]
        while len(records) < count and any(pools.values()) and attempts < min(30000, count * 100):
            for key in keys:
                while pools[key]:
                    attempts += 1
                    try:
                        record = self.make(pools[key].pop())
                        question_key = record["question"]
                        if question_key in seen:
                            raise Rejected("duplicate_question")
                        seen.add(question_key)
                        records.append(record)
                        break
                    except Rejected as exc:
                        rejected[str(exc)] += 1
                    if attempts >= min(30000, count * 100):
                        break
                if len(records) >= count or attempts >= min(30000, count * 100):
                    break
        # Shuffle task order after balanced sampling, without changing per-record IDs.
        random.Random(seed ^ 0x51A7).shuffle(records)
        report = {"requested": count, "generated": len(records), "complete": len(records) == count,
                  "seed": seed, "context": self.graph.context, "language": self.language, "root": root,
                  "tasks": dict(Counter(record["task"] for record in records)),
                  "property_states": dict(Counter(record["expected"]["value"] for record in records if record["task"] == "property")),
                  "intersection_answers": dict(Counter("nonempty" if record["expected"]["value"] else "empty" for record in records if record["task"] == "intersection")),
                  "ancestry_answers": dict(Counter("established" if record["expected"]["value"] else "not_established" for record in records if record["task"] == "ancestry")),
                  "verified": len(records), "duplicates": 0, "rejected_candidates": dict(sorted(rejected.items())),
                  "attempted_candidates": attempts, "source": self.source,
                  "review_scope": "Source fidelity, independent recomputation from supplied facts, controlled wording and known-issue exclusions. Not an exhaustive world-fact or linguistic review.",
                  "split_guidance": "Keep group_id together across train/evaluation splits. Shared ancestors and evidence can still cross groups; inspect that overlap before claiming held-out concepts."}
        return {"schema": "conceptuum.qa.batch.v1", "records": records, "report": report}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate checked, evidence-grounded QA examples for LLM training.")
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--context", type=int, default=1)
    parser.add_argument("--lang", choices=["en", "ru"], default="en")
    parser.add_argument("--root", type=int, help="optional concept ID restricting question subjects")
    parser.add_argument("--tasks", nargs="+", choices=TASKS)
    parser.add_argument("--snapshot", help="JSON graph snapshot instead of MariaDB")
    parser.add_argument("--version-file", default=str(Path(__file__).resolve().parents[1]/"visualizer/static/version.json"))
    parser.add_argument("--output", help="annotated JSONL path; default: stdout")
    parser.add_argument("--messages-output", help="optional training JSONL containing only messages")
    parser.add_argument("--report", help="optional quality-report JSON path")
    parser.add_argument("--force", action="store_true", help="replace existing output files")
    args = parser.parse_args(argv)
    try:
        options = checked_options(dict(count=args.count, seed=args.seed, context=args.context, lang=args.lang,
                                       root=args.root, tasks=args.tasks or list(TASKS)))
        paths = [Path(value) for value in (args.output, args.messages_output, args.report) if value]
        if len({str(path.resolve()).casefold() for path in paths}) != len(paths):
            raise AlgebraError("Output, messages and report must use different paths")
        inputs = {str(Path(p).resolve()).casefold() for p in (args.snapshot, args.version_file) if p}
        if any(str(path.resolve()).casefold() in inputs for path in paths):
            raise AlgebraError("Output files must not overwrite the graph snapshot or version metadata")
        if not args.force and any(path.exists() for path in paths):
            raise AlgebraError("An output file already exists; choose another path or use --force")
        graph = ConceptGraph.from_json(args.snapshot, context=args.context) if args.snapshot else ConceptGraph.from_database(context=args.context)
        source = json.loads(Path(args.version_file).read_text(encoding="utf-8-sig")) if Path(args.version_file).is_file() else {}
        result = QuestionGenerator(graph, args.lang, source=source).generate(args.count, args.seed, args.root, options["tasks"])
        lines = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in result["records"])
        outputs = [(args.output, lines), (args.messages_output, "".join(json.dumps({"messages": record["messages"]}, ensure_ascii=False) + "\n" for record in result["records"])),
                   (args.report, json.dumps(result["report"], ensure_ascii=False, indent=2) + "\n")]
        for destination, text in outputs:
            if destination:
                path = Path(destination)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
        if not args.output:
            sys.stdout.write(lines)
        print(json.dumps(result["report"], ensure_ascii=False), file=sys.stderr)
        return 0 if result["report"]["complete"] else 3
    except (AlgebraError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
