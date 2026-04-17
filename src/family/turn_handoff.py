from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from family.turn_handoff_adapter import normalize_previous_handoff
from family.turn_handoff_types import TurnHandoff
from family.turn_pipeline_types import FamilyTurnResult


@dataclass(slots=True)
class TurnHandoffBuilder:
    def build_from_turn_result(self, turn_result: FamilyTurnResult | dict[str, Any]) -> TurnHandoff:
        if isinstance(turn_result, dict):
            turn_result = FamilyTurnResult(**turn_result)

        context_view = turn_result.context_view
        live_state = turn_result.live_state
        compression_summary = turn_result.compression_summary

        notes = ["compact handoff derived from dry family turn result"]
        if context_view.get("shared_disagreement_status", "none") != "none":
            notes.append("shared disagreement posture remains visible")
        if live_state.get("verification_status", ""):
            notes.append(f"verification posture carried forward as {live_state['verification_status']}")

        return TurnHandoff(
            active_project=str(context_view.get("active_project", "")) or str(live_state.get("active_project", "")),
            active_mode=str(live_state.get("active_mode", "")) or str(context_view.get("active_mode", "")),
            continuity_anchor=str(live_state.get("continuity_anchor", "")) or str(compression_summary.get("anchor_cue", "")),
            compression_summary=dict(compression_summary),
            verification_status=str(live_state.get("verification_status", "")),
            open_obligations=list(context_view.get("open_obligations", [])),
            shared_disagreement_status=str(context_view.get("shared_disagreement_status", "none")),
            current_axis=str(live_state.get("current_axis", "")),
            notes=notes,
        )

    @staticmethod
    def export_handoff(handoff: TurnHandoff | dict[str, Any]) -> dict[str, Any]:
        if isinstance(handoff, dict):
            handoff = TurnHandoff(**handoff)
        return handoff.to_dict()

    @staticmethod
    def normalize_handoff(handoff: TurnHandoff | dict[str, Any] | None) -> TurnHandoff:
        return normalize_previous_handoff(handoff).handoff
