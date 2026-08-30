# -*- coding: utf-8 -*-
"""
fill_llm.py — token-lean LLM filling of a universe, per FILL_ALGORITHM.md.

Loop per anchor concept (frontier = concept.processed = 0):
  1. EXPAND  — one call: up to N direct species, known children excluded
  2. RELATE  — one call (if >= 8 new): typed relations inside the pool
  3. set_processed(anchor)
Final: one batched REPAIR call for relations rejected by validate().

Wire format (token-lean, one item per line, tab-separated):
  EXPAND:  primary_term <TAB> secondary_term
  RELATE:  subject <TAB> kod <TAB> object [<TAB> strength]

Term language: universum 3 (IT) is en-primary; others ru-primary.

Usage:
  python fill_llm.py --universe 5 --universe-name "медицина" \
      --endpoint http://localhost:8090/v1 --model local
  python fill_llm.py --universe 4 --max-anchors 3 --dry-run   # prompts only
  python fill_llm.py --universe 4 --candidate                 # edges as candidates
"""
import argparse
import json
import re
import urllib.request
from collections import defaultdict

from jnana_engine import JnanaEngine

SYSTEM = """You fill a relational knowledge base of concepts.
Output ONLY data lines, one item per line, fields separated by a TAB character.
No commentary, no headers, no markdown, no numbering.

Relation kods (for RELATE):
15 essential attribute; 20 attribute (degree in strength 0-100: 95 always,
70 usually, 30 sometimes, 5 rarely; 0 = explicit negation);
21 purpose; 22 agent; 23 material; 24 content; 25 application; 26 user;
27 patient; 40 overlap (degree in strength); 61 coordinate; 62 converses;
63 contrary; 64 contradictory; 70 produces; 71 hinders; 72 precedes;
74 depends on.
Use only these kods. Strength (optional): 0-100."""


def llm_call(endpoint, model, user, max_tokens=1500):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user}],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions",
                                 data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]


def parse_lines(text, fields):
    """Split response into field tuples; tolerate '-' bullets and '|' sep."""
    out = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*• ").strip()
        if not line:
            continue
        parts = [p.strip() for p in (line.split("\t") if "\t" in line
                                     else line.split("|"))]
        parts = [p for p in parts if p]
        if len(parts) >= fields:
            out.append(parts)
    return out


def expand_prompt(anchor_term, uname, known_children, n, langs):
    la, lb = langs
    return (f"Universe: {uname}. Concept: \"{anchor_term}\".\n"
            f"List up to {n} direct species (subtypes) of this concept "
            f"belonging to this universe.\n"
            f"Already known — do NOT repeat: {', '.join(known_children) or 'none'}.\n"
            f"Format per line: {la}_term<TAB>{lb}_term "
            f"(second field may be empty if no {lb} term)")


def relate_prompt(pool):
    return ("Concepts: " + ", ".join(pool) + ".\n"
            "List typed relations among them.\n"
            "Format per line: subject<TAB>kod<TAB>object[<TAB>strength]")


def repair_prompt(rejected):
    lines = "\n".join(f"{a}\t{k}\t{b} — REJECTED: {msg}" for a, k, b, msg in rejected)
    return ("These relations were rejected by the grammar validator. "
            "Fix each (choose valid subject/object from the same domain) "
            "or drop it by writing DROP.\n"
            "Format per line: subject<TAB>kod<TAB>object[<TAB>strength]\n\n" + lines)


def resolve_term(eng, term, langs):
    for lg in langs:
        r = eng.resolve_fuzzy(term, lang=lg)
        if r:
            return r[0]
    return eng.resolve_fuzzy(term)[0] if eng.resolve_fuzzy(term) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=int, required=True)
    ap.add_argument("--universe-name", default=None)
    ap.add_argument("--endpoint", default="http://localhost:8090/v1")
    ap.add_argument("--model", default="local")
    ap.add_argument("--max-anchors", type=int, default=10)
    ap.add_argument("--expand-n", type=int, default=30)
    ap.add_argument("--min-new-for-relate", type=int, default=8)
    ap.add_argument("--candidate", action="store_true",
                    help="insert edges as candidates, not auto-approved")
    ap.add_argument("--dry-run", action="store_true", help="print prompts, no LLM")
    args = ap.parse_args()

    eng = JnanaEngine(pref_lang="ru")
    langs = ("en", "ru") if args.universe == 3 else ("ru", "en")
    eng.cur.execute("SELECT nama FROM universum WHERE id=%s", (args.universe,))
    row = eng.cur.fetchone()
    uname = args.universe_name or (row[0] if row else f"u{args.universe}")

    frontier = [cid for cid, _n in eng.unprocessed(args.universe)]
    # parents first (thin branches have priority), leaves after
    frontier.sort(key=lambda c: (0 if eng.children(c) else 1,
                                 len(eng.children(c))))
    print(f"universe '{uname}': {len(frontier)} unprocessed anchors")
    frontier = frontier[:args.max_anchors]

    # group leaf anchors by parent: one RELATE call per sibling group
    leaf_groups = defaultdict(list)
    expanders = []
    for cid in frontier:
        if eng.children(cid):
            expanders.append(cid)
        else:
            leaf_groups[eng.parent.get(cid)].append(cid)

    rejected = []
    total_new = total_edges = 0

    def relate(pool, hint=None):
        nonlocal total_edges
        rprompt = relate_prompt(pool)
        if hint:
            rprompt += f"\nInclude relations involving \"{hint}\"."
        resp = llm_call(args.endpoint, args.model, rprompt)
        for parts in parse_lines(resp, 3):
            s, kod, o = parts[0], parts[1], parts[2]
            st = None
            if len(parts) > 3:
                try:
                    st = int(parts[3])
                except ValueError:
                    pass
            if not re.fullmatch(r"\d{2}", kod):
                continue
            eid, msg = eng.propose(s, kod, o, strength=st,
                                   universum_id=args.universe,
                                   source="llm:fill", auto=not args.candidate)
            if eid:
                total_edges += 1
            else:
                rejected.append((s, kod, o, msg.split(": ", 1)[-1]))
        eng.commit()

    # ---- leaf groups: one RELATE call per parent -------------------------
    for pid, leaves in leaf_groups.items():
        names = [eng.disp[c] for c in leaves]
        sibs = [eng.disp[c] for c in eng.children(pid)] if pid else []
        pool = (([eng.disp[pid]] if pid else []) + sibs)[:40]
        if not pool:
            for c in leaves:
                eng.set_processed(c)
            eng.commit()
            continue
        print(f"\n### RELATE-group {eng.disp.get(pid, '?')}: "
              f"{len(leaves)} leaves, pool {len(pool)}")
        if args.dry_run:
            print(relate_prompt(pool))
        else:
            relate(pool, hint=", ".join(names))
        for c in leaves:
            eng.set_processed(c)
        eng.commit()

    # ---- expanders: EXPAND (+ RELATE if enough new) ----------------------
    for cid in expanders:
        anchor = eng.disp[cid]
        kids = [eng.disp[c] for c in eng.children(cid)]

        prompt = expand_prompt(anchor, uname, kids, args.expand_n, langs)
        print(f"\n### EXPAND {anchor} ({len(kids)} known children)")
        if args.dry_run:
            print(prompt)
            continue
        resp = llm_call(args.endpoint, args.model, prompt)
        new_terms = []
        for parts in parse_lines(resp, 1):
            primary = parts[0]
            secondary = parts[1] if len(parts) > 1 else None
            nama = primary if langs[0] == "ru" else (secondary or primary)
            if eng.resolve_fuzzy(primary) or (secondary and eng.resolve_fuzzy(secondary)):
                continue                      # duplicate — skip silently
            terms = []
            if langs[0] == "ru":
                if secondary:
                    terms.append((secondary, "en"))
            elif secondary:
                terms.append((secondary, "ru"))
            cid2, msg = eng.add_concept(nama, anchor, lang=langs[0],
                                        universum_id=args.universe,
                                        terms=terms)
            if cid2 and "already" not in msg:
                new_terms.append(primary)
                total_new += 1
                print("  +", nama)
        eng.commit()

        if len(new_terms) >= args.min_new_for_relate:
            pool = (new_terms + kids)[:40]
            print(f"### RELATE {anchor} (pool {len(pool)})")
            relate(pool)
        eng.set_processed(cid)
        eng.commit()

    # ---- batched repair pass ----
    if rejected and not args.dry_run:
        print(f"\n### REPAIR ({len(rejected)} rejected edges)")
        resp = llm_call(args.endpoint, args.model, repair_prompt(rejected))
        fixed = 0
        for parts in parse_lines(resp, 3):
            if parts[0].upper() == "DROP":
                continue
            s, kod, o = parts[0], parts[1], parts[2]
            if not re.fullmatch(r"\d{2}", kod):
                continue
            eid, _msg = eng.propose(s, kod, o, universum_id=args.universe,
                                    source="llm:repair", auto=not args.candidate)
            if eid:
                fixed += 1
        eng.commit()
        print(f"repaired: {fixed}, dropped: {len(rejected) - fixed}")

    if not args.dry_run:
        print("\npaths:", eng.rebuild())
        eng.define()
        eng.commit()
        print(eng.stats())
    eng.close()
    print(f"\nDONE: +{total_new} concepts, +{total_edges} edges, "
          f"{len(rejected)} rejected")


if __name__ == "__main__":
    main()
