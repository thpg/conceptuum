# -*- coding: utf-8 -*-
# Лексикон книги, партия 7 (финал существительных): устройство — ясность
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'G:\Projects\conceptuum')
from jnana_engine import JnanaEngine

eng = JnanaEngine(pref_lang='ru')

NEW = [
    ('устройство', 'device', 'артефакт'),
    ('утверждение', 'assertion', 'высказывание'),
    ('уточнение', 'clarification', 'действие'),
    ('ухищрение', 'artifice', 'действие'),
    ('уход', 'care', 'действие'),
    ('участие', 'participation', 'действие'),
    ('участок', 'plot', 'часть'),
    ('ученик', 'pupil', 'человек'),
    ('учреждение', 'institution', 'организация'),
    ('фаза', 'phase', 'часть'),
    ('фактор', 'factor', 'причина'),
    ('фамилия', 'surname', 'название'),
    ('физкультурник', 'sports enthusiast', 'человек'),
    ('философ', 'philosopher', 'профессия'),
    ('философия', 'philosophy', 'наука'),
    ('флогистон', 'phlogiston', 'вещество'),
    ('фонарь', 'lantern', 'артефакт'),
    ('фонд', 'fund', 'запас'),
    ('фора', 'head start', 'свойство'),
    ('формулировка', 'formulation', 'текст'),
    ('фосфор', 'phosphorus', 'химический элемент'),
    ('фраза', 'phrase', 'высказывание'),
    ('франция', 'France', 'страна'),
    ('хамелеон', 'chameleon', 'животное'),
    ('характер', 'character', 'ментальное свойство'),
    ('хата', 'hut', 'сооружение'),
    ('химик', 'chemist', 'профессия'),
    ('хина', 'quinine', 'вещество'),
    ('хлор', 'chlorine', 'газ'),
    ('хлорофилл', 'chlorophyll', 'вещество'),
    ('экономика', 'economy', 'социальное явление'),
    ('хозяйство', 'household economy', 'экономика'),
    ('холод', 'cold', 'температура'),
    ('храбрость', 'bravery', 'нравственное качество'),
    ('христианство', 'Christianity', 'религия'),
    ('царь', 'tsar', 'человек'),
    ('цена', 'price', 'количество'),
    ('ценз', 'qualification requirement', 'социальное явление'),
    ('ценность', 'value', 'оценочное свойство'),
    ('центр', 'centre', 'точка'),
    ('цепь', 'chain', 'множество'),
    ('цилиндр', 'cylinder', 'геометрическая фигура'),
    ('частное', 'quotient', 'число'),
    ('частность', 'particularity', 'свойство'),
    ('человечество', 'humanity', 'группа'),
    ('черта', 'trait', 'свойство'),
    ('чертёж', 'drawing', 'изображение'),
    ('четверг', 'Thursday', 'период времени'),
    ('чехословакия', 'Czechoslovakia', 'страна'),
    ('членение', 'articulation', 'процесс'),
    ('чувство', 'feeling', 'эмоция'),
    ('чёска', 'carding', 'действие'),
    ('чёткость', 'precision', 'свойство'),
    ('шалаш', 'hut', 'сооружение'),
    ('шарообразность', 'sphericity', 'форма'),
    ('шатание', 'swaying', 'движение'),
    ('шахматист', 'chess player', 'человек'),
    ('ширина', 'width', 'размер'),
    ('школьник', 'schoolchild', 'человек'),
    ('шкура', 'hide', 'часть тела'),
    ('щупальце', 'tentacle', 'часть тела'),
    ('эксплуататор', 'exploiter', 'человек'),
    ('электрификация', 'electrification', 'процесс'),
    ('электромотор', 'electric motor', 'артефакт'),
    ('электрон', 'electron', 'частица'),
    ('электропроводность', 'electrical conductivity', 'физическое свойство'),
    ('электротехника', 'electrical engineering', 'наука'),
    ('эпоха', 'epoch', 'период времени'),
    ('этап', 'stage', 'часть'),
    ('ядро', 'nucleus', 'часть'),
    ('январь', 'January', 'период времени'),
    ('янтарь', 'amber', 'твёрдое вещество'),
    ('ясность', 'clarity', 'свойство'),
]

ok = bad = 0
for item in NEW:
    ru, en, parent = item[0], item[1], item[2]
    u = item[3] if len(item) > 3 else 1
    cid, msg = eng.add_concept(ru, parent, lang='ru', universum_id=u, terms=[(en, 'en')])
    if cid is None:
        bad += 1
        print('FAIL', msg)
    else:
        ok += 1
        if 'already' in str(msg):
            print('dup', msg)
print(f'ok={ok} fail={bad}')
eng.rebuild(); eng.define()
eng.cur.execute('SELECT COUNT(*) FROM concept')
print('concepts:', eng.cur.fetchone()[0])
eng.close()
