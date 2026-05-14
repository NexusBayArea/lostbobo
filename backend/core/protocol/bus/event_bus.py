from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class EventPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class EventEnvelope:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    event_type: str = ""
    schema_version: str = "1.0.0"
    priority: EventPriority = EventPriority.NORMAL
    source_plugin: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    causation_id: str | None = None
    tenant_id: str = "default"
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.sha256(json.dumps(self.payload, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class EventSubscription:
    plugin_name: str
    event_type: str
    handler: Callable[[EventEnvelope], Any]
    priority: int = 0
    filter_expression: str | None = None
    concurrency_limit: int = 1
    dead_letter_queue: bool = True


@dataclass
class EventDelivery:
    event_id: str
    subscriber: str
    attempted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    succeeded: bool = False
    error: str | None = None


class EventBus:
    def __init__(self):
        self._subscriptions: dict[str, list[EventSubscription]] = {}
        self._deliveries: list[EventDelivery] = []
        self._dead_letter: list[EventEnvelope] = []
        self._lock = asyncio.Lock()

    async def publish(self, envelope: EventEnvelope) -> None:
        async with self._lock:
            subs = list(self._subscriptions.get(envelope.event_type, []))
        tasks = []
        for sub in subs:
            tasks.append(self._deliver(sub, envelope))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe(self, subscription: EventSubscription) -> None:
        async with self._lock:
            if subscription.event_type not in self._subscriptions:
                self._subscriptions[subscription.event_type] = []
            self._subscriptions[subscription.event_type].append(subscription)
            self._subscriptions[subscription.event_type].sort(key=lambda s: s.priority, reverse=True)

    async def unsubscribe(self, plugin_name: str, event_type: str) -> None:
        async with self._lock:
            subs = self._subscriptions.get(event_type, [])
            self._subscriptions[event_type] = [s for s in subs if s.plugin_name != plugin_name]

    async def _deliver(self, sub: EventSubscription, envelope: EventEnvelope) -> None:
        try:
            await sub.handler(envelope)
            delivery = EventDelivery(
                event_id=envelope.event_id,
                subscriber=sub.plugin_name,
                succeeded=True,
            )
        except Exception as e:
            delivery = EventDelivery(
                event_id=envelope.event_id,
                subscriber=sub.plugin_name,
                succeeded=False,
                error=str(e),
            )
            if sub.dead_letter_queue:
                async with self._lock:
                    self._dead_letter.append(envelope)
        async with self._lock:
            self._deliveries.append(delivery)

    async def get_deliveries(self, event_id: str | None = None) -> list[EventDelivery]:
        if event_id:
            return [d for d in self._deliveries if d.event_id == event_id]
        return list(self._deliveries)

    async def get_dead_letter_queue(self) -> list[EventEnvelope]:
        return list(self._dead_letter)

    async def replay_dead_letter(self) -> int:
        failed = list(self._dead_letter)
        self._dead_letter = []
        republished = 0
        for envelope in failed:
            try:
                await self.publish(envelope)
                republished += 1
            except Exception:
                self._dead_letter.append(envelope)
        return republished

    @property
    async def subscriber_count(self) -> int:
        async with self._lock:
            return sum(len(s) for s in self._subscriptions.values())

    @property
    async def delivery_count(self) -> int:
        async with self._lock:
            return len(self._deliveries)
