# -*- coding: utf-8 -*-
"""Mass-apply computerhope facts to jnana3 via JnanaEngine.
1. genus isa edges (extracted + manual fixes + keyword fallback)
2. synonyms & expansions as concept_term rows
"""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

eng = JnanaEngine()

# ---------- 1. canonical genus fixes ----------
MANUAL_FIX = {
    'computer language programmers use': 'computer language',
    'table or list': 'table',
    'program or utility': 'program',
    'hardware device or portion': 'hardware device',
    'individual who is': None, 'individual': None, 'nickname': None,
    'data type definition': 'data type',
    'conditional statement in programming': 'conditional statement',
    'technique in image processing': 'technique',
    'scenario in electronic processing': 'scenario',
    'single letter or symbol': 'character',
    'special symbol or word': None,
    'named unit': 'variable',
    'portion': None, 'group': None, 'order': None,
    'overall process': 'computing process',
    'specific encoding': 'encoding',
    'open-source server': 'server',
    'client-side scripting language specification': 'specification',
    ' variable': 'variable',
    'program error': 'error',
    'program or script': None, 'program language or script': None,
    'request': None, 'mechanism': 'method',
}
TERM_FIX = {  # per-term override of genus
    'Programming languages': 'computer language',
    'Developer': None, 'System analyst': None, 'Dragon book': None,
    'DWORD': 'data type', 'QWORD': 'data type',
    'If statement': 'conditional statement',
    'Loop': 'statement',
    'Input/output statement': 'statement',
    'Logical operation': None, 'Repeat counter': None,
    'Function call': 'statement',
    'Private variable': 'variable',
    'Race condition': 'error',
    'Endian': 'data type',
    'Operator precedence': None,
}
# parent for genus concepts that must be CREATED (genus -> existing parent term)
GENUS_PARENT = {
    'computer language': 'programming language',
    'paradigm': 'method', 'technique': 'method', 'approach': 'method',
    'style': 'method', 'programming technique': 'method',
    'matrix': 'data structure', 'table': 'data structure',
    'classification': 'information object', 'specification': 'information object',
    'standard': 'specification', 'encoding': 'specification',
    'problem': 'information object', 'scenario': 'information object',
    'element': 'information object', 'graphical representation': 'information object',
    'software architecture': 'information object',
    'command': 'statement', 'string': 'data type',
    'high-level programming language': 'programming language',
    'abstract programming language': 'programming language',
    'computer programming language': 'programming language',
    'program language': 'programming language',
    'application': 'program', 'computer program': 'program',
    'utility': 'program', 'server': 'program', 'package': 'software',
    'software compiler': 'compiler',
    'punctuation mark': 'character',
    'bitwise operation': 'computing process',
    'computer error': 'error',
    'hardware device': 'предмет',
    'object': 'information object',
    'conditional block': 'conditional statement',
    'international computing society': None,  # skip
}
# ---------- 2. keyword fallback for terms without genus ----------
FALLBACK = [
    (r'compiler', 'compiler'), (r'interpreter', 'program'),
    (r'language', 'programming language'),
    (r'framework|library', 'software'),
    (r'editor|tool|utility|application|\bide\b|debugger|generator|analyzer|manager|browser', 'program'),
    (r'array|list|tree|stack|queue|matrix|table|record|field|structure', 'data structure'),
    (r'data type|\btype\b|integer|string|boolean|float|byte|word|number', 'data type'),
    (r'error|bug|exception|warning|crash|fault', 'error'),
    (r'operator', 'operator'),
    (r'statement|keyword|directive|instruction', 'statement'),
    (r'variable|constant|parameter|argument|identifier|flag|counter', 'variable'),
    (r'expression', 'expression'),
    (r'character|symbol|delimiter|bracket|parenthesis|brace|slash|quote|hyphen|dash|asterisk|tilde|caret', 'character'),
    (r'algorithm|sort|search|hash|heuristic', 'algorithm'),
    (r'function|method|procedure|routine|callback|recursion|macro|subroutine', 'method'),
    (r'code|syntax|notation|comment', 'source code'),
    (r'database|sql|query|index', 'database'),
    (r'process|thread|execution|runtime|compile|build', 'computing process'),
    (r'memory|address|pointer|buffer|register|cache', 'data structure'),
    (r'program|script', 'program'),
    (r'paradigm|programming|coding|development', 'development'),
]
DEFAULT_PARENT = 'information object'

def norm(term):
    return term.strip()

def resolve_loose(term):
    t = norm(term)
    cid = eng.resolve(t)
    if cid is None and t.lower().endswith('s') and len(t) > 3:
        cid = eng.resolve(t[:-1])
        if cid is None and t.lower().endswith('es'):
            cid = eng.resolve(t[:-2])
    return cid

def ensure_genus(g):
    """Return concept id of genus, creating it if we know where to hang it."""
    cid = resolve_loose(g)
    if cid is not None:
        return cid
    parent = GENUS_PARENT.get(g, DEFAULT_PARENT)
    if parent is None:
        return None
    pid = resolve_loose(parent)
    if pid is None:
        pid = eng.resolve(DEFAULT_PARENT)
    cid, msg = eng.add_concept(g, pid, lang='en', universum_id=3)
    log.append(f"  +род {g} -> {parent}")
    return cid

facts = [json.loads(l) for l in open('dict_facts.jsonl', encoding='utf-8')]
genus3 = {d['term']: d['genus'] for d in json.load(open('dict_genus3.json', encoding='utf-8'))}

log, stats = [], {'new': 0, 'linked': 0, 'syn': 0, 'exp': 0, 'skip': 0}

for f in facts:
    term = norm(f['term'])
    g = genus3.get(term)
    if term in TERM_FIX:
        g = TERM_FIX[term]
    elif g and g in MANUAL_FIX:
        g = MANUAL_FIX[g]
    if g:
        g = MANUAL_FIX.get(g, g)
        if g:
            g = g.strip()

    cid = resolve_loose(term)
    gid = None
    if g:
        gid = ensure_genus(g)

    if cid is None:
        # create the term concept
        if gid is not None:
            parent = gid
        else:
            parent = None
            tl = term.lower()
            for pat, p in FALLBACK:
                if re.search(pat, tl):
                    parent = resolve_loose(p)
                    if parent: break
            if parent is None:
                parent = eng.resolve(DEFAULT_PARENT)
        cid, msg = eng.add_concept(term, parent, lang='en', universum_id=3)
        if isinstance(cid, int):
            stats['new'] += 1
            if gid is not None:
                stats['linked'] += 1
        else:
            stats['skip'] += 1
            log.append(f"  ! {term}: {msg}")
            continue
    else:
        # existing concept: add isa edge to genus if we have one
        if gid is not None and gid != cid:
            r = eng.propose(cid, '14', gid, universum_id=3,
                            source='dict:computerhope', auto=True,
                            rationale='genus from article first sentence')
            if isinstance(r[0], int):
                stats['linked'] += 1

    # synonyms & expansion
    syns = list(f.get('synonyms') or [])
    if f.get('expansion'):
        syns.append(f['expansion'])
    for s in syns:
        s = norm(s)
        if not s or s.lower() == term.lower() or len(s) > 60:
            continue
        existing = eng.resolve(s)
        if existing is not None and existing != cid:
            continue  # homonym, skip to avoid wrong merge
        if existing == cid:
            continue
        eng.cur.execute(
            "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'en')",
            (cid, s))
        eng.reload()
        if f.get('expansion') == s:
            stats['exp'] += 1
        else:
            stats['syn'] += 1

eng.commit()
eng.rebuild()
eng.define()
print('STATS:', stats)
print('LOG (first 30):')
for l in log[:30]:
    print(l)
print(eng.stats())
eng.close()
