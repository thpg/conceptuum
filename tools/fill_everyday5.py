# -*- coding: utf-8 -*-
"""Бытовой универсум, проход D (финал): одежда, приготовление пищи,
мышление + фикс 4 rejected из прохода C."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

U = 1

NEW = [
    ("синтез", "synthesis (thinking)", "мышление"),
    ("согревание", "warming", "физический процесс"),
    ("лежание", "lying (rest)", "физиологический процесс"),
    ("парк", "park", "ландшафт"),
]

EDGES = [
    # фикс rejected прохода C
    ("одеяло", "80", "согревание", None),
    ("сидение", "61", "лежание", None),
    ("сад", "61", "парк", None),
    # ---- одежда ----
    ("брюки", "61", "футболка", None),
    ("куртка", "61", "футболка", None),
    ("шарф", "61", "варежки", None),
    ("перчатки", "61", "варежки", None),
    ("брюки", "61", "куртка", None),
    ("одежда", "80", "защита", None),
    ("одежда", "81", "ткань", None),
    ("одежда", "61", "обувь", None),
    # ---- приготовление пищи ----
    ("запекание", "61", "тушение", None),
    ("замешивание", "83", "тесто", None),
    ("чистка", "72", "нарезка", None),
    ("нарезка", "61", "чистка", None),
    ("соление", "61", "запекание", None),
    ("запекание", "83", "мясо", None),
    ("тушение", "83", "мясо", None),
    ("процеживание", "61", "соление", None),
    # ---- мышление ----
    ("анализ", "63", "синтез", None),
    ("анализ", "61", "сравнение", None),
    ("рассуждение", "61", "воображение", None),
    ("планирование", "72", "решение", None),
    ("анализ", "72", "решение", None),
    ("воображение", "61", "планирование", None),
    ("решение", "70", "действие", None),
    ("сравнение", "61", "счёт", None),
]

CLOSED = [
    "брюки","варежки","куртка","перчатки","футболка","шарф",
    "запекание","замешивание","нарезка","соление","тушение","чистка",
    "анализ","воображение","планирование","рассуждение","решение","сравнение",
    "синтез","согревание","лежание","парк",
]


def main():
    eng = JnanaEngine(pref_lang="ru")
    added = 0
    for ru, en, parent in NEW:
        cid, msg = eng.add_concept(ru, parent, lang="ru", universum_id=U,
                                   terms=[(en, "en")] if en else None)
        if cid is None:
            print("  x NEW:", msg)
        elif "already" in msg:
            print("  EXISTS:", ru)
        else:
            added += 1
    eng.commit()
    print(f"concepts: +{added}")

    ok = rej = 0
    for a, kod, b, st in EDGES:
        eid, msg = eng.propose(a, kod, b, strength=st, universum_id=U,
                               source="llm:fill:self", auto=True)
        if eid:
            ok += 1
        elif "duplicate" in msg:
            pass
        else:
            rej += 1
            print("  x EDGE:", msg)
    eng.commit()
    print(f"edges: +{ok} ok, {rej} rejected of {len(EDGES)}")

    closed = 0
    for t in CLOSED:
        cid = eng.resolve(t)
        if cid:
            eng.set_processed(cid)
            closed += 1
        else:
            print("  ? CLOSED not found:", t)
    eng.commit()
    print(f"processed: {closed} of {len(CLOSED)}")

    print("paths:", eng.rebuild())
    weak = eng.define()
    eng.commit()
    print(eng.stats())
    rest = eng.unprocessed(U)
    print("unprocessed(uid=1):", len(rest))
    if rest:
        print("остаток:", ", ".join(eng.disp.get(c, str(c)) for c in rest[:100]))
    eng.close()


if __name__ == "__main__":
    main()
