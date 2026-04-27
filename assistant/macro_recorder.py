import time
from typing import List, Dict, Any

try:
    from pynput import keyboard as pynput_keyboard
except ImportError:
    pynput_keyboard = None


SPECIAL_KEYS = {
    "Key.alt_l": "alt",
    "Key.alt_r": "alt",
    "Key.ctrl_l": "ctrl",
    "Key.ctrl_r": "ctrl",
    "Key.shift_l": "shift",
    "Key.shift_r": "shift",
    "Key.cmd": "win",
    "Key.cmd_l": "win",
    "Key.cmd_r": "win",
    "Key.tab": "tab",
    "Key.enter": "enter",
    "Key.esc": "esc",
    "Key.space": "space",
    "Key.backspace": "backspace",
    "Key.delete": "delete",
    "Key.up": "up",
    "Key.down": "down",
    "Key.left": "left",
    "Key.right": "right",
    "Key.f1": "f1",
    "Key.f2": "f2",
    "Key.f3": "f3",
    "Key.f4": "f4",
    "Key.f5": "f5",
    "Key.f6": "f6",
    "Key.f7": "f7",
    "Key.f8": "f8",
    "Key.f9": "f9",
    "Key.f10": "f10",
    "Key.f11": "f11",
    "Key.f12": "f12",
}


def normalize_key(key) -> str:
    key_str = str(key)

    if key_str in SPECIAL_KEYS:
        return SPECIAL_KEYS[key_str]

    if hasattr(key, "char") and key.char:
        return key.char.lower()

    return key_str.replace("Key.", "").lower()


class KeyboardMacroRecorder:
    """
    Записывает клавиатурные действия пользователя.

    Запись не пытается понять «смысл» действия. Она сохраняет события:
    - key_down
    - key_up
    - delay

    При воспроизведении эти события выполняются через pyautogui.
    """

    def __init__(self):
        if pynput_keyboard is None:
            raise ImportError("Для записи макросов установите pynput: pip install pynput")

        self.events: List[Dict[str, Any]] = []
        self.listener = None
        self.is_recording = False
        self.last_time = None

    def start(self):
        self.events = []
        self.is_recording = True
        self.last_time = time.time()

        self.listener = pynput_keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self.listener.start()

    def stop(self):
        self.is_recording = False

        if self.listener:
            self.listener.stop()
            self.listener = None

        return self.compact_events(self.events)

    def _add_delay(self):
        now = time.time()
        delay = now - self.last_time
        self.last_time = now

        if delay > 0.05:
            self.events.append({
                "mode": "delay",
                "value": round(delay, 3),
            })

    def _on_press(self, key):
        if not self.is_recording:
            return

        self._add_delay()
        self.events.append({
            "mode": "key_down",
            "value": normalize_key(key),
        })

    def _on_release(self, key):
        if not self.is_recording:
            return

        self._add_delay()
        self.events.append({
            "mode": "key_up",
            "value": normalize_key(key),
        })

    def compact_events(self, events):
        """
        Упрощает типичный hotkey вида:
        key_down alt, key_down tab, key_up tab, key_up alt
        в {"mode": "hotkey", "value": ["alt", "tab"]}

        Если паттерн сложный, сохраняет raw macro.
        """
        no_delays = [e for e in events if e["mode"] != "delay"]

        if len(no_delays) == 4:
            if no_delays[0]["mode"] == "key_down" and no_delays[1]["mode"] == "key_down":
                if no_delays[2]["mode"] == "key_up" and no_delays[3]["mode"] == "key_up":
                    k1 = no_delays[0]["value"]
                    k2 = no_delays[1]["value"]

                    if no_delays[2]["value"] == k2 and no_delays[3]["value"] == k1:
                        return [{
                            "mode": "hotkey",
                            "value": [k1, k2],
                        }]

        return events
