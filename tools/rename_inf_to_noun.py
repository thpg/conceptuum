# -*- coding: utf-8 -*-
"""Канон оставшихся инфинитивов — отглагольное существительное.

Если существительное уже есть в базе — сливаем.
Если нет — переименовываем узел (инфинитив остаётся термином).
Согласиться → согласие и т.п.

  python tools/rename_inf_to_noun.py
  python tools/rename_inf_to_noun.py apply
"""
import io
import os
import re
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymorphy3
from jnana_engine import JnanaEngine

APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"
morph = pymorphy3.MorphAnalyzer()

HIGH = {
    "сущее", "предмет", "вещь", "свойство", "явление",
    "действие", "процесс", "отношение", "состояние", "событие",
}

# явный канон для возвратных и прочих, где суффикс врёт
MAP = {
    "согласиться": "согласие",
    "отказаться": "отказ",
    "отказываться": "отказ",
    "пытаться": "попытка",
    "собраться": "собрание",
    "собираться": "собрание",
    "улыбнуться": "улыбка",
    "касаться": "касание",
    "колебаться": "колебание",
    "нуждаться": "нужда",
    "ссылаться": "ссылка",
    "стремиться": "стремление",
    "увлекаться": "увлечение",
    "готовиться": "подготовка",
    "заниматься": "занятие",
    "поссориться": "ссора",
    "потребоваться": "требование",
    "познакомиться": "знакомство",
    "равняться": "равенство",
    "разниться": "различие",
    "разобраться": "разбор",
    "обратиться": "обращение",
    "понизиться": "понижение",
    "разлагаться": "разложение",
    "учиться": "учение",
    "взорваться": "взрыв",
    "кончаться": "окончание",
    "пересечься": "пересечение",
    "пересекаться": "пересечение",
    "перекрещиваться": "перекрещивание",
    "светиться": "свечение",
    "сжиматься": "сжатие",
    "сопровождаться": "сопровождение",
    "развёртываться": "развёртывание",
    "совершенствоваться": "совершенствование",
    "предъявляться": "предъявление",
    "произноситься": "произнесение",
    "растворяться": "растворение",
    "стараться": "старание",
    "толковаться": "толкование",
    "опускаться": "опускание",
    "оформиться": "оформление",
    "смыкаться": "смыкание",
    "соприкасаться": "соприкосновение",
    "размагнититься": "размагничивание",
}


def is_inf(n):
    if " " in n or "-" in n:
        return False
    return any(p.tag.POS == "INFN" for p in morph.parse(n))


def real_noun(w):
    """Словарное существительное (лемма = само слово), не выдумка на -ка."""
    best = 0
    for p in morph.parse(w):
        if p.tag.POS != "NOUN":
            continue
        if p.normal_form.replace("ё", "е") != w.replace("ё", "е"):
            continue
        best = max(best, p.score)
    return best >= 0.45


def auto_noun(inf):
    """Согласиться → согласие: -ить даёт -ие / -ение, что есть в словаре."""
    v = re.sub(r"(ся|сь)$", "", inf)
    cands = []
    if v.endswith("ить") and len(v) > 5:
        s = v[:-3]
        cands = [s + "ие", s + "ение"]
    elif v.endswith("ать") and len(v) > 5:
        s = v[:-3]
        cands = [s + "ание"]
    elif v.endswith("еть") and len(v) > 5:
        s = v[:-3]
        cands = [s + "ение"]
    elif v.endswith("овать") and len(v) > 8:
        s = v[:-5]
        cands = [s + "ование"]
    for c in cands:
        if c not in HIGH and real_noun(c):
            return c
    return None


def main():
    eng = JnanaEngine()
    by_name = defaultdict(list)
    for cid, n in eng.names.items():
        by_name[n].append(cid)

    infs = {n: c for c, n in eng.names.items() if is_inf(n)}
    plan = []  # (inf_cid, noun, 'merge'|'rename')

    targets = dict(MAP)

    # группа: несколько инфинитивов → одно существительное
    groups = defaultdict(list)
    for inf, noun in targets.items():
        if inf not in infs:
            continue
        if noun in HIGH:
            continue
        groups[noun].append(inf)

    for noun, inflist in sorted(groups.items()):
        existing = [c for c in by_name.get(noun, []) if c not in infs.values()]
        if existing:
            dst = existing[0]
            for inf in inflist:
                plan.append((infs[inf], dst, noun, "merge"))
        else:
            first, *rest = inflist
            plan.append((infs[first], None, noun, "rename"))
            for inf in rest:
                plan.append((infs[inf], infs[first], noun, "merge-after-rename"))

    print("plan", len(plan))
    for cid, dst, noun, kind in plan:
        print(f"  {kind:20s} {eng.names[cid]:30s} -> {noun}")

    leftover = sorted(set(infs) - {eng.names[c] for c, *_ in plan})
    print(f"\nleave {len(leftover)} infinitives")
    print(", ".join(leftover[:60]))

    if not APPLY:
        print("\n(dry-run; pass 'apply' to write)")
        return

    # rename first so merge-after-rename sees the new nama
    renamed_id = {}  # old inf nama -> cid (same cid, new name)
    n_ren, n_mer = 0, 0
    for cid, dst, noun, kind in plan:
        if kind == "rename":
            ok, msg = eng.rename_concept(cid, noun, reload=False)
            print(("OK" if ok else "NO"), msg)
            if ok:
                n_ren += 1
                renamed_id[noun] = cid
                eng.names[cid] = noun
        elif kind == "merge":
            ok, msg = eng.merge_concepts(cid, dst, keep_genus=False, reload=False)
            print(("OK" if ok else "NO"), msg)
            if ok:
                n_mer += 1
                eng.names.pop(cid, None)
        elif kind == "merge-after-rename":
            dst2 = renamed_id.get(noun)
            if not dst2:
                print("NO no renamed target", noun)
                continue
            ok, msg = eng.merge_concepts(cid, dst2, keep_genus=False, reload=False)
            print(("OK" if ok else "NO"), msg)
            if ok:
                n_mer += 1
                eng.names.pop(cid, None)

    eng.commit()
    eng.reload()
    npaths = eng.rebuild()
    weak = eng.define()
    print(f"renamed {n_ren}; merged {n_mer}; paths {npaths}; weak {len(weak)}")
    print(eng.stats())


if __name__ == "__main__":
    main()
