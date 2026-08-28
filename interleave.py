# -*- coding: utf-8 -*-
"""
interleave.py — experiment: word-by-word generation with facts injected
into the model's reasoning stream.

Modes:
  --think (default)  facts are injected into a <think>...</think> block
                     (the model's "thinking"); the final answer after
                     </think> is generated clean, without injections.
  --no-think         facts are injected directly into the answer stream.

Loop (think mode):
  1. model generates the next word of its thinking (native llama.cpp
     /completion, KV-cached prefix)
  2. the word is looked up in the conceptuum base (question language first)
  3. if found, a short fact "[term — genus; key relation]" is appended
     and thinking continues with the extended context
  4. after --think-words, the block is closed and the model writes
     the final answer from its fact-enriched thinking

Usage:
    python interleave.py "Why does water turn into ice?"
    python interleave.py "Почему вода превращается в лёд?" --think-words 60
    python interleave.py "..." --no-think          # old behaviour
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
    """One-line fact from the cached definition; species list dropped."""
    eng.cur.execute("SELECT defin FROM concept WHERE dharma=%s", (cid,))
    row = eng.cur.fetchone()
    if not row or not row[0]:
        return None
    defin = row[0].split(". Species:")[0]
    return "; ".join(defin.split("; ")[:3])


def take_one_word(chunk):
    """Keep only up to the end of the first word (boundary not included).
    No boundary at all -> mid-word tokens, keep all."""
    if not chunk:
        return "", False
    lead = 1 if chunk[:1] in (" ", "\n") else 0
    cuts = [x for x in (chunk.find(" ", lead), chunk.find("\n", lead)) if x != -1]
    if not cuts:
        return chunk, False
    return chunk[:min(cuts)], True


def gen_loop(eng, endpoint, prompt, max_words, inject, qlang):
    """Word-by-word generation; if inject=True, append a base fact
    after every model word that matches a known concept."""
    text, injected, seen = "", [], set()
    empty = 0
    for _ in range(max_words * 3):
        chunk, eos = gen_chunk(endpoint, prompt + text)
        if not chunk:
            empty += 1
            if empty >= 3 or eos:
                break
            continue
        empty = 0
        if not inject:                       # plain mode: take whole chunks
            text += chunk
            if eos or len(text.split()) >= max_words:
                break
            continue
        piece, boundary = take_one_word(chunk)
        text += piece
        if eos:
            break
        if not boundary or not re.search(r"\w", piece):
            continue                         # mid-word, or pure punctuation
        token = re.sub(r"[^\w\-]", "", piece.split()[-1].lower())
        if len(token) < 3:
            continue
        cids = eng.resolve_fuzzy(token, lang=qlang) or eng.resolve_fuzzy(token)
        for cid in cids:
            if cid in seen:
                continue
            fact = short_fact(eng, cid, qlang)
            if fact:
                seen.add(cid)
                injected.append(fact)
                text += f" [{fact}]"
                break
        if len(text.split()) >= max_words:
            break
    return text, injected


def interleave(eng, endpoint, question, think, think_words, answer_words):
    qlang = detect_lang(question)
    eng.pref_lang = qlang
    base = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"
    if not think:
        thought, injected = gen_loop(eng, endpoint, base, answer_words, True, qlang)
        return thought, "", injected
    # phase 1: thinking with fact injection
    think_prefix = base + "<think>\n"
    thought, injected = gen_loop(eng, endpoint, think_prefix, think_words, True, qlang)
    # phase 2: clean final answer from the enriched thinking
    closed = think_prefix + thought + "\n</think>\n"
    answer, _ = gen_loop(eng, endpoint, closed, answer_words, False, qlang)
    return thought, answer, injected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--endpoint", default="http://localhost:8090")
    ap.add_argument("--think", dest="think", action="store_true", default=True)
    ap.add_argument("--no-think", dest="think", action="store_false")
    ap.add_argument("--think-words", type=int, default=40)
    ap.add_argument("--answer-words", type=int, default=80)
    args = ap.parse_args()

    eng = JnanaEngine(pref_lang="en")
    thought, answer, injected = interleave(eng, args.endpoint, args.question,
                                           args.think, args.think_words,
                                           args.answer_words)
    if args.think:
        print("=== THINKING (model words + injected facts) ===")
        print(thought)
        print()
        print("=== FINAL ANSWER (clean) ===")
        print(answer)
    else:
        print("=== RAW STREAM (model words + injected facts) ===")
        print(thought)
        print()
        print("=== CLEANED (facts removed) ===")
        print(re.sub(r"\s*\[[^\]]*\]", "", thought))
    print()
    print(f"=== INJECTED FACTS: {len(injected)} ===")
    for f in injected:
        print("-", f)


if __name__ == "__main__":
    main()
