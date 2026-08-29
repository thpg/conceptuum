# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql
c = pymysql.connect(host='127.0.0.1', user='root', password='123', database='jnana3', charset='utf8mb4')
cur = c.cursor()
def kids(pid, label):
    cur.execute("SELECT c.dharma, c.nama FROM edge e JOIN concept c ON c.dharma=e.dh1 WHERE e.kod='14' AND e.status='ok' AND e.dh2=%s ORDER BY c.nama", (pid,))
    print(f'--- {label} ({pid}):')
    for r in cur.fetchall():
        print('   ', r[0], r[1])
kids(16, 'сущее')
kids(2535, 'явление')
kids(18, 'свойство')
kids(19, 'действие')
kids(1853, 'знание')
kids(20, 'отношение')
for n in ['общество', 'коллектив', 'информация', 'пространство', 'множество', 'качество']:
    cur.execute('SELECT dharma, universum_id FROM concept WHERE nama=%s', (n,))
    print(n, '->', cur.fetchall())
