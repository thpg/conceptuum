# -*- coding: utf-8 -*-
"""
interleave.py — experiment: word-by-word generation with facts injected
into the model's own output stream ("thinking").

Loop:
  1. model generates the next word (native llama.cpp /completion, KV-cached)
  2. the word is looked up in the conceptuum base (question language first)
  3. if found, a short fact "(term — genus; key relation)" is appended
     in parentheses, and generation continues with the extended context

Usage:
    python interleave.py "Why does water turn into ice?"
    python interleave.py "Чем кошка отличается от камня?" --endpoint http://localhost:8090
"""
import argparse
import json
import re
import urllib.request

from jnana_engine import JnanaEngine
from ask import detect_lang


def gen_chunk(endpoint, prompt, n_predict=10):
    body = json.dumps({
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": 0.2,
        "cache_prompt": True,
        "stop": ["<|im_end|>"],
    }).encode("utf-8")
    req = urllib.request.Request(endpoint.rstrip("/") + "/completion",
                                 data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d.get("content", ""), bool(d.get("stopped_eos") or
                                      d.get("stopping_word") == "<|im_end|>")


def short_fact(eng, cid, qlang):
    """One-line fact: preferred-language term + genus + first relations."""
    term = eng.disp.get(cid, eng.names.get(cid, "?"))
    eng.cur.execute("SELECT defin FROM concept WHERE dharma=%s", (cid,))
    row = eng.cur.fetchone()
    if not row or not row[0]:
        return None
    defin = row[0]
    # keep it short: up to the second relation, drop species list
    defin = defin.split(". Species:")[0]
    parts = defin.split("; ")
    defin = "; ".join(parts[:3])
    return f"{defin}"


def take_one_word(chunk):
    """From a generated chunk, keep only up to the end of the first word
    (space not included). No space at all -> mid-word tokens, keep all."""
    if not chunk:
        return "", False
    lead = 1 if chunk[:1] in (" ", "\n") else 0
    i = chunk.find(" ", lead)
    j = chunk.find("\n", lead)
    cuts = [x for x in (i, j) if x != -1]
    if not cuts:
        return chunk, False            # mid-word or last piece, no boundary yet
    return chunk[:min(cuts)], True     # one complete word


def interleave(eng, endpoint, question, max_words=50):
    qlang = detect_lang(question)
    eng.pref_lang = qlang
    prefix = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"
    text = ""
    injected = []
    seen_injected = set()
    empty = 0
    for _ in range(max_words * 3):
        chunk, eos = gen_chunk(endpoint, prefix + text)
        if not chunk:
            empty += 1
            if empty >= 3 or eos:
                break
            continue
        empty = 0
        piece, boundary = take_one_word(chunk)
        text += piece
        if eos:
            break
        if not boundary or not re.search(r"\w", piece):
            continue                     # mid-word, or pure punctuation/space
        token = re.sub(r"[^\w\-]", "", piece.split()[-1].lower())
        if len(token) < 3:
            continue
        cids = eng.resolve_all(token, lang=qlang) or eng.resolve_all(token)
        for cid in cids:
            if cid in seen_injected:
                continue
            fact = short_fact(eng, cid, qlang)
            if fact:
                seen_injected.add(cid)
                injected.append(fact)
                text += f" [{fact}]"
                break
        if len(text.split()) >= max_words:
            break
    return text, injected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--endpoint", default="http://localhost:8090")
    ap.add_argument("--max-words", type=int, default=50)
    args = ap.parse_args()

    eng = JnanaEngine(pref_lang="en")
    text, injected = interleave(eng, args.endpoint, args.question, args.max_words)

    print("=== RAW STREAM (model words + injected facts) ===")
    print(text)
    print()
    print("=== CLEANED (facts removed) ===")
    print(re.sub(r"\s*\[[^\]]*\]", "", text))
    print()
    print(f"=== INJECTED FACTS: {len(injected)} ===")
    for f in injected:
        print("-", f)


if __name__ == "__main__":
    main()
