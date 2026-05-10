"""News ingestion for prediction market signals."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.plugins.prediction_market.forecasting.signals import ForecastSignal


class NewsIngestor:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or ""

    async def ingest(self, query: str | None = None) -> list[ForecastSignal]:
        return [
            ForecastSignal(
                id=str(uuid4()),
                source="news",
                signal_type="sentiment",
                market_id=query or "general",
                timestamp=datetime.now(UTC),
                value=0.6,
                confidence=0.5,
                metadata={"query": query, "headline_count": 10},
            )
        ]


class TwitterIngestor:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or ""

    async def ingest(self, topic: str | None = None) -> list[ForecastSignal]:
        return [
            ForecastSignal(
                id=str(uuid4()),
                source="twitter",
                signal_type="social_sentiment",
                market_id=topic or "general",
                timestamp=datetime.now(UTC),
                value=0.55,
                confidence=0.4,
                metadata={"topic": topic, "tweet_count": 100},
            )
        ]


class WeatherIngestor:
    def __init__(self) -> None:
        pass

    async def ingest(self, location: str = "us-east-1") -> list[ForecastSignal]:
        return [
            ForecastSignal(
                id=str(uuid4()),
                source="weather",
                signal_type="forecast",
                market_id=f"weather-{location}",
                timestamp=datetime.now(UTC),
                value=0.7,
                confidence=0.8,
                metadata={"location": location, "temperature_c": 22},
            )
        ]
