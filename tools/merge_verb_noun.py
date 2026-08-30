# -*- coding: utf-8 -*-
"""Инфинитив и отглагольное существительное — одно понятие.

Канон: существительное, инфинитив становится термином.

  python tools/merge_verb_noun.py
  python tools/merge_verb_noun.py apply
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jnana_engine import JnanaEngine

APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

# ложные пары по общему префиксу (из merge_verbs.py + новые)
EXCLUDE_INF = {
    "возрастать", "воспользоваться", "воспроизводить", "выбрасывать",
    "использовать", "передать", "передавать", "передаваться",
    "пересекаться", "пересечься", "подавлять", "подвергаться",
    "подвергнуть", "подвергнуться", "потерпеть", "потребоваться",
    "предохранить", "предсказать", "проверить", "проверять",
    "проверяться", "произноситься", "разредить", "разрезать",
    "распределить", "совершенствоваться", "отобрать", "прийтись",
    "приходиться", "познакомиться", "учиться", "научиться",
    "доставлять", "поступать",  # ≠ постановка
    "толковаться", "сложиться", "складываться",
}

MANUAL_VN = {
    "воздействовать": "воздействие",
    "влиять": "влияние",
    "влияться": "влияние",
}

NOUN_SUF = ("ование", "евание", "ирование", "ение", "ание", "тие", "ство")


def is_inf(n):
    if " " in n or "-" in n:
        return False
    if n.endswith(("ость", "есть", "ность", "тость")):
        return False
    return n.endswith(("ться", "тись", "чься", "ить", "ать", "ять", "еть",
                       "уть", "ти", "чь", "ть"))


def inf_stem(v):
    v = re.sub(r"(ся|сь)$", "", v)
    for e in ("ивать", "ывать", "овать", "евать", "ать", "ять", "еть",
              "ить", "уть", "ти", "чь", "ть"):
        if v.endswith(e) and len(v) - len(e) >= 3:
            return v[:-len(e)]
    return v


def noun_stem(n):
    for s in NOUN_SUF:
        if n.endswith(s) and len(n) - len(s) >= 3:
            return n[:-len(s)]
    return n


def pair_ok(inf, noun):
    if inf in EXCLUDE_INF:
        return False
    si, sn = inf_stem(inf), noun_stem(noun)
    if len(si) < 3 or len(sn) < 3:
        return False
    return si == sn


def main():
    eng = JnanaEngine()
    names = dict(eng.names)
    infs = [(c, n) for c, n in names.items() if is_inf(n)]
    nouns = [(c, n) for c, n in names.items()
             if not is_inf(n) and any(n.endswith(s) for s in NOUN_SUF)]

    proposed, skipped = [], []
    seen_inf = set()
    by_name = {}
    for cid, n in names.items():
        by_name.setdefault(n, []).append(cid)
    for inf, noun in MANUAL_VN.items():
        ic = (by_name.get(inf) or [None])[0]
        nc = (by_name.get(noun) or [None])[0]
        if ic and nc and ic != nc:
            proposed.append((ic, nc, f"manual {inf} -> {noun}"))
            seen_inf.add(ic)

    # 1) пары под одним родителем — самый надёжный сигнал
    for pid, kids in eng.children_map.items():
        kinf = [(c, names[c]) for c in kids if is_inf(names[c])]
        knoun = [(c, names[c]) for c in kids if not is_inf(names[c])]
        for ic, inf in kinf:
            if inf in EXCLUDE_INF:
                continue
            hits = [(nc, nn) for nc, nn in knoun if pair_ok(inf, nn)]
            if len(hits) == 1:
                proposed.append((ic, hits[0][0],
                                 f"sib {inf} -> {hits[0][1]} under {names.get(pid, '?')}"))
                seen_inf.add(ic)
            elif len(hits) > 1:
                skipped.append(f"ambiguous {inf}: {[h[1] for h in hits]}")

    # 2) глобально: основа совпала однозначно
    for ic, inf in infs:
        if ic in seen_inf or inf in EXCLUDE_INF:
            continue
        hits = [(nc, nn) for nc, nn in nouns if pair_ok(inf, nn)]
        # одно существительное с равной основой
        exact = [(nc, nn) for nc, nn in hits if inf_stem(inf) == noun_stem(nn)]
        use = exact if len(exact) == 1 else (hits if len(hits) == 1 else [])
        if len(use) == 1:
            nc, nn = use[0]
            if eng.children(ic):
                skipped.append(f"inf has children {inf} -> {nn}")
                continue
            proposed.append((ic, nc, f"stem {inf} -> {nn}"))
            seen_inf.add(ic)
        elif len(hits) > 1:
            skipped.append(f"ambiguous {inf}: {[h[1] for h in hits[:6]]}")

    seen, uniq = set(), []
    for s, d, r in proposed:
        if s in seen or s == d:
            continue
        seen.add(s)
        uniq.append((s, d, r))

    print(f"proposed merges: {len(uniq)}")
    for s, d, r in uniq:
        print(f"  {names[s]:30s} -> {names[d]:30s}  [{r}]")
    print(f"\nskipped: {len(skipped)}")
    for line in skipped[:80]:
        print("  ", line)

    if not APPLY:
        print("\n(dry-run; pass 'apply' to write)")
        return

    merged = 0
    for s, d, r in uniq:
        if s not in eng.names or d not in eng.names:
            print("skip gone", r)
            continue
        ok, msg = eng.merge_concepts(s, d, keep_genus=False, reload=False)
        print(("OK" if ok else "NO"), msg, r)
        if ok:
            merged += 1
            # names map: src gone
            eng.names.pop(s, None)
    eng.commit()
    eng.reload()

    npaths = eng.rebuild()
    weak = eng.define()
    print(f"merged {merged}; paths {npaths}; weak {len(weak)}")
    print(eng.stats())


if __name__ == "__main__":
    main()
