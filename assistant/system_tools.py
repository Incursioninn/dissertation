import ctypes
import time
from datetime import datetime

import pyautogui
import win32gui
import win32process
import psutil


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

user32 = ctypes.windll.user32

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def press_vk(key):
    user32.keybd_event(key, 0, KEYEVENTF_EXTENDEDKEY, 0)
    time.sleep(0.05)
    user32.keybd_event(key, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

def get_active_exe_path():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()

        if not hwnd:
            return None

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        if not pid.value:
            return None

        return psutil.Process(pid.value).exe()

    except Exception as error:
        print(f"[AUTO_LEARN] Не удалось определить активный exe: {error}")
        return None

def volume_up():
    press_vk(VK_VOLUME_UP)


def volume_down():
    press_vk(VK_VOLUME_DOWN)


def volume_mute():
    press_vk(VK_VOLUME_MUTE)


def switch_window():
    pyautogui.hotkey("alt", "tab")


def get_time_reply():
    now = datetime.now()
    return f"Сейчас {now.hour} часов {now.minute:02d} минут."


def get_date_reply():
    today = datetime.now()
    month = MONTHS_RU.get(today.month, "")
    return f"Сегодня {today.day} {month} {today.year} года."
