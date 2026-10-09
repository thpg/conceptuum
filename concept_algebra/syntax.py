"""A bounded expression parser; query text is never executed as Python or SQL."""
from dataclasses import dataclass
import json
from typing import Any, Tuple


class AlgebraError(ValueError):
    """A query or snapshot error suitable for display to a caller."""


class ParseError(AlgebraError):
    def __init__(self, message, source, position):
        self.source = source
        self.position = position
        self.line = source.count("\n", 0, position) + 1
        self.column = position - source.rfind("\n", 0, position)
        super().__init__(f"{message} at line {self.line}, column {self.column}")


@dataclass(frozen=True)
class Node:
    kind: str
    value: Any = None
    args: Tuple["Node", ...] = ()
    start: int = 0
    end: int = 0
    depth: int = 1

    def to_dict(self):
        result = {"kind": self.kind, "start": self.start, "end": self.end}
        if self.value is not None:
            result["value"] = dict(self.value) if isinstance(self.value, dict) else self.value
        if self.args:
            result["args"] = [arg.to_dict() for arg in self.args]
        return result


@dataclass(frozen=True)
class Token:
    kind: str
    value: Any
    start: int
    end: int


ALIASES = {
    "+": "|", "∪": "|", "or": "|",
    "*": "&", "∩": "&", "and": "&",
    "\\": "-", "∖": "-", "△": "^", "⊕": "^", "xor": "^",
    "!": "~", "¬": "~", "not": "~",
    "⊆": "<=", "⊂": "<", "⊇": ">=", "⊃": ">",
    "≤": "<=", "≥": ">=",
    "=": "==", "≠": "!=",
}
PRECEDENCE = {"|": 10, "^": 20, "&": 30, "-": 30}
COMPARISONS = {"==", "!=", "<=", "<", ">=", ">"}
FUNCTIONS = {
    "exact": 1, "parents": 1, "children": 1,
    "ancestors": 1, "descendants": 1,
    "count": 1, "empty": 1, "disjoint": 2,
    "related": 2, "subjects": 2,
    "has": 2, "lacks": 2, "unknown": 2, "conflicts": 2,
}
RELATION_FUNCTIONS = {"related", "subjects", "has", "lacks", "unknown", "conflicts"}
FACT_FUNCTIONS = {"has", "lacks", "unknown", "conflicts"}


def _tokens(source):
    i = 0
    count = 0
    while i < len(source):
        if source[i].isspace():
            i += 1
            continue
        count += 1
        if count > 2048:
            raise ParseError("Expression exceeds 2048 tokens", source, i)
        start = i
        char = source[i]
        if char in "\"'":
            quote = char
            i += 1
            value = []
            while i < len(source) and source[i] != quote:
                char = source[i]
                if char == "\\":
                    i += 1
                    if i == len(source):
                        raise ParseError("Unterminated escape", source, i - 1)
                    char = source[i]
                    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", "'": "'", '"': '"'}
                    if char == "u":
                        digits = source[i + 1:i + 5]
                        if len(digits) != 4 or any(c not in "0123456789abcdefABCDEF" for c in digits):
                            raise ParseError("Expected four hexadecimal digits after \\u", source, i)
                        char = chr(int(digits, 16))
                        if 0xD800 <= ord(char) <= 0xDFFF:
                            raise ParseError("Use a literal Unicode character instead of a surrogate escape", source, i)
                        i += 4
                    elif char in escapes:
                        char = escapes[char]
                    else:
                        raise ParseError("Unsupported string escape", source, i)
                value.append(char)
                i += 1
            if i == len(source):
                raise ParseError("Unterminated quoted term", source, start)
            i += 1
            yield Token("string", "".join(value), start, i)
        elif char == "#":
            i += 1
            first = i
            while i < len(source) and source[i] in "0123456789":
                i += 1
            if first == i:
                raise ParseError("Expected a positive concept ID after #", source, start)
            value = int(source[first:i])
            if value <= 0 or value > 2147483647:
                raise ParseError("Concept ID must be from 1 to 2147483647", source, start)
            yield Token("id", value, start, i)
        elif char in "0123456789":
            i += 1
            while i < len(source) and source[i] in "0123456789":
                i += 1
            yield Token("number", int(source[start:i]), start, i)
        elif char.isalpha() or char == "_":
            i += 1
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
            value = source[start:i]
            if value in ALIASES:
                yield Token("op", ALIASES[value], start, i)
            else:
                yield Token("name", value, start, i)
        elif len(source[i:i + 2]) == 2 and source[i:i + 2] in COMPARISONS:
            i += 2
            yield Token("op", source[start:i], start, i)
        elif char in "|&-^~+*\\!<>=∪∩∖△⊕¬⊆⊂⊇⊃≠≤≥":
            i += 1
            yield Token("op", ALIASES.get(char, char), start, i)
        elif char in "(),:":
            i += 1
            yield Token(char, char, start, i)
        elif char == "∅":
            i += 1
            yield Token("name", "EMPTY", start, i)
        else:
            raise ParseError(f"Unexpected character {char!r}", source, i)
    yield Token("end", "", len(source), len(source))


class _Parser:
    def __init__(self, source):
        self.source = source
        self.tokens = list(_tokens(source))
        self.cursor = 0
        self.nodes = 0
        self.nesting = 0

    @property
    def token(self):
        return self.tokens[self.cursor]

    def take(self):
        token = self.token
        self.cursor += 1
        return token

    def fail(self, message, token=None):
        raise ParseError(message, self.source, (token or self.token).start)

    def expect(self, kind):
        if self.token.kind != kind:
            self.fail(f"Expected {kind!r}")
        return self.take()

    def node(self, kind, value=None, args=(), start=0, end=0):
        self.nodes += 1
        depth = 1 + max((arg.depth for arg in args), default=0)
        if self.nodes > 1024 or depth > 64:
            raise ParseError("Expression exceeds the node or depth limit", self.source, start)
        return Node(kind, value, tuple(args), start, end, depth)

    def expression(self):
        left = self.binary(0)
        if self.token.kind == "op" and self.token.value in COMPARISONS:
            op = self.take()
            right = self.binary(0)
            left = self.node("compare", op.value, (left, right), left.start, right.end)
            if self.token.kind == "op" and self.token.value in COMPARISONS:
                self.fail("Comparisons cannot be chained; use separate expressions")
        return left

    def binary(self, minimum):
        left = self.primary()
        while self.token.kind == "op" and PRECEDENCE.get(self.token.value, -1) >= minimum:
            op = self.take()
            right = self.binary(PRECEDENCE[op.value] + 1)
            left = self.node("binary", op.value, (left, right), left.start, right.end)
        return left

    def primary(self):
        self.nesting += 1
        if self.nesting > 64:
            self.fail("Expression exceeds 64 nested groups or calls")
        try:
            return self._primary()
        finally:
            self.nesting -= 1

    def _primary(self):
        token = self.token
        if token.kind == "op" and token.value == "~":
            self.take()
            arg = self.primary()
            return self.node("not", args=(arg,), start=token.start, end=arg.end)
        if token.kind == "(":
            self.take()
            result = self.expression()
            self.expect(")")
            return result
        if token.kind == "id":
            self.take()
            return self.node("ref", {"id": token.value}, start=token.start, end=token.end)
        if token.kind == "number":
            self.take()
            return self.node("integer", token.value, start=token.start, end=token.end)
        if token.kind in {"name", "string"}:
            self.take()
            if token.kind == "name" and self.token.kind == "(":
                return self.call(token)
            if token.kind == "name" and self.token.kind == ":":
                self.take()
                term = self.expect("string")
                return self.node("ref", {"term": term.value, "lang": token.value}, start=token.start, end=term.end)
            if token.kind == "name" and token.value in {"U", "EMPTY"}:
                return self.node("constant", token.value, start=token.start, end=token.end)
            return self.node("ref", {"term": token.value}, start=token.start, end=token.end)
        self.fail("Expected a concept, function, U, EMPTY, or parenthesized expression")

    def call(self, token):
        name = token.value
        if name not in FUNCTIONS:
            self.fail(f"Unknown function {name!r}", token)
        self.expect("(")
        args = []
        if name in RELATION_FUNCTIONS:
            relation = self.token
            if relation.kind not in {"number", "name", "string"}:
                self.fail("Expected a relation code or alias, such as 23 or material")
            self.take()
            args.append(self.node("relation", str(relation.value), start=relation.start, end=relation.end))
            self.expect(",")
        if self.token.kind != ")":
            args.append(self.expression())
            while self.token.kind == ",":
                self.take()
                args.append(self.expression())
        end = self.expect(")").end
        if len(args) != FUNCTIONS[name]:
            self.fail(f"{name} expects {FUNCTIONS[name]} argument(s)", token)
        if name == "exact" and args[0].kind != "ref":
            self.fail("exact expects one concept reference", token)
        if name in FACT_FUNCTIONS and args[1].kind != "ref":
            self.fail(f"{name} expects one exact property target, not a set expression", token)
        return self.node("call", name, args, token.start, end)


def parse(source):
    """Parse a single expression, retaining character offsets for diagnostics."""
    if not isinstance(source, str):
        raise AlgebraError("Expression must be a string")
    if len(source) > 8192:
        raise ParseError("Expression exceeds 8192 characters", source, 8192)
    parser = _Parser(source)
    result = parser.expression()
    if parser.token.kind != "end":
        parser.fail("Unexpected trailing input; quote multiword terms")
    return result


def format_expression(node):
    """Unambiguous, parseable representation, including resolved ID expressions."""
    if node.kind == "ref":
        if "id" in node.value:
            return "#" + str(node.value["id"])
        prefix = node.value.get("lang", "")
        return (prefix + ":" if prefix else "") + json.dumps(node.value["term"], ensure_ascii=False)
    if node.kind in {"constant", "integer"}:
        return str(node.value)
    if node.kind == "relation":
        return json.dumps(node.value)
    if node.kind == "not":
        return "~(" + format_expression(node.args[0]) + ")"
    if node.kind in {"binary", "compare"}:
        return "(" + format_expression(node.args[0]) + " " + node.value + " " + format_expression(node.args[1]) + ")"
    if node.kind == "call":
        return node.value + "(" + ", ".join(map(format_expression, node.args)) + ")"
    raise AlgebraError("Unknown AST node kind")
