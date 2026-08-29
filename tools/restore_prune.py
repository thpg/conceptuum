# -*- coding: utf-8 -*-
"""Откат ошибочно удалённых при чистке рёбер (2026-08-28).
Правило: удаление оправдано, только если у рода есть ребро с тем же кодом
и ТЕМ ЖЕ объектом (b2 == b). Совпадение по поддереву объекта (полёт isa
движение) — это уточнение вида, а не избыточность: такие рёбра
восстанавливаются из дампа jnana3_pre. Порядок — сверху вниз по таксономии."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine
import pymysql

ATTR = ('20', '21', '22', '23', '24', '25', '26', '27')

pre = pymysql.connect(host="127.0.0.1", user="root", passwd="123",
                      db="jnana3_pre", charset="utf8mb4")
pc = pre.cursor()
pc.execute("SELECT id, dh1, kod, dh2, universum_id, strength, status, source "
           "FROM edge")
pre_edges = {r[0]: r[1:] for r in pc.fetchall()}

eng = JnanaEngine(pref_lang="ru")
cur_ids = {i for *_x, i in eng.edges}
deleted = {i: e for i, e in pre_edges.items() if i not in cur_ids}
print("deleted:", len(deleted))

# текущие атрибутивные рёбра: (cid, kod) -> set(obj)
live = {}
for a, b, k, s, st, i in eng.edges:
    if st == 'ok' and k in ATTR:
        live.setdefault((a, k), set()).add(b)

def has_exact_dup(a, k, b):
    for anc in [x for x in eng.ancestors(a) if x != a]:
        if b in live.get((anc, k), ()):
            return True
    return False

# сверху вниз: сначала роды
def depth(cid):
    return len(eng.ancestors(cid))

restored = kept_deleted = 0
for i, (a, k, b, u, s, st, src) in sorted(deleted.items(),
                                          key=lambda kv: depth(kv[1][0])):
    if k not in ATTR or st != 'ok':
        continue
    if has_exact_dup(a, k, b):
        kept_deleted += 1
        continue
    eng.cur.execute(
        "INSERT INTO edge (id, dh1, kod, dh2, universum_id, strength, status, source)"
        " VALUES (%s,%s,%s,%s,%s,%s,'ok',%s)", (i, a, k, b, u, s, src))
    live.setdefault((a, k), set()).add(b)
    restored += 1
    print(f"  restore #{i} {eng.disp[a]} -[{k}]-> {eng.disp[b]} ({s}%)")
eng.commit()
print(f"restored: {restored}, still pruned (exact dup): {kept_deleted}")
print("paths:", eng.rebuild())
eng.define()
eng.commit()
print(eng.stats())
eng.close()
pre.close()
