from .text_processing import normalize_text


def collect_target_names(actions_config: dict):
    names = set()
    for key, config in actions_config.get("targets", {}).items():
        names.add(key)
        for alias in config.get("aliases", []):
            names.add(alias)
    return sorted(name for name in names if name)


def add_phrase(intent_data: list, phrase: str, intent: str):
    item = {"phrase": normalize_text(phrase), "intent": intent}
    if item not in intent_data:
        intent_data.append(item)
        return True
    return False


def augment_dataset(intent_data: list, actions_config: dict, synonyms_config: dict):
    added = 0
    targets = collect_target_names(actions_config)

    open_verbs = list(synonyms_config.get("verbs", {}).get("open_target", {}).get("synonyms", []))
    learned_verbs = synonyms_config.get("learned_verbs", {})
    open_verbs.extend([verb for verb, intent in learned_verbs.items() if intent == "open_target"])
    delete_verbs = synonyms_config.get("verbs", {}).get("delete_target", {}).get("synonyms", [])

    for target_name in targets:
        for verb in open_verbs:
            if add_phrase(intent_data, f"{verb} {target_name}", "open_target"):
                added += 1
        for verb in delete_verbs:
            if add_phrase(intent_data, f"{verb} {target_name}", "delete_target"):
                added += 1

    return added
