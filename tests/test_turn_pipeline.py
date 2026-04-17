from __future__ import annotations

from family.turn_pipeline import FamilyTurnPipeline
from family.turn_pipeline_types import FamilyTurnInput


def _input(**overrides) -> FamilyTurnInput:
    payload = {
        "current_message": "Please continue the family scaffold build work in this repository.",
        "active_project": "family-scaffold",
        "current_task": "continue the family scaffold build",
        "recent_anchor_cue": "family-scaffold",
        "disagreement_events": [],
        "verification_status": "passed",
        "last_verified_result": "compression layer smoke passed",
        "action_required": False,
        "execution_intent": "",
        "monitor_hint": "",
        "archive_consulted": False,
        "current_environment_state": "local repository ready",
        "open_obligations": ["keep the pipeline canary narrow"],
        "previous_live_state": {},
        "explicit_mode_hint": "",
    }
    payload.update(overrides)
    return FamilyTurnInput(**payload)


def test_simple_stable_build_like_turn_runs_through_all_stages() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(_input()).to_dict()

    assert result["context_view"]["active_project"] == "family-scaffold"
    assert result["mode_inference"]["active_mode"] == "build"
    assert result["live_state"]["active_mode"] == "build"
    assert result["compression_summary"]["next_state_hint"] == "continue_build"
    assert result["execution_request"] == {}
    assert result["execution_decision"] == {}
    assert result["approval_request"] == {}


def test_action_required_low_risk_inspection_turn_produces_execution_decision_and_stays_dry() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Inspect the repository metadata for family-scaffold.",
            current_task="inspect repository metadata",
            action_required=True,
            execution_intent="inspect repository metadata",
        )
    ).to_dict()

    assert result["execution_request"]["action_type"] == "inspect"
    assert result["execution_decision"]["decision"] == "allow"
    assert result["verification_record"]["verification_status"] == "unknown"


def test_approval_required_action_turn_returns_approval_request_and_does_not_fake_verification_pass() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Apply the patch to the repository files now.",
            current_task="apply repository patch",
            action_required=True,
            execution_intent="apply repository patch",
        )
    ).to_dict()

    assert result["execution_decision"]["decision"] == "require_approval"
    assert result["approval_request"]["approved"] is False
    assert result["verification_record"]["verification_status"] != "passed"


def test_denied_action_turn_keeps_verification_posture_honest() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Install pytest as a dependency for this project.",
            current_task="install pytest dependency",
            action_required=True,
            execution_intent="install pytest dependency",
        )
    ).to_dict()

    assert result["execution_decision"]["decision"] == "deny"
    assert result["verification_record"]["verification_status"] == "unknown"


def test_unresolved_disagreement_turn_keeps_disagreement_visible_and_does_not_fake_resolution() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Both routes still seem plausible, so hold open the disagreement while we continue.",
            disagreement_events=[
                {
                    "event_id": "dg_pipeline",
                    "timestamp": "2026-04-17T00:00:00Z",
                    "disagreement_type": "action",
                    "tracey_position": "preserve continuity-first line",
                    "seyn_position": "prefer verification-first line",
                    "severity": 0.82,
                    "still_open": True,
                    "later_resolution": "",
                    "house_law_implicated": "do_not_flatten_plurality",
                    "epistemic_resolution_claimed": False,
                }
            ],
        )
    ).to_dict()

    assert result["context_view"]["shared_disagreement_status"].startswith("open:")
    assert "open_disagreement" in result["live_state"]["tension_flags"]
    assert result["router_decision"]["epistemic_resolution_claimed"] is False


def test_handoff_carried_disagreement_stays_visible_without_synthetic_event_reconstruction() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Continue carefully from the baton while keeping plurality visible.",
            disagreement_events=[],
            previous_handoff={
                "active_project": "family-scaffold",
                "active_mode": "build",
                "continuity_anchor": "family-scaffold",
                "verification_status": "pending",
                "shared_disagreement_status": "open:action:meaningful",
                "current_axis": "continue scaffold from baton",
                "compression_summary": {"active_question": "continue scaffold from baton"},
                "open_obligations": ["keep the pipeline canary narrow"],
                "extra_field": "ignore me",
            },
        )
    ).to_dict()

    assert result["context_view"]["shared_disagreement_status"] == "open:action:meaningful"
    assert "open_disagreement" in result["live_state"]["tension_flags"]
    assert "synthetic event" in " ".join(result["notes"])
    assert result["router_decision"]["epistemic_resolution_claimed"] is False


def test_router_lead_can_exist_even_when_execution_gate_blocks_permission() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Apply the patch to the repository files now.",
            current_task="apply repository patch",
            action_required=True,
            execution_intent="apply repository patch",
        )
    ).to_dict()

    assert result["router_decision"]["lead_brain_for_action"] in {"tracey", "seyn", "none"}
    assert result["execution_decision"]["decision"] == "require_approval"


def test_verification_heavy_turn_keeps_verification_visible_and_does_not_auto_pass() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Verify the correctness of the family scaffold and review the risky parts.",
            current_task="verify the family scaffold correctness",
            verification_status="pending",
            action_required=True,
            last_verified_result="",
        )
    ).to_dict()

    assert result["live_state"]["verification_status"] == "pending"
    assert result["verification_record"]["verification_status"] == "unknown"
    assert result["compression_summary"]["caution"] == "verification remains unsettled"


def test_unresolved_disagreement_remains_preserved_even_when_action_is_gated() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Apply the patch, but both routes still seem plausible.",
            current_task="apply repository patch while disagreement stays open",
            action_required=True,
            execution_intent="apply repository patch",
            disagreement_events=[
                {
                    "event_id": "dg_pipeline_gate",
                    "timestamp": "2026-04-17T00:00:00Z",
                    "disagreement_type": "action",
                    "tracey_position": "preserve continuity-first line",
                    "seyn_position": "prefer verification-first line",
                    "severity": 0.82,
                    "still_open": True,
                }
            ],
        )
    ).to_dict()

    assert result["execution_decision"]["decision"] == "require_approval"
    assert result["context_view"]["shared_disagreement_status"].startswith("open:")
    assert result["router_decision"]["epistemic_resolution_claimed"] is False


def test_outputs_remain_compact_and_not_transcript_like() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(_input()).to_dict()

    assert set(result.keys()) == {
        "context_view",
        "mode_inference",
        "live_state",
        "monitor_output",
        "mirror_summary",
        "effort_route",
        "router_decision",
        "execution_request",
        "execution_decision",
        "approval_request",
        "verification_record",
        "delta_log_event",
        "compression_summary",
        "reactivation_result",
        "notes",
    }
    assert "transcript" not in result
    assert "history" not in result


def test_previous_handoff_still_improves_delta_without_large_synthetic_baseline() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(
        _input(
            current_message="Review and verify the family scaffold now.",
            current_task="verify the family scaffold",
            verification_status="pending",
            recent_anchor_cue="",
            previous_handoff={
                "active_project": "family-scaffold",
                "active_mode": "build",
                "continuity_anchor": "family-scaffold",
                "verification_status": "passed",
                "shared_disagreement_status": "none",
                "current_axis": "continue the family scaffold build",
                "compression_summary": {"active_question": "continue the family scaffold build"},
                "open_obligations": ["keep the pipeline canary narrow"],
            },
        )
    ).to_dict()

    assert result["delta_log_event"]["mode_shift"] == "build->audit"


def test_no_sleep_logic_is_introduced() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(_input()).to_dict()

    assert "sleep_state" not in result
    assert "wake_state" not in result


def test_no_real_execution_or_persistence_is_introduced() -> None:
    pipeline = FamilyTurnPipeline()
    result = pipeline.run(_input()).to_dict()

    assert "tool_call" not in result
    assert "filesystem_mutation" not in result
    assert "network_session" not in result
    assert "persistence_write" not in result
