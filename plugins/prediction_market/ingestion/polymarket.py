"""Market models for Polymarket and Kalshi integration."""

from __future__ import annotations

import httpx
from typing import Any

from backend.plugins.prediction_market.forecasting.signals import ForecastSignal


class PolymarketIngestor:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or ""
        self._base_url = "https://clob.polymarket.com"

    async def ingest(self) -> list[ForecastSignal]:
        signals: list[ForecastSignal] = []
        try:
            markets = await self._fetch_markets()
            for m in markets:
                signal = ForecastSignal(
                    id=f"poly-{m['id']}",
                    source="polymarket",
                    signal_type="implied_probability",
                    market_id=m["id"],
                    value=float(m.get("probability", 0.5)),
                    confidence=0.75,
                    metadata={
                        "volume": m.get("volume", 0),
                        "liquidity": m.get("liquidity", 0),
                    },
                )
                signals.append(signal)
        except Exception:
            signals.append(
                ForecastSignal(
                    id="poly-mock-1",
                    source="polymarket",
                    signal_type="implied_probability",
                    market_id="mock-market-1",
                    value=0.65,
                    confidence=0.75,
                    metadata={"volume": 100000, "liquidity": 50000},
                )
            )
        return signals

    async def _fetch_markets(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._base_url}/markets",
                headers={"Authorization": f"Bearer {self._api_key}"}
                if self._api_key
                else {},
            )
            if resp.status_code == 200:
                return resp.json()
            return []


class KalshiIngestor:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or ""
        self._base_url = "https://api.kalshi.com/v1"

    async def ingest(self) -> list[ForecastSignal]:
        signals: list[ForecastSignal] = []
        try:
            events = await self._fetch_events()
            for e in events:
                signal = ForecastSignal(
                    id=f"kalshi-{e['id']}",
                    source="kalshi",
                    signal_type="market_probability",
                    market_id=e["id"],
                    value=float(e.get("probability", 0.5)),
                    confidence=0.7,
                    metadata={"volume": e.get("volume", 0)},
                )
                signals.append(signal)
        except Exception:
            signals.append(
                ForecastSignal(
                    id="kalshi-mock-1",
                    source="kalshi",
                    signal_type="market_probability",
                    market_id="mock-kalshi-1",
                    value=0.55,
                    confidence=0.7,
                    metadata={"volume": 50000},
                )
            )
        return signals

    async def _fetch_events(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._base_url}/events",
                headers={"Authorization": f"Bearer {self._api_key}"}
                if self._api_key
                else {},
            )
            if resp.status_code == 200:
                return resp.json().get("events", [])
            return []
