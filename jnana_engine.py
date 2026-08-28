# -*- coding: utf-8 -*-
"""
jnana_engine.py — движок базы логических связей понятий (jnana3).

Слои:
  хранилище  : concept / concept_term / edge / relevant / universum / concept_path
  валидация  : правила читаются из relevant (сигнатуры, симметрия, транзитивность)
  вывод      : concept_path (транзитивное замыкание kod 14), наследование
  интерфейс  : verify / propose / approve / add_concept / rebuild / define

Использование:
    eng = JnanaEngine()
    eng.verify("Linux", "operating system")
    eng.propose("Docker", "74", "computer network", strength=90, rationale="needs network")
    eng.approve([id1, id2])
    eng.rebuild(); eng.define()
"""

import pymysql
from collections import defaultdict

DB = dict(host="127.0.0.1", user="root", password="123", database="jnana3", charset="utf8")
KOD_ISA = "14"
SYMMETRIC_DEFAULT = {"61", "62", "63", "64", "73"}


class JnanaEngine:
    def __init__(self, autocommit=False, **conn_kw):
        cfg = {**DB, **conn_kw}
        self.conn = pymysql.connect(**cfg, autocommit=autocommit)
        self.cur = self.conn.cursor()
        self.reload()

    # ---------- загрузка в память ----------
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
        for cid, term, lang in self.cur.fetchall():
            self.term2id[(term.lower(), lang)] = cid
            self.term2id.setdefault(term.lower(), cid)
            self.terms_of[cid].append((term, lang))
        self.cur.execute(
            "SELECT kod, long_name, sig_subject, sig_subject2, sig_object, sig_object2, sig_object3,"
            " is_symmetric, is_transitive FROM relevant")
        self.rules = {r[0]: dict(name=r[1], ss=r[2], ss2=r[3], so=r[4], so2=r[5], so3=r[6],
                                 sym=bool(r[7]), trans=bool(r[8]))
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

    def commit(self):
        self.conn.commit()
        self.reload()

    def close(self):
        self.conn.close()

    # ---------- навигация ----------
    def resolve(self, term, lang=None):
        if lang:
            return self.term2id.get((term.lower(), lang))
        return self.term2id.get(term.lower())

    def ancestors(self, cid):
        return self.anc.get(cid, {})

    def children(self, cid):
        return [a for a, b in self.parent.items() if b == cid]

    def in_subtree(self, cid, anchor):
        return cid == anchor or anchor in self.anc.get(cid, {})

    # ---------- verify ----------
    def verify(self, t1, t2, lang=None):
        """Проверка утверждения «t1 связан с t2» против графа.
        Возвращает (verdict, detail, missing_terms)."""
        i1 = self.resolve(t1, lang)
        i2 = self.resolve(t2, lang)
        missing = [t for t, i in ((t1, i1), (t2, i2)) if i is None]
        if missing:
            return "unknown", f"неизвестные термины: {', '.join(missing)}", missing
        if i2 in self.anc.get(i1, {}):
            return "yes", f"{t1} — вид «{t2}» (глубина {self.anc[i1][i2]})", []
        if i1 in self.anc.get(i2, {}):
            return "reverse", f"наоборот: «{t2}» — вид «{t1}»", []
        adj = defaultdict(list)
        for a, b, k, s, st, i in self.edges:
            if st != "ok":
                continue
            adj[a].append((b, k, "→"))
            adj[b].append((a, k, "←"))
        for b, k, d in adj[i1]:
            if b == i2:
                return "yes", f"{t1} {d}[{self.rules[k]['name']}] {t2}", []
        for z, k1, d1 in adj[i1]:
            for b, k2, d2 in adj[z]:
                if b == i2:
                    return ("indirect",
                            f"{t1} {d1}[{self.rules[k1]['name']}] {self.names[z]} "
                            f"{d2}[{self.rules[k2]['name']}] {t2}", [])
        return "no", f"связь между «{t1}» и «{t2}» не найдена", []

    # ---------- валидация ----------
    def validate(self, a, kod, b, universum_id=None):
        """(ok, сообщение). Правила читаются из relevant."""
        kod = str(kod)
        rule = self.rules.get(kod)
        if rule is None:
            return False, f"неизвестный kod {kod}"
        if a is None or b is None:
            return False, "понятие не найдено"
        if rule["sym"] and a > b:
            a, b = b, a
        u = universum_id or self.concept_u.get(a, 1)
        for x, y, k, s, st, i in self.edges:
            if (x, y, k) == (a, b, kod):
                return False, "дубликат"
        if kod == KOD_ISA:
            if b in self.anc.get(a, {}) or a in self.anc.get(b, {}):
                return False, "цикл в иерархии"
        if rule["ss"] is not None:
            ok_subj = self.in_subtree(a, rule["ss"]) or (
                rule.get("ss2") and self.in_subtree(a, rule["ss2"]))
            if not ok_subj:
                return False, f"сигнатура: субъект должен быть в поддереве #{rule['ss']}"
        if rule["so"] is not None:
            ok_obj = (self.in_subtree(b, rule["so"])
                      or (rule.get("so2") and self.in_subtree(b, rule["so2"]))
                      or (rule.get("so3") and self.in_subtree(b, rule["so3"])))
            if not ok_obj:
                return False, f"сигнатура: объект должен быть в поддереве #{rule['so']}"
        # избыточность по наследованию (предупреждение, не отказ)
        warn = None
        if kod in ("70", "80", "82", "83"):
            for x, y, k, s, st, i in self.edges:
                if x == a and k == kod and y != b and self.in_subtree(b, y):
                    warn = f"избыточно: наследуется от «{self.names[y]}»"
        return True, warn or "ok"

    # ---------- propose / approve ----------
    def propose(self, t1, kod, t2, strength=None, rationale=None,
                universum_id=None, source="llm", auto=False):
        """Предложить ребро. auto=True -> сразу status='ok'."""
        a = self.resolve(t1) if not isinstance(t1, int) else t1
        b = self.resolve(t2) if not isinstance(t2, int) else t2
        ok, msg = self.validate(a, str(kod), b, universum_id)
        if not ok:
            return None, f"ОТКЛОНЕНО {t1}→{t2} [{kod}]: {msg}"
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
        return eid, f"{'ПРИНЯТО' if auto else 'КАНДИДАТ'} {t1} —[{kod}]→ {t2} (#{eid})" + (
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
        """Новое понятие + родовое ребро. parent — имя или id.
        passport: dict(vol_ed=.., cont_abs=.., ...); terms: [(term, lang), ...]"""
        if isinstance(parent, str):
            pid = self.resolve(parent)
        else:
            pid = parent
        if pid is None:
            return None, f"родитель «{parent}» не найден"
        if nama in self.id_of:
            return self.id_of[nama], f"уже есть: {nama}"
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
        return cid, f"+понятие {nama} → {self.names[pid]} (u{u})"

    # ---------- rebuild ----------
    def rebuild(self):
        """Пересборка транзитивного замыкания concept_path."""
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
        """Регенерация кэша дефиниций concept.defin. Возвращает список слабых."""
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
        for d, n in self.names.items():
            rod = self.parent.get(d)
            spec = []
            for k, t, s in sorted(out_e.get(d, [])):
                if k in self.LBL_OUT:
                    spec.append(f"{self.LBL_OUT[k]}: {self.names[t]}"
                                + (f" ({s}%)" if s else ""))
            for k, f, s in sorted(in_e.get(d, [])):
                if k in self.rules and self.rules[k]["sym"] and k in self.LBL_OUT:
                    spec.append(f"{self.LBL_OUT[k]}: {self.names[f]}")
                elif k in self.LBL_IN:
                    spec.append(f"{self.LBL_IN[k]}: {self.names[f]}")
            kids = [self.names[c] for c in sorted(children.get(d, []),
                                                  key=lambda x: self.names[x])]
            defin = f"{n} — {self.names[rod] if rod else 'universe (no genus)'}"
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

    # ---------- статистика ----------
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
    for t1, t2 in [("Linux", "operating system"), ("patch", "bug"),
                   ("вода", "лёд"), ("человек", "камень")]:
        print(t1, "~", t2, "->", eng.verify(t1, t2)[:2])
    eng.close()
