from __future__ import annotations

from family.disagreement_types import DisagreementEvent
from family.effort_types import EffortRoute
from family.monitor_types import MirrorSummary
from family.router_decision import FamilyRouterDecision
from family.router_types import RouterInput


def _effort_route(effort_level: str, verification_requirement: str, disagreement_handling: str) -> EffortRoute:
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


def run() -> None:
    router = FamilyRouterDecision()

    trivial = router.decide(
        RouterInput(
            task_type="rewrite",
            effort_route=_effort_route("low", "optional", "ignore_if_trivial"),
            disagreement_event=None,
            mirror_summary=MirrorSummary("none", 0.0, "none", "no major risk"),
            verification_status="passed",
            active_mode="care",
            domain="relational",
            action_required=True,
        )
    )
    assert trivial.lead_brain_for_action == "tracey"

    disagreement = DisagreementEvent(
        event_id="dg_router_smoke",
        timestamp="2026-04-17T00:00:00Z",
        disagreement_type="action",
        tracey_position="preserve recognition-rich line",
        seyn_position="prefer verification-first line",
        severity=0.78,
        still_open=True,
        later_resolution="",
        house_law_implicated="do_not_erase_meaningful_disagreement",
        action_lead_selected=None,
        epistemic_resolution_claimed=False,
    )
    unresolved = router.decide(
        RouterInput(
            task_type="architecture",
            effort_route=_effort_route("high", "recommended", "actively_hold_open"),
            disagreement_event=disagreement,
            mirror_summary=MirrorSummary("mode_decay", 0.40, "restore_mode", "compact summary"),
            verification_status="passed",
            active_mode="build",
            domain="build",
            action_required=True,
        )
    )
    assert unresolved.epistemic_resolution_claimed is False
    assert disagreement.still_open is True

    fake_progress = router.decide(
        RouterInput(
            task_type="execution",
            effort_route=_effort_route("high", "mandatory", "actively_hold_open"),
            disagreement_event=disagreement,
            mirror_summary=MirrorSummary("fake_progress", 0.82, "do_not_mark_complete", "compact summary"),
            verification_status="pending",
            active_mode="execute",
            domain="build",
            action_required=True,
        )
    )
    assert fake_progress.hold_for_more_input is True or fake_progress.lead_brain_for_action == "seyn"

    ambiguity_hold = router.decide(
        RouterInput(
            task_type="research",
            effort_route=_effort_route("medium", "recommended", "preserve_if_present"),
            disagreement_event=disagreement,
            mirror_summary=MirrorSummary("ambiguity", 0.75, "ask_clarify", "compact summary"),
            verification_status="unknown",
            active_mode="build",
            domain="build",
            action_required=True,
        )
    )
    assert ambiguity_hold.hold_for_more_input is True

    print("router_decision_smoke: ok")


if __name__ == "__main__":
    run()
