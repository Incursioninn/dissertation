import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant.data_store import load_actions
from assistant.entities import extract_entities


def test_open_target():
    actions = load_actions()
    entities = extract_entities("открой браузер", "open_target", actions)
    assert entities["target_name"] == "браузер"


def test_type_text():
    actions = load_actions()
    entities = extract_entities("напечатай привет мир", "type_text", actions)
    assert entities["typed_text"] == "привет мир"


def test_reminder():
    actions = load_actions()
    entities = extract_entities("напомни через пять минут проверить почту", "set_reminder", actions)
    assert entities["minutes"] == 5


if __name__ == "__main__":
    test_open_target()
    test_type_text()
    test_reminder()
    print("Entity tests passed.")
