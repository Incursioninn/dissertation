from click import command

from .config import WAKE_WORD, LOW_CONFIDENCE_THRESHOLD, ALLOW_COMMANDS_WITHOUT_WAKE_WORD
from .data_store import load_actions, load_intents, load_synonyms, save_intents, load_synonyms, save_intents
from .entities import extract_entities
from .dataset_augmenter import augment_dataset
from .command_normalizer import canonicalize_command
from .event_bus import EventBus, NullEventBus
from .executor import CommandExecutor
from .intent_model import Command, IntentClassifier
from .fallback_engine import apply_contextual_fallback
from .intent_guard import apply_intent_guards
from .logger import setup_logger, log_command
from .speech import StreamingSpeechRecognizer, SpeechSynthesizer


class VoiceAssistant:
    def __init__(self, event_callback=None):
        self.event_bus = EventBus(event_callback) if event_callback else NullEventBus()
        self.logger = setup_logger()

        self.event_bus.emit("status", "Загружаю данные...")
        self.intent_data = load_intents()
        self.actions_config = load_actions()
        self.synonyms_config = load_synonyms()

        added = augment_dataset(self.intent_data, self.actions_config, self.synonyms_config)
        if added:
            save_intents(self.intent_data)
            self.event_bus.emit("status", f"Обучающая выборка расширена: +{added} фраз")

        self.event_bus.emit("status", "Инициализирую нейросеть...")
        self.classifier = IntentClassifier(self.intent_data)
        self.classifier.train()

        self.stt = StreamingSpeechRecognizer(event_bus=self.event_bus)
        self.tts = SpeechSynthesizer(event_bus=self.event_bus)

        self.executor = CommandExecutor(self.actions_config, self.classifier, self.synonyms_config)
        self.pending_low_confidence_command = None
        self.running = True

    def stop(self):
        self.running = False
        self.event_bus.emit("status", "Остановка ассистента...")

    def analyze(self, text: str):
        normalized_text = canonicalize_command(text, self.synonyms_config)
        intent, confidence = self.classifier.predict(normalized_text)
        intent = apply_intent_guards(normalized_text, intent)
        entities = extract_entities(normalized_text, intent, self.actions_config)

        command_text = normalized_text if intent != "none" else text
        command = Command(text=command_text, intent=intent, confidence=confidence, entities=entities)
        print(f"[COMMAND] {command}")
        self.event_bus.emit(
            "command",
            f"intent={command.intent}, confidence={command.confidence:.2f}, entities={command.entities}",
            {
                "text": command.text,
                "intent": command.intent,
                "confidence": command.confidence,
                "entities": command.entities,
            },
        )
        return command

    def process_text(self, text: str):
        text = text.strip()

        if not text:
            self.tts.say("Я не расслышал команду.")
            return False

        low = text.lower()

        if any(phrase in low for phrase in ["выход", "завершить работу", "стоп ассистент"]):
            self.tts.say("Останавливаюсь. До свидания.")
            return True

        command = self.analyze(text)
        from assistant.fallback_engine import apply_contextual_fallback

        command = apply_contextual_fallback(
            command,
            self.actions_config,
            self.synonyms_config
        )

        if command.intent == "none":
            if len(command.text.split()) >= 2:
                reply = self.executor.start_auto_learning(command.text)
            else:
                reply = "Я не понял команду"

            self.tts.say(reply)
            return

        # Завершение записи макроса должно срабатывать без дополнительного подтверждения.
        if command.intent == "finish_recording":
            reply = self.executor.execute(command, self.tts, self.stt)
            self.tts.say(reply)
            self.event_bus.emit("actions_updated", "Список действий обновлён")
            log_command(command.text, command.intent, command.confidence, command.entities, reply)
            return False

        if command.confidence < LOW_CONFIDENCE_THRESHOLD and command.intent not in {"confirm", "reject", "finish_recording"}:
            self.pending_low_confidence_command = command
            reply = f"Я не совсем уверен. Выполнить команду: {command.text}? Скажи да или отмена."
            self.tts.say(reply)
            log_command(command.text, command.intent, command.confidence, command.entities, reply)
            return False

        if command.intent == "confirm" and self.pending_low_confidence_command:
            pending = self.pending_low_confidence_command
            self.pending_low_confidence_command = None
            reply = self.executor.execute(pending, self.tts, self.stt)
            self.tts.say(reply)
            log_command(pending.text, pending.intent, pending.confidence, pending.entities, reply)
            return False

        if command.intent == "reject" and self.pending_low_confidence_command:
            self.pending_low_confidence_command = None
            reply = "Хорошо, отменяю."
            self.tts.say(reply)
            log_command(command.text, command.intent, command.confidence, command.entities, reply)
            return False

        reply = self.executor.execute(command, self.tts, self.stt)
        self.tts.say(reply)

        if command.intent in {"learn_macro", "confirm", "delete_target"}:
            self.event_bus.emit("actions_updated", "Список действий обновлён")

        log_command(command.text, command.intent, command.confidence, command.entities, reply)
        return False

    def run(self):
        self.event_bus.emit("status", "Ассистент запущен")
        self.tts.say("Голосовой помощник запущен.")

        while self.running:
            self.executor.check_reminders(self.tts)

            text = self.stt.listen_phrase()
            print(f"[STT] {text}")

            low = text.lower()

            if WAKE_WORD in low:
                after_wake = low.split(WAKE_WORD, 1)[1].strip(" ,.!?")

                if after_wake.startswith("слушай"):
                    after_wake = after_wake.replace("слушай", "", 1).strip(" ,.!?")

                if after_wake:
                    if self.process_text(after_wake):
                        break
                else:
                    self.tts.say("Слушаю.")
                    command_text = self.stt.listen_phrase()
                    if self.process_text(command_text):
                        break

            elif ALLOW_COMMANDS_WITHOUT_WAKE_WORD:
                if self.process_text(low):
                    break

        self.event_bus.emit("status", "Ассистент остановлен")
