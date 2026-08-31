# -*- coding: utf-8 -*-
"""88 фразовых to-инфинитивов: термин без 'to ' и канон, где он очевиден."""
import os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fill_props import finish
from jnana_engine import JnanaEngine

# nama → extra en terms (кроме автоматически снятого to)
NOUN = {
    "беречь": ["care", "safekeeping"],
    "вкладывать": ["investment", "insertion"],
    "внести": ["contribution", "bringing in"],
    "воспитывать": ["upbringing"],
    "воспользоваться": ["use"],
    "впадать": ["inflow"],
    "вспыхивать": ["flare-up"],
    "встать": ["standing up"],
    "выбрасывать": ["throwing out"],
    "выдвинуть": ["putting forward"],
    "выдолбить": ["hollowing out"],
    "выжечь": ["burning out"],
    "выйти": ["going out", "exit"],
    "вылететь": ["flying out"],
    "вырабатываться": ["development (being developed)"],
    "вырваться": ["breakout"],
    "выяснять": ["clarification"],
    "говориться": ["being said"],
    "даваться": ["being given"],
    "добиваться": ["striving"],
    "загораться": ["catching fire"],
    "зайти": ["dropping in"],
    "заставить": ["compulsion"],
    "исходить": ["proceeding from"],
    "констатировать": ["ascertainment"],
    "крыться": ["being hidden"],
    "навлечь": ["bringing upon"],
    "надевать": ["putting on"],
    "надеть": ["putting on"],
    "напереть": ["leaning on"],
    "наслать": ["sending down"],
    "недоставать": ["lack"],
    "облекаться": ["clothing oneself"],
    "обогащаться": ["enrichment"],
    "обстоять": ["state of affairs"],
    "оказаться": ["turning out"],
    "окучивать": ["hilling"],
    "отвыкнуть": ["breaking a habit"],
    "отдаваться": ["devotion"],
    "отдалить": ["moving away"],
    "откинуть": ["throwing back"],
    "отобрать": ["taking away"],
    "отстать": ["lag"],
    "оттенить": ["setting off"],
    "оформление": ["design", "formalization"],
    "перебирать": ["sorting through"],
    "переглянуться": ["exchange of glances"],
    "передать": ["transmission"],
    "повиснуть": ["hanging down"],
    "подводить": ["bringing to"],
    "подлежать": ["being subject to"],
    "подобрать": ["picking up"],
    "подразумеваться": ["implication"],
    "подытожить": ["summing up"],
    "попасться": ["getting caught"],
    "предъявление": ["presentation"],
    "приводиться": ["being cited"],
    "приписываться": ["attribution"],
    "присутствовать": ["presence"],
    "приходиться": ["falling on"],
    "продержаться": ["holding out"],
    "произнесение": ["pronunciation"],
    "проложить": ["laying a route"],
    "пропустить": ["letting through"],
    "размагничивание": ["demagnetization"],
    "разредить": ["thinning out"],
    "раскалить": ["heating red-hot"],
    "расплавить": ["melting down"],
    "руководствоваться": ["being guided"],
    "садиться": ["sitting down"],
    "сжечь": ["burning down"],
    "складываться": ["taking shape"],
    "сколачивать": ["knocking together"],
    "смочь": ["ability"],
    "совершенствование": ["self-improvement"],
    "сопровождение": ["accompaniment"],
    "состояться": ["taking place"],
    "ссылка": ["reference"],
    "толкование": ["interpretation"],
    "тухнуть": ["going out (flame)"],
    "увлечение": ["enthusiasm"],
    "узнать": ["finding out"],
    "уметь": ["know-how"],
    "устареть": ["obsolescence"],
    "усыплять": ["lulling"],
    "учесть": ["taking into account"],
    "уяснить": ["grasping"],
    "числиться": ["being listed"],
}


def main():
    eng = JnanaEngine()
    eng.cur.execute(
        "SELECT concept_id, term FROM concept_term WHERE lang='en' AND LOWER(term) LIKE %s",
        ("to %",))
    rows = eng.cur.fetchall()
    added = 0
    for cid, term in rows:
        others = [t for t, lg in eng.terms_of[cid] if lg == "en"
                  and not t.lower().startswith("to ")]
        if others:
            continue
        stem = term[3:].strip() if term.lower().startswith("to ") else ""
        extra = []
        if stem:
            extra.append(stem)
        nama = eng.names[cid]
        extra += NOUN.get(nama, [])
        have = {t.lower() for t, lg in eng.terms_of[cid] if lg == "en"}
        for t in extra:
            if t.lower() in have:
                continue
            eng.cur.execute(
                "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'en')",
                (cid, t))
            if eng.cur.rowcount:
                added += 1
                print(f"  + {nama:28s}  en {t!r}")
                have.add(t.lower())
    eng.commit()
    print(f"added {added}")
    finish(eng)
    eng.close()


if __name__ == "__main__":
    main()
