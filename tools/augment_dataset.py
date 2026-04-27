import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant.data_store import load_actions, load_intents, load_synonyms, save_intents
from assistant.dataset_augmenter import augment_dataset


def main():
    intents = load_intents()
    actions = load_actions()
    synonyms = load_synonyms()

    added = augment_dataset(intents, actions, synonyms)
    save_intents(intents)
    print(f"Добавлено фраз: {added}")


if __name__ == "__main__":
    main()
