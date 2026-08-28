# -*- coding: utf-8 -*-
"""
ask.py — demo: ground a small local LLM with the conceptuum knowledge base.

Pipeline:
  1. Find concept terms (1-3 word n-grams) from the question in the base —
     the question's language first, other languages only as fallback.
  2. Drop orphan matches (homonym noise): keep concepts that share at
     least one edge with another found concept.
  3. Pull their canonical definitions + direct relations.
  4. Inject them as a verified FACTS block into the prompt.
  5. Send to any OpenAI-compatible local endpoint (llama.cpp, Ollama, LM Studio).

Usage:
    python ask.py "Why does water turn into ice?"                 # retrieve + ask LLM
    python ask.py "Why does water turn into ice?" --no-llm        # retrieve only
    python ask.py "Что производит замерзание?" --lang ru

Options:
    --endpoint   OpenAI-compatible base URL (default http://localhost:11434/v1)
    --model      model name (default: qwen3:4b)
    --max-facts  max concepts to ground on (default 8)
"""
import argparse
import json
import sys
import urllib.request
from collections import defaultdict

from jnana_engine import JnanaEngine

STOP = {"the", "a", "an", "is", "are", "of", "to", "in", "on", "and", "or",
        "why", "how", "what", "does", "do", "did", "it", "its", "into",
        "что", "как", "почему", "это", "и", "или", "в", "на", "с", "не",
        "чем", "какие", "каких", "какой", "есть", "существуют", "существует"}


def detect_lang(question):
    """Rough guess: Cyrillic -> ru, otherwise en."""
    return "ru" if any("Ѐ" <= c <= "ӿ" for c in question) else "en"


def find_concepts(eng, question, limit, qlang):
    words = [w.strip(".,?!()\"'«»").lower() for w in question.split()]
    words = [w for w in words if w and w not in STOP]
    found, seen = [], set()
    for n in (3, 2, 1):                       # longest n-grams first
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            # question language first; other languages only as fallback;
            # exact match first, morphological (prefix) match as fallback
            if n == 1:
                cids = (eng.resolve_fuzzy(phrase, lang=qlang)
                        or eng.resolve_fuzzy(phrase))
            else:
                cids = (eng.resolve_all(phrase, lang=qlang)
                        or eng.resolve_phrase_fuzzy(phrase, lang=qlang)
                        or eng.resolve_all(phrase)
                        or eng.resolve_phrase_fuzzy(phrase))
            for cid in cids:                  # homonyms: all universes
                if cid not in seen:
                    seen.add(cid)
                    found.append(cid)
    return filter_connected(eng, found)[:limit]


def filter_connected(eng, cids):
    """Drop homonym noise: keep the largest cluster of concepts that are
    adjacent in the graph or share a common neighbour (2 hops)."""
    if len(cids) <= 1:
        return cids
    s = set(cids)
    adj = defaultdict(set)
    for a, b, _kod, _strength, status, _id in eng.edges:
        if status == "ok":
            adj[a].add(b)
            adj[b].add(a)
    def related(x, y):
        return y in adj[x] or bool(adj[x] & adj[y])
    # connected components over the found concepts
    seen, comps = set(), []
    for c in cids:
        if c in seen:
            continue
        comp, stack = [], [c]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            comp.append(x)
            stack.extend(y for y in cids if y not in seen and related(x, y))
        comps.append(comp)
    big = max(comps, key=len)
    return big if len(big) > 1 else cids


def facts_block(eng, cids):
    eng.cur.execute("SELECT id, nama FROM universum")
    unames = dict(eng.cur.fetchall())
    lines = []
    for cid in cids:
        eng.cur.execute("SELECT defin, universum_id FROM concept WHERE dharma=%s", (cid,))
        row = eng.cur.fetchone()
        if row and row[0]:
            u = unames.get(row[1], row[1])
            lines.append(f"- [{u}] " + row[0])
    return "\n".join(lines)


def related_block(eng, cids, limit=10):
    """One-hop neighbours of the found concepts: direct relations and isa
    parents (inheritance). Species are skipped (already in defin).
    Ranked by number of links to the found set."""
    s = set(cids)
    score = defaultdict(int)
    for a, b, kod, _strength, status, _id in eng.edges:
        if status != "ok":
            continue
        if a in s and b not in s:
            score[b] += 1                     # found -> neighbour / parent
        elif b in s and a not in s and kod != "14":
            score[a] += 1                     # neighbour -> found (no species)
    if not score:
        return ""
    eng.cur.execute("SELECT id, nama FROM universum")
    unames = dict(eng.cur.fetchall())
    lines = []
    for c in sorted(score, key=lambda c: (-score[c], c))[:limit]:
        eng.cur.execute("SELECT defin, universum_id FROM concept WHERE dharma=%s", (c,))
        row = eng.cur.fetchone()
        if row and row[0]:
            d = row[0].split(". Species:")[0]
            lines.append(f"- [{unames.get(row[1], row[1])}] " + d)
    return "\n".join(lines)


def ask_llm(endpoint, model, question, facts, related=""):
    prompt = (
        "Answer using ONLY the verified facts below when they are relevant; "
        "say what follows from them, and say plainly if they are not enough.\n\n"
        f"FACTS:\n{facts}\n"
    )
    if related:
        prompt += f"\nRELATED FACTS (one step away in the graph):\n{related}\n"
    prompt += f"\nQUESTION: {question}\nANSWER:"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 512,
    }).encode("utf-8")
    req = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions",
                                 data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--endpoint", default="http://localhost:11434/v1")
    ap.add_argument("--model", default="qwen3:4b")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--max-facts", type=int, default=8)
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()

    qlang = args.lang
    if qlang == "en" and detect_lang(args.question) == "ru":
        qlang = "ru"                      # auto-switch unless --lang was explicit
    eng = JnanaEngine(pref_lang=qlang)
    cids = find_concepts(eng, args.question, args.max_facts, qlang)
    if not cids:
        print("No known concepts found in the question.")
        return
    facts = facts_block(eng, cids)
    related = related_block(eng, cids)
    print("=== GROUNDING (from conceptuum) ===")
    print(facts)
    if related:
        print()
        print("=== RELATED (1 hop) ===")
        print(related)
    print()

    if args.no_llm:
        return
    try:
        print("=== ANSWER (grounded LLM) ===")
        print(ask_llm(args.endpoint, args.model, args.question, facts, related))
    except Exception as e:
        print(f"[LLM endpoint unreachable: {e}]")
        print("Run with --no-llm to see retrieval only, or start a local server "
              "(Ollama / llama.cpp / LM Studio) and pass --endpoint/--model.")


if __name__ == "__main__":
    main()
