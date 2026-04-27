from dataclasses import replace
import pymorphy3

morph = pymorphy3.MorphAnalyzer()


def normalize(word: str):
    parsed = morph.parse(word)
    return parsed[0].normal_form if parsed else word


def apply_contextual_fallback(command, actions_config, synonyms_config):
    words = command.text.split()

    # ❗ ТРОГАЕМ ТОЛЬКО КОМАНДЫ С ОБЪЕКТАМИ
    TARGET_INTENTS = {
        "open_target",
        "delete_target",
        "open_folder"
    }

    if command.intent not in TARGET_INTENTS:
        return command

    if len(words) >= 2:
        verb = normalize(words[0])

        def normalize_list(words):
            return {normalize(w) for w in words}

        open_verbs = synonyms_config.get("verbs", {}).get("open_target", {}).get("synonyms", [])
        delete_verbs = synonyms_config.get("verbs", {}).get("delete_target", {}).get("synonyms", [])
        learned = list(synonyms_config.get("learned_verbs", {}).keys())

        all_verbs = (
            normalize_list(open_verbs)
            | normalize_list(delete_verbs)
            | normalize_list(learned)
        )

        # ❗ ЕСЛИ ГЛАГОЛ НЕПОХОЖ → fallback
        if verb not in all_verbs:
            return replace(command, intent="none", entities={})

    # ❗ только для finish_recording строгая проверка
    if command.intent == "finish_recording":
        allowed = {"готово", "закончил", "закончила", "останови запись", "стоп запись"}
        if command.text.lower().strip() not in allowed:
            return replace(command, intent="none", entities={})

    return command