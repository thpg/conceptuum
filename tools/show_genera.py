# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql
c = pymysql.connect(host='127.0.0.1', user='root', password='123', database='jnana3', charset='utf8mb4')
cur = c.cursor()
cur.execute("SELECT dh2, COUNT(*) FROM edge WHERE kod='14' AND status='ok' GROUP BY dh2")
rows = [(d, k) for d, k in cur.fetchall() if k >= 5]
rows.sort(key=lambda x: -x[1])
ids = ','.join(str(d) for d, _ in rows)
cur.execute('SELECT dharma, nama, universum_id FROM concept WHERE dharma IN (%s)' % ids)
names = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
for d, k in rows:
    n = names.get(d)
    print(f'{d:5d} u{n[1]} {n[0]:30s} видов:{k}')
