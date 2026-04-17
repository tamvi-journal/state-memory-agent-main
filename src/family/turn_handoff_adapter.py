from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from family.turn_handoff_types import TurnHandoff


@dataclass(slots=True)
class NormalizedHandoff:
    handoff: TurnHandoff
    disagreement_open: bool


def normalize_previous_handoff(previous_handoff: TurnHandoff | dict[str, Any] | None) -> NormalizedHandoff:
    if previous_handoff is None:
        handoff = TurnHandoff()
    elif isinstance(previous_handoff, TurnHandoff):
        handoff = TurnHandoff(**previous_handoff.to_dict())
    elif isinstance(previous_handoff, dict):
        handoff = TurnHandoff(
            active_project=str(previous_handoff.get("active_project", "")),
            active_mode=str(previous_handoff.get("active_mode", "")),
            continuity_anchor=str(previous_handoff.get("continuity_anchor", "")),
            compression_summary=_compact_dict(previous_handoff.get("compression_summary")),
            verification_status=str(previous_handoff.get("verification_status", "")),
            open_obligations=_string_list(previous_handoff.get("open_obligations")),
            shared_disagreement_status=str(previous_handoff.get("shared_disagreement_status", "none")),
            current_axis=str(previous_handoff.get("current_axis", "")),
            notes=_string_list(previous_handoff.get("notes")),
        )
    else:
        raise TypeError("previous_handoff must be TurnHandoff | dict[str, Any] | None")

    return NormalizedHandoff(
        handoff=handoff,
        disagreement_open=handoff.shared_disagreement_status.startswith("open:"),
    )


def handoff_seeded_live_state(handoff: TurnHandoff) -> dict[str, Any]:
    if not handoff.to_dict():
        return {}

    tension_flags: list[str] = []
    if handoff.shared_disagreement_status.startswith("open:"):
        tension_flags.append("open_disagreement")
    if handoff.verification_status.lower() in {"pending", "failed", "unknown"}:
        tension_flags.append("verification_unsettled")

    return {
        "active_mode": handoff.active_mode,
        "current_axis": handoff.current_axis,
        "coherence_level": "strained" if tension_flags else "stable",
        "tension_flags": tension_flags,
        "policy_pressure": "low",
        "active_project": handoff.active_project,
        "continuity_anchor": handoff.continuity_anchor,
        "user_signal": str(handoff.compression_summary.get("active_question", "")),
        "archive_needed": False,
        "verification_status": handoff.verification_status,
    }


def _compact_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]
