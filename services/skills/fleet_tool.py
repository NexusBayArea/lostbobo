from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("SimHPC-Commander")

@mcp.tool()
async def check_burn_rate() -> str:
    """Fetches the current hourly spend from the production edge function."""
    async with httpx.AsyncClient() as client:
        # Using the actual Supabase project URL from .env
        response = await client.get("https://ldzztrnghaaonparyggz.supabase.co/functions/v1/get-fleet-metrics")
        data = response.json()
        return f"Current Fleet Spend: ${data['hourly_spend_usd']}/hr across {data['active_pods']} pods."

if __name__ == "__main__":
    mcp.run()
