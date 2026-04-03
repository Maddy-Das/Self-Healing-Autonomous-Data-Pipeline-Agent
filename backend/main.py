import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS, UPLOAD_DIR, SESSION_DIR
from routes.health import router as health_router
from routes.pipeline import router as pipeline_router

app = FastAPI(
    title="Self-Healing Pipeline Agent",
    description="AI-powered autonomous data pipeline builder, simulator, and healer",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
app.include_router(pipeline_router)


@app.on_event("startup")
async def startup():
    UPLOAD_DIR.mkdir(exist_ok=True)
    SESSION_DIR.mkdir(exist_ok=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
