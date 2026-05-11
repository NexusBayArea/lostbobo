"""
tests/e2e/conftest.py
Updated for tenant isolation + current middleware stack
"""

import asyncio
import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# ── Stable test identifiers ───────────────────────────────────────────────────
TEST_TENANT_ID = "e2e-tenant-001"
TEST_RUN_ID = "e2e-run-001"
TEST_TRACE_ID = "e2e-trace-001"
TEST_SLA_TIER = "enterprise"
TEST_DOMAIN = "structural"
TEST_SOLVER = "MFEM"
TEST_CLAIM_TEXT = (
    "The aluminium bracket will not exceed 2mm displacement "
    "under a 30kN axial load at room temperature."
)


class SupabaseStub:
    """In-memory Supabase replacement – works with TenantScopedClient"""

    def __init__(self):
        self._tables: dict[str, list[dict]] = {}
        self._rpc_responses: dict[str, Any] = {}

    def table(self, name: str):
        return _TableProxy(self, name)

    def rpc(self, fn_name: str, params: dict | None = None):
        return _RpcProxy(self, fn_name)

    def seed_rpc(self, fn_name: str, response: Any):
        self._rpc_responses[fn_name] = response

    def get_rows(self, table: str):
        return list(self._tables.get(table, []))


class _TableProxy:
    def __init__(self, stub, table):
        self._stub = stub
        self._table = table
        self._filters = []
        self._single = False

    def select(self, cols="*"):
        return self

    def eq(self, col, val):
        self._filters.append((col, val))
        return self

    def insert(self, data):
        rows = [data] if isinstance(data, dict) else data
        self._stub._tables.setdefault(self._table, []).extend(rows)
        return self

    def upsert(self, data, **_):
        return self.insert(data)

    def single(self):
        self._single = True
        return self

    def execute(self):
        rows = self._stub._tables.get(self._table, [])
        for col, val in self._filters:
            rows = [r for r in rows if r.get(col) == val]
        result = MagicMock()
        result.data = rows[0] if self._single and rows else rows
        return result


class _RpcProxy:
    def __init__(self, stub, fn_name):
        self._stub = stub
        self._fn_name = fn_name

    def execute(self):
        result = MagicMock()
        result.data = self._stub._rpc_responses.get(self._fn_name, {"allowed": True})
        return result


# ── LLM Stub (routes by content, respects guarded_llm_call) ───────────────────
def make_llm_response(text: str):
    response = MagicMock()
    response.content = [MagicMock(text=text, type="text")]
    response.usage = MagicMock(input_tokens=120, output_tokens=45)
    return response


LLM_RESPONSES = {}  # Stub responses kept minimal for this context


@pytest.fixture
def supabase_stub():
    return SupabaseStub()


@pytest.fixture
def llm_stub():
    def _create(**kwargs):
        # Real guarded_llm_call path is exercised
        content = str(kwargs.get("messages", ""))
        if "claim" in content.lower() or "hypothesis" in content.lower():
            return make_llm_response(LLM_RESPONSES.get("claim_extraction", "stub"))
        return make_llm_response(LLM_RESPONSES.get("certificate_synthesis", "stub"))

    mock = MagicMock()
    mock.messages.create.side_effect = _create
    return mock
