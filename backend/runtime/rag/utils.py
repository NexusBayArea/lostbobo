from typing import List

def get_tenant_from_context() -> str:
    # Logic to extract tenant_id from request context or global state
    return "public"

def combine_results(results: List[List]) -> List:
    combined = []
    seen = set()
    for batch in results:
        for item in batch:
            key = item.get("id")
            if key and key not in seen:
                seen.add(key)
                combined.append(item)
    return combined
