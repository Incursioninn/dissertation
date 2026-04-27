import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant.data_store import load_intents, save_intents
from assistant.intent_model import INTENTS
from assistant.text_processing import normalize_text


def add_phrase(phrase, intent):
    if intent not in INTENTS:
        raise ValueError(f"Неизвестный intent: {intent}. Доступные: {', '.join(INTENTS)}")

    data = load_intents()
    item = {"phrase": normalize_text(phrase), "intent": intent}

    if item not in data:
        data.append(item)
        save_intents(data)
        print("Фраза добавлена.")
    else:
        print("Такая фраза уже есть.")


def list_intents():
    print("\n".join(INTENTS))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add")
    add.add_argument("phrase")
    add.add_argument("intent")

    sub.add_parser("intents")

    args = parser.parse_args()

    if args.command == "add":
        add_phrase(args.phrase, args.intent)
    elif args.command == "intents":
        list_intents()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
