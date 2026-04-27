import sys
from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant.intent_model import Command
from assistant.fallback_engine import apply_contextual_fallback


def test_false_finish_recording_becomes_none():
    cmd = Command(
        text="стр тони игру",
        intent="finish_recording",
        confidence=0.99,
        entities={},
    )
    result = apply_contextual_fallback(cmd, {"targets": {}, "folders": {}})
    assert result.intent == "none"


def test_exact_ready_stays_finish_recording():
    cmd = Command(
        text="готово",
        intent="finish_recording",
        confidence=0.99,
        entities={},
    )
    result = apply_contextual_fallback(cmd, {"targets": {}, "folders": {}})
    assert result.intent == "finish_recording"


if __name__ == "__main__":
    test_false_finish_recording_becomes_none()
    test_exact_ready_stays_finish_recording()
    print("Fallback tests passed.")
