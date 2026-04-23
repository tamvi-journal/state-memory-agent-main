from __future__ import annotations

from tracey.tracey_adapter import TraceyAdapter


def test_tracey_adapter_emits_compact_namespaced_patch() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="Please refactor the runtime shape and keep verification before completion in build mode.",
        live_state={
            "active_mode": "build",
            "active_project": "state-agent-runtime-test",
            "continuity_anchor": "build-thread",
        },
        monitor_summary={
            "recommended_intervention": "ask_clarify",
            "primary_risk": "ambiguity",
        },
    )

    patch = tracey_turn["state_patch"]
    assert set(patch.keys()) == {
        "tracey_mode_hint",
        "tracey_recognition_signal",
        "tracey_monitor_intervention",
        "tracey_reactivated_count",
        "tracey_build_mode_active",
        "tracey_response_constraint",
    }
    assert patch["tracey_build_mode_active"] is True
    assert patch["tracey_monitor_intervention"] == "ask_clarify"
    assert patch["tracey_reactivated_count"] <= 3


def test_tracey_adapter_adds_build_memory_anchors() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="This build refactor should keep the brain as the final synthesis layer.",
        live_state={
            "active_mode": "build",
            "active_project": "state-agent-runtime-test",
            "continuity_anchor": "state-agent-runtime-test build thread",
        },
        monitor_summary=None,
    )

    contents = {anchor["content"] for anchor in tracey_turn["reactivated_anchors"]}
    assert "brain speaks last" in contents
    assert "state-agent-runtime-test build thread" in contents


def test_tracey_adapter_uses_response_hints_instead_of_response_rewrite() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="The route is unclear, so keep ambiguity open.",
        live_state={"active_mode": "paper"},
        monitor_summary={"recommended_intervention": "ask_clarify"},
    )

    assert "response_hints" in tracey_turn
    assert "state_patch" in tracey_turn
    assert "adapt_response" not in dir(adapter)
    assert tracey_turn["response_hints"]["keep_ambiguity_open"] is True
