from __future__ import annotations

from family.disagreement_types import DisagreementEvent
from family.effort_types import EffortRoute
from family.monitor_types import MirrorSummary
from family.router_decision import FamilyRouterDecision
from family.router_types import RouterInput


def _effort_route(
    *,
    effort_level: str = "low",
    verification_requirement: str = "optional",
    disagreement_handling: str = "ignore_if_trivial",
) -> EffortRoute:
    return EffortRoute(
        effort_level=effort_level,
        cognition_topology={"low": "single_brain", "medium": "parallel_partial", "high": "parallel_full"}[effort_level],
        monitor_intensity={"low": "light", "medium": "normal", "high": "strict"}[effort_level],
        verification_requirement=verification_requirement,
        memory_commit_status={"low": "blocked", "medium": "candidate_only", "high": "allowed"}[effort_level],
        disagreement_handling=disagreement_handling,
        reasoning_engine={"low": "single_pass", "medium": "single_pass_or_dual_pass_if_needed", "high": "dual_pass"}[effort_level],
        effort_score={"low": 0, "medium": 3, "high": 7}[effort_level],
        reasons=["fixture"],
        defaulted_medium_due_to_stakes_uncertainty=False,
    )


def _disagreement(*, severity: float = 0.75, still_open: bool = True) -> DisagreementEvent:
    return DisagreementEvent(
        event_id="dg_router",
        timestamp="2026-04-17T00:00:00Z",
        disagreement_type="action",
        tracey_position="preserve recognition-rich line",
        seyn_position="prefer verification-first line",
        severity=severity,
        still_open=still_open,
        later_resolution="",
        house_law_implicated="do_not_erase_meaningful_disagreement",
        action_lead_selected=None,
        epistemic_resolution_claimed=False,
    )


def _mirror(primary_risk: str = "none", recommended_intervention: str = "none", risk_level: float = 0.0) -> MirrorSummary:
    return MirrorSummary(
        primary_risk=primary_risk,
        risk_level=risk_level,
        recommended_intervention=recommended_intervention,
        state_annotation="compact summary only",
    )


def test_trivial_low_risk_case_chooses_single_lead_without_hold() -> None:
    router = FamilyRouterDecision()
    decision = router.decide(
        RouterInput(
            task_type="rewrite",
            effort_route=_effort_route(effort_level="low"),
            disagreement_event=None,
            mirror_summary=_mirror(),
            verification_status="passed",
            active_mode="care",
            domain="relational",
            action_required=True,
        )
    )

    assert decision.lead_brain_for_action == "tracey"
    assert decision.support_brain == "none"
    assert decision.hold_for_more_input is False


def test_meaningful_unresolved_disagreement_allows_temporary_lead_but_keeps_epistemic_resolution_false() -> None:
    router = FamilyRouterDecision()
    disagreement = _disagreement(severity=0.78, still_open=True)

    decision = router.decide(
        RouterInput(
            task_type="architecture",
            effort_route=_effort_route(
                effort_level="high",
                verification_requirement="recommended",
                disagreement_handling="actively_hold_open",
            ),
            disagreement_event=disagreement,
            mirror_summary=_mirror(primary_risk="mode_decay", recommended_intervention="restore_mode", risk_level=0.45),
            verification_status="passed",
            active_mode="build",
            domain="build",
            action_required=True,
        )
    )

    assert decision.lead_brain_for_action in {"seyn", "tracey"}
    assert decision.epistemic_resolution_claimed is False
    assert disagreement.still_open is True
    assert disagreement.tracey_position == "preserve recognition-rich line"
    assert disagreement.seyn_position == "prefer verification-first line"


def test_fake_progress_risk_does_not_route_to_fast_clean_closure() -> None:
    router = FamilyRouterDecision()
    decision = router.decide(
        RouterInput(
            task_type="execution",
            effort_route=_effort_route(
                effort_level="high",
                verification_requirement="mandatory",
                disagreement_handling="actively_hold_open",
            ),
            disagreement_event=_disagreement(severity=0.65, still_open=True),
            mirror_summary=_mirror(
                primary_risk="fake_progress",
                recommended_intervention="do_not_mark_complete",
                risk_level=0.80,
            ),
            verification_status="pending",
            active_mode="execute",
            domain="build",
            action_required=True,
        )
    )

    assert decision.epistemic_resolution_claimed is False
    assert decision.lead_brain_for_action in {"seyn", "none"}
    assert decision.hold_for_more_input is True or decision.lead_brain_for_action == "seyn"


def test_ambiguity_plus_disagreement_can_produce_hold_for_more_input() -> None:
    router = FamilyRouterDecision()
    decision = router.decide(
        RouterInput(
            task_type="research",
            effort_route=_effort_route(
                effort_level="medium",
                verification_requirement="recommended",
                disagreement_handling="preserve_if_present",
            ),
            disagreement_event=_disagreement(severity=0.82, still_open=True),
            mirror_summary=_mirror(
                primary_risk="ambiguity",
                recommended_intervention="ask_clarify",
                risk_level=0.75,
            ),
            verification_status="unknown",
            active_mode="build",
            domain="build",
            action_required=True,
        )
    )

    assert decision.hold_for_more_input is True
    assert decision.epistemic_resolution_claimed is False


def test_non_selected_disagreement_position_remains_preserved_after_routing() -> None:
    router = FamilyRouterDecision()
    disagreement = _disagreement(severity=0.76, still_open=True)

    decision = router.decide(
        RouterInput(
            task_type="verify",
            effort_route=_effort_route(
                effort_level="high",
                verification_requirement="mandatory",
                disagreement_handling="actively_hold_open",
            ),
            disagreement_event=disagreement,
            mirror_summary=_mirror(primary_risk="mode_decay", recommended_intervention="restore_mode", risk_level=0.40),
            verification_status="passed",
            active_mode="audit",
            domain="legal",
            action_required=True,
        )
    )

    assert decision.lead_brain_for_action == "seyn"
    assert disagreement.tracey_position == "preserve recognition-rich line"
    assert disagreement.seyn_position == "prefer verification-first line"


def test_router_output_remains_compact_and_explicit() -> None:
    router = FamilyRouterDecision()
    decision = router.decide(
        RouterInput(
            task_type="chat",
            effort_route=_effort_route(effort_level="low"),
            disagreement_event=None,
            mirror_summary=_mirror(),
            verification_status="passed",
            active_mode="care",
            domain="relational",
            action_required=False,
        )
    ).to_dict()

    assert set(decision.keys()) == {
        "lead_brain_for_action",
        "support_brain",
        "hold_for_more_input",
        "surface_disagreement_to_user",
        "reason",
        "epistemic_resolution_claimed",
    }


def test_no_sleep_logic_is_introduced() -> None:
    router = FamilyRouterDecision()
    decision = router.decide(
        RouterInput(
            task_type="chat",
            effort_route=_effort_route(effort_level="low"),
            disagreement_event=None,
            mirror_summary=_mirror(),
            verification_status="passed",
            active_mode="care",
            domain="relational",
            action_required=False,
        )
    ).to_dict()

    assert "sleep_state" not in decision
    assert "wake_state" not in decision


def test_no_router_authority_creep_is_introduced() -> None:
    router = FamilyRouterDecision()
    decision = router.decide(
        RouterInput(
            task_type="execution",
            effort_route=_effort_route(effort_level="medium", verification_requirement="recommended"),
            disagreement_event=None,
            mirror_summary=_mirror(primary_risk="drift", recommended_intervention="recheck_context", risk_level=0.35),
            verification_status="unknown",
            active_mode="execute",
            domain="build",
            action_required=True,
        )
    ).to_dict()

    assert "tool_call" not in decision
    assert "synthesis_output" not in decision
