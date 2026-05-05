from typing import Any

from backend.plugins.base import PluginBase
from backend.plugins.registry import PluginRegistry


@PluginRegistry.register("market_trading")
class MarketTradingPlugin(PluginBase):
    async def run(self, params: dict[str, Any]) -> dict[str, Any]:
        symbol = params.get("symbol", "BTC")
        return {"status": "success", "prediction": "bullish", "symbol": symbol}
