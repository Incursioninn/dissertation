import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn

from .config import (
    CACHE_DIR, MODEL_CACHE_FILE, VOCAB_CACHE_FILE, META_CACHE_FILE,
    EMBEDDING_DIM, HIDDEN_DIM, EPOCHS, LEARNING_RATE,
    INTENT_THRESHOLD, MAX_SEQUENCE_LENGTH,
)
from .text_processing import tokenize, normalize_text


INTENTS = [
    "open_target", "type_text", "get_time", "get_date", "volume_up", "volume_down",
    "volume_mute", "switch_window", "open_folder", "create_file", "set_reminder",
    "list_targets", "delete_target", "learn_macro", "finish_recording", "confirm", "reject", "none",
]

INTENT_TO_IDX = {name: index for index, name in enumerate(INTENTS)}
IDX_TO_INTENT = {index: name for name, index in INTENT_TO_IDX.items()}
PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"


@dataclass
class Command:
    text: str
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)


class GRUIntentNet(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.gru = nn.GRU(embedding_dim, hidden_dim, batch_first=True)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        embedded = self.embedding(x)
        _, hidden = self.gru(embedded)
        last_hidden = hidden[-1]
        return self.classifier(last_hidden)


class IntentClassifier:
    def __init__(self, intent_data: List[dict]):
        self.intent_data = intent_data
        self.words = []
        self.word_to_idx = {}
        self.model = None

    def dataset_hash(self):
        payload = json.dumps(self.intent_data, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def build_vocab(self):
        words = {PAD_TOKEN, UNK_TOKEN}

        for item in self.intent_data:
            intent = item.get("intent")
            if intent not in INTENT_TO_IDX:
                raise ValueError(f"Неизвестный intent в intents.json: {intent}")

            for token in tokenize(item["phrase"]):
                words.add(token)

        self.words = [PAD_TOKEN, UNK_TOKEN] + sorted(words - {PAD_TOKEN, UNK_TOKEN})
        self.word_to_idx = {word: index for index, word in enumerate(self.words)}

    @property
    def vocab_size(self):
        return len(self.words)

    def text_to_sequence(self, text: str):
        tokens = tokenize(text)
        ids = [self.word_to_idx.get(token, self.word_to_idx[UNK_TOKEN]) for token in tokens]
        ids = ids[:MAX_SEQUENCE_LENGTH]
        ids += [self.word_to_idx[PAD_TOKEN]] * (MAX_SEQUENCE_LENGTH - len(ids))
        return np.array(ids, dtype=np.int64)

    def load_from_cache(self):
        if not MODEL_CACHE_FILE.exists() or not VOCAB_CACHE_FILE.exists() or not META_CACHE_FILE.exists():
            return False

        with open(META_CACHE_FILE, "r", encoding="utf-8") as file:
            meta = json.load(file)

        if meta.get("dataset_hash") != self.dataset_hash():
            return False

        with open(VOCAB_CACHE_FILE, "r", encoding="utf-8") as file:
            self.words = json.load(file)

        self.word_to_idx = {word: index for index, word in enumerate(self.words)}

        self.model = GRUIntentNet(self.vocab_size, EMBEDDING_DIM, HIDDEN_DIM, len(INTENTS))
        self.model.load_state_dict(torch.load(MODEL_CACHE_FILE, map_location="cpu"))
        self.model.eval()

        print("[NN] GRU-модель загружена из cache.")
        return True

    def save_to_cache(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        torch.save(self.model.state_dict(), MODEL_CACHE_FILE)

        with open(VOCAB_CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(self.words, file, ensure_ascii=False, indent=2)

        with open(META_CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "dataset_hash": self.dataset_hash(),
                    "vocab_size": self.vocab_size,
                    "intents": INTENTS,
                    "architecture": "Embedding+GRU",
                    "max_sequence_length": MAX_SEQUENCE_LENGTH,
                },
                file,
                ensure_ascii=False,
                indent=2,
            )

        print("[NN] GRU-модель сохранена в cache.")

    def train(self, force=False):
        if not force and self.load_from_cache():
            return

        print("[NN] Обучаю GRU intent-модель...")
        self.build_vocab()

        x_data = np.stack([self.text_to_sequence(item["phrase"]) for item in self.intent_data])
        y_data = np.array([INTENT_TO_IDX[item["intent"]] for item in self.intent_data], dtype=np.int64)

        x_tensor = torch.from_numpy(x_data)
        y_tensor = torch.from_numpy(y_data)

        self.model = GRUIntentNet(self.vocab_size, EMBEDDING_DIM, HIDDEN_DIM, len(INTENTS))

        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=LEARNING_RATE)

        self.model.train()
        for _ in range(EPOCHS):
            optimizer.zero_grad()
            outputs = self.model(x_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()

        self.model.eval()
        self.save_to_cache()

    def predict(self, text: str, threshold: float = INTENT_THRESHOLD) -> Tuple[str, float]:
        if not text or self.model is None or self.vocab_size == 0:
            return "none", 0.0

        clean_text = normalize_text(text)
        sequence = self.text_to_sequence(clean_text)
        x_tensor = torch.from_numpy(sequence).unsqueeze(0)

        with torch.no_grad():
            logits = self.model(x_tensor)
            probabilities = torch.softmax(logits, dim=1)[0]
            confidence, index = torch.max(probabilities, dim=0)

        confidence_value = float(confidence.item())
        intent = IDX_TO_INTENT[int(index)]

        print(f"[NN] text='{clean_text}' intent={intent} confidence={confidence_value:.2f}")

        if confidence_value < threshold:
            return "none", confidence_value

        return intent, confidence_value

    def add_training_phrase(self, phrase: str, intent: str):
        phrase = normalize_text(phrase)
        if not phrase:
            return
        if intent not in INTENT_TO_IDX:
            raise ValueError(f"Неизвестный intent: {intent}")

        item = {"phrase": phrase, "intent": intent}
        if item not in self.intent_data:
            self.intent_data.append(item)

    def add_open_target_training(self, target_name: str):
        target_name = normalize_text(target_name)

        if not target_name:
            return

        verbs = [
            "открой", "запусти", "стартани", "включи", "загрузи",
            "активируй", "открой мне", "запусти мне",
            "можешь открыть", "можешь запустить",
            "давай открой", "давай запусти",
        ]

        for verb in verbs:
            self.add_training_phrase(f"{verb} {target_name}", "open_target")

        self.train(force=True)

    def add_delete_target_training(self, target_name: str):
        target_name = normalize_text(target_name)
        if not target_name:
            return

        self.add_training_phrase(f"удали {target_name}", "delete_target")
        self.add_training_phrase(f"забудь {target_name}", "delete_target")
        self.train(force=True)
