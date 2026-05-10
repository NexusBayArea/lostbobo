"""Public forecast feed — API routes and WebSocket streaming."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.plugins.prediction_market.evaluation.scoring import ScoringEngine


router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


class PublicForecast(BaseModel):
    market_id: str
    question: str
    current_price: float
    calibrated_probability: float
    confidence: float
    regime: str
    source_count: int
    last_updated: str


class LeaderboardEntry(BaseModel):
    rank: int
    participant: str
    brier_score: float
    n_forecasts: int


@router.get("/feeds/public")
async def public_feed() -> dict[str, Any]:
    return {
        "feeds": [
            {
                "market_id": "demo-1",
                "question": "Will BTC exceed $100k by end of 2026?",
                "current_price": 0.68,
                "calibrated_probability": 0.65,
                "confidence": 0.82,
                "regime": "normal",
                "source_count": 3,
                "last_updated": datetime.now(UTC).isoformat(),
            }
        ],
        "updated_at": datetime.now(UTC).isoformat(),
    }


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 20) -> dict[str, Any]:
    engine = ScoringEngine()
    mock_entries = [
        {
            "participant_id": f"agent_{i}",
            "brier_score": round(0.05 * i, 4),
            "n_forecasts": 50 - i * 2,
        }
        for i in range(1, 11)
    ]
    ranked = await engine.compute_leaderboard(mock_entries)
    return {
        "leaderboard": ranked[:limit],
        "as_of": datetime.now(UTC).isoformat(),
    }


@router.websocket("/stream")
async def stream_feed(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            feed = await public_feed()
            await websocket.send_json(feed)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
