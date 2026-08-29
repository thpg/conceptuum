# -*- coding: utf-8 -*-
# Чистое извлечение лексем: склейка переносов, слияние словоформ,
# стоп-лист служебных лексем. Выход: lex_{noun,verb,adj}.tsv
import sys, io, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymorphy3, pymysql

morph = pymorphy3.MorphAnalyzer()
raw = open(r'G:\Projects\conceptuum\books\logika1954.txt', encoding='utf-8').read()
raw = re.sub(r'===PAGE \d+===', ' ', raw)
raw = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', raw)   # склейка переносов
words = re.findall(r'[А-Яа-яЁё]+', raw)

VERB_POS = {'VERB', 'INFN', 'PRTF', 'PRTS', 'GRND'}
KEEP = {'NOUN', 'ADJF'} | VERB_POS

STOP = set('''быть мочь являться иметь иметься этот тот который такой другой иной
весь каждый свой сам всякий данный следующий некоторый один наш ваш какой какой-то
самый такой-то делать сделать говорить называться стать становиться получить получать
дать давать взять брать знать указать указывать сказать называть видеть видеться
оставаться идти привести приводить представлять находиться состоять существовать
бывать следовать относиться входить выходить вытекать возникать возникнуть
получаться происходить происходить служить являть выражать выражать выражаться
означать заключаться заключать составлять составить называться составить
хороший плохой новый старый большой маленький первый второй последний
нужный должный необходимый возможный невозможный известный неизвестный
определённый неопределённый различный разный одинаковый особый общий частный
единичный собственный основной главный важный особенный специальный
некий никакой всяческий прочий иной'''.split())

freq = collections.Counter()
lemma_pos = {}
for w in words:
    if len(w) < 3:
        continue
    p = morph.parse(w)[0]
    pos = p.tag.POS
    if pos not in KEEP:
        continue
    if 'Name' in p.tag or 'Patr' in p.tag or 'Surn' in p.tag:
        continue
    lemma = p.normal_form
    if lemma in STOP:
        continue
    if not p.is_known:          # мусорные обрывки переносов
        continue
    if len(lemma) < 4 and lemma not in ('мир', 'вид', 'род', 'раз', 'дело', 'луч', 'сон', 'бой', 'воз', 'гуж'):
        continue
    gpos = 'VERB' if pos in VERB_POS else pos
    # приоритет NOUN/ADJF над глаголом при совпадении леммы
    if lemma not in lemma_pos or lemma_pos[lemma] == 'VERB':
        lemma_pos[lemma] = gpos
    freq[lemma] += 1

c = pymysql.connect(host='127.0.0.1', user='root', password='123', database='jnana3', charset='utf8mb4')
cur = c.cursor()
cur.execute("SELECT DISTINCT LOWER(term) FROM concept_term")
db_terms = set()
for (t,) in cur.fetchall():
    db_terms.add(t)
    for w in re.findall(r'[А-Яа-яЁёA-Za-z-]+', t):
        if len(w) >= 3 and re.search(r'[А-Яа-яЁё]', w):
            db_terms.add(morph.parse(w)[0].normal_form)

groups = {'NOUN': [], 'VERB': [], 'ADJF': []}
for lemma, n in freq.items():
    if lemma in db_terms:
        continue
    groups[lemma_pos[lemma]].append((lemma, n))
for g in groups.values():
    g.sort(key=lambda x: (-x[1], x[0]))

for name, g in groups.items():
    path = rf'G:\Projects\conceptuum\books\lex_{name.lower()}.tsv'
    with open(path, 'w', encoding='utf-8') as f:
        for lemma, n in g:
            f.write(f'{lemma}\t{n}\n')
    print(f'{name}: {len(g)} лексем вне базы -> {path}')
print('ИТОГО:', sum(len(g) for g in groups.values()))
