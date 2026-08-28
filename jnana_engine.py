# -*- coding: utf-8 -*-
"""
jnana_engine.py — engine for the concept-relation knowledge base (jnana3).

Layers:
  storage    : concept / concept_term / edge / relevant / universum / concept_path
  validation : rules are read from `relevant` (signatures, symmetry, transitivity)
  inference  : concept_path (transitive closure of kod 14), inheritance
  interface  : verify / propose / approve / add_concept / rebuild / define

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
        # display names: pref_lang terms override the default label
        self.disp = dict(self.names)
        if self.pref_lang:
            self.cur.execute("SELECT concept_id, term FROM concept_term WHERE lang=%s",
                             (self.pref_lang,))
            for cid, term in self.cur.fetchall():
                self.disp[cid] = term
        self.cur.execute(
            "SELECT kod, long_name, sig_subject, sig_subject2, sig_subject3, sig_subject4,"
            " sig_object, sig_object2, sig_object3, sig_object4,"
            " is_symmetric, is_transitive FROM relevant")
        self.rules = {r[0]: dict(name=r[1], ss=r[2], ss2=r[3], ss3=r[4], ss4=r[5],
                                 so=r[6], so2=r[7], so3=r[8], so4=r[9],
                                 sym=bool(r[10]), trans=bool(r[11]))
                      for r in self.cur.fetchall()}
        self.cur.execute("SELECT dh1, dh2, kod, strength, status, id FROM edge")
        self.edges = self.cur.fetchall()
        self.parent = {a: b for a, b, k, s, st, i in self.edges
                       if k == KOD_ISA and st == "ok"}
        self.cur.execute("SELECT ancestor, descendant, depth FROM concept_path")
        self.anc = defaultdict(dict)
        for a, d, depth in self.cur.fetchall():
            self.anc[d][a] = depth
        return self

    def set_processed(self, cid, flag=True):
        """Mark a concept as processed: genus, general properties and
        species have been specified. Does NOT mean closed — side relations
        and additions remain possible."""
        self.cur.execute("UPDATE concept SET processed=%s WHERE dharma=%s",
                         (1 if flag else 0, cid))

    def unprocessed(self, universum_id=None):
        """Concepts still awaiting a fill pass (frontier for filling)."""
        q = "SELECT dharma, nama FROM concept WHERE processed=0"
        if universum_id:
            q += f" AND universum_id={int(universum_id)}"
        self.cur.execute(q)
        return self.cur.fetchall()

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
        return [a for a, b in self.parent.items() if b == cid]

    def in_subtree(self, cid, anchor):
        # walk the live parent chain (self.parent is rebuilt on every reload,
        # unlike concept_path which is only refreshed by rebuild())
        x, guard = cid, 0
        while x is not None and guard < 64:
            if x == anchor:
                return True
            x = self.parent.get(x)
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
    def validate(self, a, kod, b, universum_id=None):
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
        for x, y, k, s, st, i in self.edges:
            if (x, y, k) == (a, b, kod):
                return False, "duplicate"
        if kod == KOD_ISA:
            if b in self.anc.get(a, {}) or a in self.anc.get(b, {}):
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
        # inheritance redundancy (warning, not a refusal)
        warn = None
        if kod in ("70", "80", "82", "83"):
            for x, y, k, s, st, i in self.edges:
                if x == a and k == kod and y != b and self.in_subtree(b, y):
                    warn = f"redundant: inherited from '{self.disp[y]}'"
        return True, warn or "ok"

    # ---------- propose / approve ----------
    def propose(self, t1, kod, t2, strength=None, rationale=None,
                universum_id=None, source="llm", auto=False):
        """Propose an edge. auto=True -> immediately status='ok'."""
        a = self.resolve(t1) if not isinstance(t1, int) else t1
        b = self.resolve(t2) if not isinstance(t2, int) else t2
        ok, msg = self.validate(a, str(kod), b, universum_id)
        if not ok:
            return None, f"REJECTED {t1}->{t2} [{kod}]: {msg}"
        if self.rules[str(kod)]["sym"] and a > b:
            a, b = b, a
        u = universum_id or self.concept_u.get(a, 1)
        status = "ok" if auto else "candidate"
        self.cur.execute(
            "INSERT INTO edge (dh1,kod,dh2,universum_id,strength,status,source,rationale)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (a, str(kod), b, u, strength, status, source, rationale))
        eid = self.cur.lastrowid
        if auto:
            self.reload()
        return eid, f"{'ACCEPTED' if auto else 'CANDIDATE'} {t1} —[{kod}]→ {t2} (#{eid})" + (
            f" [warn: {msg}]" if msg != "ok" else "")

    def approve(self, edge_ids, accept=True):
        status = "ok" if accept else "rejected"
        self.cur.executemany("UPDATE edge SET status=%s WHERE id=%s",
                             [(status, i) for i in edge_ids])
        self.commit()
        return len(edge_ids)

    # ---------- add_concept ----------
    def add_concept(self, nama, parent, lang="en", universum_id=None,
                    passport=None, terms=None, auto=True):
        """New concept + genus edge. parent — name or id.
        passport: dict(vol_ed=.., cont_abs=.., ...); terms: [(term, lang), ...]"""
        if isinstance(parent, str):
            pid = self.resolve(parent)
        else:
            pid = parent
        if pid is None:
            return None, f"parent '{parent}' not found"
        if nama in self.id_of:
            return self.id_of[nama], f"already exists: {nama}"
        cid = max(self.names) + 1
        u = universum_id or self.concept_u.get(pid, 1)
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
        """Rebuild the transitive closure concept_path."""
        self.cur.execute("SELECT dh1, dh2 FROM edge WHERE kod='14' AND status='ok'")
        parent = dict(self.cur.fetchall())
        pairs = {}
        for start in parent:
            x, d = start, 1
            while x in parent:
                key = (parent[x], start)
                if key not in pairs or pairs[key] > d:
                    pairs[key] = d
                x = parent[x]
                d += 1
                if d > 25:
                    break
        self.cur.execute("DELETE FROM concept_path")
        self.cur.executemany("INSERT INTO concept_path VALUES (%s,%s,%s)",
                             [(a, b, d) for (a, b), d in pairs.items()])
        self.commit()
        return len(pairs)

    # ---------- define ----------
    LBL_OUT = {"15": "essential attribute", "21": "inherent", "23": "typical",
               "25": "sometimes", "27": "rarely", "70": "produces", "71": "hinders",
               "72": "precedes", "73": "accompanies", "74": "depends on",
               "80": "purpose", "81": "material", "82": "capable of",
               "83": "directed at", "63": "opposite", "62": "mutual with",
               "61": "coordinate with"}
    LBL_IN = {"70": "produced by", "72": "follows", "82": "bearer",
              "83": "object of", "74": "needed for"}

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
            rod = self.parent.get(d)
            spec = []
            for k, t, s in sorted(out_e.get(d, [])):
                if k in self.LBL_OUT:
                    spec.append(f"{self.LBL_OUT[k]}: {self.disp[t]}"
                                + (f" ({s}%)" if s else ""))
            for k, f, s in sorted(in_e.get(d, [])):
                if k in self.rules and self.rules[k]["sym"] and k in self.LBL_OUT:
                    spec.append(f"{self.LBL_OUT[k]}: {self.disp[f]}")
                elif k in self.LBL_IN:
                    spec.append(f"{self.LBL_IN[k]}: {self.disp[f]}")
            kids = [self.disp[c] for c in sorted(children.get(d, []),
                                                 key=lambda x: self.disp[x])]
            defin = f"{n} — {self.disp[rod] if rod else 'universe (no genus)'}"
            if spec:
                defin += "; " + "; ".join(spec)
            if kids:
                defin += ". Species: " + ", ".join(kids)
            self.cur.execute("UPDATE concept SET defin=%s WHERE dharma=%s",
                             (defin[:1000], d))
            if not spec and not kids and rod:
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
        return dict(concepts=c, edges=e, candidates=cand, paths=p, by_universum=by_u)


if __name__ == "__main__":
    eng = JnanaEngine()
    print(eng.stats())
