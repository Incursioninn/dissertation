import ctypes
import psutil

user32 = ctypes.windll.user32


def get_foreground_exe_path():
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        if not pid.value:
            return None

        process = psutil.Process(pid.value)
        return process.exe()
    except Exception as error:
        print(f"[LEARNING] Не удалось определить активный exe: {error}")
        return None
