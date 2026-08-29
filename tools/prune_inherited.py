# -*- coding: utf-8 -*-
"""Чистка избыточных атрибутов по правилу наследования (2026-08-28):
ребро вида удаляется, если то же свойство (тот же kod и объект/род объекта)
уже указано у рода и strength не отклоняется на 25+ пунктов (override)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine
from collections import defaultdict

ATTR = ('20', '21', '22', '23', '24', '25', '26', '27')

eng = JnanaEngine(pref_lang="ru")
by_pair = defaultdict(dict)
for a, b, k, s, st, i in eng.edges:
    if st == 'ok' and k in ATTR:
        by_pair[(a, k)][b] = (s, i)

to_delete = {}
for (a, k), objs in by_pair.items():
    for anc in [x for x in eng.ancestors(a) if x != a]:
        for b, (s, i) in objs.items():
            for b2, (s2, i2) in by_pair.get((anc, k), {}).items():
                if b2 != b:
                    continue  # subtype object = specialization, keep
                override = (s is not None and s2 is not None
                            and abs(s - s2) >= 25)
                if not override:
                    to_delete[i] = (a, k, b, anc)

print("to delete:", len(to_delete))
for i in sorted(to_delete):
    a, k, b, anc = to_delete[i]
    eng.cur.execute("DELETE FROM edge WHERE id=%s", (i,))
eng.commit()
print("deleted.")
print("paths:", eng.rebuild())
eng.define()
eng.commit()
print(eng.stats())
eng.close()
