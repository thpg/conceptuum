# -*- coding: utf-8 -*-
"""Универсум «логика» (U=5), проход 4: гл. VII — основные
законы логического мышления. Фикс связей прохода 3 (74)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

U = 5

NEW = [
    ("явление", "phenomenon", "сущее", 1),
    # четыре закона
    ("закон тождества", "law of identity", "логический закон", U),
    ("закон противоречия", "law of contradiction", "логический закон", U),
    ("закон исключённого третьего", "law of excluded middle", "логический закон", U),
    ("закон достаточного основания", "law of sufficient reason", "логический закон", U),
    # ошибки против законов
    ("подмена понятия", "substitution of concept", "логическая ошибка", U),
    ("двусмысленность", "equivocation", "логическая ошибка", U),
    ("софизм", "sophism", "логическая ошибка", U),
    # основания
    ("причина", "cause", "явление", U),
    ("следствие", "effect", "явление", U),
    ("причинная связь", "causal connection", "отношение", U),
    ("аксиома", "axiom", "суждение", U),
    ("логическое основание", "logical ground (reason)", "суждение", U),
]

# реальное основание = причина (книга гл. VII §5): синоним-термин
SYNONYMS = [("причина", "реальное основание", "ru"),
            ("причина", "real ground", "en")]

PREFLIGHT = ["логический закон", "логическая ошибка", "отношение", "сущее",
             "суждение", "определённость", "непротиворечивость",
             "последовательность", "обоснованность",
             "условное суждение", "основание условного суждения",
             "следствие условного суждения", "обращение", "превращение",
             "подлежащее", "сказуемое", "связка"]

EDGES = [
    # фикс прохода 3 (объекты вне сигнатур 20/27 -> 74 dependence)
    ("условное суждение", "74", "основание условного суждения", None),
    ("условное суждение", "74", "следствие условного суждения", None),
    ("обращение", "74", "подлежащее", None),
    ("обращение", "74", "сказуемое", None),
    ("превращение", "74", "связка", None),
    # законы — координаты
    ("закон тождества", "61", "закон противоречия", None),
    ("закон тождества", "61", "закон исключённого третьего", None),
    ("закон тождества", "61", "закон достаточного основания", None),
    ("закон противоречия", "61", "закон исключённого третьего", None),
    ("закон противоречия", "61", "закон достаточного основания", None),
    ("закон исключённого третьего", "61", "закон достаточного основания", None),
    # закон -> коренная черта мышления (книга §1, §6)
    ("закон тождества", "20", "определённость", 95),
    ("закон противоречия", "20", "непротиворечивость", 95),
    ("закон исключённого третьего", "20", "последовательность", 95),
    ("закон достаточного основания", "20", "обоснованность", 95),
    # ошибки
    ("подмена понятия", "61", "двусмысленность", None),
    ("подмена понятия", "61", "софизм", None),
    ("двусмысленность", "61", "софизм", None),
    ("софизм", "20", "подмена понятия", 95),
    # причина/следствие
    ("причина", "70", "следствие", None),
    ("причина", "62", "следствие", None),
    ("причинная связь", "74", "причина", None),
    ("причинная связь", "74", "следствие", None),
    ("закон достаточного основания", "74", "причинная связь", None),
    # основания
    ("логическое основание", "61", "аксиома", None),
]

CLOSED = [ru for ru, en, p, u in NEW]


def main():
    eng = JnanaEngine(pref_lang="ru")
    missing = [t for t in PREFLIGHT if not eng.resolve(t)]
    if missing:
        print("PREFLIGHT MISSING:", ", ".join(missing))
    added = 0
    for ru, en, parent, u in NEW:
        cid, msg = eng.add_concept(ru, parent, lang="ru", universum_id=u,
                                   terms=[(en, "en")] if en else None)
        if cid is None:
            print("  x NEW:", msg)
        elif "already" in msg:
            print("  EXISTS:", ru)
        else:
            added += 1
    for base, term, lg in SYNONYMS:
        cid = eng.resolve(base)
        if cid:
            eng.cur.execute(
                "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
                (cid, term, lg))
            print("  +term:", term, "->", base)
    eng.commit()
    print(f"concepts: +{added}")

    ok = rej = 0
    for a, kod, b, st in EDGES:
        eid, msg = eng.propose(a, kod, b, strength=st, universum_id=U,
                               source="llm:fill:self", auto=True)
        if eid:
            ok += 1
        elif "duplicate" in msg:
            pass
        else:
            rej += 1
            print("  x EDGE:", msg)
    eng.commit()
    print(f"edges: +{ok} ok, {rej} rejected of {len(EDGES)}")

    closed = 0
    for t in CLOSED:
        cid = eng.resolve(t)
        if cid:
            eng.set_processed(cid)
            closed += 1
        else:
            print("  ? CLOSED not found:", t)
    eng.commit()
    print(f"processed: {closed} of {len(CLOSED)}")

    print("paths:", eng.rebuild())
    eng.define()
    eng.commit()
    print(eng.stats())
    eng.close()


if __name__ == "__main__":
    main()
