from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from family.effort_types import EffortInput, EffortRoute


@dataclass(slots=True)
class EffortAllocator:
    def route(self, effort_input: EffortInput | dict[str, Any]) -> EffortRoute:
        if isinstance(effort_input, dict):
            effort_input = EffortInput(**effort_input)

        score = 0
        reasons: list[str] = []

        if effort_input.task_type in {"architecture", "execution", "research", "verify"}:
            score += 2
            reasons.append("task_type is architecture/execution/research/verify (+2)")

        if effort_input.ambiguity_score >= 0.70:
            score += 2
            reasons.append("ambiguity_score >= 0.70 (+2)")

        if effort_input.risk_score >= 0.70:
            score += 2
            reasons.append("risk_score >= 0.70 (+2)")

        if effort_input.stakes_signal is not None and effort_input.stakes_signal >= 0.70:
            score += 2
            reasons.append("stakes_signal >= 0.70 (+2)")

        if effort_input.action_required:
            score += 2
            reasons.append("action_required is true (+2)")

        if effort_input.memory_commit_possible:
            score += 2
            reasons.append("memory_commit_possible is true (+2)")

        if effort_input.disagreement_likelihood >= 0.60:
            score += 2
            reasons.append("disagreement_likelihood >= 0.60 (+2)")

        if effort_input.mode_confidence < 0.50:
            score += 1
            reasons.append("mode_confidence < 0.50 (+1)")

        if effort_input.verification_gap_estimate >= 0.60:
            score += 1
            reasons.append("verification_gap_estimate >= 0.60 (+1)")

        if effort_input.high_risk_domain:
            score += 2
            reasons.append("high_risk_domain is true (+2)")

        if effort_input.unanswerable_likelihood >= 0.60:
            score += 1
            reasons.append("unanswerable_likelihood >= 0.60 (+1)")

        if effort_input.cue_strength >= 0.75:
            score -= 2
            reasons.append("cue_strength >= 0.75 (-2)")

        if effort_input.task_type in {"rewrite", "formatting", "small_talk"}:
            score -= 2
            reasons.append("task_type is rewrite/formatting/small_talk (-2)")

        defaulted_medium_due_to_stakes_uncertainty = False
        effort_level = self._effort_level_from_score(score)

        if self._has_strong_safety_floor(effort_input) and effort_level == "low":
            effort_level = "medium"
            reasons.append("strong safety floor prevents cue-driven drop to low")

        if self._stakes_uncertain(effort_input) and effort_level == "low":
            effort_level = "medium"
            defaulted_medium_due_to_stakes_uncertainty = True
            reasons.append("stakes unavailable or low-confidence -> precautionary medium")

        route = EffortRoute(
            effort_level=effort_level,
            cognition_topology=self._topology(effort_level),
            monitor_intensity=self._monitor_intensity(effort_level),
            verification_requirement=self._verification_requirement(effort_level),
            memory_commit_status=self._memory_commit_status(effort_level),
            disagreement_handling=self._disagreement_handling(effort_level),
            reasoning_engine=self._reasoning_engine(effort_level),
            effort_score=score,
            reasons=reasons,
            defaulted_medium_due_to_stakes_uncertainty=defaulted_medium_due_to_stakes_uncertainty,
        )
        return route

    def export_route_event(self, effort_input: EffortInput | dict[str, Any], route: EffortRoute | None = None) -> dict[str, Any]:
        if isinstance(effort_input, dict):
            effort_input = EffortInput(**effort_input)
        if route is None:
            route = self.route(effort_input)

        event = effort_input.to_dict()
        event.update(
            {
                "effort_score": route.effort_score,
                "effort_level": route.effort_level,
                "cognition_topology": route.cognition_topology,
                "monitor_intensity": route.monitor_intensity,
                "verification_requirement": route.verification_requirement,
                "memory_commit_status": route.memory_commit_status,
                "disagreement_handling": route.disagreement_handling,
                "reasoning_engine": route.reasoning_engine,
                "defaulted_medium_due_to_stakes_uncertainty": route.defaulted_medium_due_to_stakes_uncertainty,
                "reasons": list(route.reasons),
            }
        )
        return event

    @staticmethod
    def _effort_level_from_score(score: int) -> str:
        if score <= 1:
            return "low"
        if 2 <= score <= 5:
            return "medium"
        return "high"

    @staticmethod
    def _stakes_uncertain(effort_input: EffortInput) -> bool:
        return effort_input.stakes_signal is None or effort_input.stakes_confidence < 0.50

    @staticmethod
    def _has_strong_safety_floor(effort_input: EffortInput) -> bool:
        return (
            effort_input.high_risk_domain
            or effort_input.risk_score >= 0.70
            or (effort_input.stakes_signal is not None and effort_input.stakes_signal >= 0.70)
            or effort_input.verification_gap_estimate >= 0.60
        )

    @staticmethod
    def _topology(effort_level: str) -> str:
        return {
            "low": "single_brain",
            "medium": "parallel_partial",
            "high": "parallel_full",
        }[effort_level]

    @staticmethod
    def _monitor_intensity(effort_level: str) -> str:
        return {
            "low": "light",
            "medium": "normal",
            "high": "strict",
        }[effort_level]

    @staticmethod
    def _verification_requirement(effort_level: str) -> str:
        return {
            "low": "optional",
            "medium": "recommended",
            "high": "mandatory",
        }[effort_level]

    @staticmethod
    def _memory_commit_status(effort_level: str) -> str:
        return {
            "low": "blocked",
            "medium": "candidate_only",
            "high": "allowed",
        }[effort_level]

    @staticmethod
    def _disagreement_handling(effort_level: str) -> str:
        return {
            "low": "ignore_if_trivial",
            "medium": "preserve_if_present",
            "high": "actively_hold_open",
        }[effort_level]

    @staticmethod
    def _reasoning_engine(effort_level: str) -> str:
        return {
            "low": "single_pass",
            "medium": "single_pass_or_dual_pass_if_needed",
            "high": "dual_pass",
        }[effort_level]
