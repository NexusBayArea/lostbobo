"""
Scaling rules and policies for autoscaler
"""

from typing import Any

from app.core.config import get_settings

settings = get_settings()


def get_scaling_policy() -> dict[str, Any]:
    """
    Get scaling policy configuration
    """
    return {
        "min_workers": settings.MIN_WARM_WORKERS,
        "max_workers": 20,
        "target_utilization": 0.75,
        "scale_up_threshold": 0.8,
        "scale_down_threshold": 0.3,
        "evaluation_periods": 2,
        "cooldown_period": 60,  # seconds
    }


def should_scale_up(current_workers: int, queue_depth: int, policy: dict[str, Any]) -> bool:
    """
    Determine if we should scale up based on policy
    """
    if current_workers >= policy["max_workers"]:
        return False

    # Simple heuristic: scale up if queue depth > workers * threshold
    threshold = policy["scale_up_threshold"]
    if queue_depth > current_workers * threshold:
        return True

    return False


def should_scale_down(current_workers: int, queue_depth: int, policy: dict[str, Any]) -> bool:
    """
    Determine if we should scale down based on policy
    """
    if current_workers <= policy["min_workers"]:
        return False

    # Simple heuristic: scale down if queue depth < workers * threshold
    threshold = policy["scale_down_threshold"]
    if queue_depth < current_workers * threshold:
        return True

    return False


def calculate_desired_workers(
    current_workers: int, queue_depth: int, policy: dict[str, Any]
) -> int:
    """
    Calculate desired worker count based on queue depth and policy
    """
    # Don't scale below min or above max
    if queue_depth == 0:
        return policy["min_workers"]

    # Simple calculation: workers needed to process queue at target utilization
    target_utilization = policy["target_utilization"]
    # Assume each worker can process 1 job per unit time (simplified)
    raw_needed = queue_depth / target_utilization

    # Apply bounds
    desired = max(policy["min_workers"], min(int(raw_needed), policy["max_workers"]))

    return desired
