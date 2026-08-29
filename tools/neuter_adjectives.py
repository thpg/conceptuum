# -*- coding: utf-8 -*-
# Ревизия прилагательных: каноническая форма понятия = средний род («тяжёлое»).
# Мужской/женский род — термины того же понятия. Носитель входит в общее
# «тяжёлое» связью (код 14/2X). Коллизии с существующими понятиями — слияние.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymorphy3, pymysql

APPLY = len(sys.argv) > 1 and sys.argv[1] == 'apply'
morph = pymorphy3.MorphAnalyzer()
conn = pymysql.connect(host='127.0.0.1', user='root', password='123',
                       database='jnana3', charset='utf8mb4')
cur = conn.cursor()

cur.execute("SELECT dharma, nama, universum_id FROM concept")
names, adj = {}, {}
for cid, nama, u in cur.fetchall():
    names.setdefault(nama, (cid, u))
    if ' ' in nama:        # многословные понятия (Новый год) не трогаем
        continue
    p = morph.parse(nama)[0]
    if p.tag.POS == 'ADJF' and 'Surn' not in p.tag:
        adj[cid] = (nama, u)

def neuter(phrase):
    out = []
    for w in phrase.split():
        p = morph.parse(w)[0]
        if p.tag.POS == 'ADJF':
            f = p.inflect({'neut', 'sing', 'nomn'})
            out.append(f.word if f else w)
        else:
            out.append(w)
    return ' '.join(out)

# цели и дубликаты целей среди самих прилагательных
target = {}
for cid, (nama, u) in adj.items():
    target[cid] = neuter(nama)

renamed = merged = kept = 0
report = []
# сначала слияния: цель занята другим понятием или другим прилагательным
seen_tgt = {}
for cid, (nama, u) in sorted(adj.items(), key=lambda kv: kv[1][0]):
    tgt = target[cid]
    if tgt == nama:
        kept += 1
        continue
    dest = None
    if tgt in names and names[tgt][0] != cid:
        dest = names[tgt][0]               # коллизия с существующим понятием
    elif tgt in seen_tgt and seen_tgt[tgt] != cid:
        dest = seen_tgt[tgt]               # два прилагательных -> одна форма
    if dest:
        report.append(('MERGE', nama, tgt, dest))
        if APPLY:
            cur.execute("SELECT term, lang FROM concept_term WHERE concept_id=%s", (cid,))
            for term, lang in cur.fetchall():
                cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
                            (dest, term, lang))
            cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')", (dest, nama))
            cur.execute("DELETE FROM edge WHERE dh1=%s OR dh2=%s", (cid, cid))
            cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (cid,))
            cur.execute("DELETE FROM concept WHERE dharma=%s", (cid,))
        merged += 1
    else:
        report.append(('RENAME', nama, tgt, cid))
        if APPLY:
            cur.execute("UPDATE concept SET nama=%s WHERE dharma=%s", (tgt, cid))
            cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')", (cid, nama))
            cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')", (cid, tgt))
        seen_tgt[tgt] = cid
        names[tgt] = (cid, u)
        renamed += 1

with open(r'G:\Projects\conceptuum\books\adj_report.txt', 'w', encoding='utf-8') as f:
    f.write(f'прилагательных: {len(adj)}, переименовано: {renamed}, слито: {merged}, уже ср.род: {kept}\n\n')
    for op, src, tgt, cid in report:
        f.write(f'{op}\t{src}\t-> {tgt}\n')
print(f'переименовано: {renamed}, слито: {merged}, уже ср.род: {kept}')
if APPLY:
    conn.commit()
    print('APPLIED')
conn.close()
