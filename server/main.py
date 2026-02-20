"""
Mahjong Score API — FastAPI entry point.

Run with:
    uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

Interactive docs available at http://localhost:8000/docs once the server is running.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers.score import router as score_router

app = FastAPI(
    title="Mahjong Score API",
    version="0.1.0",
    description=(
        "Wraps the pyriichi scoring engine to evaluate a winning hand "
        "and return yaku, han/fu, and payment breakdown."
    ),
)

# Allow all origins during development; restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(score_router)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok"}
