# -*- coding: utf-8 -*-
"""Миграция кодов связей (2026-08-28):
1) степенные коды 21/23/25/27 -> 20 'attribute', степень уходит в edge.strength
   (95/70/30/5 по корзинам, где strength NULL);
2) перенос функциональной серии 8X в освободившийся диапазон 2X:
   80->21 (function), 82->22 (agent), 81->23 (material), 83->27 (patient);
3) новые коды назначения: 24 content, 25 application, 26 user;
4) relevant: старые 21/23/25/27 и 80-83 удаляем, вставляем новые описания.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from jnana_engine import JnanaEngine

DEG2STR = {"21": 95, "23": 70, "25": 30, "27": 5}
MAP8X = {"80": "21", "82": "22", "81": "23", "83": "27"}

# kod, long_name, description, sample, ss..ss4, so..so4, sym, trans
NEW_RELEVANT = [
    ("20", "attribute",
     "Атрибуция: предмет и его качество, компонент, функция или способность. "
     "Вид атрибута выводится по корню объекта (свойство/предмет/действие), "
     "степень хранится в strength (0-100).",
     "чашка белая; чашка с ручкой; нож — резать; птица — летать.",
     17, 19, 1913, 20, 18, 17, 19, 1913, 0, 0),
    ("21", "function (purpose)",
     "dh1 (предмет, обычно артефакт) предназначен для dh2 (действие). "
     "Степень — в strength.",
     "нож — резать; мост — соединять.",
     17, None, 1913, None, 19, 1913, None, None, 0, 0),
    ("22", "agent (capable of)",
     "dh1 (предмет, обычно организм) способен производить dh2 (действие).",
     "птица — летать; человек — мыслить.",
     17, None, None, None, 19, None, None, None, 0, 0),
    ("23", "material",
     "dh1 (предмет) изготовлен из dh2 (вещество). Степень — в strength "
     "(монета — металл 95, стол — дерево 70).",
     "стол — дерево; монета — металл.",
     17, None, None, None, 21, None, None, None, 0, 0),
    ("24", "content (intended content)",
     "dh1 (ёмкость, сосуд, упаковка) предназначен для хранения/подачи dh2 "
     "(вещество или предмет).",
     "кофейная чашка — кофе; солонка — соль; ваза — цветы.",
     17, None, None, None, 21, 17, None, None, 0, 0),
    ("25", "application (acts upon)",
     "dh1 (инструмент) предназначен для воздействия на dh2 (предмет).",
     "открывалка — бутылка; удочка — рыба; пилочка — ногти.",
     17, None, None, None, 17, None, None, None, 0, 0),
    ("26", "user (intended user)",
     "dh1 (предмет) предназначен для пользователя dh2 (предмет-агент).",
     "детский стул — ребёнок; будка — собака.",
     17, None, None, None, 17, None, None, None, 0, 0),
    ("27", "patient (object of action)",
     "dh1 (действие) типично направлено на dh2 (предмет). Степень — в strength.",
     "читать — книга; строить — сооружение.",
     19, 1913, None, None, 17, 18, 1913, None, 0, 0),
]


def main():
    eng = JnanaEngine(pref_lang="ru")
    cur = eng.cur

    # --- шаг 1: степени -> strength, код -> 20
    for kod, st in DEG2STR.items():
        cur.execute("UPDATE edge SET strength=%s WHERE kod=%s AND strength IS NULL",
                    (st, kod))
    cur.execute("UPDATE edge SET kod='20' WHERE kod IN ('21','23','25','27')")
    print("step1: degree edges -> 20, affected:", cur.rowcount)

    # --- шаг 2: 8X -> 2X
    for old, new in MAP8X.items():
        cur.execute("UPDATE edge SET kod=%s WHERE kod=%s", (new, old))
        print(f"step2: {old} -> {new}, affected: {cur.rowcount}")

    # --- шаг 3: relevant
    cur.execute("DELETE FROM relevant WHERE kod IN ('21','23','25','27','80','81','82','83')")
    cur.execute(
        "UPDATE relevant SET long_name='attribute', "
        "description='Атрибуция: предмет и его качество, компонент, функция или "
        "способность. Вид выводится по корню объекта, степень — в strength.', "
        "sample='чашка белая; чашка с ручкой; нож — резать.', "
        "sig_subject=17, sig_subject2=19, sig_subject3=1913, sig_subject4=20, "
        "sig_object=18, sig_object2=17, sig_object3=19, sig_object4=1913 "
        "WHERE kod='20'")
    for row in NEW_RELEVANT[1:]:
        cur.execute(
            "INSERT INTO relevant (kod, long_name, description, sample, "
            "sig_subject, sig_subject2, sig_subject3, sig_subject4, "
            "sig_object, sig_object2, sig_object3, sig_object4, "
            "is_symmetric, is_transitive) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", row)
    print("step3: relevant updated")
    eng.commit()

    # --- шаг 4: перегенерация
    print("paths:", eng.rebuild())
    eng.define()
    eng.commit()
    print(eng.stats())

    # контроль: распределение кодов
    cur.execute("SELECT kod, COUNT(*) FROM edge GROUP BY kod ORDER BY kod")
    print("kod distribution:", cur.fetchall())
    eng.close()


if __name__ == "__main__":
    main()
