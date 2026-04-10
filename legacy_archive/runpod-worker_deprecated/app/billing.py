import os
import requests
from datetime import datetime, timedelta

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
HEADERS = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
RUNPOD_GQL_URL = f"https://api.runpod.io/graphql?api_key={RUNPOD_API_KEY}"

def _gql(query: str) -> dict:
    """Execute a RunPod GraphQL query."""
    if not RUNPOD_API_KEY:
        raise RuntimeError("RUNPOD_API_KEY not set")
    resp = requests.post(RUNPOD_GQL_URL, json={"query": query}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"RunPod GraphQL error: {data['errors']}")
    return data

def get_pod_billing_gql():
    """Fetch billing info using GraphQL (more reliable/consistent)."""
    query = """
    query {
      myself {
        pods {
          id
          name
          runtime { uptimeInSeconds }
          costPerHr
        }
      }
    }
    """
    try:
        res = _gql(query)
        pods = res["data"]["myself"]["pods"]
        total_cost = 0
        for p in pods:
            uptime = (p.get("runtime") or {}).get("uptimeInSeconds", 0) or 0
            cost_hr = p.get("costPerHr", 0) or 0
            total_cost += (uptime / 3600) * cost_hr
        return total_cost
    except Exception as e:
        print(f"GraphQL billing error: {e}")
        return 0

def get_pod_billing_rest(start_date=None):
    """Legacy REST billing (v2). Use as fallback if GQL is unavailable."""
    url = "https://api.runpod.io/v2/billing/pods"
    params = {}
    if start_date:
        params["start"] = start_date.isoformat() + "Z"
        params["bucket"] = "day"
    try:
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        else:
            print(f"REST Billing Error {resp.status_code}: {resp.text}")
            return []
    except Exception as e:
        print(f"REST Billing exception: {e}")
        return []

def get_total_cost(days=7):
    """Get total cost using the most reliable method available."""
    # For short-term (active pods), GQL is more accurate
    if days <= 1:
        return get_pod_billing_gql()
    
    # For historical data, use REST (if available)
    start = (datetime.utcnow() - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    billing_data = get_pod_billing_rest(start)
    total_cost = sum(record.get("cost", 0) for record in billing_data)
    return total_cost


def check_budget_cap(daily_limit=50):
    billing = get_pod_billing()
    today = datetime.utcnow().date().isoformat()
    today_cost = sum(r["cost"] for r in billing if r["startTime"].startswith(today))
    if today_cost > daily_limit:
        print(f"Daily budget cap hit - ${today_cost:.2f} > ${daily_limit}")
        return True
    return False


if __name__ == "__main__":
    cost_7d = get_total_cost(7)
    print(f"Total pod cost last 7 days: ${cost_7d:.2f}")
