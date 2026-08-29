# -*- coding: utf-8 -*-
"""Add English terms (lang='en') for all everyday-universe concepts."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

T = {
"вещь":"thing","цвет":"color","синий":"blue","красный":"red","визуальное":"visual",
"сенсорное":"sensory","мебель":"furniture","стол":"table","материал":"material",
"деревянное":"wooden","зеленый":"green","желтый":"yellow","черный":"black",
"белый":"white","сущее":"entity","предмет":"object","свойство":"property",
"действие":"action","отношение":"relation","вещество":"substance","жидкость":"liquid",
"металл":"metal","газ":"gas","организм":"organism","растение":"plant",
"животное":"animal","человек":"human","артефакт":"artifact","инструмент":"tool",
"одежда":"clothing","сооружение":"structure","транспортное средство":"vehicle",
"природный объект":"natural object","водоём":"body of water","форма рельефа":"landform",
"небесное тело":"celestial body","вкус":"taste","запах":"smell","звук":"sound",
"тактильное качество":"tactile quality","физическое свойство":"physical property",
"размер":"size","вес":"weight","форма":"shape","температура":"temperature",
"ментальное свойство":"mental property","интеллектуальная способность":"intellectual ability",
"нравственное качество":"moral quality","темперамент":"temperament",
"оценочное свойство":"evaluative property","красота":"beauty","полезность":"usefulness",
"физический процесс":"physical process","движение":"motion","рост":"growth",
"разрушение":"destruction","ментальный процесс":"mental process","мышление":"thinking",
"восприятие":"perception","желание":"desire","память":"memory",
"социальное действие":"social action","общение":"communication","труд":"labor",
"обмен":"exchange","управление":"management","пространственное отношение":"spatial relation",
"нахождение в месте":"location","соседство":"adjacency","временное отношение":"temporal relation",
"предшествование":"precedence","одновременность":"simultaneity",
"причинное отношение":"causal relation","порождение":"production",
"препятствование":"hindrance","структурное отношение":"structural relation",
"часть-целое":"part-whole","социальное отношение":"social relation","владение":"ownership",
"родство":"kinship","подчинённость":"subordination","договорённость":"agreement",
"твёрдое вещество":"solid","камень":"stone","песок":"sand","лёд":"ice",
"древесина":"wood","ткань":"fabric","стекло":"glass","кирпич":"brick","вода":"water",
"молоко":"milk","кровь":"blood","масло":"oil","железо":"iron","золото":"gold",
"медь":"copper","воздух":"air","кислород":"oxygen","пища":"food","хлеб":"bread",
"мясо":"meat","млекопитающее":"mammal","птица":"bird","рыба":"fish",
"насекомое":"insect","собака":"dog","кошка":"cat","лошадь":"horse","корова":"cow",
"воробей":"sparrow","орёл":"eagle","утка":"duck","щука":"pike","акула":"shark",
"муравей":"ant","пчела":"bee","бабочка":"butterfly","дерево":"tree",
"кустарник":"shrub","трава":"grass","цветок":"flower","дуб":"oak","берёза":"birch",
"сосна":"pine","посуда":"dishware","тарелка":"plate","чашка":"cup",
"кастрюля":"pot","стул":"chair","шкаф":"cabinet","кровать":"bed","рубашка":"shirt",
"брюки":"trousers","пальто":"coat","обувь":"footwear","сапоги":"boots",
"туфли":"shoes","молоток":"hammer","пила":"saw","нож":"knife","игла":"needle",
"автомобиль":"car","поезд":"train","самолёт":"airplane","корабль":"ship",
"велосипед":"bicycle","дом":"house","мост":"bridge","башня":"tower","дорога":"road",
"помещение":"premises","комната":"room","река":"river","озеро":"lake","море":"sea",
"океан":"ocean","гора":"mountain","холм":"hill","долина":"valley","равнина":"plain",
"солнце":"sun","луна":"moon","звезда":"star","планета":"planet","сладкий":"sweet",
"кислый":"sour","солёный":"salty","горький":"bitter","ароматный":"fragrant",
"зловонный":"foul-smelling","громкий":"loud","тихий":"quiet","мягкий":"soft",
"твёрдый":"hard","гладкий":"smooth","шероховатый":"rough","большой":"big",
"маленький":"small","тяжёлый":"heavy","лёгкий":"light","круглый":"round",
"квадратный":"square","длинный":"long","горячий":"hot","холодный":"cold",
"тёплый":"warm","умный":"smart","глупый":"stupid","добрый":"kind","злой":"evil",
"честный":"honest","храбрый":"brave","трусливый":"cowardly",
"вспыльчивый":"hot-tempered","спокойный":"calm","красивый":"beautiful",
"уродливый":"ugly","полезный":"useful","вредный":"harmful",
"физиологический процесс":"physiological process","дыхание":"breathing",
"питание":"nutrition","сон":"sleep","размножение":"reproduction","ходьба":"walking",
"бег":"running","полёт":"flight","плавание":"swimming","падение":"falling",
"зрение":"vision","слух":"hearing","запоминание":"memorization",
"вспоминание":"recall","рассуждение":"reasoning","воображение":"imagination",
"эмоция":"emotion","радость":"joy","гнев":"anger","страх":"fear","печаль":"sadness",
"любовь":"love","ненависть":"hatred","разговор":"conversation",
"переписка":"correspondence","строительство":"construction","земледелие":"farming",
"резание":"cutting","шитьё":"sewing","торговля":"trade","покупка":"buying",
"продажа":"selling","дарение":"gifting","обучение":"teaching","лечение":"treatment",
"игра":"play","кровное родство":"blood kinship","брак":"marriage","дружба":"friendship",
"кожа":"skin","деталь":"part","колесо":"wheel","окно":"window","механизм":"mechanism",
"двигатель":"engine","домашнее животное":"domestic animal","хвойное дерево":"conifer",
"лиственное дерево":"deciduous tree","мёд":"honey","мука":"flour","сидение":"sitting",
"отдых":"rest","хранение":"storage","защита":"protection",
"приготовление пищи":"cooking","замерзание":"freezing","излучение":"radiation",
"высокий":"tall","низкий":"low","короткий":"short","лживый":"deceitful",
"документ":"document","письмо":"letter",
}

eng = JnanaEngine()
added, skipped = 0, []
for ru, en in T.items():
    cid = eng.resolve(ru)
    if cid is None:
        skipped.append((ru, 'no concept')); continue
    existing = eng.resolve(en)
    if existing is not None and existing != cid:
        skipped.append((ru, f'en term "{en}" taken by #{existing}')); continue
    if existing == cid:
        continue
    eng.cur.execute("INSERT IGNORE INTO concept_term (concept_id,term,lang) VALUES (%s,%s,'en')",
                    (cid, en))
    added += 1
eng.commit()
print(f'added: {added}, skipped: {len(skipped)}')
for s in skipped: print('  skip:', s)

# regenerate English-display definitions
eng2 = JnanaEngine(pref_lang='en')
weak = eng2.define()
print('defin regenerated (en display), weak:', len(weak))
for t in ('water', 'ice', 'dog', 'freezing'):
    cid = eng2.resolve(t)
    if cid:
        eng2.cur.execute('SELECT defin FROM concept WHERE dharma=%s', (cid,))
        print(t, '::', eng2.cur.fetchone()[0])
eng2.close()
