import os
import subprocess
import webbrowser
import time
import pyautogui
from pathlib import Path


class ActionEngine:
    def execute_target(self, target_config: dict):
        if not target_config:
            raise ValueError("Пустая конфигурация цели.")

        mode = target_config.get("mode")
        value = target_config.get("value")

        if mode == "url":
            webbrowser.open(value)
            return

        if mode == "command":
            subprocess.Popen([value])
            return

        if mode == "path":
            path = os.path.expandvars(value)
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            subprocess.Popen([path])
            return

        if mode == "paths":
            for raw_path in value:
                path = os.path.expandvars(raw_path)
                if os.path.exists(path):
                    subprocess.Popen([path])
                    return
            raise FileNotFoundError("Ни один путь из списка не найден.")

        if mode == "folder":
            path = os.path.expandvars(value)
            subprocess.Popen(["explorer", path])
            return

        if mode == "hotkey":
            pyautogui.hotkey(*value)
            return

        if mode == "press":
            pyautogui.press(value)
            return

        if mode == "key_down":
            pyautogui.keyDown(value)
            return

        if mode == "key_up":
            pyautogui.keyUp(value)
            return

        if mode == "delay":
            time.sleep(float(value))
            return

        if mode == "macro":
            for step in value:
                self.execute_target(step)
            return

        raise ValueError(f"Неизвестный режим выполнения: {mode}")

    def create_desktop_file(self, filename="note_from_assistant.txt", content="Новая заметка.\n"):
        desktop = Path(os.path.expandvars(r"%USERPROFILE%\Desktop"))
        filepath = desktop / filename
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)
        subprocess.Popen(["notepad.exe", str(filepath)])
