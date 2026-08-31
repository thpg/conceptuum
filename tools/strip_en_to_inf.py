# -*- coding: utf-8 -*-
"""English 'to …' is the infinitive, like Russian согласиться.
Keep it as a term; add the form without 'to ' so display/search
can use a non-infinitive English label.

  python tools/strip_en_to_inf.py
  python tools/strip_en_to_inf.py apply
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jnana_engine import JnanaEngine

APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"


def main():
    eng = JnanaEngine()
    eng.cur.execute(
        "SELECT concept_id, term FROM concept_term WHERE lang='en' AND LOWER(term) LIKE %s",
        ("to %",))
    rows = eng.cur.fetchall()
    added = skipped = 0
    for cid, term in rows:
        stem = term[3:].strip() if term.lower().startswith("to ") else ""
        # только простой to+слово: не «to be given», не «to act upon»
        if (not stem or " " in stem or stem.lower().startswith("to ")):
            skipped += 1
            continue
        have = {t.lower() for t, lg in eng.terms_of[cid] if lg == "en"}
        if stem.lower() in have:
            skipped += 1
            continue
        print(f"  + {eng.names[cid]:30s}  en '{stem}'  (from '{term}')")
        if APPLY:
            eng.cur.execute(
                "INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'en')",
                (cid, stem))
        added += 1
    if APPLY:
        eng.commit()
    print(f"{'added' if APPLY else 'would add'} {added}, skip {skipped}")


if __name__ == "__main__":
    main()
