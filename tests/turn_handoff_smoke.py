from __future__ import annotations

from family.turn_handoff import TurnHandoffBuilder
from family.turn_pipeline import FamilyTurnPipeline
from family.turn_pipeline_types import FamilyTurnInput


def run() -> None:
    pipeline = FamilyTurnPipeline()
    handoff_builder = TurnHandoffBuilder()

    first = pipeline.run(
        FamilyTurnInput(
            current_message="Please continue the family scaffold build work in this repository.",
            active_project="family-scaffold",
            current_task="continue the family scaffold build",
            recent_anchor_cue="family-scaffold",
            verification_status="passed",
            last_verified_result="turn pipeline smoke passed",
            action_required=False,
            current_environment_state="local repository ready",
            open_obligations=["keep handoff compact"],
        )
    )
    handoff = handoff_builder.build_from_turn_result(first).to_dict()
    assert handoff["continuity_anchor"] == "family-scaffold"

    second = pipeline.run(
        FamilyTurnInput(
            current_message="Continue the scaffold from the family-scaffold baton.",
            active_project="",
            current_task="continue scaffold from baton",
            recent_anchor_cue="",
            verification_status="",
            action_required=False,
            current_environment_state="second dry turn",
            previous_handoff=handoff,
        )
    ).to_dict()
    assert second["live_state"]["continuity_anchor"] == "family-scaffold"

    normalized = handoff_builder.normalize_handoff(
        {
            **handoff,
            "unknown_extra": "ignored",
        }
    ).to_dict()
    assert normalized["continuity_anchor"] == "family-scaffold"

    disagreement_first = pipeline.run(
        FamilyTurnInput(
            current_message="Both routes still seem plausible, so keep the disagreement open.",
            active_project="family-scaffold",
            current_task="hold open the disagreement",
            recent_anchor_cue="family-scaffold",
            verification_status="pending",
            disagreement_events=[
                {
                    "event_id": "dg_handoff_smoke",
                    "timestamp": "2026-04-17T00:00:00Z",
                    "disagreement_type": "action",
                    "tracey_position": "preserve continuity-first line",
                    "seyn_position": "prefer verification-first line",
                    "severity": 0.82,
                    "still_open": True,
                }
            ],
            action_required=False,
            current_environment_state="first disagreement turn",
        )
    )
    disagreement_handoff = handoff_builder.build_from_turn_result(disagreement_first).to_dict()
    disagreement_second = pipeline.run(
        FamilyTurnInput(
            current_message="Continue carefully from the baton without flattening plurality.",
            active_project="",
            current_task="continue carefully from baton",
            recent_anchor_cue="",
            verification_status="",
            disagreement_events=[],
            action_required=False,
            current_environment_state="second disagreement turn",
            previous_handoff=disagreement_handoff,
        )
    ).to_dict()
    assert disagreement_second["context_view"]["shared_disagreement_status"].startswith("open:")
    assert disagreement_second["live_state"]["verification_status"] == "pending"

    print("turn_handoff_smoke: ok")


if __name__ == "__main__":
    run()
