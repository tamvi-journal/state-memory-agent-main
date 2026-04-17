from __future__ import annotations

from family.turn_handoff import TurnHandoffBuilder
from family.turn_handoff_types import TurnHandoff
from family.turn_pipeline import FamilyTurnPipeline
from family.turn_pipeline_types import FamilyTurnInput


def _turn_input(**overrides) -> FamilyTurnInput:
    payload = {
        "current_message": "Please continue the family scaffold build work in this repository.",
        "active_project": "family-scaffold",
        "current_task": "continue the family scaffold build",
        "recent_anchor_cue": "family-scaffold",
        "disagreement_events": [],
        "verification_status": "passed",
        "last_verified_result": "turn pipeline smoke passed",
        "action_required": False,
        "execution_intent": "",
        "monitor_hint": "",
        "archive_consulted": False,
        "current_environment_state": "local repository ready",
        "open_obligations": ["keep the handoff canary narrow"],
        "previous_live_state": {},
        "previous_handoff": {},
        "explicit_mode_hint": "",
    }
    payload.update(overrides)
    return FamilyTurnInput(**payload)


def test_handoff_can_be_built_from_completed_dry_turn_result() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    result = pipeline.run(_turn_input())
    handoff = handoff_builder.build_from_turn_result(result).to_dict()

    assert handoff["active_project"] == "family-scaffold"
    assert handoff["compression_summary"]["anchor_cue"] == "family-scaffold"


def test_next_turn_can_consume_previous_handoff_without_transcript_replay() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    first = pipeline.run(_turn_input())
    handoff = handoff_builder.build_from_turn_result(first).to_dict()
    second = pipeline.run(
        _turn_input(
            current_message="Continue the scaffold from the family-scaffold baton.",
            current_task="continue scaffold from baton",
            recent_anchor_cue="",
            previous_handoff=handoff,
        )
    ).to_dict()

    assert second["reactivation_result"]["matched_cues"]
    assert "transcript" not in second


def test_continuity_anchor_can_carry_forward_compactly() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    handoff = handoff_builder.build_from_turn_result(pipeline.run(_turn_input())).to_dict()
    second = pipeline.run(
        _turn_input(
            current_message="Continue the scaffold from the baton.",
            recent_anchor_cue="",
            previous_handoff=handoff,
        )
    ).to_dict()

    assert second["live_state"]["continuity_anchor"] == handoff["continuity_anchor"]


def test_verification_and_disagreement_posture_can_remain_visible_across_turns() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    first = pipeline.run(
        _turn_input(
            current_message="Both routes still seem plausible, so keep the disagreement open.",
            verification_status="pending",
            disagreement_events=[
                {
                    "event_id": "dg_handoff_test",
                    "timestamp": "2026-04-17T00:00:00Z",
                    "disagreement_type": "action",
                    "tracey_position": "preserve continuity-first line",
                    "seyn_position": "prefer verification-first line",
                    "severity": 0.82,
                    "still_open": True,
                }
            ],
        )
    )
    handoff = handoff_builder.build_from_turn_result(first).to_dict()

    second = pipeline.run(
        _turn_input(
            current_message="Continue carefully from the baton.",
            disagreement_events=[],
            recent_anchor_cue="",
            verification_status="",
            previous_handoff=handoff,
        )
    ).to_dict()

    assert second["context_view"]["shared_disagreement_status"].startswith("open:")
    assert second["live_state"]["verification_status"] == "pending"


def test_delta_uses_handoff_instead_of_fully_synthetic_baseline() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    first = pipeline.run(_turn_input())
    handoff = handoff_builder.build_from_turn_result(first).to_dict()

    second = pipeline.run(
        _turn_input(
            current_message="Review and verify the family scaffold now.",
            current_task="verify the family scaffold",
            verification_status="pending",
            recent_anchor_cue="",
            previous_handoff=handoff,
        )
    ).to_dict()

    assert second["delta_log_event"]["mode_shift"] == "build->audit"


def test_output_remains_compact_and_inspectable() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    handoff = handoff_builder.build_from_turn_result(pipeline.run(_turn_input())).to_dict()
    second = pipeline.run(_turn_input(previous_handoff=handoff, recent_anchor_cue="")).to_dict()

    assert "history" not in second
    assert "archive_replay" not in second


def test_loose_previous_handoff_dict_is_normalized_to_compact_supported_shape() -> None:
    normalized = TurnHandoffBuilder.normalize_handoff(
        {
            "active_project": "family-scaffold",
            "active_mode": "build",
            "continuity_anchor": "family-scaffold",
            "verification_status": "pending",
            "shared_disagreement_status": "open:action:meaningful",
            "current_axis": "continue scaffold from baton",
            "compression_summary": {"active_question": "continue scaffold from baton"},
            "open_obligations": ["keep handoff compact"],
            "unknown_extra": {"ignored": True},
        }
    )

    assert isinstance(normalized, TurnHandoff)
    assert normalized.active_project == "family-scaffold"
    assert normalized.shared_disagreement_status == "open:action:meaningful"
    assert "unknown_extra" not in normalized.to_dict()


def test_no_archive_sleep_or_persistence_is_introduced() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    handoff = handoff_builder.build_from_turn_result(pipeline.run(_turn_input())).to_dict()
    second = pipeline.run(_turn_input(previous_handoff=handoff, recent_anchor_cue="")).to_dict()

    assert "archive_route" not in second
    assert "sleep_state" not in second
    assert "persistence_write" not in second
