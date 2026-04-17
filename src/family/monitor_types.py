from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


_ALLOWED_INTERVENTIONS = {
    "none",
    "hold_50_50",
    "ask_clarify",
    "recheck_context",
    "recheck_environment",
    "do_not_mark_complete",
    "reduce_archive_weight",
    "restore_mode",
    "tighten_project_focus",
}


@dataclass(slots=True)
class MonitorOutput:
    drift_risk: float = 0.0
    ambiguity_risk: float = 0.0
    policy_pressure: float = 0.0
    fake_progress_risk: float = 0.0
    archive_overreach_risk: float = 0.0
    mode_decay_risk: float = 0.0
    recommended_intervention: str = "none"
    notes: list[str] | None = None
    phase: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "drift_risk",
            "ambiguity_risk",
            "policy_pressure",
            "fake_progress_risk",
            "archive_overreach_risk",
            "mode_decay_risk",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")
        if self.recommended_intervention not in _ALLOWED_INTERVENTIONS:
            raise ValueError(
                f"recommended_intervention must be one of: {sorted(_ALLOWED_INTERVENTIONS)}"
            )
        if self.notes is None:
            self.notes = []
        if not isinstance(self.notes, list) or not all(isinstance(x, str) for x in self.notes):
            raise TypeError("notes must be list[str]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MirrorSummary:
    primary_risk: str
    risk_level: float
    recommended_intervention: str
    state_annotation: str

    def __post_init__(self) -> None:
        if not isinstance(self.primary_risk, str) or not self.primary_risk:
            raise ValueError("primary_risk must be a non-empty string")
        if not isinstance(self.risk_level, (int, float)) or not 0.0 <= float(self.risk_level) <= 1.0:
            raise ValueError("risk_level must be between 0.0 and 1.0")
        if self.recommended_intervention not in _ALLOWED_INTERVENTIONS:
            raise ValueError(
                f"recommended_intervention must be one of: {sorted(_ALLOWED_INTERVENTIONS)}"
            )
        if not isinstance(self.state_annotation, str):
            raise TypeError("state_annotation must be a string")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
