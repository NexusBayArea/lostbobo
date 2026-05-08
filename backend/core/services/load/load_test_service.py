"""
LoadTestService — Kernel-managed load testing.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


class LoadTestService:
    def __init__(self, kernel):
        self.kernel = kernel

    async def run_load_test(self, test_name: str) -> Any:
        log.info("Running load test: %s", test_name)
        return {"status": "success", "test": test_name}
