"""Controlled, bilingual wording for evidence-grounded training questions."""

TASKS = ("parents", "ancestry", "shared_genus", "intersection", "difference", "count", "property", "inference")
RELATIONS = {
    "en": {"14": "genus", "20": "attribute", "21": "purpose", "22": "capability", "23": "material", "30": "coextension"},
    "ru": {"14": "род", "20": "признак", "21": "назначение", "22": "способность", "23": "материал", "30": "равнообъёмность"},
}
SYSTEM = {
    "en": (
        "Answer using only the supplied Conceptuum facts. Names refer to the specified concept IDs. "
        "A genus link goes from a narrower concept to a broader concept; it is transitive. "
        "For catalog questions, count concept records, not real-world objects: a concept set includes its root, "
        "descendants and coextensions, restricted to the listed domain. Coextension works in both directions. "
        "Properties inherit only through genus links. A more specific assertion overrides an ancestor's assertion; "
        "incomparable positive and negative assertions yield conflict. Strength 0 is an explicit negative; "
        "a positive strength or an unspecified strength is a positive assertion, not a probability or universal quantifier. "
        "No applicable assertion means unknown, not negative. Sharing a genus alone does not establish disjointness, "
        "and genus inclusion alone does not establish its converse. These are inferences from supplied records, not certified world facts."
    ),
    "ru": (
        "Отвечай только по приведённым фактам Conceptuum. Названия обозначают понятия с указанными ID. "
        "Связь рода направлена от более узкого понятия к более широкому и транзитивна. "
        "В вопросах о каталоге считай записи понятий, а не реальные объекты: множество включает исходное понятие, "
        "его виды и равнообъёмные понятия в пределах указанной области. Равнообъёмность двусторонняя. "
        "Свойства наследуются только по родовым связям. Более частное утверждение переопределяет утверждение предка; "
        "несравнимые положительное и отрицательное утверждения дают конфликт. Сила 0 означает явное отрицание; "
        "положительная или неуказанная сила означает положительное утверждение, но не вероятность и не утверждение обо всех объектах. "
        "Отсутствие применимого утверждения означает неизвестность, а не отрицание. Общий род сам по себе не доказывает "
        "несовместимость; включение вида в род не доказывает обратное включение. Это выводы из предоставленных записей, а не проверенные факты о мире."
    ),
}


def wording(task, spec, expected, concepts, lang):
    names = {item["id"]: item["name"] for item in concepts}
    ref = lambda cid: f'“{names[cid]}” (#{cid})'
    listed = lambda ids: "; ".join(ref(cid) for cid in ids)
    ru = lang == "ru"
    a = ref(spec["a"])
    b = ref(spec["b"]) if "b" in spec else None
    value = expected["value"]
    if task == "parents":
        question = f"Какие непосредственные роды указаны для понятия {a}?" if ru else f"Which direct broader concepts are recorded for {a}?"
        answer = ("Непосредственные роды: " if ru else "The direct broader concepts are: ") + listed(value) + "."
    elif task == "ancestry":
        question = f"Позволяют ли приведённые родовые связи отнести понятие {a} к понятию {b}?" if ru else f"Do the supplied genus links classify {a} under {b}?"
        if value:
            answer = ("Да. Цепочка от вида к роду: " if ru else "Yes. The narrower-to-broader chain is: ") + " → ".join(ref(cid) for cid in spec["path"]) + "."
        else:
            answer = "По приведённым связям это не установлено. Обратное направление цепочки не доказывает включение; это не явное отрицание связи." if ru else "This is not established by the supplied links. Reversing the chain does not establish inclusion; this is not an explicit negative assertion."
    elif task == "shared_genus":
        question = f"Какие непосредственные роды являются общими для понятий {a} и {b}?" if ru else f"Which recorded direct broader concepts do {a} and {b} share?"
        answer = ("Общие непосредственные роды: " if ru else "Their shared direct broader concepts are: ") + listed(value) + "."
    elif task in {"intersection", "difference", "count"}:
        if task == "intersection":
            question = f"Какие записи из указанной области каталога принадлежат одновременно множеству {a} и множеству {b}?" if ru else f"Within the listed catalog domain, which records belong to both the {a} set and the {b} set?"
        elif task == "difference":
            question = f"Какие записи из указанной области каталога принадлежат множеству {a}, но не принадлежат множеству {b}?" if ru else f"Within the listed catalog domain, which records belong to the {a} set but not the {b} set?"
        else:
            question = f"Сколько различных записей в указанной области каталога принадлежат хотя бы одному из множеств {a} и {b}?" if ru else f"How many distinct records in the listed catalog domain belong to at least one of the {a} and {b} sets?"
        if task == "count":
            answer = f"Число записей понятий: {value}. Общие записи учитываются один раз." if ru else f"There are {value} concept records. Shared records are counted once."
        elif value:
            answer = ("Записи понятий: " if ru else "The concept records are: ") + listed(value) + "."
        else:
            answer = "В указанной области нет подходящих записей. Это не доказывает несовместимость реальных классов." if ru else "No records match in the listed domain. This does not prove that the real-world classes are incompatible."
    elif task == "property":
        relation = RELATIONS[lang][spec["relation"]]
        target = ref(spec["target"])
        question = (f"Каков статус связи «{relation}» от понятия {a} к понятию {target} по приведённым фактам: положительный, отрицательный, неизвестный или конфликтующий?"
                    if ru else f"For {a}, what is the recorded status of the {relation} relation to {target}: positive, negative, unknown, or conflict?")
        states = {
            "positive": ("Положительный: наиболее частные применимые утверждения положительны.", "Positive: the most specific applicable assertions are positive."),
            "negative": ("Отрицательный: наиболее частные применимые утверждения содержат явное отрицание.", "Negative: the most specific applicable assertions explicitly deny this relation."),
            "unknown": ("Неизвестный: для этого понятия и его родовых предков нет применимого утверждения. Это не означает отрицание.", "Unknown: there is no applicable assertion on this concept or its genus ancestors. This is not an explicit negative."),
            "conflict": ("Конфликтующий: среди наиболее частных применимых утверждений есть и положительные, и отрицательные.", "Conflict: the most specific applicable assertions include both positive and negative assertions."),
        }
        answer = states[value][0 if ru else 1]
        if expected.get("evidence_ids"):
            answer += (" Связи-основания: " if ru else " Supporting edge IDs: ") + ", ".join("#" + str(i) for i in expected["evidence_ids"]) + "."
        if expected.get("overridden_ids"):
            answer += (" Более общие утверждения переопределены: " if ru else " More general assertions are overridden: ") + ", ".join("#" + str(i) for i in expected["overridden_ids"]) + "."
    else:
        if spec["inference"] == "shared_membership":
            parent = ref(spec["parent"])
            question = f"Устанавливают ли приведённые связи, что оба понятия {a} и {b} относятся к роду {parent}?" if ru else f"Do the supplied links establish that both {a} and {b} fall under {parent}?"
            answer = "Да. Для каждого из двух понятий приведена родовая связь с указанным родом." if ru else "Yes. Each of the two concepts has a supplied genus link to that broader concept."
        elif spec["inference"] == "siblings_disjoint":
            question = f"Достаточно ли только приведённых родовых связей, чтобы заключить, что понятия {a} и {b} несовместимы?" if ru else f"Do the supplied genus links alone establish that {a} and {b} are disjoint?"
            answer = "Нет. Общий род сам по себе не доказывает ни несовместимость, ни пересечение. Для такого вывода нужны дополнительные сведения." if ru else "No. A shared genus alone establishes neither disjointness nor overlap. Additional evidence is required."
        else:
            question = f"Достаточно ли только связи «{a} — вид понятия {b}», чтобы установить обратное включение {b} в {a}?" if ru else f"Does the genus link from {a} to {b} alone establish the reverse inclusion of {b} in {a}?"
            answer = "Нет. Включение вида в род не доказывает обратное включение. По этим данным обратное включение не установлено." if ru else "No. Inclusion of a narrower concept in a broader one does not establish the reverse inclusion. The converse is not established by these facts."
    return question, answer


def messages(question, answer, grounding, lang):
    ru = lang == "ru"
    names = {item["id"]: item["name"] for item in grounding["concepts"]}
    lines = [question, "", "Факты:" if ru else "Facts:"]
    for edge in grounding["facts"]:
        relation = RELATIONS[lang][edge["relation"]]
        degree = "не указана" if ru else "unspecified"
        if edge["strength"] is not None:
            degree = str(edge["strength"])
        lines.append(f"[{edge['id']}] #{edge['subject']} {names[edge['subject']]} -- {relation} ({edge['relation']}) --> "
                     f"#{edge['target']} {names[edge['target']]} [{('сила' if ru else 'strength')}: {degree}]")
    if grounding["domain"]:
        lines += ["", ("Область каталога: " if ru else "Catalog domain: ") + "; ".join(f"#{cid} {names[cid]}" for cid in grounding["domain"])]
    if grounding["scope"] == "selected_premises":
        lines += ["", "Рассматривай только перечисленные посылки." if ru else "Consider only the listed premises."]
    else:
        lines += ["", "Для этого запроса фрагмент полон; не добавляй отсутствующие связи." if ru else "This fragment is complete for this query; do not add unstated links."]
    return [{"role": "system", "content": SYSTEM[lang]}, {"role": "user", "content": "\n".join(lines)}, {"role": "assistant", "content": answer}]
