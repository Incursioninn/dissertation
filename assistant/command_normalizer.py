from .text_processing import normalize_text


def get_open_verbs(synonyms_config: dict):
    open_config = synonyms_config.get("verbs", {}).get("open_target", {})
    verbs = list(open_config.get("synonyms", []))

    learned = synonyms_config.get("learned_verbs", {})
    for verb, intent in learned.items():
        if intent == "open_target":
            verbs.append(verb)

    return sorted(set(verbs), key=len, reverse=True)


def canonicalize_unknown_open_verb(text: str, synonyms_config: dict):
    text = normalize_text(text)

    open_config = synonyms_config.get("verbs", {}).get("open_target", {})
    canonical = open_config.get("canonical", "открой")
    verbs = get_open_verbs(synonyms_config)

    for verb in verbs:
        verb = normalize_text(verb)

        if text == verb:
            return canonical

        if text.startswith(verb + " "):
            rest = text[len(verb):].strip()
            return f"{canonical} {rest}".strip()

    return text


def canonicalize_command(text: str, synonyms_config: dict):
    return canonicalize_unknown_open_verb(text, synonyms_config)


def split_possible_verb_and_target(text: str):
    """
    "стартани игру" -> ("стартани", "игру")
    "заведи мой редактор" -> ("заведи", "мой редактор")
    """
    text = normalize_text(text)
    parts = text.split(maxsplit=1)

    if len(parts) != 2:
        return None, text

    return parts[0], parts[1]
