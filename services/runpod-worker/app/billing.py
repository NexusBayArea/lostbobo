import requests
from datetime import datetime, timedelta

API_KEY = "YOUR_RUNPOD_API_KEY"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def get_pod_billing(start_date=None):
    url = "https://api.runpod.io/v2/billing/pods"
    params = {}
    if start_date:
        params["start"] = start_date.isoformat() + "Z"
        params["bucket"] = "day"
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code == 200:
        return resp.json()["data"]
    else:
        print(f"Error {resp.status_code}: {resp.text}")
        return []


def get_total_cost(days=7):
    start = (datetime.utcnow() - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    billing_data = get_pod_billing(start)
    total_cost = sum(record["cost"] for record in billing_data)
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
