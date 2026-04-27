import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant.data_store import load_intents
from assistant.intent_model import IntentClassifier


TESTS = [
    ("открой браузер", "open_target"),
    ("напечатай привет мир", "type_text"),
    ("сколько время", "get_time"),
    ("сделай громче", "volume_up"),
    ("открой документы", "open_folder"),
]


def main():
    clf = IntentClassifier(load_intents())
    clf.train()

    correct = 0
    for phrase, expected in TESTS:
        intent, confidence = clf.predict(phrase)
        print(phrase, "=>", intent, confidence)
        if intent == expected:
            correct += 1

    accuracy = correct / len(TESTS)
    print(f"Accuracy: {accuracy:.2f}")
    assert accuracy >= 0.8


if __name__ == "__main__":
    main()
