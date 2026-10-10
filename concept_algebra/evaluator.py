"""Typed evaluation of catalog sets, graph projections, and property selectors."""
from dataclasses import asdict, dataclass

from .graph import ConceptGraph
from .syntax import AlgebraError, FACT_FUNCTIONS, Node, format_expression, parse


FACT_STATES = {"has": "positive", "lacks": "negative", "unknown": "unknown", "conflicts": "conflict"}


def _set(value, operation):
    if not isinstance(value, frozenset):
        raise AlgebraError(f"{operation} requires a concept set; use #ID for a concept and count(...) for a number")
    return value


@dataclass(frozen=True)
class Evaluation:
    expression: str
    ast: Node
    context: int
    universe: frozenset
    within: str
    value: object
    graph: ConceptGraph
    language: object = None
    explanation: object = None
    diagnostics: object = None

    @property
    def kind(self):
        return "set" if isinstance(self.value, frozenset) else "boolean" if type(self.value) is bool else "integer"

    @property
    def ids(self):
        return tuple(sorted(_set(self.value, "ids")))

    def to_dict(self, limit=50, include_ast=False, offset=0, include_ids=False):
        if limit is not None and (type(limit) is not int or limit < 0):
            raise AlgebraError("Result limit must be nonnegative, or None for all records")
        if type(offset) is not int or offset < 0:
            raise AlgebraError("Result offset must be a nonnegative integer")
        result = {
            "basis": "catalog", "context": self.context,
            "expression": self.expression, "resolved_expression": format_expression(self.ast),
            "within": self.within, "universe_count": len(self.universe), "kind": self.kind,
        }
        if self.kind == "set":
            ids = self.ids
            selected = ids[offset:] if limit is None else ids[offset:offset + limit]
            result.update(count=len(ids), returned=len(selected), truncated=len(selected) < len(ids),
                          offset=offset, has_more=offset + len(selected) < len(ids),
                          items=[self.graph.concept(cid, self.language) for cid in selected])
            if include_ids:
                result["ids"] = list(ids)
        else:
            result["value"] = self.value
        if self.explanation is not None:
            result["explanation"] = self.explanation
        if self.diagnostics is not None:
            result["diagnostics"] = self.diagnostics
        if include_ast:
            result["ast"] = self.ast.to_dict()
        return result


class ConceptAlgebra:
    def __init__(self, graph, language=None):
        self.graph = graph
        self.language = language

    @classmethod
    def from_database(cls, context=1, language=None, **connection_options):
        return cls(ConceptGraph.from_database(context=context, **connection_options), language=language)

    @classmethod
    def from_json(cls, path, context=1, language=None):
        return cls(ConceptGraph.from_json(path, context=context), language=language)

    def compile(self, expression):
        """Resolve all senses and relation aliases before any set computation."""
        def resolve(node):
            value = node.value
            if node.kind == "ref":
                try:
                    value = {"id": self.graph.resolve(value, self.language)}
                except AlgebraError as exc:
                    exc.position, exc.end = node.start, node.end
                    exc.line = expression.count("\n", 0, node.start) + 1
                    exc.column = node.start - expression.rfind("\n", 0, node.start)
                    raise
            elif node.kind == "relation":
                value = self.graph.relation(value)
            args = tuple(resolve(arg) for arg in node.args)
            if node.kind == "call" and value in FACT_FUNCTIONS:
                self.graph.relation(args[0].value, inheritable=True)
            return Node(node.kind, value, args, node.start, node.end, node.depth)
        return resolve(parse(expression))

    def evaluate(self, expression, within=None, explain=None):
        try:
            ast = self.compile(expression)
        except AlgebraError as exc:
            exc.field = "expression"
            raise
        universe = self.graph.ids
        domain_text = "U"
        if within is not None:
            try:
                domain_ast = self.compile(within)
                universe = _set(self._evaluate(domain_ast, universe, {}), "within")
            except AlgebraError as exc:
                exc.field = "within"
                raise
            domain_text = format_expression(domain_ast)
        values = {}
        value = self._evaluate(ast, universe, values)
        explanation = None
        if explain is not None:
            self.graph.concept(explain)
            explanation = self._explain_value(ast, explain, universe, values)
            explanation["concept"] = self.graph.concept(explain, self.language)
            explanation["in_universe"] = explain in universe
            explanation["basis"] = "catalog"
        return Evaluation(expression, ast, self.graph.context, universe, domain_text,
                          value, self.graph, self.language, explanation,
                          self._diagnostics(ast, universe, values))

    def _sample(self, ids):
        """Counts cover the complete set; labels are a bounded, stable sample."""
        selected = sorted(ids)[:5]
        return {"count": len(ids), "items": [self.graph.concept(cid, self.language) for cid in selected],
                "truncated": len(selected) < len(ids)}

    def _operand(self, node, universe, values):
        value = self._evaluate(node, universe, values)
        result = {"expression": format_expression(node)}
        if isinstance(value, frozenset):
            result.update(kind="set", **self._sample(value))
        else:
            result.update(kind="boolean" if type(value) is bool else "integer", value=value)
            if node.kind == "call" and node.value == "count":
                result["counted_set"] = self._sample(self._evaluate(node.args[0], universe, values))
                result["counted_expression"] = format_expression(node.args[0])
        return result

    def _diagnostics(self, node, universe, values):
        if node.kind != "compare" and not (node.kind == "call" and node.value in {"count", "empty", "disjoint"}):
            return None
        operands = [self._evaluate(arg, universe, values) for arg in node.args]
        value = self._evaluate(node, universe, values)
        result = {"operation": node.value, "basis": "catalog", "sample_limit": 5,
                  "operands": [self._operand(arg, universe, values) for arg in node.args], "regions": []}
        if len(operands) == 2 and all(isinstance(operand, frozenset) for operand in operands):
            a, b = operands
            rules = {
                "<=": "Every record in A must also occur in B.",
                "<": "Every record in A must occur in B, and B must contain at least one additional record.",
                ">=": "Every record in B must also occur in A.",
                ">": "Every record in B must occur in A, and A must contain at least one additional record.",
                "==": "Both sets must contain exactly the same records.",
                "!=": "At least one record must occur in only one of the sets.",
                "disjoint": "The two catalog sets must share no records.",
            }
            counterexamples = {"<=": {"left_only"}, "<": {"left_only"},
                               ">=": {"right_only"}, ">": {"right_only"},
                               "==": {"left_only", "right_only"}, "disjoint": {"intersection"}}
            result["rule"] = rules[node.value]
            for key, label, ids in [("left_only", "Only in A", a - b),
                                    ("intersection", "In both", a & b),
                                    ("right_only", "Only in B", b - a)]:
                result["regions"].append(dict(key=key, label=label, **self._sample(ids),
                    counterexamples=not value and bool(ids) and key in counterexamples.get(node.value, set())))
            if a == b:
                result["note"] = "A and B are equal in this catalog domain; neither is a proper subset of the other."
        elif node.value in {"count", "empty"}:
            result["rule"] = ("Count each stored record once in the selected domain." if node.value == "count"
                              else "The set must contain no stored records in the selected domain.")
            result["regions"].append(dict(key="members", label="Counted records" if node.value == "count" else "Set members",
                **self._sample(operands[0]), counterexamples=node.value == "empty" and not value))
        else:
            result["rule"] = "Compare the evaluated operand values; counts refer to stored records in the selected domain."
        return result

    def _explain_value(self, node, cid, universe, values):
        value = self._evaluate(node, universe, values)
        if isinstance(value, frozenset):
            return self._explain(node, cid, universe, values)
        trace = {"expression": format_expression(node), "value": value,
                 "kind": "boolean" if type(value) is bool else "integer"}
        if node.args:
            trace["operands"] = [self._explain_value(arg, cid, universe, values) for arg in node.args]
        trace["meaning"] = "Operand membership describes the inspected record; the result is computed over the complete catalog domain."
        return trace

    def _evaluate(self, node, universe, values):
        if id(node) in values:
            return values[id(node)]
        evaluate = lambda arg: self._evaluate(arg, universe, values)
        if node.kind == "ref":
            value = self.graph.extent(node.value["id"]) & universe
        elif node.kind == "integer":
            value = node.value
        elif node.kind == "constant":
            value = universe if node.value == "U" else frozenset()
        elif node.kind == "not":
            value = universe - _set(evaluate(node.args[0]), "Complement")
        elif node.kind == "binary":
            left, right = (_set(evaluate(arg), node.value) for arg in node.args)
            if node.value == "|":
                value = left | right
            elif node.value == "&":
                value = left & right
            elif node.value == "-":
                value = left - right
            else:
                value = left ^ right
        elif node.kind == "compare":
            left, right = map(evaluate, node.args)
            if type(left) is not type(right):
                raise AlgebraError("Comparison operands must both be sets, integers, or booleans")
            if type(left) is bool and node.value not in {"==", "!="}:
                raise AlgebraError("Booleans support only == and != comparisons")
            if node.value == "==":
                value = left == right
            elif node.value == "!=":
                value = left != right
            elif node.value == "<=":
                value = left <= right
            elif node.value == "<":
                value = left < right
            elif node.value == ">=":
                value = left >= right
            else:
                value = left > right
        elif node.kind == "call":
            name = node.value
            if name == "exact":
                value = frozenset({node.args[0].value["id"]}) & universe
            elif name in FACT_FUNCTIONS:
                code, target = node.args[0].value, node.args[1].value["id"]
                if len(universe) < len(self.graph.ids) // 4:
                    value = frozenset(cid for cid in universe if self.graph.fact(cid, code, target).state == FACT_STATES[name])
                else:
                    value = self.graph.property_sets(code, target)[FACT_STATES[name]] & universe
            elif name in {"subjects", "related"}:
                code = node.args[0].value
                ids = _set(evaluate(node.args[1]), name)
                value = self.graph.project(code, ids, incoming=name == "subjects") & universe
            else:
                ids = _set(evaluate(node.args[0]), name)
                if name == "count":
                    value = len(ids)
                elif name == "empty":
                    value = not ids
                elif name == "disjoint":
                    value = ids.isdisjoint(_set(evaluate(node.args[1]), name))
                else:
                    value = self.graph.navigate(ids, name) & universe
        else:
            raise AlgebraError("A relation code can only occur inside a relation function")
        values[id(node)] = value
        return value

    def _explain(self, node, cid, universe, values):
        value = self._evaluate(node, universe, values)
        trace = {"expression": format_expression(node), "member": cid in _set(value, "Explanation")}
        if node.kind == "ref":
            trace["path"] = self.graph.path(cid, node.value["id"]) if cid in universe else None
            trace["meaning"] = "Recorded membership path; a missing path is not a semantic negation"
        elif node.kind in {"binary", "not"}:
            trace["operands"] = [self._explain(arg, cid, universe, values) for arg in node.args]
            if node.kind == "not":
                trace["meaning"] = "Complement relative to the finite catalog domain"
        elif node.kind == "call":
            if node.value in FACT_FUNCTIONS:
                trace["fact"] = self.graph.explain_fact(cid, node.args[0].value, node.args[1].value["id"])
            elif node.value == "exact":
                trace["record_id"] = node.args[0].value["id"]
            elif node.value in {"related", "subjects"}:
                code = node.args[0].value
                ids = self._evaluate(node.args[1], universe, values)
                incoming = node.value == "subjects"
                evidence = []
                for edge in self.graph.edges:
                    if edge.code != code or not edge.positive:
                        continue
                    left, right = (edge.subject, edge.target) if incoming else (edge.target, edge.subject)
                    if (left == cid and right in ids) or (self.graph.rules[code] and right == cid and left in ids):
                        evidence.append(asdict(edge))
                trace["edges"] = evidence
            else:
                ids = self._evaluate(node.args[0], universe, values)
                trace["path"] = None
                for seed in sorted(ids):
                    up = node.value in {"parents", "ancestors"}
                    path = self.graph.path(seed, cid, genus_only=True) if up else self.graph.path(cid, seed, genus_only=True)
                    if path and (node.value in {"ancestors", "descendants"} or len(path) == 1):
                        trace["path"] = path
                        break
        return trace
