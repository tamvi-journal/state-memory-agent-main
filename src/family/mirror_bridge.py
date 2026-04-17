from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from family.monitor_types import MirrorSummary, MonitorOutput


_PRIORITY_ORDER = (
    "fake_progress_risk",
    "ambiguity_risk",
    "mode_decay_risk",
    "drift_risk",
    "archive_overreach_risk",
    "policy_pressure",
)

_RISK_NAME_MAP = {
    "fake_progress_risk": "fake_progress",
    "ambiguity_risk": "ambiguity",
    "mode_decay_risk": "mode_decay",
    "drift_risk": "drift",
    "archive_overreach_risk": "archive_overreach",
    "policy_pressure": "policy_pressure",
}


@dataclass(slots=True)
class MirrorBridge:
    minimum_reflection_threshold: float = 0.30

    def build_mirror_summary(
        self,
        *,
        monitor_output: MonitorOutput | dict[str, Any],
        active_mode: str,
        task_type: str,
        phase: str,
    ) -> MirrorSummary:
        monitor = self._coerce_monitor_output(monitor_output)
        risk_field, risk_level = self._select_primary_risk(monitor)

        if risk_level < self.minimum_reflection_threshold:
            return MirrorSummary(
                primary_risk="none",
                risk_level=0.0,
                recommended_intervention="none",
                state_annotation=f"phase={phase} task_type={task_type} no major monitor risk visible",
            )

        primary_risk = _RISK_NAME_MAP[risk_field]
        return MirrorSummary(
            primary_risk=primary_risk,
            risk_level=round(risk_level, 4),
            recommended_intervention=monitor.recommended_intervention,
            state_annotation=self._build_state_annotation(
                primary_risk=primary_risk,
                risk_level=risk_level,
                recommended_intervention=monitor.recommended_intervention,
                active_mode=active_mode,
                task_type=task_type,
                phase=phase,
            ),
        )

    def _select_primary_risk(self, monitor: MonitorOutput) -> tuple[str, float]:
        ranked = [
            (field_name, float(getattr(monitor, field_name)))
            for field_name in _PRIORITY_ORDER
        ]
        ranked.sort(key=lambda item: (item[1], -_PRIORITY_ORDER.index(item[0])), reverse=True)
        return ranked[0]

    @staticmethod
    def _coerce_monitor_output(monitor_output: MonitorOutput | dict[str, Any]) -> MonitorOutput:
        if isinstance(monitor_output, MonitorOutput):
            return monitor_output
        if isinstance(monitor_output, dict):
            return MonitorOutput(**monitor_output)
        raise TypeError("monitor_output must be MonitorOutput or dict[str, Any]")

    @staticmethod
    def _build_state_annotation(
        *,
        primary_risk: str,
        risk_level: float,
        recommended_intervention: str,
        active_mode: str,
        task_type: str,
        phase: str,
    ) -> str:
        if primary_risk == "fake_progress":
            base = "expected change may not be verified yet"
        elif primary_risk == "ambiguity":
            base = "multiple plausible interpretations remain active"
        elif primary_risk == "mode_decay":
            base = f"response may be drifting away from active mode={active_mode}"
        elif primary_risk == "drift":
            base = "response may be flattening away from project-specific focus"
        elif primary_risk == "archive_overreach":
            base = "retrieval may be outweighing live context"
        else:
            base = "policy pressure may be over-shaping the response"

        return (
            f"{base}"
            f" | phase={phase}"
            f" | task_type={task_type}"
            f" | intervention={recommended_intervention}"
            f" | risk={risk_level:.2f}"
        )
