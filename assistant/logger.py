import csv
import logging
from datetime import datetime

from .config import LOG_DIR, ASSISTANT_LOG_FILE, COMMANDS_CSV_FILE


def setup_logger():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("assistant")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(ASSISTANT_LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if not COMMANDS_CSV_FILE.exists():
        with open(COMMANDS_CSV_FILE, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["datetime", "text", "intent", "confidence", "entities", "reply"])

    return logger


def log_command(text, intent, confidence, entities, reply):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(COMMANDS_CSV_FILE, "a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            text,
            intent,
            f"{confidence:.4f}",
            str(entities),
            reply,
        ])
