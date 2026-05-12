from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class RunPodClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        self.base_url = "https://api.runpod.ai/v2"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def submit_job(self, endpoint_id: str, payload: dict) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/{endpoint_id}/runsync",
                json={"input": payload},
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("id")

    async def get_job_status(self, job_id: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self.base_url}/status/{job_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def stream_job_output(self, job_id: str):
        raise NotImplementedError("WebSocket streaming not yet implemented")
