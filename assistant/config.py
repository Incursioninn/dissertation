from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = BASE_DIR / "cache"
LOG_DIR = BASE_DIR / "logs"

INTENTS_FILE = DATA_DIR / "intents.json"
ACTIONS_FILE = DATA_DIR / "actions.json"
SYNONYMS_FILE = DATA_DIR / "synonyms.json"

MODEL_CACHE_FILE = CACHE_DIR / "intent_gru_model.pt"
VOCAB_CACHE_FILE = CACHE_DIR / "intent_vocab.json"
META_CACHE_FILE = CACHE_DIR / "intent_meta.json"

ASSISTANT_LOG_FILE = LOG_DIR / "assistant.log"
COMMANDS_CSV_FILE = LOG_DIR / "commands.csv"

VOSK_MODEL_PATH = MODELS_DIR / "vosk-model-small-ru-0.22"

SAMPLE_RATE = 16000
BLOCK_SIZE = 4000

WAKE_WORD = "компьютер"

INTENT_THRESHOLD = 0.50
LOW_CONFIDENCE_THRESHOLD = 0.72

EMBEDDING_DIM = 64
HIDDEN_DIM = 96
EPOCHS = 350
LEARNING_RATE = 0.01
MAX_SEQUENCE_LENGTH = 12

ALLOW_COMMANDS_WITHOUT_WAKE_WORD = True
