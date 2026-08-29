# -*- coding: utf-8 -*-
# Ревизия: слияние видовых/возвратных глагольных понятий в одно.
# Режим 1 (по умолчанию): только отчёт books/merge_report.txt
# Режим 2 (apply): выполнить слияние.
import sys, io, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymorphy3, pymysql

APPLY = len(sys.argv) > 1 and sys.argv[1] == 'apply'

morph = pymorphy3.MorphAnalyzer()
conn = pymysql.connect(host='127.0.0.1', user='root', password='123',
                       database='jnana3', charset='utf8mb4')
cur = conn.cursor()

cur.execute("SELECT dharma, nama FROM concept WHERE universum_id=1")
verbs, nouns = {}, {}
for cid, nama in cur.fetchall():
    p = morph.parse(nama)[0]
    if p.tag.POS in ('VERB', 'INFN'):
        verbs[cid] = nama
    elif p.tag.POS == 'NOUN':
        nouns.setdefault(nama, cid)

def norm(v):
    return re.sub(r'(ся|сь)$', '', v)

def lcp(a, b):
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return i

# --- формы, которые НЕ участвуют в авто-группировке (ложные соседи по префиксу).
# Сами по себе остаются понятиями; если для них есть запись в MANUAL/OVERRIDE —
# они попадут в свою ручную группу.
EXCLUDE = {
    'возрастать',            # ≠ возражать
    'воспользоваться',       # ≠ восполнить
    'воспроизводить',        # ≠ воспринимать (reproduce ≠ perceive)
    'выбрасывать',           # ≠ выбрать
    'использовать',          # ≠ исполнить
    'передать', 'передавать', 'передаваться',   # ≠ передвигать
    'пересекаться', 'пересечься',               # ≠ перестать
    'подавлять',             # ≠ подавать
    'подвергаться', 'подвергнуть', 'подвергнуться',  # ≠ подвести
    'потерпеть',             # ≠ потерять
    'потребоваться',         # ≠ потреблять
    'предохранить',          # ≠ предостерегать
    'предсказать',           # ≠ представить
    'проверить', 'проверять', 'проверяться',    # ≠ провести (проверка ≠ проведение)
    'произноситься',         # ≠ производить
    'разредить', 'разрезать',                   # ≠ разрешить
    'распределить',          # ≠ распространить
    'совершенствоваться',    # ≠ совершать
    'отобрать',              # ≠ отображать
    'прийтись', 'приходиться',                  # ≠ прийти (необходимость ≠ приход)
    'познакомиться',         # ≠ познавать
    'учиться', 'научиться',  # учение ≠ обучение (не сливаем с «учить»)
    'доставлять',            # ≠ достать
}

# --- ручная карта слияний (форма -> каноническая форма) ---
MANUAL = {}
def grp(*forms, canon):
    for f in forms:
        MANUAL[f] = canon
grp('вывести', 'выводиться', canon='вывести')
grp('решать', 'решить', 'решаться', canon='решать')
grp('взяться', 'браться', canon='браться')
grp('начать', 'начинать', 'начаться', 'начинаться', canon='начинать')
grp('прийти', 'приходить', canon='приходить')
grp('прийтись', 'приходиться', canon='приходиться')
grp('выйти', canon='выйти')   # выходить нет в базе; одиночка
grp('найти', 'находить', canon='находить')
grp('ответить', 'отвечать', canon='отвечать')
grp('погибнуть', 'гибнуть', canon='гибнуть')
grp('умереть', 'умирать', canon='умирать')
grp('есть', 'поедать', canon='есть')
grp('добыть', 'добываться', canon='добыть')
grp('написать', 'писать', canon='писать')
grp('занять', 'занимать', 'заниматься', canon='заниматься')
grp('отразиться', 'отражать', 'отражаться', canon='отражать')
grp('перейти', 'переходить', canon='переходить')
grp('понять', 'понимать', 'пониматься', canon='понимать')
grp('появиться', 'появляться', canon='появляться')
grp('принять', 'принимать', 'приниматься', canon='принимать')
grp('пройти', 'проходить', canon='проходить')
grp('прочитать', 'читать', canon='читать')
grp('разобрать', 'разобраться', canon='разобраться')
grp('рассмотреть', 'рассматривать', 'рассматриваться', canon='рассматривать')
grp('связать', 'связывать', 'связываться', canon='связывать')
grp('сдать', 'сдавать', 'сдаваться', canon='сдавать')
grp('смешать', 'смешивать', 'смешиваться', canon='смешивать')
grp('сослаться', 'ссылаться', canon='ссылаться')
grp('убедить', 'убеждать', 'убедиться', 'убеждаться', canon='убеждать')  # НЕ «убеждение»
grp('признать', 'признаваться', canon='признать')
grp('превратить', 'превратиться', 'превращать', 'превращаться', canon='превращать')
grp('приобрести', 'приобретаться', canon='приобрести')
grp('заметить', 'замечать', canon='замечать')
grp('запомнить', canon='запомнить')
grp('выучить', canon='учить')
grp('научиться', 'учиться', canon='учиться')
grp('вычислить', canon='вычислить')
grp('сформулировать', 'формулироваться', canon='формулироваться')
grp('улучшить', canon='улучшать')
grp('выбрать', canon='выбрать')
grp('потерять', canon='терять')
grp('подвести', canon='подводить')

# --- явные каноны (в т.ч. существительные, которые эвристика может не найти) ---
CANON_OVERRIDE = {
    'воспринимать': 'восприятие', 'восприниматься': 'восприятие',
    'провести': 'проведение', 'проводить': 'проведение', 'проводиться': 'проведение',
    'проверить': 'проверять', 'проверять': 'проверять', 'проверяться': 'проверять',
    'передать': 'передать', 'передавать': 'передать', 'передаваться': 'передать',
    'использовать': 'использование',
    'предстать': 'представить', 'представить': 'представить',
    'представиться': 'представить', 'представляться': 'представить',
    'выступать': 'выступление', 'выступить': 'выступление',
    'подготавливать': 'подготовка', 'подготовить': 'подготовка', 'подготовиться': 'подготовка',
    'возразить': 'возражение', 'возражать': 'возражение',
}

HINT = dict(MANUAL)
HINT.update(CANON_OVERRIDE)

# --- автогруппировка по общему префиксу >= 5 (без EXCLUDE) ---
sv = sorted(verbs.items(), key=lambda kv: norm(kv[1]))
auto = []
cur_g = [sv[0]]
for item in sv[1:]:
    if lcp(norm(cur_g[-1][1]), norm(item[1])) >= 5:
        cur_g.append(item)
    else:
        auto.append(cur_g)
        cur_g = [item]
auto.append(cur_g)

# --- union-find: сливаем пересекающиеся группы (авто + ручные) ---
parent = {}
def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra

form2cid = {v: k for k, v in verbs.items()}
for g in auto:
    forms = [v for _, v in g if v not in EXCLUDE]
    for f in forms[1:]:
        union(forms[0], f)
for f, c in HINT.items():
    if f in form2cid:
        union(f, '@' + c)   # узел-канон (может быть существительным или новым именем)

groupmap = collections.defaultdict(set)
for x in list(parent):
    groupmap[find(x)].add(x)

# --- поиск существительного-канона ---
# существительное подходит, если общий префикс покрывает его основу (без суффикса -1 буква)
ACT_SUF = ('ение', 'ание', 'ние', 'тие', 'ка', 'ба')
def noun_target(forms):
    best = None
    for n in nouns:
        for suf in ACT_SUF:
            if n.endswith(suf):
                stem = n[:-len(suf)]
                m = max(lcp(n, norm(f)) for f in forms)
                if m >= max(5, len(stem) - 1):
                    if best is None or len(n) < len(best):
                        best = n
                break
    return best

def canon_inf(forms):
    # невозвратный предпочтительнее возвратного; при равенстве — несовершенный вид
    def key(f):
        aspects = {p.tag.aspect for p in morph.parse(f) if p.tag.POS in ('VERB', 'INFN')}
        return (f != norm(f), 'impf' not in aspects, len(f), f)
    return sorted(forms, key=key)[0]

report = []
for root, nodes in groupmap.items():
    hints = [n[1:] for n in nodes if n.startswith('@')]
    forms = sorted(n for n in nodes if not n.startswith('@'))
    if not forms:
        continue
    canon = hints[0] if hints else (noun_target(forms) or canon_inf(forms))
    members = [f for f in forms if f != canon]
    if not members:
        continue
    kind = 'NOUN' if canon in nouns else ('verb' if canon in form2cid else 'NEW')
    report.append((canon, kind, members))

report.sort(key=lambda r: r[0])
with open(r'G:\Projects\conceptuum\books\merge_report.txt', 'w', encoding='utf-8') as f:
    f.write(f'групп слияния: {len(report)}\n\n')
    for canon, kind, members in report:
        f.write(f'{canon}  [{kind}]  <=  {", ".join(members)}\n')
print('групп слияния:', len(report))
print('отчёт: books/merge_report.txt')

if APPLY:
    moved = deleted = skipped = 0
    for canon, kind, members in report:
        if canon in form2cid:
            cid_canon = form2cid[canon]
        elif canon in nouns:
            cid_canon = nouns[canon]
        else:
            skipped += 1
            continue
        for m in members:
            cid_m = form2cid.get(m)
            if cid_m is None or cid_m == cid_canon:
                continue
            cur.execute("SELECT term, lang FROM concept_term WHERE concept_id=%s", (cid_m,))
            for term, lang in cur.fetchall():
                cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
                            (cid_canon, term, lang))
                moved += 1
            # само слово-форму тоже оставляем термином
            cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')",
                        (cid_canon, m))
            cur.execute("DELETE FROM edge WHERE dh1=%s OR dh2=%s", (cid_m, cid_m))
            cur.execute("DELETE FROM concept WHERE dharma=%s", (cid_m,))
            cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (cid_m,))
            deleted += 1
    conn.commit()
    print(f'перенесено терминов: {moved}, удалено понятий: {deleted}, пропущено групп (канон не найден): {skipped}')
conn.close()
