# -*- coding: utf-8 -*-
"""
jnana_engine.py — engine for the concept-relation knowledge base (jnana3).

Layers:
  storage    : concept / concept_term / edge / relevant / universum / concept_path
  validation : rules are read from `relevant` (signatures, symmetry, transitivity)
  inference  : concept_path (transitive closure of kod 14), inheritance
  interface  : verify / propose / approve / add_concept / add_genus /
               merge_concepts / rebuild / define
  taxonomy   : kod 14 is a DAG — two genera on one concept, universum on the edge

Usage:
    eng = JnanaEngine(pref_lang="en")
    eng.verify("Linux", "operating system")
    eng.propose("Docker", "74", "computer network", strength=90, rationale="needs network")
    eng.approve([id1, id2])
    eng.rebuild(); eng.define()

pref_lang selects the display language for definitions (terms of that language
from concept_term replace the concept label when available).
"""

import pymysql
from collections import defaultdict

DB = dict(host="127.0.0.1", user="root", password="123", database="jnana3", charset="utf8")
KOD_ISA = "14"
SYMMETRIC_DEFAULT = {"61", "62", "63", "64", "73"}


def _norm(s):
    """Normalize for matching: lowercase, ё -> е."""
    return s.lower().replace("ё", "е")


_MORPH = None
_LEMMA_CACHE = {}


def _lemma(word):
    """Normal form of a Russian word via pymorphy3 (lazy, cached).
    Non-Cyrillic words and missing library -> the word itself."""
    if not any("Ѐ" <= c <= "ӿ" for c in word):
        return word
    if word in _LEMMA_CACHE:
        return _LEMMA_CACHE[word]
    global _MORPH
    if _MORPH is None:
        try:
            import pymorphy3
            _MORPH = pymorphy3.MorphAnalyzer()
        except Exception:
            _MORPH = False
    lemma = _MORPH.parse(word)[0].normal_form if _MORPH else word
    _LEMMA_CACHE[word] = lemma
    return lemma


def _term_key(term):
    """Lemmatized key of a term: каждое русское слово -> начальная форма."""
    return " ".join(_lemma(w) for w in _norm(term).split())


def _pick_disp(lang, terms):
    """English 'to …' is an infinitive term, not the display label."""
    if lang != "en":
        return terms[0] if terms else None
    stems, rest, stripped = set(), [], None
    for t in terms:
        low = t.strip().lower()
        if low.startswith("to "):
            s = t.strip()[3:].strip()
            if s:
                stems.add(s.lower())
                if not stripped:
                    stripped = s
            continue
        rest.append(t)
    for t in rest:
        if t.lower() not in stems:
            return t
    if rest:
        return rest[0]
    return stripped


def _prefix_match(a, b):
    """Morphological near-match without a stemmer:
    - equal after normalization, or
    - common prefix >= 4 chars covering the shorter word up to its last
      letter (melts~melt, договоров~договор), or
    - same first 2 letters + equal consonant skeleton, for vowel-drop
      roots (камня~камень, суд~суда).
    Length difference over 3 chars is rejected (существуют !~ сущее)."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 3:
        return False
    cp = 0
    for x, y in zip(a, b):
        if x != y:
            break
        cp += 1
    if cp >= 4 and cp >= min(len(a), len(b)) - 1:
        return True
    skel = lambda s: "".join(c for c in s if c not in "аеёиоуыэюяьъaeiouy")
    return a[:2] == b[:2] and len(skel(a)) >= 2 and skel(a) == skel(b)


class JnanaEngine:
    def __init__(self, autocommit=False, pref_lang=None, **conn_kw):
        self.pref_lang = pref_lang
        cfg = {**DB, **conn_kw}
        self.conn = pymysql.connect(**cfg, autocommit=autocommit)
        self.cur = self.conn.cursor()
        self.reload()

    # ---------- loading into memory ----------
    def reload(self):
        self.cur.execute("SELECT dharma, nama, universum_id FROM concept")
        self.names = {}
        self.concept_u = {}
        for d, n, u in self.cur.fetchall():
            self.names[d] = n
            self.concept_u[d] = u
        self.id_of = {n: d for d, n in self.names.items()}
        self.cur.execute("SELECT concept_id, term, lang FROM concept_term")
        self.term2id = {}
        self.terms_of = defaultdict(list)
        self.term_index = []           # (normalized term, lang, cid) for fuzzy match
        self.lemma2ids = defaultdict(set)   # (lemmatized key, lang) -> cids
        for cid, term, lang in self.cur.fetchall():
            t = _norm(term)
            self.term2id[(term.lower(), lang)] = cid
            self.term2id.setdefault(term.lower(), cid)
            self.term2id.setdefault((t, lang), cid)
            self.term2id.setdefault(t, cid)
            self.terms_of[cid].append((term, lang))
            self.term_index.append((t, lang, cid))
            self.lemma2ids[(_term_key(term), lang)].add(cid)
        # display names: pref_lang terms override the default label.
        # English "to …" infinitives are the same as Russian инфинитивы —
        # a term, not the label. Prefer a noun/gerund; if none, strip "to ".
        self.disp = dict(self.names)
        if self.pref_lang:
            self.cur.execute(
                "SELECT concept_id, term FROM concept_term WHERE lang=%s",
                (self.pref_lang,))
            by = defaultdict(list)
            for cid, term in self.cur.fetchall():
                by[cid].append(term)
            for cid, terms in by.items():
                picked = _pick_disp(self.pref_lang, terms)
                if picked:
                    self.disp[cid] = picked
        self.cur.execute(
            "SELECT kod, long_name, sig_subject, sig_subject2, sig_subject3, sig_subject4,"
            " sig_object, sig_object2, sig_object3, sig_object4,"
            " is_symmetric, is_transitive FROM relevant")
        self.rules = {r[0]: dict(name=r[1], ss=r[2], ss2=r[3], ss3=r[4], ss4=r[5],
                                 so=r[6], so2=r[7], so3=r[8], so4=r[9],
                                 sym=bool(r[10]), trans=bool(r[11]))
                      for r in self.cur.fetchall()}
        self.cur.execute("SELECT id, nama FROM universum")
        self.uni_names = {i: n for i, n in self.cur.fetchall()}
        self.cur.execute("SELECT dh1, dh2, kod, strength, status, id FROM edge")
        self.edges = self.cur.fetchall()
        # ISA is a DAG: one concept may have several genera, each tagged
        # with a universum. self.parent keeps a single "home" parent
        # (edge universum matching concept.universum_id, else the first)
        # so older callers (fill_llm leaf grouping) keep working.
        self.parents = defaultdict(list)   # child -> [(parent, universum_id)]
        self.children_map = defaultdict(list)
        self.parent = {}
        self.cur.execute(
            "SELECT dh1, dh2, universum_id FROM edge WHERE kod=%s AND status='ok'",
            (KOD_ISA,))
        for a, b, u in self.cur.fetchall():
            self.parents[a].append((b, u))
            self.children_map[b].append(a)
        for a, pairs in self.parents.items():
            home = self.concept_u.get(a)
            pick = next((p for p, u in pairs if u == home), pairs[0][0])
            self.parent[a] = pick
        self.cur.execute("SELECT ancestor, descendant, depth FROM concept_path")
        self.anc = defaultdict(dict)
        for a, d, depth in self.cur.fetchall():
            self.anc[d][a] = depth
        return self

    # processed levels (concept.processed, 0–3; never a closed door):
    #   0  not filled
    #   1  genus and species (taxonomy)
    #   2  essential and specific properties (kod 15, 20–27)
    #   3  parallel relations (30/40, 61–64, 70–74)
    PROC_SPEC = ("15", "20", "21", "22", "23", "24", "25", "26", "27")
    PROC_PARA = ("30", "40", "61", "62", "63", "64", "70", "71", "72", "73", "74")

    def set_processed(self, cid, level=1):
        """Set fill level. bool True/False kept as 1/0 for old callers.
        Does NOT mean closed — later levels and extra edges stay possible."""
        if isinstance(level, bool):
            level = 1 if level else 0
        level = int(level)
        if level < 0 or level > 3:
            raise ValueError("processed level must be 0..3")
        self.cur.execute("UPDATE concept SET processed=%s WHERE dharma=%s",
                         (level, cid))

    def unprocessed(self, universum_id=None, below=1):
        """Concepts with processed < below (default: still at 0)."""
        q = "SELECT dharma, nama FROM concept WHERE processed<%s"
        args = [int(below)]
        if universum_id:
            q += " AND universum_id=%s"
            args.append(int(universum_id))
        self.cur.execute(q, args)
        return self.cur.fetchall()

    def raise_processed_from_edges(self):
        """Raise 1→2 if the concept has essential/specific edges,
        2→3 if it also has parallel (non-isa) relations. Never lowers,
        never invents level 1 (taxonomy flag stays explicit)."""
        spec, para = set(), set()
        for a, b, k, s, st, i in self.edges:
            if st != "ok":
                continue
            if k in self.PROC_SPEC:
                spec.add(a)
            elif k in self.PROC_PARA:
                para.add(a)
        n2 = n3 = 0
        self.cur.execute("SELECT dharma, processed FROM concept")
        for cid, p in self.cur.fetchall():
            p = int(p or 0)
            np = p
            if p >= 1 and cid in spec and np < 2:
                np = 2
            if np >= 2 and cid in para and np < 3:
                np = 3
            if np != p:
                self.cur.execute("UPDATE concept SET processed=%s WHERE dharma=%s",
                                 (np, cid))
                if np == 2:
                    n2 += 1
                else:
                    n3 += 1
        self.commit()
        return n2, n3

    def commit(self):
        self.conn.commit()
        self.reload()

    def close(self):
        self.conn.close()

    # ---------- navigation ----------
    def resolve(self, term, lang=None):
        if lang:
            return self.term2id.get((term.lower(), lang))
        return self.term2id.get(term.lower())

    def resolve_all(self, term, lang=None):
        """All concepts matching the term (homonyms across universes).
        Returns a list of concept ids, possibly empty."""
        t = term.lower()
        seen, out = set(), []
        self.cur.execute(
            "SELECT DISTINCT concept_id FROM concept_term WHERE LOWER(term)=%s"
            + (" AND lang=%s" if lang else ""),
            (t, lang) if lang else (t,))
        for (cid,) in self.cur.fetchall():
            if cid not in seen:
                seen.add(cid)
                out.append(cid)
        return out

    def resolve_fuzzy(self, token, lang=None):
        """Exact -> lemmatized -> prefix/skeleton match of a single word."""
        t = _norm(token)
        r = self.resolve_all(t, lang)
        if r:
            return r
        # lemmatized lookup (pymorphy3), e.g. камня -> камень
        key = _lemma(t)
        if key != t or any("Ѐ" <= c <= "ӿ" for c in t):
            cids = set()
            for lg in ([lang] if lang else ()):
                cids |= self.lemma2ids.get((key, lg), set())
            if not lang:
                for (k, _lg), ids in self.lemma2ids.items():
                    if k == key:
                        cids |= ids
            if cids:
                return sorted(cids)
        # last resort: prefix/skeleton scan (English inflection, typos)
        seen, out = set(), []
        for term, lg, cid in self.term_index:
            if " " in term or (lang and lg != lang):
                continue
            if _prefix_match(t, term) and cid not in seen:
                seen.add(cid)
                out.append(cid)
        return out

    def resolve_phrase_fuzzy(self, phrase, lang=None):
        """Word-wise morphological match of a multiword term."""
        words = [_norm(w) for w in phrase.split()]
        r = self.resolve_all(_norm(phrase), lang)
        if r:
            return r
        # lemmatized phrase lookup: юридическую ответственность -> ключ термина
        key = " ".join(_lemma(w) for w in words)
        cids = set()
        if lang:
            cids |= self.lemma2ids.get((key, lang), set())
        else:
            for (k, _lg), ids in self.lemma2ids.items():
                if k == key:
                    cids |= ids
        if cids:
            return sorted(cids)
        # last resort: word-wise prefix match
        seen, out = set(), []
        for term, lg, cid in self.term_index:
            tw = term.split()
            if len(tw) != len(words) or (lang and lg != lang):
                continue
            if all(_prefix_match(w, t) for w, t in zip(words, tw)) and cid not in seen:
                seen.add(cid)
                out.append(cid)
        return out

    def ancestors(self, cid):
        return self.anc.get(cid, {})

    def children(self, cid):
        return list(self.children_map.get(cid, []))

    def genera(self, cid, universum_id=None):
        """Direct genus links: list of (parent_id, universum_id)."""
        pairs = self.parents.get(cid, [])
        if universum_id is None:
            return list(pairs)
        return [(p, u) for p, u in pairs if u == universum_id]

    def in_subtree(self, cid, anchor, universum_id=None):
        """True if anchor is cid or an ancestor of cid.
        Walks the live ISA DAG (all genera, or only those of universum_id).
        Unlike concept_path, this is current even before rebuild()."""
        if cid == anchor:
            return True
        seen, stack, guard = set(), [cid], 0
        while stack and guard < 256:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            if x == anchor:
                return True
            for p, u in self.parents.get(x, []):
                if universum_id is None or u == universum_id:
                    stack.append(p)
            guard += 1
        return False

    # ---------- verify ----------
    def verify(self, t1, t2, lang=None):
        """Check the statement "t1 is related to t2" against the graph.
        Returns (verdict, detail, missing_terms)."""
        i1 = self.resolve(t1, lang)
        i2 = self.resolve(t2, lang)
        missing = [t for t, i in ((t1, i1), (t2, i2)) if i is None]
        if missing:
            return "unknown", f"unknown terms: {', '.join(missing)}", missing
        if i2 in self.anc.get(i1, {}):
            return "yes", f"{t1} is a kind of '{t2}' (depth {self.anc[i1][i2]})", []
        if i1 in self.anc.get(i2, {}):
            return "reverse", f"reversed: '{t2}' is a kind of '{t1}'", []
        adj = defaultdict(list)
        for a, b, k, s, st, i in self.edges:
            if st != "ok":
                continue
            adj[a].append((b, k, "->"))
            adj[b].append((a, k, "<-"))
        for b, k, d in adj[i1]:
            if b == i2:
                return "yes", f"{t1} {d}[{self.rules[k]['name']}] {t2}", []
        for z, k1, d1 in adj[i1]:
            for b, k2, d2 in adj[z]:
                if b == i2:
                    return ("indirect",
                            f"{t1} {d1}[{self.rules[k1]['name']}] {self.disp[z]} "
                            f"{d2}[{self.rules[k2]['name']}] {t2}", [])
        return "no", f"no relation found between '{t1}' and '{t2}'", []

    # ---------- validation ----------
    def validate(self, a, kod, b, universum_id=None, strength=None):
        """(ok, message). Rules are read from `relevant`."""
        kod = str(kod)
        rule = self.rules.get(kod)
        if rule is None:
            return False, f"unknown kod {kod}"
        if a is None or b is None:
            return False, "concept not found"
        if rule["sym"] and a > b:
            a, b = b, a
        u = universum_id or self.concept_u.get(a, 1)
        self.cur.execute(
            "SELECT universum_id FROM edge WHERE dh1=%s AND dh2=%s AND kod=%s AND status<>'rejected'",
            (a, b, kod))
        existing_u = {row[0] for row in self.cur.fetchall()}
        if u in existing_u:
            return False, "duplicate"
        if existing_u and kod != KOD_ISA:
            return False, "duplicate"
        if kod == KOD_ISA:
            if self.in_subtree(a, b) or self.in_subtree(b, a):
                return False, "cycle in hierarchy"
        if rule["ss"] is not None:
            ok_subj = any(rule.get(k) and self.in_subtree(a, rule[k])
                          for k in ("ss", "ss2", "ss3", "ss4"))
            if not ok_subj:
                return False, f"signature: subject must be in subtree #{rule['ss']}"
        if rule["so"] is not None:
            ok_obj = any(rule.get(k) and self.in_subtree(b, rule[k])
                         for k in ("so", "so2", "so3", "so4"))
            if not ok_obj:
                return False, f"signature: object must be in subtree #{rule['so']}"
        # inheritance redundancy (warning, not a refusal):
        # ancestor already carries the same code + same object.
        # strength == 0 is an explicit negation/exception -> not redundant.
        warn = None
        if kod in ("70", "20", "21", "22", "23", "24", "25", "26", "27") \
                and strength != 0:
            have = {(x, k, y) for x, y, k, s, st, i in self.edges
                    if st == "ok"}
            for anc in self.ancestors(a):
                if anc != a and (anc, kod, b) in have:
                    warn = f"redundant: inherited from '{self.disp[anc]}'"
                    break
        return True, warn or "ok"

    # ---------- propose / approve ----------
    def propose(self, t1, kod, t2, strength=None, rationale=None,
                universum_id=None, source="llm", auto=False):
        """Propose an edge. auto=True -> immediately status='ok'."""
        def rid(t):
            if isinstance(t, int):
                return t
            return self.resolve(t) or (self.resolve_fuzzy(t) or [None])[0]
        a, b = rid(t1), rid(t2)
        ok, msg = self.validate(a, str(kod), b, universum_id, strength=strength)
        if not ok:
            return None, f"REJECTED {t1}->{t2} [{kod}]: {msg}"
        if self.rules[str(kod)]["sym"] and a > b:
            a, b = b, a
        u = universum_id or self.concept_u.get(a, 1)
        status = "ok" if auto else "candidate"
        try:
            self.cur.execute(
                "INSERT INTO edge (dh1,kod,dh2,universum_id,strength,status,source,rationale)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (a, str(kod), b, u, strength, status, source, rationale))
        except pymysql.err.IntegrityError:
            return None, f"REJECTED {t1}->{t2} [{kod}]: duplicate"
        eid = self.cur.lastrowid
        self.reload()
        return eid, f"{'ACCEPTED' if auto else 'CANDIDATE'} {t1} —[{kod}]→ {t2} (#{eid})" + (
            f" [warn: {msg}]" if msg != "ok" else "")

    def approve(self, edge_ids, accept=True):
        status = "ok" if accept else "rejected"
        self.cur.executemany("UPDATE edge SET status=%s WHERE id=%s",
                             [(status, i) for i in edge_ids])
        self.commit()
        return len(edge_ids)

    def add_genus(self, cid, parent, universum_id=None, auto=True):
        """Attach a (possibly additional) genus to an existing concept.
        universum_id is stored on the kod-14 edge — two discourses, one node."""
        pid = self.resolve(parent) if isinstance(parent, str) else parent
        if pid is None:
            return None, f"parent '{parent}' not found"
        if cid not in self.names:
            return None, f"concept {cid} not found"
        u = universum_id if universum_id is not None else self.concept_u.get(cid, 1)
        for p, u0 in self.parents.get(cid, []):
            if p == pid and u0 == u:
                return None, "already has this genus"
        return self.propose(cid, KOD_ISA, pid, universum_id=u,
                            source="genus", auto=auto)

    def merge_concepts(self, src, dst, keep_genus=False, reload=True):
        """Absorb src into dst. Terms of src become terms of dst; the src
        nama is kept as a ru term. Non-isa edges are retargeted. isa of src
        is dropped unless keep_genus (then transferred as extra genera of
        dst). Self-loops and unique-key clashes are deleted. Does not
        rebuild() — caller should rebuild+define after a batch."""
        if src == dst:
            return False, "same concept"
        if src not in self.names or dst not in self.names:
            return False, "concept not found"
        self.cur.execute(
            "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')",
            (dst, self.names[src]))
        self.cur.execute("SELECT term, lang FROM concept_term WHERE concept_id=%s", (src,))
        for term, lang in self.cur.fetchall():
            self.cur.execute(
                "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
                (dst, term, lang))
        self.cur.execute(
            "SELECT id, dh1, dh2, kod, universum_id FROM edge WHERE dh1=%s OR dh2=%s",
            (src, src))
        for eid, a, b, kod, u in self.cur.fetchall():
            new_a = dst if a == src else a
            new_b = dst if b == src else b
            drop = False
            if new_a == new_b:
                drop = True
            elif kod == KOD_ISA and a == src and not keep_genus:
                drop = True
            else:
                self.cur.execute(
                    "SELECT id FROM edge WHERE dh1=%s AND dh2=%s AND kod=%s AND universum_id=%s AND id<>%s",
                    (new_a, new_b, kod, u, eid))
                if self.cur.fetchone():
                    drop = True
            if drop:
                self.cur.execute("DELETE FROM edge WHERE id=%s", (eid,))
            else:
                self.cur.execute("UPDATE edge SET dh1=%s, dh2=%s WHERE id=%s",
                                 (new_a, new_b, eid))
        self.cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (src,))
        self.cur.execute("DELETE FROM concept_path WHERE ancestor=%s OR descendant=%s",
                         (src, src))
        self.cur.execute("DELETE FROM concept WHERE dharma=%s", (src,))
        if reload:
            self.reload()
        return True, f"merged {src} -> {dst}"

    def rename_concept(self, cid, new_nama, reload=True):
        """Change the canonical label. Old nama stays as a ru term.
        If another concept already has new_nama, refuse — merge instead."""
        if cid not in self.names:
            return False, "concept not found"
        old = self.names[cid]
        if old == new_nama:
            return True, "same name"
        other = [d for d, n in self.names.items() if n == new_nama and d != cid]
        if other:
            return False, f"name taken by {other[0]}"
        self.cur.execute("UPDATE concept SET nama=%s WHERE dharma=%s", (new_nama, cid))
        self.cur.execute(
            "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')",
            (cid, old))
        self.cur.execute(
            "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')",
            (cid, new_nama))
        self.names[cid] = new_nama
        if reload:
            self.reload()
        return True, f"renamed {old} -> {new_nama}"

    # ---------- add_concept ----------
    def add_concept(self, nama, parent, lang="en", universum_id=None,
                    passport=None, terms=None, auto=True):
        """New concept + genus edge. parent — name or id.
        passport: dict(vol_ed=.., cont_abs=.., ...); terms: [(term, lang), ...]
        Same nama in the same universum: return existing and attach the
        genus if it is a new one. Same nama in another universum: homonym
        (different meaning) — a new node."""
        if isinstance(parent, str):
            pid = self.resolve(parent)
        else:
            pid = parent
        if pid is None:
            return None, f"parent '{parent}' not found"
        u = universum_id or self.concept_u.get(pid, 1)
        for did, n in self.names.items():
            if n == nama and self.concept_u.get(did) == u:
                self.add_genus(did, pid, universum_id=u, auto=auto)
                return did, f"already exists: {nama}"
        cid = max(self.names) + 1 if self.names else 1
        cols = dict(vol_zero=0, vol_ed=0, vol_countable=None, vol_sobir=0,
                    vol_sootn=0, cont_konkr=None, cont_abs=None, cont_empir=1)
        if passport:
            cols.update(passport)
        self.cur.execute(
            "INSERT INTO concept (dharma,nama,universum_id,vol_zero,vol_ed,vol_countable,"
            "vol_sobir,vol_sootn,cont_konkr,cont_abs,cont_empir)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (cid, nama, u, cols["vol_zero"], cols["vol_ed"], cols["vol_countable"],
             cols["vol_sobir"], cols["vol_sootn"], cols["cont_konkr"],
             cols["cont_abs"], cols["cont_empir"]))
        self.cur.execute("INSERT INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
                         (cid, nama, lang))
        for term, lg in (terms or []):
            self.cur.execute(
                "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
                (cid, term, lg))
        self.cur.execute(
            "INSERT INTO edge (dh1,kod,dh2,universum_id,status,source)"
            " VALUES (%s,'14',%s,%s,%s,'llm')",
            (cid, pid, u, "ok" if auto else "candidate"))
        self.reload()
        return cid, f"+concept {nama} -> {self.names[pid]} (u{u})"

    # ---------- rebuild ----------
    def rebuild(self):
        """Rebuild the transitive closure concept_path over the ISA DAG.
        Diamond paths keep the shortest depth. Universum is not stored on
        the path (a descendant in any discourse is still a descendant)."""
        up = defaultdict(list)
        self.cur.execute("SELECT dh1, dh2 FROM edge WHERE kod='14' AND status='ok'")
        for a, b in self.cur.fetchall():
            up[a].append(b)
        pairs = {}
        for start in list(up):
            seen = {start: 0}
            stack = [(start, 0)]
            while stack:
                x, d = stack.pop()
                if d >= 25:
                    continue
                for p in up.get(x, []):
                    nd = d + 1
                    if p in seen and seen[p] <= nd:
                        continue
                    seen[p] = nd
                    key = (p, start)
                    if key not in pairs or pairs[key] > nd:
                        pairs[key] = nd
                    stack.append((p, nd))
        self.cur.execute("DELETE FROM concept_path")
        if pairs:
            self.cur.executemany("INSERT INTO concept_path VALUES (%s,%s,%s)",
                                 [(a, b, d) for (a, b), d in pairs.items()])
        self.commit()
        return len(pairs)

    # ---------- define ----------
    LBL_OUT = {"15": "essential attribute", "20": "attribute",
               "30": "coextensive with", "40": "overlaps",
               "70": "produces", "71": "hinders",
               "72": "precedes", "73": "accompanies", "74": "depends on",
               "21": "purpose", "22": "capable of", "23": "made of",
               "24": "holds", "25": "acts upon", "26": "intended for",
               "27": "directed at", "63": "opposite", "62": "mutual with",
               "61": "coordinate with"}
    LBL_IN = {"70": "produced by", "72": "follows", "22": "bearer",
              "23": "material of", "24": "contained in", "25": "handled by",
              "26": "used by", "27": "object of", "74": "needed for"}

    @staticmethod
    def _attr_band(s):
        """Степень атрибуции (код 20) словами, как раньше давали коды 21-27.
        strength == 0 — явное отрицание/исключение (пингвин не летает)."""
        if s is None:
            return "attribute"
        if s == 0:
            return "no"
        return ("inherent" if s >= 90 else "typical" if s >= 50
                else "sometimes" if s >= 10 else "rarely")

    def define(self):
        """Regenerate the definition cache concept.defin. Returns weak concepts."""
        out_e, in_e = defaultdict(list), defaultdict(list)
        children = defaultdict(list)
        for a, b, k, s, st, i in self.edges:
            if st != "ok":
                continue
            if k == KOD_ISA:
                children[b].append(a)
            else:
                out_e[a].append((k, b, s))
                in_e[b].append((k, a, s))
        weak = []
        for d, n in self.disp.items():
            rods = self.parents.get(d, [])
            spec = []
            for k, t, s in sorted(out_e.get(d, [])):
                if k in self.LBL_OUT:
                    lbl = self._attr_band(s) if k == "20" else self.LBL_OUT[k]
                    if s == 0 and k != "20":
                        lbl = "not " + lbl
                    spec.append(f"{lbl}: {self.disp[t]}"
                                + (f" ({s}%)" if s else ""))
            for k, f, s in sorted(in_e.get(d, [])):
                if s == 0:
                    continue  # отрицание — факт о субъекте, не об объекте
                if k in self.rules and self.rules[k]["sym"] and k in self.LBL_OUT:
                    spec.append(f"{self.LBL_OUT[k]}: {self.disp[f]}")
                elif k in self.LBL_IN:
                    spec.append(f"{self.LBL_IN[k]}: {self.disp[f]}")
            kids = [self.disp[c] for c in sorted(children.get(d, []),
                                                 key=lambda x: self.disp[x])]
            if not rods:
                rod_s = "universe (no genus)"
            elif len(rods) == 1:
                rod_s = self.disp[rods[0][0]]
            else:
                bits = []
                for pid, uid in rods:
                    un = self.uni_names.get(uid, str(uid))
                    bits.append(f"{self.disp[pid]} [{un}]")
                rod_s = "; ".join(bits)
            defin = f"{n} — {rod_s}"
            if spec:
                defin += "; " + "; ".join(spec)
            if kids:
                defin += ". Species: " + ", ".join(kids)
            self.cur.execute("UPDATE concept SET defin=%s WHERE dharma=%s",
                             (defin[:1000], d))
            if not spec and not kids and rods:
                weak.append(n)
        self.commit()
        return weak

    # ---------- statistics ----------
    def stats(self):
        self.cur.execute("SELECT COUNT(*) FROM concept")
        c = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM edge")
        e = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM edge WHERE status='candidate'")
        cand = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM concept_path")
        p = self.cur.fetchone()[0]
        self.cur.execute("SELECT universum_id, COUNT(*) FROM concept GROUP BY universum_id")
        by_u = dict(self.cur.fetchall())
        self.cur.execute("SELECT processed, COUNT(*) FROM concept GROUP BY processed")
        by_p = {int(k): n for k, n in self.cur.fetchall()}
        return dict(concepts=c, edges=e, candidates=cand, paths=p,
                    by_universum=by_u, by_processed=by_p)


if __name__ == "__main__":
    eng = JnanaEngine()
    print(eng.stats())
