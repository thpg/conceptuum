# -*- coding: utf-8 -*-
"""Final cleanup: drop redundant isa parents, delete childless garbage genera,
merge IDE/integrated development environment duplicate."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

eng = JnanaEngine(); cur = eng.cur
log = []

def cid_of(nama):
    cur.execute("SELECT dharma FROM concept WHERE nama=%s", (nama,))
    r = cur.fetchone()
    return r[0] if r else None

def drop_edge(child, parent):
    c, p = cid_of(child), cid_of(parent)
    if c and p:
        cur.execute("DELETE FROM edge WHERE dh1=%s AND dh2=%s AND kod='14'", (c, p))
        log.append(f"drop {child} -/-> {parent}")

def set_parent(child, parent):
    c, p = cid_of(child), cid_of(parent)
    if c and p:
        cur.execute("DELETE FROM edge WHERE dh1=%s AND kod='14'", (c,))
        cur.execute("INSERT IGNORE INTO edge (dh1,kod,dh2,universum_id,status,source) VALUES (%s,'14',%s,3,'ok','dict:computerhope')", (c, p))
        log.append(f"set {child} -> {parent}")

def del_if_childless(nama):
    c = cid_of(nama)
    if not c: return
    cur.execute("SELECT COUNT(*) FROM edge WHERE dh2=%s AND kod='14'", (c,))
    if cur.fetchone()[0] == 0:
        cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (c,))
        cur.execute("DELETE FROM edge WHERE dh1=%s OR dh2=%s", (c, c))
        cur.execute("DELETE FROM concept WHERE dharma=%s", (c,))
        log.append(f"delete genus {nama}")

DROPS = [
    ('compilation', 'process the computer takes'),
    ('git', 'distributed revision control system'),
    ('programming language', 'computer language'),
    ('Java', 'programming language'),
    ('data type', 'language construct'),
    ('data structure', 'predefined format'),
    ('algorithm', 'solution'),
    ('machine language', 'collection'),
    ('high-level language', 'computer programming language'),
    ('procedural language', 'computer programming language'),
    ('Pascal', 'high-level programming language'),
    ('PHP', 'server-side interpreted scripting language'),
    ('C++', 'high-level programming language'),
    ('Kotlin', 'cross-platform programming language'),
    ('Objective-C', 'object-oriented language'),
    ('Lisp', 'high-level programming language'),
    ('Clojure', 'dialect'),
    ('Erlang', 'functional programming language'),
    ('XML', 'specification'),
    ('statement', 'single line'),
    ('endless loop', 'continuous repetition'),
    ('argument', 'language construct'),
    ('inheritance', 'ability'), ('polymorphism', 'ability'),
    ('floating-point', 'variable'),
    ('boolean', 'data'),
    ('intermediate language', 'information object'),
    ('fuzz testing', 'technique'),
    ('code refactoring', 'development'),
    ('imperative programming', 'paradigm'),
    ('declarative programming', 'computer programming paradigm'),
    ('object-oriented programming', 'programming language paradigm'),
    ('functional programming', 'style'),
    ('logic programming', 'computer programming paradigm'),
    ('event-driven programming', 'computer programming paradigm'),
    ('debugger', 'program'), ('linker', 'computer program'), ('assembler', 'program'),
    ('Eclipse', 'project'), ('REPL', 'interactive top level'),
    ('bubble sort', 'algorithm'),
    ('branch', 'information object'), ('branch', 'alternate version'),
]
for c, p in DROPS:
    drop_edge(c, p)

set_parent('branch', 'statement')
set_parent('simple sorting technique', 'algorithm')

# merge 'integrated development environment' into 'IDE'
ide, ide2 = cid_of('IDE'), cid_of('integrated development environment')
if ide and ide2:
    cur.execute("UPDATE IGNORE edge SET dh2=%s WHERE dh2=%s", (ide, ide2))
    cur.execute("DELETE FROM edge WHERE dh2=%s", (ide2,))
    cur.execute("UPDATE IGNORE concept_term SET concept_id=%s WHERE concept_id=%s", (ide, ide2))
    cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (ide2,))
    cur.execute("DELETE FROM edge WHERE dh1=%s", (ide2,))
    cur.execute("DELETE FROM concept WHERE dharma=%s", (ide2,))
    log.append("merged integrated development environment -> IDE")
set_parent('IntelliJ IDEA', 'IDE')
set_parent('Eclipse', 'IDE')

for g in ('process the computer takes', 'solution', 'single line',
          'distributed revision control system', 'server-side interpreted scripting language',
          'cross-platform programming language', 'functional programming language',
          'continuous repetition', 'predefined format', 'alternate version',
          'ability', 'interactive top level', 'open-source version control system'):
    del_if_childless(g)

eng.commit()
print('\n'.join(log))
print('---')
print('paths:', eng.rebuild())
eng.define()
eng.reload()
cur.execute("SELECT dh1,COUNT(*) c FROM edge WHERE kod='14' GROUP BY dh1 HAVING c>1")
print('multi-parent left:', len(cur.fetchall()))
print(eng.stats())
eng.close()
