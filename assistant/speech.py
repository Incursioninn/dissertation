import json
import queue

import pyttsx3
import sounddevice as sd
from vosk import Model, KaldiRecognizer

from .config import SAMPLE_RATE, BLOCK_SIZE, VOSK_MODEL_PATH
from .event_bus import NullEventBus


class StreamingSpeechRecognizer:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus or NullEventBus()

        if not VOSK_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Модель Vosk не найдена: {VOSK_MODEL_PATH}. "
                "Скачайте русскую модель и распакуйте её в папку models."
            )

        print("[STT] Загружаю модель Vosk...")
        self.event_bus.emit("status", "Загружаю модель Vosk...")
        self.model = Model(str(VOSK_MODEL_PATH))
        print("[STT] Модель Vosk загружена.")
        self.event_bus.emit("status", "Модель Vosk загружена")

    def listen_phrase(self) -> str:
        recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
        recognizer.SetWords(True)

        audio_queue = queue.Queue()

        def callback(indata, frames, time, status):
            if status:
                print(status)
                self.event_bus.emit("error", str(status))
            audio_queue.put(bytes(indata))

        print("[AUDIO] Слушаю фразу...")
        self.event_bus.emit("status", "Слушаю...")

        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while True:
                data = audio_queue.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        self.event_bus.emit("recognized", text)
                        return text


class SpeechSynthesizer:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus or NullEventBus()
        self.engine = pyttsx3.init()
        rate = self.engine.getProperty("rate")
        self.engine.setProperty("rate", rate - 20)

    def say(self, text: str):
        if not text:
            return

        print("Ассистент:", text)
        self.event_bus.emit("assistant_reply", text)
        self.engine.say(text)
        self.engine.runAndWait()
