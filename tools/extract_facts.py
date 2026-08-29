# -*- coding: utf-8 -*-
"""Extract candidate facts v2: better genus extraction.
Preprocess: strip leading 'Short for ...,', 'Alternatively called ...,',
handle 'may refer to any of the following: 1. ...' by taking sense 1.
"""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

STOP_TAIL = {'a','an','the','type','kind','form','way','set','piece','part','single',
             'general','small','large','specific','particular','common','special'}

def first_sentence(text):
    m = re.search(r'by Computer Hope (.{10,500}?\.)', text)
    return m.group(1).strip() if m else None

def clean(t):
    return t.strip().strip('.,;:').strip()

def strip_prefixes(s):
    s = re.sub(r'^(?:First developed|Originally developed|Developed|Created|Invented|Founded|Released|Introduced|Started|Used|When) [^,.]{5,80}[,.]?\s+', '', s, flags=re.I)
    s = re.sub(r'^[Ss]hort for [^,.]{3,80},\s+', '', s)
    s = re.sub(r'^(?:An?\s+)?[A-Za-z0-9\- ]{2,40}?\s+can refer to any of the following:\s*1\.\s*', '', s)
    s = re.sub(r'^[Aa]lternatively called [^,.]{3,60},\s+', '', s)
    s = re.sub(r'^[Aa]lso (?:called|known as) [^,.]{3,60},\s+', '', s)
    return s.strip()

def extract_synonyms(text):
    syns = []
    for pat in (r'[Aa]lternatively called (?:an? |the )?([^,.;()]{2,60})',
                r'[Aa]lso (?:called|known as|referred to as) (?:an? |the )?([^,.;()]{2,60})',
                r'[Ss]ometimes (?:called|abbreviated as|referred to as) (?:an? |the )?([^,.;()]{2,60})'):
        for m in re.finditer(pat, text):
            cand = clean(m.group(1))
            for c in re.split(r'\s+or\s+|\s+and\s+', cand):
                c = clean(c)
                if c and len(c.split()) <= 5 and c[0].isalpha():
                    syns.append(c)
    return syns

def extract_expansion(text):
    m = re.search(r'[Ss]hort for ([^,.;()]{3,80})', text)
    return clean(m.group(1)) if m else None

GENUS_RE = re.compile(
    r'^(?:An?|The)\s+.{0,45}?\bis\s+(?:an?|the)\s+'
    r'([a-z][a-z0-9\- ]{2,50}?)'
    r'(?:\s+(?:that|which|used|to|of|with|for|when|where|whose|designed|made|created|'
    r'written|found|stored|composed|consisting|containing|capable|responsible|built|'
    r'developed|based|intended|meant|considered|described|known)\b|\s*[,.])')

def extract_genus(s, term):
    s2 = strip_prefixes(s)
    m = GENUS_RE.match(s2)
    if not m:
        return None
    g = clean(m.group(1)).lower()
    words = g.split()
    while words and words[-1] in STOP_TAIL:
        words.pop()
    if not words or len(words) > 4:
        return None
    g = ' '.join(words)
    if g == term.lower() or g in ('term','word','acronym','abbreviation','name','concept','idea'):
        return None
    return g

out = open('dict_facts.jsonl', 'w', encoding='utf-8')
n = 0
for line in open('dict_articles.jsonl', encoding='utf-8'):
    a = json.loads(line)
    if a.get('status') != 200:
        continue
    s = first_sentence(a['text'])
    if not s:
        continue
    fact = {'term': a['term'], 'url': a['url'], 'first': s,
            'synonyms': extract_synonyms(a['text'][:1500]),
            'expansion': extract_expansion(a['text'][:800]),
            'genus': extract_genus(s, a['term'])}
    out.write(json.dumps(fact, ensure_ascii=False) + '\n')
    n += 1
out.close()

facts = [json.loads(l) for l in open('dict_facts.jsonl', encoding='utf-8')]
print('facts:', n)
print('with genus:', sum(1 for f in facts if f['genus']))
print('with synonyms:', sum(1 for f in facts if f['synonyms']))
print('with expansion:', sum(1 for f in facts if f['expansion']))
