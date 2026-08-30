# -*- coding: utf-8 -*-
"""Оставшиеся инфинитивы → уже существующее существительное того же корня.
Если такого слова в базе нет — инфинитив не трогаем.

  python tools/merge_inf_to_noun.py
  python tools/merge_inf_to_noun.py apply
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymorphy3
from jnana_engine import JnanaEngine

APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"
morph = pymorphy3.MorphAnalyzer()

EXCLUDE = {
    ("носить", "нос"), ("висеть", "висок"), ("возить", "воз"),
    ("поливать", "пол"), ("поливать", "полка"),
    ("платить", "платок"), ("передать", "перед"),
    ("садиться", "сад"), ("отобрать", "отображение"),
    ("приходиться", "приход"), ("расти", "раса"), ("расти", "растение"),
    ("совать", "сова"), ("уловить", "уловка"),
    ("связывать", "связка"), ("складываться", "складка"),
    ("думать", "дума"), ("надевать", "над"), ("надеть", "над"),
    ("толковаться", "толкание"), ("сложиться", "сложение"),
    ("поступать", "постановка"), ("классифицировать", "классика"),
    ("учиться", "учить"), ("подвергнуться", "подвергнуть"),
    ("приходиться", "приходить"),
}

# однозначные пары, которые суффиксная генерация не собирает
SPECIAL = {
    "жить": "жизнь",
    "любить": "любовь",
    "учить": "учение",
    "читать": "чтение",
    "дышать": "дыхание",
    "летать": "полёт",
    "лететь": "полёт",
    "мыслить": "мысль",
    "бояться": "страх",
    "участвовать": "участие",
    "записать": "запись",
    "возрастать": "возрастание",
    "формулироваться": "формулировка",
    "характеризовать": "характеристика",
    "верить": "вера",
    "играть": "игра",
    "трудиться": "труд",
    "ударить": "удар",
    "судить": "суд",
    "пленить": "плен",
}

CONCRETE_ROOTS = {
    "вещь", "предмет", "часть тела", "организм", "вещество",
    "артефакт", "деталь", "природный объект",
}
# в эти узлы инфинитив не сливаем — это категории, не имя действия
HIGH_GENUS = {
    "сущее", "предмет", "вещь", "свойство", "явление",
    "действие", "процесс", "отношение", "состояние", "событие",
}

VERB_END = (
    "ироваться", "оваться", "еваться", "ировать",
    "ивать", "ывать", "овать", "евать",
    "аться", "иться", "еться", "уться", "яться",
    "ать", "ять", "ить", "еть", "уть", "ти", "чь",
)

# явные отглагольные суффиксы (не «а»/голое)
DEVERBAL = (
    "ирование", "ование", "евание", "ствование",
    "ение", "ание", "тие", "ствие", "ация", "яция",
    "истика", "ство", "ьба", "ость", "ие",
)


def is_inf(n):
    if " " in n or "-" in n:
        return False
    return any(p.tag.POS == "INFN" for p in morph.parse(n))


def inf_stems(v):
    v0 = re.sub(r"(ся|сь)$", "", v)
    stems = {v0}
    for e in VERB_END:
        rest_len = len(v0) - len(e)
        # длинный суффикс не режем до 3 букв (поливать↛пол, надевать↛над)
        min_rest = 4 if len(e) >= 4 else 3
        if v0.endswith(e) and rest_len >= min_rest:
            stems.add(v0[: -len(e)])
    extra = set()
    if v0.endswith("вести"):
        extra.add(v0[: -len("сти")] + "д")
    return {s for s in (stems | extra) if len(s) >= 3}


def candidate_forms(inf):
    forms = set()
    if inf in SPECIAL:
        forms.add(SPECIAL[inf])
    for s in inf_stems(inf):
        for suf in DEVERBAL:
            forms.add(s + suf)
        if len(s) >= 4:
            forms.add(s + "а")
            forms.add(s + "я")
            forms.add(s + "ка")
            forms.add(s + "ь")
        if len(s) >= 5:
            forms.add(s)
    raw = re.sub(r"(ся|сь)$", "", inf)
    if raw.endswith("ировать") and len(raw) > 9:
        s = raw[:-8]
        forms.update({s, s + "ация", s + "ирование"})
    return {f for f in forms if len(f) >= 3}


def in_concrete(eng, cid):
    x, g = cid, 0
    while x is not None and g < 16:
        if eng.names.get(x) in CONCRETE_ROOTS:
            return True
        ps = eng.parents.get(x)
        x = ps[0][0] if ps else None
        g += 1
    return False


def deverbal_rank(n):
    for i, s in enumerate(DEVERBAL):
        if n.endswith(s):
            return 100 - i
    return 0


def main():
    eng = JnanaEngine()
    names = dict(eng.names)
    by_name = {}
    for cid, n in names.items():
        by_name.setdefault(n, []).append(cid)

    infs = [(c, n) for c, n in names.items() if is_inf(n)]
    print(f"infinitives {len(infs)}")

    proposed, leftover = [], []
    for ic, inf in sorted(infs, key=lambda x: x[1]):
        hits = []
        for form in candidate_forms(inf):
            for nc in by_name.get(form, []):
                if nc == ic or is_inf(names[nc]):
                    continue
                if (inf, names[nc]) in EXCLUDE:
                    continue
                if names[nc] in HIGH_GENUS:
                    continue
                if in_concrete(eng, nc) and deverbal_rank(names[nc]) == 0:
                    continue
                hits.append(nc)
        by_n = {}
        for nc in hits:
            by_n.setdefault(names[nc], set()).add(nc)
        # омонимы одного имени — не угадываем
        uniq = {n: next(iter(ids)) for n, ids in by_n.items() if len(ids) == 1}
        if inf in SPECIAL and SPECIAL[inf] in uniq:
            nn = SPECIAL[inf]
            proposed.append((ic, uniq[nn], f"{inf} -> {nn}"))
            continue
        if len(uniq) == 1:
            nn, nc = next(iter(uniq.items()))
            proposed.append((ic, nc, f"{inf} -> {nn}"))
        elif len(uniq) > 1:
            ranked = sorted(uniq, key=deverbal_rank, reverse=True)
            if deverbal_rank(ranked[0]) > 0 and deverbal_rank(ranked[1]) == 0:
                nn = ranked[0]
                proposed.append((ic, uniq[nn], f"{inf} -> {nn}"))
            else:
                leftover.append(f"{inf} ambiguous {ranked}")
        else:
            leftover.append(inf)

    print(f"\nproposed: {len(proposed)}")
    for s, d, r in proposed:
        print(f"  {r}")
    print(f"\nleave as-is: {len(leftover)}")
    for line in leftover:
        print(f"  {line}")

    if not APPLY:
        print("\n(dry-run; pass 'apply' to write)")
        return

    merged = 0
    for s, d, r in proposed:
        if s not in eng.names or d not in eng.names:
            print("skip gone", r)
            continue
        ok, msg = eng.merge_concepts(s, d, keep_genus=False, reload=False)
        print(("OK" if ok else "NO"), msg)
        if ok:
            merged += 1
            eng.names.pop(s, None)
    eng.commit()
    eng.reload()
    npaths = eng.rebuild()
    weak = eng.define()
    print(f"merged {merged}; paths {npaths}; weak {len(weak)}")
    print(eng.stats())


if __name__ == "__main__":
    main()
