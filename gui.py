import json
import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from assistant.assistant_core import VoiceAssistant
from assistant.config import ACTIONS_FILE


class AssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Offline Voice Assistant")
        self.root.geometry("1050x640")

        self.event_queue = queue.Queue()
        self.assistant = None
        self.assistant_thread = None

        self.status = tk.StringVar(value="Готов к запуску")
        self.last_intent = tk.StringVar(value="-")
        self.last_confidence = tk.StringVar(value="-")
        self.last_text = tk.StringVar(value="-")

        self.build_ui()
        self.load_actions_tree()
        self.root.after(100, self.process_events)

    def build_ui(self):
        main = ttk.PanedWindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=10)
        right = ttk.Frame(main, padding=10)
        main.add(left, weight=3)
        main.add(right, weight=2)

        info = ttk.LabelFrame(left, text="Состояние", padding=10)
        info.pack(fill="x")

        ttk.Label(info, text="Статус:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(info, textvariable=self.status).grid(row=0, column=1, sticky="w", padx=8)

        ttk.Label(info, text="Распознано:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
        ttk.Label(info, textvariable=self.last_text).grid(row=1, column=1, sticky="w", padx=8)

        ttk.Label(info, text="Intent:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w")
        ttk.Label(info, textvariable=self.last_intent).grid(row=2, column=1, sticky="w", padx=8)

        ttk.Label(info, text="Confidence:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w")
        ttk.Label(info, textvariable=self.last_confidence).grid(row=3, column=1, sticky="w", padx=8)

        buttons = ttk.Frame(left, padding=(0, 10, 0, 10))
        buttons.pack(fill="x")

        self.start_button = ttk.Button(buttons, text="Запустить ассистента", command=self.start_assistant)
        self.start_button.pack(side="left")

        self.stop_button = ttk.Button(buttons, text="Остановить", command=self.stop_assistant, state="disabled")
        self.stop_button.pack(side="left", padx=8)

        self.clear_button = ttk.Button(buttons, text="Очистить лог", command=self.clear_log)
        self.clear_button.pack(side="left")

        ttk.Button(buttons, text="Обновить действия", command=self.load_actions_tree).pack(side="left", padx=8)

        log_frame = ttk.LabelFrame(left, text="Лог", padding=8)
        log_frame.pack(fill="both", expand=True)

        self.log_box = ScrolledText(log_frame, height=24, wrap="word")
        self.log_box.pack(fill="both", expand=True)

        actions_frame = ttk.LabelFrame(right, text="Известные действия", padding=8)
        actions_frame.pack(fill="both", expand=True)

        self.actions_tree = ttk.Treeview(actions_frame, columns=("mode", "value"), show="tree headings")
        self.actions_tree.heading("#0", text="Название")
        self.actions_tree.heading("mode", text="Mode")
        self.actions_tree.heading("value", text="Value")
        self.actions_tree.column("#0", width=160)
        self.actions_tree.column("mode", width=80)
        self.actions_tree.column("value", width=280)
        self.actions_tree.pack(fill="both", expand=True)

        help_frame = ttk.LabelFrame(right, text="Обучение действию", padding=8)
        help_frame.pack(fill="x", pady=(10, 0))

        help_text = (
            "1. Скажи: компьютер научись действию <название>\\n"
            "2. Выполни клавиатурное действие вручную\\n"
            "3. Скажи: компьютер готово\\n\\n"
            "Пример: компьютер научись действию следующее окно"
        )
        ttk.Label(help_frame, text=help_text, justify="left").pack(anchor="w")

        self.write_log("GUI готов. Нажми «Запустить ассистента».")

    def load_actions_tree(self):
        for item in self.actions_tree.get_children():
            self.actions_tree.delete(item)

        try:
            with open(ACTIONS_FILE, "r", encoding="utf-8") as file:
                config = json.load(file)
        except Exception as error:
            self.write_log(f"[ERROR] Не удалось загрузить actions.json: {error}")
            return

        targets_root = self.actions_tree.insert("", "end", text="targets", values=("", ""))
        for name, action in sorted(config.get("targets", {}).items()):
            mode = action.get("mode", "")
            value = action.get("value", "")
            value_str = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value)
            self.actions_tree.insert(targets_root, "end", text=name, values=(mode, value_str[:160]))

        folders_root = self.actions_tree.insert("", "end", text="folders", values=("", ""))
        for name, action in sorted(config.get("folders", {}).items()):
            mode = action.get("mode", "")
            value = action.get("value", "")
            self.actions_tree.insert(folders_root, "end", text=name, values=(mode, str(value)))

        self.actions_tree.item(targets_root, open=True)
        self.actions_tree.item(folders_root, open=True)

    def event_callback(self, event_type, message="", data=None):
        self.event_queue.put((event_type, message, data or {}))

    def start_assistant(self):
        if self.assistant_thread and self.assistant_thread.is_alive():
            return

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status.set("Запуск...")

        def runner():
            try:
                self.assistant = VoiceAssistant(event_callback=self.event_callback)
                self.assistant.run()
            except Exception as error:
                self.event_queue.put(("error", str(error), {}))
            finally:
                self.event_queue.put(("stopped", "Ассистент завершил работу", {}))

        self.assistant_thread = threading.Thread(target=runner, daemon=True)
        self.assistant_thread.start()

    def stop_assistant(self):
        if self.assistant:
            self.assistant.stop()
        self.status.set("Останавливается...")
        self.write_log("[SYSTEM] Остановка будет выполнена после завершения текущего прослушивания.")

    def process_events(self):
        try:
            while True:
                event_type, message, data = self.event_queue.get_nowait()

                if event_type == "status":
                    self.status.set(message)
                    self.write_log(f"[STATUS] {message}")

                elif event_type == "recognized":
                    self.last_text.set(message)
                    self.write_log(f"[STT] {message}")

                elif event_type == "command":
                    intent = data.get("intent", "-")
                    confidence = data.get("confidence", 0.0)
                    self.last_intent.set(intent)
                    self.last_confidence.set(f"{confidence:.2f}")
                    self.write_log(f"[COMMAND] {message}")

                elif event_type == "assistant_reply":
                    self.write_log(f"[ASSISTANT] {message}")

                elif event_type == "actions_updated":
                    self.write_log(f"[ACTIONS] {message}")
                    self.load_actions_tree()

                elif event_type == "error":
                    self.status.set("Ошибка")
                    self.write_log(f"[ERROR] {message}")

                elif event_type == "stopped":
                    self.status.set("Остановлен")
                    self.start_button.config(state="normal")
                    self.stop_button.config(state="disabled")
                    self.write_log(f"[SYSTEM] {message}")

                else:
                    self.write_log(f"[{event_type.upper()}] {message}")

        except queue.Empty:
            pass

        self.root.after(100, self.process_events)

    def write_log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def clear_log(self):
        self.log_box.delete("1.0", "end")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AssistantGUI().run()
