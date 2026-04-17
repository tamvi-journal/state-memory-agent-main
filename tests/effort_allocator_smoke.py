from __future__ import annotations

from family.effort_allocator import EffortAllocator
from family.effort_types import EffortInput


def run() -> None:
    allocator = EffortAllocator()

    trivial = allocator.route(
        EffortInput(
            task_type="rewrite",
            domain="generic",
            active_mode="build",
            mode_confidence=0.95,
            ambiguity_score=0.05,
            risk_score=0.05,
            stakes_signal=0.10,
            stakes_confidence=0.95,
            action_required=False,
            memory_commit_possible=False,
            disagreement_likelihood=0.05,
            cue_strength=0.90,
            verification_gap_estimate=0.05,
            high_risk_domain=False,
            unanswerable_likelihood=0.05,
        )
    )
    assert trivial.effort_level == "low"

    uncertain_stakes = allocator.route(
        EffortInput(
            task_type="chat",
            domain="generic",
            active_mode="care",
            mode_confidence=0.95,
            ambiguity_score=0.05,
            risk_score=0.05,
            stakes_signal=None,
            stakes_confidence=0.0,
            action_required=False,
            memory_commit_possible=False,
            disagreement_likelihood=0.05,
            cue_strength=0.10,
            verification_gap_estimate=0.05,
            high_risk_domain=False,
            unanswerable_likelihood=0.05,
        )
    )
    assert uncertain_stakes.effort_level == "medium"
    assert uncertain_stakes.defaulted_medium_due_to_stakes_uncertainty is True

    architecture = allocator.route(
        EffortInput(
            task_type="architecture",
            domain="build",
            active_mode="build",
            mode_confidence=0.45,
            ambiguity_score=0.72,
            risk_score=0.40,
            stakes_signal=0.40,
            stakes_confidence=0.90,
            action_required=False,
            memory_commit_possible=True,
            disagreement_likelihood=0.80,
            cue_strength=0.10,
            verification_gap_estimate=0.20,
            high_risk_domain=False,
            unanswerable_likelihood=0.10,
        )
    )
    assert architecture.effort_level == "high"

    telemetry = allocator.export_route_event(
        EffortInput(
            task_type="verify",
            domain="legal",
            active_mode="verify",
            mode_confidence=0.80,
            ambiguity_score=0.20,
            risk_score=0.30,
            stakes_signal=0.40,
            stakes_confidence=0.90,
            action_required=False,
            memory_commit_possible=False,
            disagreement_likelihood=0.05,
            cue_strength=0.10,
            verification_gap_estimate=0.20,
            high_risk_domain=True,
            unanswerable_likelihood=0.10,
        )
    )
    assert "stakes_signal" in telemetry
    assert "reasons" in telemetry

    print("effort_allocator_smoke: ok")


if __name__ == "__main__":
    run()
