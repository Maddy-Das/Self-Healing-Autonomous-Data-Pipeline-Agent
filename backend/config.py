import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
SESSION_DIR = BASE_DIR / "sessions"

UPLOAD_DIR.mkdir(exist_ok=True)
SESSION_DIR.mkdir(exist_ok=True)

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
GLM_MODEL = "glm-5.1"  # GLM model name

# ── Simulation ─────────────────────────────────────────
MAX_HEALING_ITERATIONS = 3
SIMULATION_TIMEOUT_SECONDS = 30
MAX_UPLOAD_SIZE_MB = 50

# ── CORS ───────────────────────────────────────────────
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

raw_cors_origins = os.getenv("CORS_ORIGINS", "")
if raw_cors_origins.strip():
    CORS_ORIGINS = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]
else:
    CORS_ORIGINS = DEFAULT_CORS_ORIGINS
