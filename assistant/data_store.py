import json
from pathlib import Path

from .config import DATA_DIR, INTENTS_FILE, ACTIONS_FILE, SYNONYMS_FILE


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data):
    ensure_data_dir()
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_intents():
    return load_json(INTENTS_FILE)


def save_intents(intent_data):
    save_json(INTENTS_FILE, intent_data)


def load_actions():
    return load_json(ACTIONS_FILE)


def save_actions(actions_config):
    save_json(ACTIONS_FILE, actions_config)


def load_synonyms():
    return load_json(SYNONYMS_FILE)


def save_synonyms(synonyms_data):
    save_json(SYNONYMS_FILE, synonyms_data)
