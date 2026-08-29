# -*- coding: utf-8 -*-
"""Миграция 4X -> 40 + strength (2026-08-29). Рёбер 4X в базе нет,
чистим только relevant и доводим описание 40."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123',
                       db='jnana3', charset='utf8mb4')
cur = conn.cursor()
cur.execute("DELETE FROM relevant WHERE kod IN ('41','43','45','47','48')")
print('deleted old 4X rows:', cur.rowcount)
cur.execute(
    "UPDATE relevant SET long_name='overlap',"
    " description='Объёмы понятий частично пересекаются. Степень пересечения —"
    " в strength (0-100): 70 = сильное, 50 = примерно половина,"
    " 5 = незначительное, NULL = пересечение возможно, но не зафиксировано.',"
    " sample='студент — спортсмен (70); певец — шахтёр (5).',"
    " is_symmetric=1 WHERE kod='40'")
print('updated 40:', cur.rowcount)
conn.commit()
cur.execute("SELECT kod, long_name, is_symmetric FROM relevant ORDER BY kod")
for r in cur.fetchall():
    print(r)
conn.close()
