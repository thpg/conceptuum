# -*- coding: utf-8 -*-
# Фикс «закрытого носителя»: прилагательное-понятие, чей носитель — один класс,
# получает родом класс носителя, а свойство уходит в отдельное ребро.
# Правило: судоходное -> водоём (README, design notes).
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='123',
                       database='jnana3', charset='utf8mb4')
cur = conn.cursor()

# --- новая шкала: чистота -> состояние ---
cur.execute("SELECT COALESCE(MAX(dharma),0)+1 FROM concept")
cid = cur.fetchone()[0]
cur.execute("INSERT INTO concept (dharma, nama, universum_id) VALUES (%s,'чистота',1)", (cid,))
cur.execute("INSERT INTO edge (dh1, kod, dh2, universum_id, status, source) VALUES (%s,'14',2633,1,'ok','genus-fix')", (cid,))
cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,'чистота','ru')", (cid,))
cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,'cleanliness','en')", (cid,))
print('+ создано: чистота', cid, '-> состояние')

def move(child, parent):
    cur.execute("UPDATE edge SET dh2=%s WHERE dh1=%s AND kod='14'", (parent, child))
    print(f'  род: {child} -> {parent}')

def attr(subj, kod, obj, strength=None):
    cur.execute("SELECT COUNT(*) FROM edge WHERE dh1=%s AND kod=%s AND dh2=%s AND status='ok'", (subj, kod, obj))
    if cur.fetchone()[0]:
        print(f'  пропуск (есть): {subj} -{kod}-> {obj}'); return
    cur.execute("INSERT INTO edge (dh1,kod,dh2,universum_id,status,source,strength) VALUES (%s,%s,%s,1,'ok','bearer-fix',%s)",
                (subj, kod, obj, strength))
    print(f'  edge: {subj} -{kod}-> {obj} strength={strength}')

# --- переносы рода (носитель закрыт) ---
MOVES = [
 # (child, new_parent, property edge: (kod, object, strength) or None)
 ('жилое',            'помещение',          ('21', 'жить', None)),
 ('отопительное',     'устройство',         ('21', 'нагревание', None)),
 ('втяжное',          'устройство',         None),
 ('удушливое',        'воздух',             ('71', 'дыхание', None)),
 ('гусеничное',       'транспортное средство', ('20', 'гусеница', None)),
 ('хищное',           'животное',           ('20', 'охота', 90)),
 ('нехищное',         'животное',           ('20', 'охота', 0)),
 ('рогатое',          'животное',           ('20', 'рог', None)),
 ('жвачное',          'животное',           None),
 ('позвоночное',      'животное',           ('20', 'позвоночник', None)),
 ('беспозвоночное',   'животное',           ('20', 'позвоночник', 0)),
 ('одноклеточное',    'организм',           ('20', 'клетка', None)),
 ('ластоногое',       'животное',           None),
 ('цветковое',        'растение',           ('20', 'цветок', None)),
 ('перелётное',       'птица',              None),   # полёт наследуется от птицы (95%)
 ('высокоорганизованное', 'организм',       None),
 ('больное',          'организм',           ('20', 'болезнь', 90)),
 ('убитое',           'организм',           None),
 ('грязное',          cid,                  None),   # -> чистота
 ('чистое',           cid,                  None),
]
ids = {}
cur.execute("SELECT dharma, nama FROM concept")
for d, n in cur.fetchall():
    ids.setdefault(n, d)

for child, parent, edge in MOVES:
    pid = parent if isinstance(parent, int) else ids[parent]
    move(ids[child], pid)
    if edge:
        kod, obj, st = edge
        attr(ids[child], kod, ids[obj], st)

# --- дополнительные связи без смены рода ---
attr(ids['вооружённое'], '20', ids['оружие'], 90)
attr(ids['невооружённое'], '20', ids['оружие'], 0)
attr(ids['убийство'], '70', ids['убитое'], None)   # убийство производит убитое

# --- пары несовместимости ---
for a, b, kod in [('хищное','нехищное','64'), ('позвоночное','беспозвоночное','64'),
                  ('вооружённое','невооружённое','64'), ('грязное','чистое','63')]:
    attr(ids[a], kod, ids[b])

conn.commit()
print('готово')
conn.close()
