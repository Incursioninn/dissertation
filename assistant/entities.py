import re
from typing import Any, Dict

from .text_processing import normalize_text, remove_command_verbs


WORD_NUMBERS = {
    "одну": 1, "одна": 1, "один": 1, "два": 2, "две": 2, "три": 3,
    "четыре": 4, "пять": 5, "шесть": 6, "семь": 7, "восемь": 8,
    "девять": 9, "десять": 10, "пятнадцать": 15, "двадцать": 20, "тридцать": 30,
}


def extract_entities(text: str, intent: str, actions_config: dict) -> Dict[str, Any]:
    text = normalize_text(text)
    entities = {}

    if intent == "open_target":
        target_name = extract_target_name(text, actions_config)
        if target_name:
            entities["target_name"] = target_name

    elif intent == "delete_target":
        target_name = extract_delete_target_name(text, actions_config)
        if target_name:
            entities["target_name"] = target_name

    elif intent == "open_folder":
        folder_name = extract_folder_name(text, actions_config)
        if folder_name:
            entities["folder_name"] = folder_name

    elif intent == "type_text":
        typed_text = extract_text_to_type(text)
        if typed_text:
            entities["typed_text"] = typed_text

    elif intent == "set_reminder":
        minutes = extract_minutes(text)
        reminder_text = extract_reminder_text(text)
        if minutes:
            entities["minutes"] = minutes
        if reminder_text:
            entities["reminder_text"] = reminder_text

    elif intent == "learn_macro":
        macro_name = extract_macro_name(text)
        if macro_name:
            entities["macro_name"] = macro_name

    return entities


def extract_target_name(text: str, actions_config: dict):
    candidate = remove_command_verbs(text)
    target_key = find_item_key(candidate, actions_config.get("targets", {}))
    if target_key:
        return target_key
    return candidate if candidate else None


def extract_delete_target_name(text: str, actions_config: dict):
    candidate = remove_command_verbs(text)
    target_key = find_item_key(candidate, actions_config.get("targets", {}))
    if target_key:
        return target_key
    return candidate if candidate else None


def extract_folder_name(text: str, actions_config: dict):
    candidate = remove_command_verbs(text)
    folder_key = find_item_key(candidate, actions_config.get("folders", {}))
    if folder_key:
        return folder_key
    return candidate if candidate else None


def find_item_key(candidate: str, items: dict):
    candidate = normalize_text(candidate)
    for key, config in items.items():
        names = [key] + config.get("aliases", [])
        for name in names:
            name = normalize_text(name)
            if candidate == name or candidate in name or name in candidate:
                return key
    return None


def extract_text_to_type(text: str):
    triggers = ["напечатай фразу", "напечатай текст", "напечатай", "введи текст", "введи", "напиши текст", "напиши"]
    for trigger in triggers:
        if trigger in text:
            return text.split(trigger, 1)[1].strip(" :,.!?\"'")
    return None


def extract_minutes(text: str):
    match = re.search(r"через\s+(\d+)\s+мин", text)
    if match:
        return int(match.group(1))

    match = re.search(r"через\s+(\w+)\s+мин", text)
    if match:
        return WORD_NUMBERS.get(match.group(1))
    return None


def extract_reminder_text(text: str):
    text = re.sub(r"напомни( мне)?", "", text).strip()
    text = re.sub(r"создай напоминание", "", text).strip()
    text = re.sub(r"через\s+(\d+|\w+)\s+мин\w*", "", text).strip()
    return text or "о вашей задаче"


def extract_macro_name(text: str):
    text = normalize_text(text)
    triggers = [
        "научись действию",
        "запомни действие",
        "создай действие",
        "научись",
    ]

    for trigger in triggers:
        if trigger in text:
            value = text.split(trigger, 1)[1].strip(" :,.!?\"'")
            return value or None

    return None
