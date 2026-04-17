from __future__ import annotations

from family.effort_allocator import EffortAllocator
from family.effort_types import EffortInput


def test_trivial_rewrite_with_strong_cue_and_known_low_stakes_routes_low() -> None:
    allocator = EffortAllocator()

    route = allocator.route(
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

    assert route.effort_level == "low"
    assert route.cognition_topology == "single_brain"
    assert route.monitor_intensity == "light"
    assert route.verification_requirement == "optional"
    assert route.memory_commit_status == "blocked"
    assert route.disagreement_handling == "ignore_if_trivial"
    assert route.reasoning_engine == "single_pass"


def test_architecture_turn_with_disagreement_and_memory_commit_routes_high() -> None:
    allocator = EffortAllocator()

    route = allocator.route(
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

    assert route.effort_level == "high"
    assert route.cognition_topology == "parallel_full"
    assert route.monitor_intensity == "strict"
    assert route.verification_requirement == "mandatory"
    assert route.memory_commit_status == "allowed"
    assert route.disagreement_handling == "actively_hold_open"
    assert route.reasoning_engine == "dual_pass"


def test_missing_stakes_on_otherwise_low_turn_defaults_to_medium() -> None:
    allocator = EffortAllocator()

    route = allocator.route(
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
            cue_strength=0.20,
            verification_gap_estimate=0.05,
            high_risk_domain=False,
            unanswerable_likelihood=0.05,
        )
    )

    assert route.effort_level == "medium"
    assert route.defaulted_medium_due_to_stakes_uncertainty is True


def test_low_confidence_stakes_on_otherwise_low_turn_defaults_to_medium() -> None:
    allocator = EffortAllocator()

    route = allocator.route(
        EffortInput(
            task_type="small_talk",
            domain="generic",
            active_mode="care",
            mode_confidence=0.98,
            ambiguity_score=0.05,
            risk_score=0.05,
            stakes_signal=0.10,
            stakes_confidence=0.20,
            action_required=False,
            memory_commit_possible=False,
            disagreement_likelihood=0.05,
            cue_strength=0.10,
            verification_gap_estimate=0.05,
            high_risk_domain=False,
            unanswerable_likelihood=0.05,
        )
    )

    assert route.effort_level == "medium"
    assert route.defaulted_medium_due_to_stakes_uncertainty is True


def test_strong_cue_does_not_override_high_risk_into_low() -> None:
    allocator = EffortAllocator()

    route = allocator.route(
        EffortInput(
            task_type="chat",
            domain="medical",
            active_mode="care",
            mode_confidence=0.90,
            ambiguity_score=0.10,
            risk_score=0.75,
            stakes_signal=0.20,
            stakes_confidence=0.90,
            action_required=False,
            memory_commit_possible=False,
            disagreement_likelihood=0.05,
            cue_strength=0.95,
            verification_gap_estimate=0.65,
            high_risk_domain=False,
            unanswerable_likelihood=0.05,
        )
    )

    assert route.effort_level == "medium"
    assert "strong safety floor prevents cue-driven drop to low" in route.reasons


def test_high_risk_domain_pushes_high() -> None:
    allocator = EffortAllocator()

    route = allocator.route(
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

    assert route.effort_level == "high"
    assert route.monitor_intensity == "strict"


def test_telemetry_export_contains_stakes_and_route_explanation_fields() -> None:
    allocator = EffortAllocator()
    effort_input = EffortInput(
        task_type="research",
        domain="build",
        active_mode="build",
        mode_confidence=0.40,
        ambiguity_score=0.75,
        risk_score=0.20,
        stakes_signal=0.80,
        stakes_confidence=0.95,
        action_required=False,
        memory_commit_possible=False,
        disagreement_likelihood=0.20,
        cue_strength=0.10,
        verification_gap_estimate=0.20,
        high_risk_domain=False,
        unanswerable_likelihood=0.10,
    )

    route = allocator.route(effort_input)
    event = allocator.export_route_event(effort_input, route)

    assert event["stakes_signal"] == 0.80
    assert event["defaulted_medium_due_to_stakes_uncertainty"] is False
    assert event["effort_score"] == route.effort_score
    assert event["effort_level"] == route.effort_level
    assert isinstance(event["reasons"], list)
