from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

StateMemoryLifecycle = Literal[
    "observed",
    "candidate",
    "canonical",
    "archived",
    "deprecated",
    "invalidated",
]

StateMemoryEventType = Literal[
    "coherence_drop",
    "coherence_spike",
    "resonance_lock",
    "positive_afterglow",
    "route_clarity_gain",
    "self_location_shift",
    "repair_event",
    "wake_degraded",
    "wake_blocked",
    "wake_clarify_first",
    "anchor_reactivation",
    "policy_drift",
    "mode_shift",
    "state_invariant",
    "verification_boundary",
    "generic_state_event",
]

STATE_MEMORY_SCHEMA_VERSION = "state-memory-record/v0.1"
ACTIVE_LIFECYCLES: tuple[StateMemoryLifecycle, ...] = (
    "observed",
    "candidate",
    "canonical",
)
INERT_LIFECYCLES: tuple[StateMemoryLifecycle, ...] = (
    "archived",
    "deprecated",
    "invalidated",
)


@dataclass(slots=True)
class StateMemoryRecord:
    event_type: StateMemoryEventType
    scope: str
    summary: str
    record_id: str = field(default_factory=lambda: f"sm_{uuid4().hex}")
    session_id: str = ""
    source: str = "runtime"
    lifecycle_status: StateMemoryLifecycle = "observed"
    evidence: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    supersedes: list[str] = field(default_factory=list)
    superseded_by: str = ""

    def validate(self) -> None:
        if not self.record_id:
            raise ValueError("record_id is required")
        if not self.scope:
            raise ValueError("scope is required")
        if not self.summary:
            raise ValueError("summary is required")
        if self.lifecycle_status not in ACTIVE_LIFECYCLES + INERT_LIFECYCLES:
            raise ValueError(f"invalid lifecycle_status={self.lifecycle_status!r}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": STATE_MEMORY_SCHEMA_VERSION,
            "record_id": self.record_id,
            "event_type": self.event_type,
            "scope": self.scope,
            "session_id": self.session_id,
            "summary": self.summary,
            "source": self.source,
            "lifecycle_status": self.lifecycle_status,
            "created_at": self.created_at,
            "evidence": dict(self.evidence),
            "tags": list(self.tags),
            "supersedes": list(self.supersedes),
            "superseded_by": self.superseded_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateMemoryRecord":
        record = cls(
            record_id=str(data.get("record_id", "")),
            event_type=str(data.get("event_type", "generic_state_event")),  # type: ignore[arg-type]
            scope=str(data.get("scope", "")),
            session_id=str(data.get("session_id", "")),
            summary=str(data.get("summary", "")),
            source=str(data.get("source", "runtime")),
            lifecycle_status=str(data.get("lifecycle_status", "observed")),  # type: ignore[arg-type]
            created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            evidence=dict(data.get("evidence", {})),
            tags=[str(item) for item in data.get("tags", [])],
            supersedes=[str(item) for item in data.get("supersedes", [])],
            superseded_by=str(data.get("superseded_by", "")),
        )
        record.validate()
        return record


def lifecycle_rank(status: str) -> int:
    ranks = {
        "canonical": 0,
        "candidate": 1,
        "observed": 2,
        "archived": 3,
        "deprecated": 4,
        "invalidated": 5,
    }
    return ranks.get(str(status), 99)
