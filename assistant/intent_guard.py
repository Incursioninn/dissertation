from .text_processing import normalize_text

FINISH_RECORDING_PHRASES = {
    "готово",
    "закончил",
    "закончила",
    "завершил",
    "завершила",
    "останови запись",
    "стоп запись",
}

CONFIRM_PHRASES = {
    "да",
    "да запомни",
    "запомни",
    "да правильно",
}

REJECT_PHRASES = {
    "нет",
    "отмена",
    "не надо",
}


def apply_intent_guards(text: str, intent: str):
    """
    Защитный слой от ложных срабатываний коротких служебных intent.

    Например, Vosk может распознать "стартани" как "стр тони",
    а модель ошибочно классифицирует это как finish_recording.
    Поэтому finish_recording разрешается только для точных служебных фраз.
    """
    clean = normalize_text(text)

    if intent == "finish_recording" and clean not in FINISH_RECORDING_PHRASES:
        return "none"

    if intent == "confirm" and clean not in CONFIRM_PHRASES:
        return "none"

    if intent == "reject" and clean not in REJECT_PHRASES:
        return "none"

    return intent
