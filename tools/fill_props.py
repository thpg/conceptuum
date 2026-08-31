# -*- coding: utf-8 -*-
"""Apply a batch of property edges. Engine validates; no LLM.

  from fill_props import run
  run(NEW, EDGES)
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from jnana_engine import JnanaEngine

# явление (2535) covers действие/процесс/состояние/событие.
# 20.object действие → явление so a process can be an attribute-object.
YAV = 2535
SIGS = [
    ("15", "sig_subject2", YAV),
    ("20", "sig_subject2", YAV),
    ("20", "sig_object3", YAV),
    ("21", "sig_object", YAV),
    ("22", "sig_object", YAV),
    ("27", "sig_subject", YAV),
]


def rid(eng, t):
    r = eng.resolve(t)
    if r:
        return r
    fz = eng.resolve_fuzzy(t) or []
    if len(fz) == 1:
        return fz[0]
    return None


def widen_signatures(eng):
    for kod, col, val in SIGS:
        eng.cur.execute(f"UPDATE relevant SET {col}=%s WHERE kod=%s", (val, kod))
    eng.commit()
    eng.reload()
    print("signatures: 15/20 subject + 20/21/22 object + 27 subject → явление")


def apply_concepts(eng, new):
    added = existed = failed = 0
    for row in new:
        ru, en, parent = row[0], row[1], row[2]
        u = row[3] if len(row) > 3 else 1
        cid, msg = eng.add_concept(ru, parent, lang="ru", universum_id=u,
                                   terms=[(en, "en")])
        print(" ", msg)
        if cid is None:
            failed += 1
        elif "already" in msg:
            existed += 1
        else:
            added += 1
    eng.commit()
    print(f"concepts +{added} existed {existed} fail {failed}")
    return added


def apply_edges(eng, edges, source="agent:props"):
    acc = rej = 0
    reasons = {}
    for row in edges:
        t1, kod, t2 = row[0], str(row[1]), row[2]
        st = row[3] if len(row) > 3 else None
        a, b = rid(eng, t1), rid(eng, t2)
        if a is None or b is None:
            why = f"unresolved {t1 if a is None else t2}"
            rej += 1
            reasons[why] = reasons.get(why, 0) + 1
            print(f"  REJECT {t1} —[{kod}]→ {t2}: {why}")
            continue
        ok, msg = eng.validate(a, kod, b, eng.concept_u.get(a, 1), strength=st)
        if not ok:
            rej += 1
            key = msg.split(":")[0]
            reasons[key] = reasons.get(key, 0) + 1
            if "duplicate" not in msg:
                print(f"  REJECT {t1} —[{kod}]→ {t2}: {msg}")
            continue
        try:
            eng.cur.execute(
                "INSERT INTO edge (dh1,kod,dh2,universum_id,strength,status,source)"
                " VALUES (%s,%s,%s,%s,%s,'ok',%s)",
                (a, kod, b, eng.concept_u.get(a, 1), st, source))
        except pymysql.err.IntegrityError:
            rej += 1
            reasons["duplicate"] = reasons.get("duplicate", 0) + 1
            continue
        eid = eng.cur.lastrowid
        eng.edges = list(eng.edges) + [(a, b, kod, st, "ok", eid)]
        acc += 1
        warn = f"  [{msg}]" if msg != "ok" else ""
        print(f"  + {eng.names[a]} —[{kod}]→ {eng.names[b]}"
              + (f" {st}%" if st is not None else "") + warn)
    eng.commit()
    print(f"edges +{acc} reject/skip {rej}")
    if reasons:
        print("  reasons:", ", ".join(f"{k} {v}" for k, v in sorted(
            reasons.items(), key=lambda x: -x[1])))
    return acc


def finish(eng):
    print("paths:", eng.rebuild())
    weak = eng.define()
    eng.commit()
    print(eng.stats())
    print("weak (genus only, still):", len(weak))


def run(new, edges, source="agent:props"):
    eng = JnanaEngine(pref_lang="ru")
    widen_signatures(eng)
    print("\n=== NEW ===")
    apply_concepts(eng, new)
    print("\n=== EDGES ===")
    apply_edges(eng, edges, source=source)
    print("\n=== FINISH ===")
    finish(eng)
    eng.close()
