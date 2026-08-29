# -*- coding: utf-8 -*-
"""Revision of dict auto-fill: reattach misplaced concepts, merge duplicates,
delete garbage genus concepts. Direct SQL + engine rebuild at the end."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

eng = JnanaEngine()
cur = eng.cur

def rid(term):
    """resolve loose"""
    t = eng.resolve(term)
    if t is None and term.lower().endswith('s'):
        t = eng.resolve(term[:-1])
    return t

def concept_by_nama(nama):
    cur.execute("SELECT dharma FROM concept WHERE nama=%s", (nama,))
    r = cur.fetchall()
    return [x[0] for x in r]

def reattach(cid, pid, report):
    if cid == pid:
        report.append(f"  skip self {cid}")
        return
    cur.execute("DELETE FROM edge WHERE dh1=%s AND kod='14'", (cid,))
    cur.execute("INSERT IGNORE INTO edge (dh1,kod,dh2,universum_id,status,source)"
                " VALUES (%s,'14',%s,3,'ok','dict:computerhope')", (cid, pid))
    report.append(f"  reattach {eng.names.get(cid,cid)} -> {eng.names.get(pid,pid)}")

def merge(dup, canon, report):
    """merge duplicate concept dup into canonical canon"""
    cur.execute("UPDATE IGNORE edge SET dh1=%s WHERE dh1=%s AND kod<>'14'", (canon, dup))
    cur.execute("DELETE FROM edge WHERE dh1=%s AND kod<>'14' AND dh1<>%s", (dup, canon))
    cur.execute("UPDATE IGNORE edge SET dh2=%s WHERE dh2=%s", (canon, dup))
    cur.execute("DELETE FROM edge WHERE dh2=%s", (dup,))
    # children of dup -> canon
    cur.execute("UPDATE edge SET dh2=%s WHERE dh2=%s AND kod='14'", (canon, dup))
    cur.execute("UPDATE IGNORE concept_term SET concept_id=%s WHERE concept_id=%s", (canon, dup))
    cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (dup,))
    cur.execute("DELETE FROM concept WHERE dharma=%s", (dup,))
    eng.reload()
    report.append(f"  MERGE dup#{dup} -> {eng.names.get(canon, canon)}")

def delete_concept(cid, report):
    cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (cid,))
    cur.execute("DELETE FROM edge WHERE dh1=%s OR dh2=%s", (cid, cid))
    cur.execute("DELETE FROM concept_path WHERE ancestor=%s OR descendant=%s", (cid, cid))
    cur.execute("DELETE FROM concept WHERE dharma=%s", (cid,))
    report.append(f"  DELETE concept #{cid}")

report = []

# ---------- A. re-parent misplaced concepts (audit A + corrections) ----------
RECLASS = {
    'executable': 'program', 'bug': 'error', 'pseudocode': 'source code',
    'exception': 'error', 'object code': 'source code', 'bytecode': 'source code',
    'intermediate language': 'programming language',
    'object-oriented programming language': 'programming language',
    'low-level programming language': 'programming language',
    'multi-paradigm programming language': 'programming language',
    'cross-platform programming language': 'programming language',
    'server-side interpreted scripting language': 'programming language',
    'open source scripting language': 'programming language',
    'functional programming language': 'programming language',
    'programming paradigm': 'paradigm', 'computer programming paradigm': 'paradigm',
    'programming language paradigm': 'paradigm',
    'software development method': 'method',
    'database system': 'database',
    'programming conditional statement': 'conditional statement',
    'runtime environment': 'program', 'compiler infrastructure': 'compiler',
    'programming interface': 'software interface',
    'computer programming algorithm': 'algorithm',
    'language construct': 'statement',
    'Server-side': 'property', 'control parameter': 'variable',
    'code block': 'source code', 'tool': 'program',
    'computer language': 'information object',  # fix wrong direction
    'formal language': 'information object',
    'programming language and variation': 'programming language',
    'Octave': 'programming language', 'LiveScript': 'programming language',
}
for nama, parent in RECLASS.items():
    cids = concept_by_nama(nama)
    pid = rid(parent)
    if pid is None:
        report.append(f"  !! parent not found: {parent}"); continue
    for cid in cids:
        reattach(cid, pid, report)

# ---------- B. garbage genera: move children, delete genus ----------
GARBAGE = {  # genus -> parent for its children
    'exact memory address': 'memory',           # Absolute address
    'extension': 'software',                    # ActiveX
    'solution': None,                           # algorithm (duplicate -> merge)
    'indexed': 'data structure',                # Array of pointers
    'memory starting point': 'memory',          # Base address
    'alternate version': 'statement',           # branch
    'experimental': 'programmer',               # Brooks, Curry
    'computer designated': 'hardware device',   # Build computer
    'nickname given': 'information object',     # Camel book
    'compound word': 'source code',             # CamelCase
    'process the computer takes': 'computing process',  # compilation
    'creation': 'computing process',            # Compile
    'fundamental principle': 'information object',      # Complementarity
    'study': 'information object',              # Computer science
    'order function calls': 'computing process',        # Control flow
    'central place': 'software',                # CPAN
    'primary location from': 'information object',      # Data source
    'control center': 'program',                # Dev Home
    'project': 'integrated development environment',    # Eclipse
    'operating system starting point': 'computing process',  # Epoch
    'value or data': 'operator',                # Equal
    'outcome': 'information object',            # Event
    'open source': 'programming language',      # F#
    'recursive mathematical function': None,    # keep genus; no action
    'boolean value returned': 'value',          # False
    'name given': 'information object',         # Foo
    'column or': 'database',                    # Foreign key
    'web-based hosting service': 'information object',  # GitHub
    'free app available': 'program',            # Grasshopper
    'variation': 'programming language',        # GW-BASIC
    'hex editor console': 'hex editor',         # Hiew
    'ability': 'information object',            # inheritance, polymorphism
    'realization': 'computing process',         # Instantiation
    'non-profit organization': 'program',       # Jupyter
    'improvised solution': 'information object',# Kludge
    'formal system': 'information object',      # Lambda calculus
    'best solution': 'information object',      # Local optimum
    'computer programming term': 'data structure',      # Mutex
    'undefined or unrepresentable value': 'value',      # NaN
    'section': 'file format',                   # Object module
    'term first thought': 'paradigm',           # Object-oriented
    'order operators': 'operator',              # Operator associatively
    'website': 'information object',            # Pastebin
    'structured library': 'software',           # PEAR
    'adjective': 'property',                    # Pythonic
    'completion': 'property',                   # Quick-and-dirty
    'standard model': 'specification',          # RDF
    'function or method': 'property',           # Recursive
    'general-purpose': 'programming language',  # Reia
    'interactive top level': 'program',         # REPL
    'management': 'development',                # version control
    'time': 'computing process',                # Run time
    'comparison': 'method',                     # Schema matching
    'small portion': 'source code',             # Snippet
    'programming and production': 'development',# Software engineering
    'cutoff point': 'memory',                   # Stack pointer
    'single line': None,                        # statement (duplicate -> merge)
    'indication': 'computing process',          # Submit
    'prefix or suffix': 'string',               # Substring
    'division': 'information object',           # Theoretical computer science
    'comprehensive software development system': 'programming language',  # Turbo Pascal
    'e-learning course provider': 'information object',   # Udacity
    'numeric': 'data type',                     # UInt8
    'website offering courses': 'information object',     # W3Schools
    'current era': 'information object',        # information age
    'change': 'computing process',              # bit flip
    'condition or exception': 'error',
    'process': 'computing process',
}

for genus, parent in GARBAGE.items():
    gids = concept_by_nama(genus)
    if not gids:
        continue
    for gid in gids:
        cur.execute("SELECT dh1 FROM edge WHERE kod='14' AND dh2=%s", (gid,))
        children = [r[0] for r in cur.fetchall()]
        for ch in children:
            ch_name = eng.names.get(ch)
            canon = rid(ch_name) if ch_name else None
            if canon is not None and canon != ch:
                merge(ch, canon, report)   # duplicate-name child -> merge
            elif parent:
                pid = rid(parent)
                if pid is None:
                    report.append(f"  !! parent missing {parent} for {ch_name}")
                    continue
                reattach(ch, pid, report)
            else:
                report.append(f"  keep child {ch_name} under {genus}")
        # delete genus if it has no children left and is in garbage set
        cur.execute("SELECT COUNT(*) FROM edge WHERE kod='14' AND dh2=%s", (gid,))
        left = cur.fetchone()[0]
        if left == 0 and parent is not None:
            delete_concept(gid, report)
            eng.reload()

eng.commit()
print('\n'.join(report))
print('---')
print('paths:', eng.rebuild())
eng.define()
print(eng.stats())
eng.close()
