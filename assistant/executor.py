import time

import keyboard

from .action_engine import ActionEngine
from .data_store import save_actions, save_intents, save_synonyms
from .learning import get_foreground_exe_path
from .skills.reminders import ReminderSkill
from .macro_recorder import KeyboardMacroRecorder
from .command_normalizer import split_possible_verb_and_target
from .system_tools import get_active_exe_path
from .system_tools import (
    get_time_reply, get_date_reply, volume_up, volume_down, volume_mute, switch_window,
)


class CommandExecutor:
    def __init__(self, actions_config: dict, intent_classifier, synonyms_config=None):
        self.actions_config = actions_config
        self.intent_classifier = intent_classifier
        self.synonyms_config = synonyms_config if synonyms_config is not None else {}
        self.action_engine = ActionEngine()
        self.pending_target_name = None
        self.pending_unknown_text = None
        self.pending_unknown_verb = None
        self.pending_confirmation = None
        self.macro_recorder = None
        self.recording_macro_name = None
        self.pending_auto_learn = None
        self.reminder_skill = ReminderSkill()
        self.skills = [self.reminder_skill]
        
    def check_auto_learning(self):
        if not self.pending_auto_learn:
            return None

        if time.time() - self.pending_auto_learn["start_time"] < 3:
            return None

        new_app = get_active_exe_path()
        old_app = self.pending_auto_learn["initial_app"]

        if new_app and new_app != old_app:
            text = self.pending_auto_learn["text"]

            parts = text.split(maxsplit=1)
            verb, target = (parts + [None])[:2]

        # сохраняем программу
            self.actions_config.setdefault("targets", {})[target] = {
                "mode": "path",
                "value": new_app,
                "aliases": []
            }
            save_actions(self.actions_config)

            # сохраняем глагол
            if verb:
                self.synonyms_config.setdefault("learned_verbs", {})[verb] = "open_target"
                save_synonyms(self.synonyms_config)

            self.pending_auto_learn = None
            return f"Запомнил {target}"
        
    def start_auto_learning(self, text):
        parts = text.split(maxsplit=1)

        if len(parts) == 2:
            verb, target = parts

            if target in self.actions_config.get("targets", {}):
                self.pending_confirmation = {
                    "type": "learn_verb",
                    "verb": verb,
                    "target": target
                }
                return f"Слово {verb} означает открыть {target}? Скажи да или отмена."

        self.pending_auto_learn = {
            "text": text,
            "start_time": time.time(),
            "initial_app": get_active_exe_path()
        }

        return "Открой нужную программу"

    def execute(self, command, tts, stt):
        intent = command.intent

        if intent == "finish_recording":
            return self.finish_macro_recording()

        if intent == "confirm":
            return self.confirm(tts, stt)

        if intent == "reject":
            self.pending_confirmation = None
            self.pending_target_name = None
            return "Хорошо, отменяю."

        for skill in self.skills:
            if skill.can_handle(intent):
                return skill.handle(command, {"tts": tts, "stt": stt})

        if intent == "open_target":
            return self.open_target(command.entities.get("target_name"))

        if intent == "open_folder":
            return self.open_folder(command.entities.get("folder_name"))

        if intent == "create_file":
            self.action_engine.create_desktop_file()
            return "Создаю файл на рабочем столе."

        if intent == "type_text":
            return self.type_text(command.entities.get("typed_text"), tts, stt)

        if intent == "get_time":
            return get_time_reply()

        if intent == "get_date":
            return get_date_reply()

        if intent == "volume_up":
            volume_up()
            return "Делаю громче."

        if intent == "volume_down":
            volume_down()
            return "Делаю тише."

        if intent == "volume_mute":
            volume_mute()
            return "Переключаю звук."

        if intent == "switch_window":
            switch_window()
            return "Переключаю окно."

        if intent == "list_targets":
            return self.list_targets()

        if intent == "learn_macro":
            return self.start_macro_learning(command.entities.get("macro_name"), tts, stt)

        if intent == "delete_target":
            return self.delete_target(command.entities.get("target_name"))

        return "Я услышал команду, но пока не умею её выполнять."

    def open_target(self, target_name: str):
        if not target_name:
            return "Не понял, что нужно открыть."

        target_name = target_name.lower().strip()
        targets = self.actions_config.setdefault("targets", {})
        target_config = targets.get(target_name)

        if not target_config:
            found_key, target_config = self.find_by_alias(target_name, targets)
            if found_key:
                target_name = found_key

        if target_config:
            try:
                self.action_engine.execute_target(target_config)
                return f"Открываю {target_name}."
            except Exception as error:
                print(f"[ACTION] Ошибка выполнения цели {target_name}: {error}")
                self.pending_target_name = target_name
                self.pending_confirmation = "learn_target"
                return f"Я нашёл {target_name}, но не смог открыть. Открой программу вручную и скажи: компьютер запомни."

        self.pending_target_name = target_name
        self.pending_confirmation = "learn_target"
        return f"Я пока не знаю {target_name}. Открой нужную программу вручную, сделай её активным окном, а затем скажи: компьютер запомни."

    def open_folder(self, folder_name: str):
        if not folder_name:
            return "Не понял, какую папку открыть."

        folders = self.actions_config.setdefault("folders", {})
        folder_config = folders.get(folder_name)

        if not folder_config:
            found_key, folder_config = self.find_by_alias(folder_name, folders)
            if found_key:
                folder_name = found_key

        if not folder_config:
            return f"Я не знаю папку {folder_name}."

        try:
            self.action_engine.execute_target(folder_config)
            return f"Открываю папку {folder_name}."
        except Exception as error:
            print(f"[ACTION] Ошибка открытия папки: {error}")
            return "Не удалось открыть папку."

    def find_by_alias(self, name: str, items: dict):
        for key, config in items.items():
            aliases = config.get("aliases", [])
            if name == key or name in aliases:
                return key, config
            for alias in aliases:
                if name in alias or alias in name:
                    return key, config
        return None, None

    def type_text(self, typed_text: str, tts, stt):
        if not typed_text:
            tts.say("Что напечатать?")
            typed_text = stt.listen_phrase().strip().lower()

        if not typed_text:
            return "Я не услышал текст для ввода."

        for char in typed_text:
            keyboard.write(char)
            time.sleep(0.01)

        return "Готово."

    def check_reminders(self, tts):
        self.reminder_skill.check(tts)

    def list_targets(self):
        targets = sorted(self.actions_config.get("targets", {}).keys())
        if not targets:
            return "Пока я не знаю ни одной программы или цели."
        visible = ", ".join(targets[:20])
        if len(targets) > 20:
            visible += f" и ещё {len(targets) - 20}."
        return f"Я знаю: {visible}."

    def delete_target(self, target_name):
        if not target_name:
            return "Не понял, что нужно удалить."

        targets = self.actions_config.setdefault("targets", {})
        found_key = target_name if target_name in targets else None

        if not found_key:
            found_key, _ = self.find_by_alias(target_name, targets)

        if not found_key:
            return f"Я не нашёл {target_name} в списке известных целей."

        self.pending_confirmation = {"type": "delete_target", "target_name": found_key}
        return f"Удалить {found_key}? Скажи да или отмена."

    def start_macro_learning(self, macro_name, tts, stt):
        if not macro_name:
            tts.say("Как назвать новое действие?")
            macro_name = stt.listen_phrase().strip().lower()

        if not macro_name:
            return "Я не услышал название действия."

        if self.macro_recorder is not None:
            return "Запись уже выполняется. Скажи готово, чтобы завершить."

        try:
            self.macro_recorder = KeyboardMacroRecorder()
            self.recording_macro_name = macro_name
            self.macro_recorder.start()
        except Exception as error:
            self.macro_recorder = None
            self.recording_macro_name = None
            return f"Не удалось начать запись действия: {error}"

        return (
            f"Начал запись действия {macro_name}. "
            "Выполни нужные клавиатурные действия вручную, затем скажи: компьютер готово."
        )

    def finish_macro_recording(self):
        if self.macro_recorder is None or not self.recording_macro_name:
            return "Сейчас нет активной записи действия."

        macro_name = self.recording_macro_name
        events = self.macro_recorder.stop()

        self.macro_recorder = None
        self.recording_macro_name = None

        if not events:
            return "Я не записал ни одного действия."

        self.actions_config.setdefault("targets", {})[macro_name] = {
            "mode": "macro",
            "value": events,
            "aliases": [],
        }

        save_actions(self.actions_config)

        self.intent_classifier.add_open_target_training(macro_name)
        self.intent_classifier.add_delete_target_training(macro_name)
        save_intents(self.intent_classifier.intent_data)

        return f"Запомнил действие {macro_name}."
    
    def finish_auto_learning(self):
        if not self.pending_auto_learn:
            return "Мне пока нечего запоминать."

        text = self.pending_auto_learn["text"]
        parts = text.split(maxsplit=1)

        if len(parts) == 2:
            verb, target = parts
        else:
            verb = None
            target = text

        new_app = get_active_exe_path()

        if not new_app:
            return "Не удалось определить активную программу."

        self.actions_config.setdefault("targets", {})[target] = {
            "mode": "path",
            "value": new_app,
            "aliases": []
        }

        save_actions(self.actions_config)

        if verb:
            self.synonyms_config.setdefault("learned_verbs", {})[verb] = "open_target"
            save_synonyms(self.synonyms_config)
            self.intent_classifier.add_training_phrase(f"{verb} {target}", "open_target")

        self.intent_classifier.add_open_target_training(target)
        save_intents(self.intent_classifier.intent_data)

        self.pending_auto_learn = None

        if verb:
            return f"Запомнил {target} и понял, что {verb} означает открыть."

        return f"Запомнил {target}."

    def start_unknown_command_learning(self, original_text: str):
        """
        Обучение неизвестной фразе вида "стартани игру".
        Первое слово считается новым глаголом, остальная часть — новой целью.
        """
        verb, target = split_possible_verb_and_target(original_text)

        if not target:
            target = original_text.strip().lower()

        self.pending_unknown_text = original_text
        self.pending_unknown_verb = verb
        self.pending_target_name = target
        self.pending_confirmation = "learn_target"

        if verb:
            return (
                f"Я пока не знаю команду {original_text}. "
                f"Предположу, что {verb} означает открыть, а {target} — название программы. "
                "Открой нужную программу вручную, сделай её активным окном, затем скажи: компьютер запомни."
            )

        return (
            f"Я пока не знаю {target}. "
            "Открой нужную программу вручную, сделай её активным окном, затем скажи: компьютер запомни."
        )

    def confirm(self, tts, stt):
        if self.pending_auto_learn:
            result = self.finish_auto_learning()
            return result

        if self.pending_confirmation == "learn_target":
            return self.confirm_learning()

        if isinstance(self.pending_confirmation, dict):
            action_type = self.pending_confirmation.get("type")

            if action_type == "learn_verb":
                verb = self.pending_confirmation["verb"]
                target = self.pending_confirmation["target"]
                self.pending_confirmation = None

                self.synonyms_config.setdefault("learned_verbs", {})[verb] = "open_target"
                save_synonyms(self.synonyms_config)

                self.intent_classifier.add_training_phrase(f"{verb} {target}", "open_target")
                save_intents(self.intent_classifier.intent_data)

                return f"Запомнил: {verb} означает открыть."

        return "Мне пока нечего подтверждать."

    def confirm_learning(self):
        if not self.pending_target_name:
            return "Мне пока нечего запоминать."

        exe_path = get_foreground_exe_path()
        if not exe_path:
            return "Не удалось определить активную программу."

        target_name = self.pending_target_name
        self.pending_target_name = None
        self.pending_unknown_text = None
        self.pending_unknown_verb = None
        self.pending_confirmation = None

        self.actions_config.setdefault("targets", {})[target_name] = {"mode": "path", "value": exe_path, "aliases": []}
        save_actions(self.actions_config)

        learned_verb = self.pending_unknown_verb
        learned_text = self.pending_unknown_text
        self.pending_unknown_verb = None
        self.pending_unknown_text = None

        if learned_verb:
            self.synonyms_config.setdefault("learned_verbs", {})[learned_verb] = "open_target"
            save_synonyms(self.synonyms_config)
            self.intent_classifier.add_training_phrase(f"{learned_verb} {target_name}", "open_target")

        if learned_text:
            self.intent_classifier.add_training_phrase(learned_text, "open_target")

        self.intent_classifier.add_open_target_training(target_name)
        self.intent_classifier.add_delete_target_training(target_name)
        save_intents(self.intent_classifier.intent_data)

        if learned_verb:
            return f"Запомнил {target_name} и понял, что {learned_verb} означает открыть."

        return f"Запомнил {target_name}."

    def confirm_delete_target(self, target_name):
        targets = self.actions_config.setdefault("targets", {})
        if target_name not in targets:
            return f"{target_name} уже отсутствует в списке."

        del targets[target_name]
        save_actions(self.actions_config)
        return f"Удалил {target_name}."
