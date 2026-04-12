"""
RunPod Service — API Layer integration for fleet management.
Mirrors core GraphQL logic from worker/runpod_api.py for direct responsiveness.
"""

import logging
import os
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_GQL_URL = f"https://api.runpod.io/graphql?api_key={RUNPOD_API_KEY}"

# Async HTTP client singleton (initialized in api.py lifespan)
_http_client: httpx.AsyncClient = None


def init_http_client(client: httpx.AsyncClient):
    """Initialize the async HTTP client from api.py lifespan."""
    global _http_client
    _http_client = client


async def _gql_async(query: str) -> dict:
    """Execute a RunPod GraphQL query (async)."""
    if not RUNPOD_API_KEY:
        raise RuntimeError("RUNPOD_API_KEY not set")
    if not _http_client:
        raise RuntimeError(
            "HTTP client not initialized - call init_http_client() first"
        )

    response = await _http_client.post(
        RUNPOD_GQL_URL, json={"query": query}, timeout=30.0
    )
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise RuntimeError(f"RunPod GraphQL error: {data['errors']}")
    return data


def _gql(query: str) -> dict:
    """Execute a RunPod GraphQL query (sync - for backward compat)."""
    if not RUNPOD_API_KEY:
        raise RuntimeError("RUNPOD_API_KEY not set")
    import requests

    resp = requests.post(RUNPOD_GQL_URL, json={"query": query}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"RunPod GraphQL error: {data['errors']}")
    return data


async def list_pods_async() -> List[Dict]:
    """Fetch all pods for the account (async)."""
    query = """
    query {
      myself {
        pods {
          id
          name
          desiredStatus
          imageName
          gpuDisplayName
          costPerHr
        }
      }
    }
    """
    res = await _gql_async(query)
    return res["data"]["myself"]["pods"]


def list_pods() -> List[Dict]:
    """Fetch all pods for the account (sync)."""
    query = """
    query {
      myself {
        pods {
          id
          name
          desiredStatus
          imageName
          gpuDisplayName
          costPerHr
        }
      }
    }
    """
    res = _gql(query)
    return res["data"]["myself"]["pods"]


async def stop_pod_async(pod_id: str) -> dict:
    """Stop a pod via direct GraphQL call (async)."""
    query = f"""
    mutation {{
      podStop(input: {{ podId: "{pod_id}" }}) {{
        id
        desiredStatus
      }}
    }}
    """
    res = await _gql_async(query)
    logger.info(f"API: Direct Pod STOP sent for {pod_id}")
    return res["data"]["podStop"]


def stop_pod(pod_id: str) -> dict:
    """Stop a pod via direct GraphQL call (sync)."""
    query = f"""
    mutation {{
      podStop(input: {{ podId: "{pod_id}" }}) {{
        id
        desiredStatus
      }}
    }}
    """
    res = _gql(query)
    logger.info(f"API: Direct Pod STOP sent for {pod_id}")
    return res["data"]["podStop"]


async def terminate_pod_async(pod_id: str) -> dict:
    """Terminate a pod via direct GraphQL call (async)."""
    query = f"""
    mutation {{
      podTerminate(input: {{ podId: "{pod_id}" }})
    }}
    """
    res = await _gql_async(query)
    logger.info(f"API: Direct Pod TERMINATE sent for {pod_id}")
    return {"pod_id": pod_id, "status": "TERMINATED"}


def terminate_pod(pod_id: str) -> dict:
    """Terminate a pod via direct GraphQL call (sync)."""
    query = f"""
    mutation {{
      podTerminate(input: {{ podId: "{pod_id}" }})
    }}
    """
    _ = _gql(query)
    logger.info(f"API: Direct Pod TERMINATE sent for {pod_id}")
    return {"pod_id": pod_id, "status": "TERMINATED"}


async def resume_pod_async(pod_id: str) -> dict:
    """Resume a stopped pod via direct GraphQL call (async)."""
    query = f"""
    mutation {{
      podResume(input: {{ podId: "{pod_id}", gpuCount: 1 }}) {{
        id
        desiredStatus
      }}
    }}
    """
    res = await _gql_async(query)
    logger.info(f"API: Direct Pod RESUME sent for {pod_id}")
    return res["data"]["podResume"]


def resume_pod(pod_id: str) -> dict:
    """Resume a stopped pod via direct GraphQL call (sync)."""
    query = f"""
    mutation {{
      podResume(input: {{ podId: "{pod_id}", gpuCount: 1 }}) {{
        id
        desiredStatus
      }}
    }}
    """
    res = _gql(query)
    logger.info(f"API: Direct Pod RESUME sent for {pod_id}")
    return res["data"]["podResume"]
