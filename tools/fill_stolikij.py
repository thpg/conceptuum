# -*- coding: utf-8 -*-
"""столикий = многоликий = многоликость = разнообразие форм.
Одно понятие; канон — существительное."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fill_props import finish, rid
from jnana_engine import JnanaEngine

def main():
    eng = JnanaEngine(pref_lang="ru")
    cid = rid(eng, "многообразное")
    if cid is None:
        print("нет многообразное")
        return
    ok, msg = eng.rename_concept(cid, "многоликость")
    print(msg)
    terms_ru = [
        "столикий", "многоликий", "многоликое", "многообразное",
        "многообразный", "разнообразие", "разнообразное", "разнообразный",
        "многообразие", "множественность",
    ]
    terms_en = [
        ("diversity", "en"),
        ("many-facedness", "en"),
        ("manifold", "en"),
        ("variety of forms", "en"),
    ]
    for t in terms_ru:
        eng.cur.execute(
            "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')",
            (cid, t))
        if eng.cur.rowcount:
            print("  +ru", t)
    for t, lg in terms_en:
        eng.cur.execute(
            "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,%s)",
            (cid, t, lg))
        if eng.cur.rowcount:
            print("  +en", t)
    eng.commit()
    print("\n=== FINISH ===")
    finish(eng)
    eng.cur.execute(
        "SELECT term, lang FROM concept_term WHERE concept_id=%s ORDER BY lang, term",
        (cid,))
    print("terms now:")
    for t, lg in eng.cur.fetchall():
        print(f"  {lg} {t}")
    eng.cur.execute("SELECT nama, defin FROM concept WHERE dharma=%s", (cid,))
    print("defin:", eng.cur.fetchone())
    eng.close()


if __name__ == "__main__":
    main()
