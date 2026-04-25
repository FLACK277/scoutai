"""
ScoutAI Configuration — Central configuration for all modules.
"""

# ─── Ollama / Mistral LLM Configuration ────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"
OLLAMA_TIMEOUT = 60          # seconds per LLM request
OLLAMA_TEMPERATURE = 0.3     # low temp for deterministic outputs
OLLAMA_NUM_CTX = 4096        # context window

# ─── Embedding Configuration ───────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# ─── Retrieval Configuration ──────────────────────────────────────────────────
FAISS_TOP_K = 20             # candidates from vector search
KEYWORD_MIN_OVERLAP = 1      # minimum skill overlap for keyword path
FINAL_TOP_K = 10             # final shortlist size

# ─── Scoring Weights ──────────────────────────────────────────────────────────
MATCH_WEIGHT_SKILL = 0.5
MATCH_WEIGHT_EXPERIENCE = 0.3
MATCH_WEIGHT_SEMANTIC = 0.2

FINAL_WEIGHT_MATCH = 0.6
FINAL_WEIGHT_PROPENSITY = 0.2
FINAL_WEIGHT_INTEREST = 0.2

# ─── Paths ─────────────────────────────────────────────────────────────────────
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.json")
