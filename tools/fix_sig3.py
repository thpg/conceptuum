# -*- coding: utf-8 -*-
"""Extend relevant with sig_object3 (actions may have phases as parts),
patch jnana_engine.py accordingly, insert the two pending edges."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql

con = pymysql.connect(host='127.0.0.1', user='root', password='123', database='jnana3', charset='utf8mb4')
cur = con.cursor()

cur.execute("SHOW COLUMNS FROM relevant")
cols = [r[0] for r in cur.fetchall()]
if 'sig_object3' not in cols:
    cur.execute("ALTER TABLE relevant ADD COLUMN sig_object3 INT NULL AFTER sig_object2")
    print("column sig_object3 added")
cur.execute("UPDATE relevant SET sig_object3=19 WHERE kod IN ('21','23','25','27')")
con.commit()
print("relevant updated:", cur.rowcount)

# --- patch engine ---
p = r'C:\Users\Игорь\Documents\kimi\workspace\jnana_engine.py'
src = open(p, encoding='utf-8').read()

if 'sig_object3' not in src:
    # SELECT: add column
    src = src.replace('sig_subject2, sig_object, sig_object2,',
                      'sig_subject2, sig_object, sig_object2, sig_object3,')
    # tuple indexes: sym/trans shift by 1
    src = re.sub(r'sym\s*=\s*r\[6\]', 'sym = r[7]', src)
    src = re.sub(r'trans\s*=\s*r\[7\]', 'trans = r[8]', src)
    # rules dict: add so3
    m = re.search(r'"so2":\s*r\[5\],', src)
    if m:
        src = src.replace(m.group(0), m.group(0) + ' "so3": r[6],')
    # validate(): extend ok_obj
    m2 = re.search(r'ok_obj\s*=.*\n', src)
    if m2:
        line = m2.group(0).rstrip('\n')
        if 'so3' not in line:
            src = src.replace(line, line + ' or (rule.get("so3") and self.in_subtree(b, rule["so3"]))')
    open(p, 'w', encoding='utf-8').write(src)
    print("engine patched")
else:
    print("engine already patched")

con.close()

# --- insert the two edges through a fresh engine ---
sys.path.insert(0, r'C:\Users\Игорь\Documents\kimi\workspace')
import importlib, jnana_engine
importlib.reload(jnana_engine)
eng = jnana_engine.JnanaEngine()

pending = [("compilation", "parsing", "21"),
           ("parsing", "lexical analysis", "21")]
for a, b, kod in pending:
    r = eng.propose(a, kod, b, universum_id=3, source="dict:computerhope",
                    rationale="process phase decomposition", auto=True)
    print(a, "->", b, kod, "=>", r)

eng.rebuild()
eng.define()
print(eng.stats())
eng.close()
