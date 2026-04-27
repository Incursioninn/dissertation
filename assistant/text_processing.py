import re

FILLER_WORDS = {
    "пожалуйста",
    "можешь",
    "можно",
    "мне",
    "давай",
    "ну",
    "ка",
    "компьютер",
    "слушай",
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ё", "е")
    text = re.sub(r"[^а-яa-z0-9\.\s:/_-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    words = [word for word in text.split() if word not in FILLER_WORDS]
    return " ".join(words)


def tokenize(text: str):
    return normalize_text(text).split()


def remove_command_verbs(text: str) -> str:
    text = normalize_text(text)
    prefixes = [
        "открой", "открыть", "запусти", "запустить", "запускай", "включи",
        "перейди на", "зайди на", "сайт", "папку", "удали", "забудь", "программу",
    ]

    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if text == prefix:
                return ""
            if text.startswith(prefix + " "):
                text = text[len(prefix):].strip()
                changed = True
    return text
