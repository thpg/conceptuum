"""Read-only graph snapshots and context-specific, evidence-preserving queries."""
from collections import defaultdict, deque, OrderedDict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from types import MappingProxyType
import unicodedata

from .syntax import AlgebraError


PROPERTY_CODES = frozenset({"15", "20", "21", "22", "23", "24", "25", "26", "27"})
RELATION_ALIASES = {
    "genus": "14", "essential": "15", "attribute": "20", "purpose": "21",
    "action": "22", "material": "23", "content": "24", "product": "25",
    "agent": "26", "patient": "27", "coextension": "30",
}


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


class UnknownConceptError(AlgebraError):
    pass


class AmbiguousConceptError(AlgebraError):
    def __init__(self, term, candidates):
        self.term = term
        self.candidates = candidates
        choices = "; ".join(f"#{c['id']} {c['name']} (U{c['context']})" for c in candidates)
        super().__init__(f"Ambiguous concept {term!r}: {choices}. Select a #ID.")


@dataclass(frozen=True)
class Concept:
    id: int
    name: str
    context: int


@dataclass(frozen=True)
class Edge:
    id: int
    subject: int
    code: str
    target: int
    context: int
    strength: object = None

    @property
    def positive(self):
        return self.strength is None or self.strength > 0


@dataclass(frozen=True)
class Fact:
    subject: int
    code: str
    target: int
    state: str
    evidence: tuple
    overridden: tuple


def _integer(value, description):
    if type(value) is not int or value <= 0:
        raise AlgebraError(f"{description} must be a positive integer")
    return value


class ConceptGraph:
    """One immutable data snapshot viewed through one relation context.

    Concept identities are global. The context selects edges, never a home
    parent or the unscoped concept_path cache. Algorithms tolerate graph cycles.
    """

    def __init__(self, snapshot, context=1):
        _integer(context, "Context")
        required = ("concept", "concept_term", "edge", "relevant", "universum")
        if not isinstance(snapshot, dict) or any(not isinstance(snapshot.get(t), list) for t in required):
            raise AlgebraError("Snapshot needs concept, concept_term, edge, relevant, and universum row lists")
        self.context = context
        try:
            universes = {r["id"]: r["nama"] for r in snapshot["universum"]}
            if context not in universes:
                raise AlgebraError(f"Unknown context U{context}; available: {sorted(universes)}")
            concepts = {}
            for row in snapshot["concept"]:
                cid = _integer(row["dharma"], "Concept ID")
                if cid in concepts or row["universum_id"] not in universes or not isinstance(row["nama"], str):
                    raise AlgebraError(f"Invalid or duplicate concept #{cid}")
                concepts[cid] = Concept(cid, row["nama"], row["universum_id"])
            self.concepts = MappingProxyType(concepts)
            self.universes = MappingProxyType(universes)
            self.ids = frozenset(concepts)
            self._terms = defaultdict(set)
            self._lookup = defaultdict(set)
            for concept in concepts.values():
                self._lookup[(None, normalize(concept.name))].add(concept.id)
            for row in snapshot["concept_term"]:
                cid, term, lang = row["concept_id"], row["term"], row["lang"]
                if cid not in concepts or not isinstance(term, str) or not isinstance(lang, str):
                    raise AlgebraError("Invalid concept_term row")
                self._terms[(cid, lang)].add(term)
                self._lookup[(lang, normalize(term))].add(cid)
                self._lookup[(None, normalize(term))].add(cid)
            rules = {}
            self._rule_names = defaultdict(set)
            for row in snapshot["relevant"]:
                code = str(row["kod"])
                if code in rules:
                    raise AlgebraError(f"Duplicate relation code {code}")
                rules[code] = bool(row.get("is_symmetric", 0))
                self._rule_names[normalize(row.get("long_name") or code)].add(code)
            self.rules = MappingProxyType(rules)
            edges, seen = [], set()
            for row in snapshot["edge"]:
                if row["status"] != "ok" or row["universum_id"] != context:
                    continue
                edge = Edge(_integer(row["id"], "Edge ID"), row["dh1"], str(row["kod"]),
                            row["dh2"], context, row.get("strength"))
                if edge.id in seen or edge.subject not in concepts or edge.target not in concepts or edge.code not in rules:
                    raise AlgebraError(f"Invalid, dangling, or duplicate accepted edge #{edge.id}")
                if edge.strength is not None and (type(edge.strength) is not int or not 0 <= edge.strength <= 100):
                    raise AlgebraError(f"Invalid strength on accepted edge #{edge.id}")
                seen.add(edge.id)
                edges.append(edge)
        except (KeyError, TypeError) as exc:
            raise AlgebraError("Malformed snapshot row or missing required field") from exc
        self.edges = tuple(sorted(edges, key=lambda e: e.id))
        self._up, self._down = defaultdict(list), defaultdict(list)
        self._genus_up, self._genus_down = defaultdict(list), defaultdict(list)
        self._out, self._incoming = defaultdict(set), defaultdict(set)
        self._assertions = defaultdict(lambda: defaultdict(list))
        for edge in self.edges:
            if edge.code in PROPERTY_CODES:
                self._assertions[(edge.code, edge.target)][edge.subject].append(edge)
            if not edge.positive:
                continue
            self._out[(edge.code, edge.subject)].add(edge.target)
            self._incoming[(edge.code, edge.target)].add(edge.subject)
            if self.rules[edge.code]:
                self._out[(edge.code, edge.target)].add(edge.subject)
                self._incoming[(edge.code, edge.subject)].add(edge.target)
            if edge.code == "14":
                self._up[edge.subject].append((edge.target, edge))
                self._down[edge.target].append((edge.subject, edge))
                self._genus_up[edge.subject].append((edge.target, edge))
                self._genus_down[edge.target].append((edge.subject, edge))
            elif edge.code == "30":
                for a, b in ((edge.subject, edge.target), (edge.target, edge.subject)):
                    self._up[a].append((b, edge))
                    self._down[a].append((b, edge))
        self._genus_cache = {}
        self._extent_cache = OrderedDict()
        self._property_cache = OrderedDict()

    @classmethod
    def from_json(cls, path, context=1):
        try:
            snapshot = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise AlgebraError("Cannot read the JSON graph snapshot") from exc
        return cls(snapshot, context=context)

    @classmethod
    def from_database(cls, context=1, **connection_options):
        """Load consistent SELECT results, roll back and close the connection.

        Credentials use the existing JNANA_* configuration. No maintenance
        method, concept_path rebuild, INSERT, UPDATE, or DELETE is invoked.
        """
        try:
            import pymysql
            from jnana_engine import DB
        except ImportError as exc:
            raise AlgebraError("Install requirements.txt for MariaDB access; JSON snapshots need no external packages") from exc
        except ValueError as exc:
            raise AlgebraError("Invalid JNANA_* database configuration") from exc

        options = dict(DB)
        options.update(connection_options)
        options["autocommit"] = False
        options.setdefault("connect_timeout", 10)
        options.setdefault("read_timeout", 30)
        try:
            connection = pymysql.connect(**options)
        except pymysql.MySQLError as exc:
            raise AlgebraError("Cannot connect to MariaDB; check JNANA_HOST, JNANA_PORT, JNANA_DATABASE, JNANA_USER and JNANA_PASSWORD") from exc
        queries = {
            "concept": "SELECT dharma,nama,universum_id FROM concept",
            "concept_term": "SELECT concept_id,term,lang FROM concept_term",
            "edge": "SELECT id,dh1,kod,dh2,universum_id,strength,status FROM edge",
            "relevant": "SELECT kod,long_name,is_symmetric FROM relevant",
            "universum": "SELECT id,nama FROM universum",
        }
        try:
            snapshot = {}
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT")
                for table, query in queries.items():
                    cursor.execute(query)
                    snapshot[table] = list(cursor.fetchall())
            return cls(snapshot, context=context)
        except pymysql.MySQLError as exc:
            raise AlgebraError("Cannot read the graph snapshot; check database availability and SELECT permissions") from exc
        finally:
            try:
                connection.rollback()
            finally:
                connection.close()

    def concept(self, cid, lang=None):
        if cid not in self.concepts:
            raise UnknownConceptError(f"Unknown concept #{cid}")
        concept = self.concepts[cid]
        terms = self._terms.get((cid, lang), ())
        label = min(terms, key=lambda t: (len(t), t.casefold(), t)) if terms else concept.name
        return {"id": cid, "name": label, "canonical_name": concept.name, "context": concept.context}

    def terms(self, cid, lang):
        """Exact stored terms, without falling back to another language."""
        self.concept(cid)
        return tuple(sorted(self._terms.get((cid, lang), ()), key=lambda term: (len(term), term.casefold(), term)))

    def resolve(self, reference, lang=None):
        if "id" in reference:
            cid = reference["id"]
            if type(cid) is not int or cid not in self.ids:
                raise UnknownConceptError(f"Unknown concept #{cid}")
            return cid
        term = reference["term"]
        language = reference.get("lang", lang)
        ids = self._lookup.get((language, normalize(term)), set())
        if not ids:
            suffix = f" in language {language!r}" if language else ""
            raise UnknownConceptError(f"Unknown concept {term!r}{suffix}; use an exact term or a #ID")
        if len(ids) != 1:
            raise AmbiguousConceptError(term, [self.concept(cid, language) for cid in sorted(ids)])
        return next(iter(ids))

    def relation(self, value, inheritable=False):
        code = RELATION_ALIASES.get(normalize(str(value)), str(value))
        if code not in self.rules:
            matches = self._rule_names.get(normalize(str(value)), set())
            if len(matches) != 1:
                raise AlgebraError(f"Unknown or ambiguous relation {value!r}; select a stored relation code")
            code = next(iter(matches))
        if inheritable and code not in PROPERTY_CODES:
            raise AlgebraError(f"Relation {code} is not an inheritable property (15 or 20-27); use subjects/related")
        return code

    @staticmethod
    def _reach(cid, links):
        seen = {cid}
        queue = deque([cid])
        while queue:
            for target, _ in links.get(queue.popleft(), ()):
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        return frozenset(seen)

    @staticmethod
    def _remember(cache, key, value, maximum):
        cache[key] = value
        cache.move_to_end(key)
        if len(cache) > maximum:
            cache.popitem(last=False)
        return value

    def extent(self, cid):
        """Root plus descendants via accepted positive 14 and bidirectional 30."""
        self.concept(cid)
        if cid in self._extent_cache:
            self._extent_cache.move_to_end(cid)
            return self._extent_cache[cid]
        return self._remember(self._extent_cache, cid, self._reach(cid, self._down), 128)

    def genus_ancestors(self, cid):
        """Reflexive genus-only closure; coextension does not copy attributes."""
        if cid not in self._genus_cache:
            self.concept(cid)
            self._genus_cache[cid] = self._reach(cid, self._genus_up)
        return self._genus_cache[cid]

    def navigate(self, ids, operation):
        result = set()
        for cid in ids:
            if operation == "parents":
                result.update(other for other, _ in self._genus_up.get(cid, ()))
            elif operation == "children":
                result.update(other for other, _ in self._genus_down.get(cid, ()))
            elif operation == "ancestors":
                result.update(self.genus_ancestors(cid) - {cid})
            elif operation == "descendants":
                result.update(self._reach(cid, self._genus_down) - {cid})
            else:
                raise AlgebraError("Unknown graph navigation operation")
        return frozenset(result)

    def project(self, code, ids, incoming=False):
        index = self._incoming if incoming else self._out
        return frozenset(other for cid in ids for other in index.get((code, cid), ()))

    def fact(self, subject, code, target):
        """Most-specific assertions for one exact (code, target) property.

        A stricter owner overrides its ancestor, regardless of path lengths.
        Incomparable owners are retained, so conflicting multiple inheritance
        never becomes an arbitrary first-parent or nearest-distance decision.
        """
        self.concept(subject)
        self.concept(target)
        code = self.relation(code, inheritable=True)
        by_owner = self._assertions.get((code, target), {})
        owners = self.genus_ancestors(subject).intersection(by_owner)
        effective = {
            owner for owner in owners
            if not any(owner != other and owner in self.genus_ancestors(other)
                       and other not in self.genus_ancestors(owner) for other in owners)
        }
        evidence = tuple(sorted((edge for owner in effective for edge in by_owner[owner]), key=lambda e: e.id))
        overridden = tuple(sorted((edge for owner in owners - effective for edge in by_owner[owner]), key=lambda e: e.id))
        positive = any(edge.positive for edge in evidence)
        negative = any(not edge.positive for edge in evidence)
        state = "conflict" if positive and negative else "positive" if positive else "negative" if negative else "unknown"
        return Fact(subject, code, target, state, evidence, overridden)

    def property_sets(self, code, target):
        code = self.relation(code, inheritable=True)
        self.concept(target)
        key = (code, target)
        if key in self._property_cache:
            self._property_cache.move_to_end(key)
            return self._property_cache[key]
        states = {state: set() for state in ("positive", "negative", "unknown", "conflict")}
        for cid in self.ids:
            states[self.fact(cid, code, target).state].add(cid)
        result = MappingProxyType({state: frozenset(ids) for state, ids in states.items()})
        return self._remember(self._property_cache, key, result, 32)

    def path(self, subject, ancestor, genus_only=False):
        links = self._genus_up if genus_only else self._up
        seen = {subject: None}
        queue = deque([subject])
        while queue and ancestor not in seen:
            current = queue.popleft()
            for target, edge in links.get(current, ()):
                if target not in seen:
                    seen[target] = (current, edge)
                    queue.append(target)
        if ancestor not in seen:
            return None
        path, current = [], ancestor
        while seen[current] is not None:
            previous, edge = seen[current]
            path.append(dict(asdict(edge), traversal_from=previous, traversal_to=current))
            current = previous
        return list(reversed(path))

    def explain_fact(self, subject, code, target):
        fact = self.fact(subject, code, target)
        return {
            "subject": subject, "relation": fact.code, "target": target,
            "context": self.context, "state": fact.state,
            "evidence": [{"edge": asdict(edge), "genus_path": self.path(subject, edge.subject, genus_only=True)}
                         for edge in fact.evidence],
            "overridden_edge_ids": [edge.id for edge in fact.overridden],
        }
