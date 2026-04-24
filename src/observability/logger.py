from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone


@dataclass(slots=True)
class EventLogger:
    """
    Small in-memory logger for phase 1.

    Replace later with persistent or structured external logging if needed.
    """

    events: list[dict[str, Any]] = field(default_factory=list)

    def log(self, category: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "category": category,
            "payload": payload,
        }
        self.events.append(event)
        return event

    def all_events(self) -> list[dict[str, Any]]:
        return list(self.events)

    def by_category(self, category: str) -> list[dict[str, Any]]:
        return [event for event in self.events if event["category"] == category]

    def clear(self) -> None:
        self.events.clear()
