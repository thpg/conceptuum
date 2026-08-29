# -*- coding: utf-8 -*-
# Ревизия ближайшего рода (genus proximum) для кластеров время/пространство:
#   январь -> месяц -> период времени (а не январь -> период времени)
#   север  -> сторона света -> направление
# Плюс: недостающие члены шкал (месяцы, среда-день, юг), слияние синонимов
# (столетие -> век, время года -> сезон).
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='123',
                       database='jnana3', charset='utf8mb4')
cur = conn.cursor()
cur.execute("SELECT dharma, nama FROM concept WHERE universum_id=1")
ids = {n: d for d, n in cur.fetchall()}

def add_concept(nama, parent, en, terms_ru=()):
    """Новое понятие U1 + род 14 + термины ru/en. Возвращает id."""
    cur.execute("SELECT COALESCE(MAX(dharma),0)+1 FROM concept")
    cid = cur.fetchone()[0]
    cur.execute("INSERT INTO concept (dharma, nama, universum_id) VALUES (%s,%s,1)", (cid, nama))
    cur.execute("INSERT INTO edge (dh1, kod, dh2, universum_id, status, source) VALUES (%s,'14',%s,1,'ok','genus-fix')",
                (cid, ids[parent]))
    cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')", (cid, nama))
    cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'en')", (cid, en))
    for t in terms_ru:
        cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')", (cid, t))
    ids[nama] = cid
    return cid

def move(child, new_parent):
    cur.execute("UPDATE edge SET dh2=%s WHERE dh1=%s AND kod='14'", (ids[new_parent], ids[child]))
    print(f'  move: {child} -> {new_parent}')

def merge(gone, keep):
    """gone становится термином keep; понятие gone удаляется."""
    cur.execute("SELECT term, lang FROM concept_term WHERE concept_id=%s", (ids[gone],))
    for term, lang in cur.fetchall():
        cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)", (ids[keep], term, lang))
    cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')", (ids[keep], gone))
    cur.execute("DELETE FROM edge WHERE dh1=%s OR dh2=%s", (ids[gone], ids[gone]))
    cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (ids[gone],))
    cur.execute("DELETE FROM concept WHERE dharma=%s", (ids[gone],))
    print(f'  merge: {gone} -> {keep}')

# 1. новые роды
add_concept('день недели', 'период времени', 'day of the week')
add_concept('часть суток', 'период времени', 'part of the day')
add_concept('сторона света', 'направление', 'cardinal direction')

# 2. переподчинение — ближайший род
for m in ['январь', 'апрель', 'июль', 'октябрь', 'декабрь']:
    move(m, 'месяц')
for d in ['понедельник', 'вторник', 'четверг', 'пятница', 'суббота', 'воскресение']:
    move(d, 'день недели')
for p in ['утро', 'вечер', 'ночь']:
    move(p, 'часть суток')
for s in ['север', 'запад', 'восток']:
    move(s, 'сторона света')

# 3. недостающие члены шкал
MONTHS = [('февраль', 'February'), ('март', 'March'), ('май', 'May'), ('июнь', 'June'),
          ('август', 'August'), ('сентябрь', 'September'), ('ноябрь', 'November')]
for ru, en in MONTHS:
    add_concept(ru, 'месяц', en)
add_concept('юг', 'сторона света', 'south')
# «среда» как день недели — омоним существующей «среды» (environment): отдельное понятие
add_concept('среда', 'день недели', 'Wednesday')

# 4. слияние синонимов
merge('столетие', 'век')
merge('время года', 'сезон')

conn.commit()
print('OK')
conn.close()
