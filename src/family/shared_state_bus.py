from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
import uuid

from family.disagreement_types import (
    ActionLead,
    DisagreementEvent,
    DisagreementType,
)


@dataclass(slots=True)
class SharedStateBus:
    current_task: str = ""
    active_project: str = ""
    shared_context_view: dict[str, Any] = field(default_factory=dict)
    last_verified_outcome: str = ""
    open_obligations: list[str] = field(default_factory=list)
    current_action_lead: str = ""
    router_decision: str = ""
    disagreement_events: list[DisagreementEvent] = field(default_factory=list)
    shared_compression_summary: str = ""
    monitor_summary: dict[str, Any] | None = None

    def record_disagreement_event(
        self,
        *,
        disagreement_type: DisagreementType,
        tracey_position: str,
        seyn_position: str,
        severity: float,
        house_law_implicated: str = "",
        timestamp: str = "",
        event_id: str = "",
    ) -> DisagreementEvent:
        event = DisagreementEvent(
            event_id=event_id or self._new_event_id(),
            timestamp=timestamp or self._utc_now_iso(),
            disagreement_type=disagreement_type,
            tracey_position=tracey_position,
            seyn_position=seyn_position,
            severity=severity,
            still_open=True,
            later_resolution="",
            house_law_implicated=house_law_implicated,
            action_lead_selected=None,
            epistemic_resolution_claimed=False,
        )
        self.disagreement_events.append(event)
        return event

    def set_action_lead(self, event_id: str, lead: ActionLead, *, router_decision: str = "") -> bool:
        for event in self.disagreement_events:
            if event.event_id == event_id:
                event.action_lead_selected = lead
                event.epistemic_resolution_claimed = False
                self.current_action_lead = lead
                if router_decision:
                    self.router_decision = router_decision
                return True
        return False

    def mark_disagreement_resolved(self, event_id: str, later_resolution: str) -> bool:
        for event in self.disagreement_events:
            if event.event_id == event_id:
                event.still_open = False
                event.later_resolution = later_resolution
                return True
        return False

    def get_open_disagreements(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.disagreement_events if event.still_open]

    def export_shared_summary(self) -> dict[str, Any]:
        return {
            "current_task": self.current_task,
            "active_project": self.active_project,
            "shared_context_view": dict(self.shared_context_view),
            "last_verified_outcome": self.last_verified_outcome,
            "open_obligations": list(self.open_obligations),
            "current_action_lead": self.current_action_lead,
            "router_decision": self.router_decision,
            "disagreement_events": [event.to_dict() for event in self.disagreement_events],
            "shared_compression_summary": self.shared_compression_summary,
            "monitor_summary": None if self.monitor_summary is None else dict(self.monitor_summary),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["disagreement_events"] = [event.to_dict() for event in self.disagreement_events]
        return payload

    @staticmethod
    def _new_event_id() -> str:
        return f"dg_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
