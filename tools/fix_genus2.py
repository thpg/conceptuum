# -*- coding: utf-8 -*-
# Ревизия рода, проход 2: грубые ошибки шкал и откат ложных переименований.
# 1) Откат: пожарное/подчинённое/окружающее/служащее/трудящееся — это сущ.
# 2) физическое свойство: признаки животных -> признак; состояния -> состояние;
#    не-физические значения -> свойство.
# 3) человек: профессии -> профессия, родственники -> родственник и т.п.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='123',
                       database='jnana3', charset='utf8mb4')
cur = conn.cursor()
cur.execute("SELECT dharma, nama FROM concept")
ids = {n: d for d, n in cur.fetchall()}

def rename(old, new):
    if old not in ids: print('  !! нет:', old); return
    cur.execute("UPDATE concept SET nama=%s WHERE dharma=%s", (new, ids[old]))
    cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'ru')", (ids[old], new))
    ids[new] = ids.pop(old)
    print(f'  rename: {old} -> {new}')

def move(child, new_parent):
    if child not in ids or new_parent not in ids:
        print('  !! нет:', child, 'или', new_parent); return
    cur.execute("UPDATE edge SET dh2=%s WHERE dh1=%s AND kod='14'", (ids[new_parent], ids[child]))
    print(f'  move: {child} -> {new_parent}')

# 1) откат ложных переименований (существительные, а не прилагательные)
rename('пожарное', 'пожарный')
rename('подчинённое', 'подчинённый')
rename('окружающее', 'окружающие')
rename('служащее', 'служащий')
rename('трудящееся', 'трудящийся')

# 2) грубые ошибки шкал
for a in ['хищное', 'нехищное', 'жвачное', 'рогатое', 'перелётное', 'ластоногое',
          'позвоночное', 'беспозвоночное', 'одноклеточное', 'высокоорганизованное',
          'цветковое']:
    move(a, 'признак')                      # биологические признаки, не «физ. свойство»
for a in ['больное', 'болезненное', 'застывшее', 'сжатое', 'неподвижное', 'жидкое']:
    move(a, 'состояние')
for a in ['судоходное', 'несудоходное', 'тесное', 'удушливое', 'гремучее',
          'деревянное', 'металлическое', 'электрическое', 'органическое',
          'неорганическое', 'газообразное', 'инертное']:
    move(a, 'свойство')
for a in ['грязное', 'чистое']:             # не оценка, а состояние
    move(a, 'состояние')
for a in ['новое', 'старое']:               # возраст/новизна, не оценка
    move(a, 'свойство')

# 3) человек: ближайшие роды
for a in ['врач', 'водитель', 'повар', 'полицейский', 'продавец', 'учитель',
          'лакей', 'строитель', 'фермер', 'музыкант', 'художник', 'писатель',
          'учёный', 'мастер', 'специалист', 'пожарный']:
    move(a, 'профессия')
for a in ['брат', 'жена', 'муж', 'сестра', 'родитель', 'ребёнок в семье']:
    move(a, 'родственник')
for a in ['шахматист', 'физкультурник']:
    move(a, 'спортсмен')
move('москвич', 'житель')
move('служащий', 'работник')
move('трудящийся', 'работник')

conn.commit()
print('OK')
conn.close()
