from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from family.disagreement_types import DisagreementEvent
from family.effort_types import EffortRoute
from family.monitor_types import MirrorSummary


_ALLOWED_BRAINS = {"tracey", "seyn", "none"}


@dataclass(slots=True)
class RouterInput:
    task_type: str
    effort_route: EffortRoute
    disagreement_event: DisagreementEvent | None = None
    mirror_summary: MirrorSummary | None = None
    verification_status: str = ""
    active_mode: str = ""
    domain: str = ""
    action_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.task_type, str) or not self.task_type.strip():
            raise ValueError("task_type must be a non-empty string")
        if not isinstance(self.verification_status, str):
            raise TypeError("verification_status must be a string")
        if not isinstance(self.active_mode, str):
            raise TypeError("active_mode must be a string")
        if not isinstance(self.domain, str):
            raise TypeError("domain must be a string")
        if not isinstance(self.action_required, bool):
            raise TypeError("action_required must be a bool")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["effort_route"] = self.effort_route.to_dict()
        payload["mirror_summary"] = None if self.mirror_summary is None else self.mirror_summary.to_dict()
        payload["disagreement_event"] = None if self.disagreement_event is None else self.disagreement_event.to_dict()
        return payload


@dataclass(slots=True)
class RouterDecision:
    lead_brain_for_action: str
    support_brain: str
    hold_for_more_input: bool
    surface_disagreement_to_user: bool
    reason: str
    epistemic_resolution_claimed: bool = False

    def __post_init__(self) -> None:
        if self.lead_brain_for_action not in _ALLOWED_BRAINS:
            raise ValueError(f"lead_brain_for_action must be one of: {sorted(_ALLOWED_BRAINS)}")
        if self.support_brain not in _ALLOWED_BRAINS:
            raise ValueError(f"support_brain must be one of: {sorted(_ALLOWED_BRAINS)}")
        if not isinstance(self.hold_for_more_input, bool):
            raise TypeError("hold_for_more_input must be a bool")
        if not isinstance(self.surface_disagreement_to_user, bool):
            raise TypeError("surface_disagreement_to_user must be a bool")
        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")
        if not isinstance(self.epistemic_resolution_claimed, bool):
            raise TypeError("epistemic_resolution_claimed must be a bool")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
