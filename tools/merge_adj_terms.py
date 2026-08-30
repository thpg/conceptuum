# -*- coding: utf-8 -*-
"""Прилагательные не меняют таксономию: ADJF-узел → термин существительного.

  python tools/merge_adj_terms.py           # отчёт
  python tools/merge_adj_terms.py apply
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jnana_engine import JnanaEngine

APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

NOUN_OE = {
    "животное", "насекомое", "млекопитающее", "существо", "подлежащее",
    "сказуемое", "жаркое", "мороженое", "приданое", "земноводное",
    "пресмыкающееся", "паукообразное", "одноклеточное", "позвоночное",
    "беспозвоночное", "цветковое", "ластоногое", "жвачное", "простейшее",
    "насекомое", "целое", "общее", "частное", "среднее", "данное",
}

TAXON_KEEP = {
    "позвоночное", "беспозвоночное", "цветковое", "ластоногое", "жвачное",
    "одноклеточное", "простейшее", "земноводное", "паукообразное",
    "хищное", "нехищное",
}

BEARER_MERGE = [
    ("судоходное", "судоходство", "водоём", "20", 90),
    ("рогатое", "рог", None, None, None),
    ("больное", "болезнь", None, None, None),
    ("грязное", "чистота", None, None, None),
    ("чистое", "чистота", None, None, None),
    ("хищное", "хищник", None, None, None),
    ("перелётное", "перелёт", None, None, None),
]

MANUAL = {
    "кошачье": "кошка", "утиное": "утка", "саранчовое": "саранча",
    "заводское": "завод", "тракторное": "трактор", "дымовое": "дым",
    "школьное": "школа", "народное": "народ", "государственное": "государство",
    "историческое": "история", "культурное": "культура", "хозяйственное": "хозяйство",
    "политическое": "политика", "национальное": "нация",
    "человеческое": "человек", "атомное": "атом", "жизненное": "жизнь",
    "партийное": "партия", "педагогическое": "педагог", "районное": "район",
    "расовое": "раса", "имущественное": "имущество",
    "классовое": "класс", "военное": "война", "техническое": "техника",
    "академическое": "академия", "производственное": "производство",
    "сельскохозяйственное": "хозяйство", "агрономическое": "агрономия",
    "художественное": "искусство", "библиотечное": "библиотека",
    "арифметическое": "арифметика", "оптическое": "оптика",
    "торговое": "торговля", "церковное": "церковь", "экономическое": "экономика",
    "кремлёвское": "кремль", "литейное": "литьё", "предвыборное": "выборы",
    "реактивное": "реакция", "абонементное": "абонемент",
    "оранжерейное": "оранжерея", "житейское": "жизнь",
    "английское": "англия", "французское": "франция", "американское": "америка",
    "греческое": "греция", "русское": "россия", "московское": "москва",
    "петербургское": "петербург", "сибирское": "сибирь",
    "славянское": "славянин", "латинское": "латынь", "каспийское": "каспий",
    "дунайское": "дунай", "потсдамское": "потсдам",
    "июльское": "июль", "октябрьское": "октябрь",
    "зимнее": "зима", "ночное": "ночь", "вечернее": "вечер",
    "северное": "север",
    "деревянное": "дерево", "железное": "железо", "медное": "медь",
    "металлическое": "металл", "минеральное": "минерал", "земляное": "земля",
    "злаковое": "злак", "растительное": "растение",
    "враждебное": "вражда", "взаимосвязанное": "взаимосвязь",
    "союзное": "союз", "качественное": "качество", "количественное": "количество",
    "философское": "философия", "религиозное": "религия",
    "демократическое": "демократия", "буржуазное": "буржуазия",
    "социалистическое": "социализм", "капиталистическое": "капитализм",
    "идеалистическое": "идеализм", "материалистическое": "материализм",
    "языковое": "язык", "словесное": "слово",
    "возрастное": "возраст", "начальное": "начало", "конечное": "конец",
    "успешное": "успех", "опытное": "опыт", "принципиальное": "принцип",
    "противоречивое": "противоречие", "суеверное": "суеверие",
    "экспериментальное": "эксперимент", "софистическое": "софизм",
    "альтернативное": "альтернатива", "поверхностное": "поверхность",
    "электрическое": "электричество",
    "древнегреческое": "греция", "зарубежное": "заграница",
    "иностранное": "иностранец", "невский": "нева",
}

DUMP_PARENTS = {"принадлежность", "происхождение"}

SUF = (
    "ическое", "алистическое", "альное", "арное", "нское", "овское",
    "евское", "инское", "цкое", "ское", "овое", "евое", "иное",
    "аное", "яное", "нное", "нее", "ое", "ее",
)


def looks_adj(n):
    if " " in n or "-" in n or n in NOUN_OE or n in TAXON_KEEP:
        return False
    return n.endswith(("ское", "цкое", "ическое", "альное", "овое", "евое",
                       "нное", "ное", "ое", "ее", "ачье"))


def fits(adj, noun):
    if len(noun) < 3 or noun == adj:
        return False
    if adj.startswith(noun):
        return adj[len(noun):] in SUF
    if noun[-1] in "аяое" and adj.startswith(noun[:-1]):
        return adj[len(noun) - 1:] in ("ное", "нее", "ое", "ее", "ское", "цкое", "овое")
    if adj.endswith("ачье") and noun == adj[:-4] + "ка":
        return True
    if adj.endswith("иное") and noun == adj[:-4] + "ка":
        return True
    return False


def find_noun(adj, nouns):
    best = None
    for cid, n in nouns:
        if fits(adj, n) and (best is None or len(n) > len(best[1])):
            best = (cid, n)
    return best


def main():
    eng = JnanaEngine()
    names = dict(eng.names)
    by_name = {}
    for cid, n in names.items():
        by_name.setdefault(n, []).append(cid)

    def cid_of(n):
        ids = by_name.get(n)
        return ids[0] if ids else None

    nouns = [(cid, n) for cid, n in names.items()]
    dump_ids = {cid for cid, n in names.items() if n in DUMP_PARENTS}

    proposed, skipped = [], []

    def add(src, dst, reason):
        if not src or not dst or src == dst:
            skipped.append(f"missing {reason}")
            return
        if eng.children(src):
            skipped.append(f"has children {names[src]} -> {names[dst]}")
            return
        proposed.append((src, dst, reason))

    for adj, canon, *_rest in BEARER_MERGE:
        add(cid_of(adj), cid_of(canon), f"bearer {adj} -> {canon}")
    for adj, canon in MANUAL.items():
        add(cid_of(adj), cid_of(canon), f"manual {adj} -> {canon}")

    for pid in dump_ids:
        for kid in eng.children(pid):
            n = names[kid]
            if cid_of(n) and any(s == kid for s, _, _ in proposed):
                continue
            if not looks_adj(n):
                skipped.append(f"dump leftover {n} ⊂ {names[pid]}")
                continue
            skipped.append(f"dump leftover {n} ⊂ {names[pid]}")

    for pid, kids in list(eng.children_map.items()):
        if pid in dump_ids:
            continue
        kid_nouns = [(c, names[c]) for c in kids]
        for c in kids:
            n = names[c]
            if not looks_adj(n) or any(s == c for s, _, _ in proposed):
                continue
            hit = find_noun(n, kid_nouns)
            if hit:
                add(c, hit[0], f"sibling {n} -> {hit[1]} (under {names.get(pid, '?')})")

    seen, uniq = set(), []
    for s, d, r in proposed:
        if s in seen:
            continue
        seen.add(s)
        uniq.append((s, d, r))

    print(f"proposed merges: {len(uniq)}")
    for s, d, r in uniq:
        print(f"  {names[s]:30s} -> {names[d]:30s}  [{r}]")
    print(f"\nskipped: {len(skipped)}")
    for line in skipped:
        print("  ", line)

    if not APPLY:
        print("\n(dry-run; pass 'apply' to write)")
        return

    merged = 0
    for s, d, r in uniq:
        eng.reload()
        if s not in eng.names or d not in eng.names:
            print("skip gone", r)
            continue
        ok, msg = eng.merge_concepts(s, d, keep_genus=False, reload=True)
        print(("OK" if ok else "NO"), msg, r)
        if ok:
            merged += 1

    eng.reload()
    for adj, canon, bearer, kod, st in BEARER_MERGE:
        dst = next((c for c, n in eng.names.items() if n == canon), None)
        if bearer and kod and dst:
            bid = next((c for c, n in eng.names.items() if n == bearer), None)
            if bid:
                eid, msg = eng.propose(bid, kod, dst, strength=st,
                                       source="adj-merge", auto=True)
                print("edge", msg)

    eng.reload()
    dump_ids = {cid for cid, n in eng.names.items() if n in DUMP_PARENTS}
    dropped = 0
    for pid in dump_ids:
        for kid in list(eng.children(pid)):
            n = eng.names[kid]
            if not looks_adj(n) and not n.endswith("ский") and not n.endswith("ской"):
                continue
            eng.cur.execute(
                "DELETE FROM edge WHERE dh1=%s AND dh2=%s AND kod='14'", (kid, pid))
            eng.cur.execute(
                "SELECT COUNT(*) FROM edge WHERE (dh1=%s OR dh2=%s) AND status='ok'",
                (kid, kid))
            n_edges = eng.cur.fetchone()[0]
            if n_edges == 0:
                eng.cur.execute("DELETE FROM concept_term WHERE concept_id=%s", (kid,))
                eng.cur.execute(
                    "DELETE FROM concept_path WHERE ancestor=%s OR descendant=%s",
                    (kid, kid))
                eng.cur.execute("DELETE FROM concept WHERE dharma=%s", (kid,))
                dropped += 1
                print("drop isolated", n)
            else:
                print("drop isa only", n)
    eng.commit()

    npaths = eng.rebuild()
    weak = eng.define()
    print(f"merged {merged}; dropped {dropped}; paths {npaths}; weak {len(weak)}")
    print(eng.stats())


if __name__ == "__main__":
    main()
