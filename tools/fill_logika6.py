# -*- coding: utf-8 -*-
# Проход 6: гл. IX (индукция), гл. X (аналогия), гл. XI (гипотеза)
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'G:\Projects\conceptuum')
from jnana_engine import JnanaEngine

U = 5  # логика
eng = JnanaEngine(pref_lang='ru')

NEW = [
    # гл. IX — индукция
    ('полная индукция', 'complete induction', 'индуктивное умозаключение'),
    ('неполная индукция', 'incomplete induction', 'индуктивное умозаключение'),
    ('индукция через простое перечисление', 'induction by simple enumeration', 'неполная индукция'),
    ('научная индукция', 'scientific induction', 'неполная индукция'),
    ('поспешное обобщение', 'hasty generalization', 'логическая ошибка'),
    ('после этого — значит по причине этого', 'post hoc ergo propter hoc', 'логическая ошибка'),
    ('условие', 'condition', 'явление'),
    ('индуктивный метод', 'inductive method', 'логический приём'),
    ('метод сходства', 'method of agreement', 'индуктивный метод'),
    ('метод различия', 'method of difference', 'индуктивный метод'),
    ('соединённый метод сходства и различия', 'joint method of agreement and difference', 'индуктивный метод'),
    ('метод остатков', 'method of residues', 'индуктивный метод'),
    ('метод сопутствующих изменений', 'method of concomitant variations', 'индуктивный метод'),
    ('наблюдение', 'observation', 'логический приём'),
    ('эксперимент', 'experiment', 'логический приём'),
    ('сходство', 'similarity', 'отношение'),
    ('различие', 'difference', 'отношение'),
    ('вероятность', 'probability', 'свойство'),
    # гл. X — аналогия
    ('ложная аналогия', 'false analogy', 'логическая ошибка'),
    # гл. XI — гипотеза
    ('предположение', 'supposition', 'суждение'),
    ('гипотеза', 'hypothesis', 'предположение'),
    ('теория', 'theory', 'знание'),
    ('проверка гипотезы', 'hypothesis testing', 'логический приём'),
]

SYNONYMS = [
    ('индуктивное умозаключение', 'индукция', 'induction'),
    ('умозаключение по аналогии', 'аналогия', 'analogy'),
    ('метод сопутствующих изменений', 'метод сопутствующих изменений', 'method of concomitant variation'),
]

EDGES = [
    ('полная индукция', 64, 'неполная индукция', None),
    ('индукция через простое перечисление', 61, 'научная индукция', None),
    ('метод сходства', 61, 'метод различия', None),
    ('метод сходства', 61, 'метод остатков', None),
    ('метод сходства', 61, 'метод сопутствующих изменений', None),
    ('метод различия', 61, 'метод остатков', None),
    ('метод остатков', 61, 'метод сопутствующих изменений', None),
    ('соединённый метод сходства и различия', 74, 'метод сходства', None),
    ('соединённый метод сходства и различия', 74, 'метод различия', None),
    ('поспешное обобщение', 74, 'индукция через простое перечисление', None),
    ('причина', 61, 'условие', None),
    ('условие', 70, 'следствие', 0),   # отрицание: условие само не вызывает следствия
    ('умозаключение по аналогии', 20, 'вероятность', 95),
    ('гипотеза', 20, 'вероятность', 70),
    ('гипотеза', 72, 'теория', None),  # гипотеза предшествует теории
    ('проверка гипотезы', 74, 'гипотеза', None),
    ('наблюдение', 61, 'эксперимент', None),
    ('сходство', 63, 'различие', None),
    ('метод сходства', 74, 'сходство', None),
    ('метод различия', 74, 'различие', None),
    ('метод сопутствующих изменений', 74, 'изменение', None),
    ('научная индукция', 74, 'индуктивный метод', None),
    # фикс отказа из прохода 4
    ('софизм', 74, 'подмена понятия', None),
]

CLOSED = [
    'полная индукция', 'неполная индукция', 'индукция через простое перечисление',
    'научная индукция', 'индуктивный метод', 'метод сходства', 'метод различия',
    'соединённый метод сходства и различия', 'метод остатков',
    'метод сопутствующих изменений', 'наблюдение', 'эксперимент',
    'гипотеза', 'проверка гипотезы',
]

added = {}
for ru, en, parent in NEW:
    cid = eng.add_concept(ru, parent, lang='ru', universum_id=U, terms=[(en, 'en')])
    added[ru] = cid
    print(f'NEW {ru} (={en}) < {parent} -> {cid}')

def rid(name):
    """Concept id by exact nama within universum U."""
    eng.cur.execute("SELECT dharma FROM concept WHERE nama=%s AND universum_id=%s", (name, U))
    row = eng.cur.fetchone()
    return row[0] if row else None

def add_syn(cid, term, lang):
    eng.cur.execute(
        "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
        (cid, term, lang))

for base, ru_syn, en_syn in SYNONYMS:
    cid = rid(base)
    if cid:
        add_syn(cid, ru_syn, 'ru')
        if en_syn and en_syn != ru_syn:
            add_syn(cid, en_syn, 'en')
        print(f'SYN {base} += {ru_syn} / {en_syn}')

rej = []
for a, kod, b, st in EDGES:
    r = eng.propose(a, kod, b, strength=st, universum_id=U, source='llm:fill:self', auto=True)
    tag = r.get('status') if isinstance(r, dict) else str(r)
    print(f'EDGE {a} -[{kod}]-> {b} : {tag}')
    if isinstance(r, dict) and r.get('status') == 'rejected':
        rej.append((a, kod, b, r.get('reason')))

for name in CLOSED:
    cid = rid(name)
    if cid:
        eng.set_processed(cid)

eng.rebuild()
print('\n--- REJECTED ---')
for x in rej:
    print(x)
print('\n--- STATS ---')
eng.stats()
print('\n--- SAMPLE DEFINITIONS ---')
eng.define()
for name in ('гипотеза', 'научная индукция', 'метод различия'):
    cid = rid(name)
    eng.cur.execute("SELECT nama, defin FROM concept WHERE dharma=%s", (cid,))
    row = eng.cur.fetchone()
    print(f'{row[0]}: {row[1]}')
eng.close()
