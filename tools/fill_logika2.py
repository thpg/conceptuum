# -*- coding: utf-8 -*-
"""Универсум «логика» (U=5), проход 2: гл. IV — определение
и деление понятия (Виноградов, Кузьмин «Логика», 1954)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

U = 5

NEW = [
    # вспомогательные общие узлы
    ("правило", "rule", "мысль", 1),
    ("ошибка", "error", "сущее", 1),
    # определение
    ("логическое правило", "logical rule", "правило", U),
    ("логическая ошибка", "logical error", "ошибка", U),
    ("определение понятия", "definition of concept", "логический приём", U),
    ("определяемое понятие", "definiendum", "понятие", U),
    ("определяющее понятие", "definiens", "понятие", U),
    ("видовое отличие", "differentia (specific difference)", "существенный признак", U),
    ("ближайший род", "proximate genus", "родовое понятие", U),
    ("правило определения", "rule of definition", "логическое правило", U),
    # виды определений
    ("генетическое определение", "genetic definition", "определение понятия", U),
    ("предварительное определение", "preliminary definition", "определение понятия", U),
    ("номинальное определение", "nominal definition", "логический приём", U),
    # ошибки определения
    ("слишком широкое определение", "too wide definition", "логическая ошибка", U),
    ("слишком узкое определение", "too narrow definition", "логическая ошибка", U),
    ("круг в определении", "circular definition", "логическая ошибка", U),
    ("тавтология", "tautology (logic)", "круг в определении", U),
    # приёмы, заменяющие определение
    ("указание", "ostension (pointing)", "логический приём", U),
    ("описание", "description (logic)", "логический приём", U),
    ("характеристика", "characterization (logic)", "логический приём", U),
    ("различение", "distinguishing", "сравнение", U),
    # деление
    ("деление понятия", "division of concept", "логический приём", U),
    ("делимое понятие", "dividend concept", "родовое понятие", U),
    ("член деления", "member of division", "видовое понятие", U),
    ("основание деления", "basis of division", "признак", U),
    ("правило деления", "rule of division", "логическое правило", U),
    ("дихотомическое деление", "dichotomous division", "деление понятия", U),
    ("расчленение", "dissection (part-whole analysis)", "логический приём", U),
    # ошибки деления
    ("чрезмерно широкое деление", "too wide division", "логическая ошибка", U),
    ("слишком узкое деление", "too narrow division", "логическая ошибка", U),
    ("скачок в делении", "leap in division", "логическая ошибка", U),
    # классификация
    ("классификация", "classification", "деление понятия", U),
    ("естественная классификация", "natural classification", "классификация", U),
    ("искусственная классификация", "artificial classification", "классификация", U),
]

PREFLIGHT = ["логический приём", "понятие", "существенный признак",
             "родовое понятие", "видовое понятие", "признак", "сравнение",
             "мысль", "сущее"]

EDGES = [
    # состав определения
    ("определение понятия", "20", "видовое отличие", 95),
    ("определение понятия", "20", "ближайший род", 95),
    ("определяемое понятие", "62", "определяющее понятие", None),
    # состав деления
    ("деление понятия", "20", "основание деления", 95),
    ("делимое понятие", "74", "член деления", None),
    # приёмы, заменяющие определение — координаты
    ("указание", "61", "описание", None),
    ("описание", "61", "характеристика", None),
    ("характеристика", "61", "различение", None),
    ("указание", "61", "характеристика", None),
    # различение — разновидность сравнения (книга §6)
    ("различение", "61", "описание", None),
    # ошибки определения
    ("слишком широкое определение", "63", "слишком узкое определение", None),
    ("слишком широкое определение", "61", "круг в определении", None),
    ("слишком узкое определение", "61", "круг в определении", None),
    # ошибки деления
    ("чрезмерно широкое деление", "63", "слишком узкое деление", None),
    ("чрезмерно широкое деление", "61", "скачок в делении", None),
    ("слишком узкое деление", "61", "скачок в делении", None),
    # классификация
    ("естественная классификация", "63", "искусственная классификация", None),
    # определение и деление — взаимодополняющие приёмы (содержание/объём)
    ("определение понятия", "62", "деление понятия", None),
    # расчленение ≠ деление (части/целое против вида/рода)
    ("расчленение", "61", "деление понятия", None),
    ("расчленение", "20", "отношение части и целого", 95),
    # правила
    ("правило определения", "61", "правило деления", None),
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
