from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class FamilyTurnInput:
    current_message: str
    active_project: str = ""
    current_task: str = ""
    recent_anchor_cue: str = ""
    disagreement_events: list[dict[str, Any]] | None = None
    verification_status: str = ""
    last_verified_result: str = ""
    action_required: bool = False
    execution_intent: str = ""
    monitor_hint: str = ""
    archive_consulted: bool = False
    current_environment_state: str = ""
    open_obligations: list[str] | None = None
    previous_live_state: dict[str, Any] | None = None
    previous_handoff: dict[str, Any] | None = None
    explicit_mode_hint: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "current_message",
            "active_project",
            "current_task",
            "recent_anchor_cue",
            "verification_status",
            "last_verified_result",
            "execution_intent",
            "monitor_hint",
            "current_environment_state",
            "explicit_mode_hint",
        ):
            if not isinstance(getattr(self, field_name), str):
                raise TypeError(f"{field_name} must be a string")
        if not self.current_message.strip():
            raise ValueError("current_message must be a non-empty string")
        if self.disagreement_events is None:
            self.disagreement_events = []
        if self.open_obligations is None:
            self.open_obligations = []
        if self.previous_live_state is None:
            self.previous_live_state = {}
        if self.previous_handoff is None:
            self.previous_handoff = {}
        if not isinstance(self.disagreement_events, list) or not all(isinstance(item, dict) for item in self.disagreement_events):
            raise TypeError("disagreement_events must be list[dict]")
        if not isinstance(self.open_obligations, list) or not all(isinstance(item, str) for item in self.open_obligations):
            raise TypeError("open_obligations must be list[str]")
        if not isinstance(self.previous_live_state, dict):
            raise TypeError("previous_live_state must be dict[str, Any] | None")
        if not isinstance(self.previous_handoff, dict):
            raise TypeError("previous_handoff must be dict[str, Any] | None")
        if not isinstance(self.action_required, bool):
            raise TypeError("action_required must be a bool")
        if not isinstance(self.archive_consulted, bool):
            raise TypeError("archive_consulted must be a bool")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FamilyTurnResult:
    context_view: dict[str, Any]
    mode_inference: dict[str, Any]
    live_state: dict[str, Any]
    monitor_output: dict[str, Any]
    mirror_summary: dict[str, Any]
    effort_route: dict[str, Any]
    router_decision: dict[str, Any]
    execution_request: dict[str, Any]
    execution_decision: dict[str, Any]
    approval_request: dict[str, Any]
    verification_record: dict[str, Any]
    delta_log_event: dict[str, Any]
    compression_summary: dict[str, Any]
    reactivation_result: dict[str, Any]
    notes: list[str] | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "context_view",
            "mode_inference",
            "live_state",
            "monitor_output",
            "mirror_summary",
            "effort_route",
            "router_decision",
            "execution_request",
            "execution_decision",
            "approval_request",
            "verification_record",
            "delta_log_event",
            "compression_summary",
            "reactivation_result",
        ):
            if not isinstance(getattr(self, field_name), dict):
                raise TypeError(f"{field_name} must be a dict[str, Any]")
        if self.notes is None:
            self.notes = []
        if not isinstance(self.notes, list) or not all(isinstance(item, str) for item in self.notes):
            raise TypeError("notes must be list[str]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
