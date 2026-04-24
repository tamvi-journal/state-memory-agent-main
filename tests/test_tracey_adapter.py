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
        "tracey_wake_resume_class",
        "tracey_wake_constraints_active",
        "tracey_wake_requires_revalidation",
        "tracey_wake_forbidden_claims",
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
    assert any("build" in content for content in contents)


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
    assert tracey_turn["response_hints"]["ambiguity_posture"] == "blocking"
    assert tracey_turn["response_hints"]["keep_ambiguity_open"] is False


def test_tracey_adapter_prefers_open_exploration_for_non_blocking_ambiguity() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="Maybe we could explore a few ways to frame this runtime refactor.",
        live_state={"active_mode": "paper"},
        monitor_summary={"recommended_intervention": "none"},
    )

    hints = tracey_turn["response_hints"]
    assert hints["ambiguity_posture"] == "exploratory"
    assert hints["keep_ambiguity_open"] is True
    assert hints["search_posture"] == "none"


def test_tracey_adapter_marks_blocking_ambiguity_for_precision_demand() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="Clarify exactly which worker should handle this.",
        live_state={"active_mode": "paper"},
        monitor_summary={"recommended_intervention": "ask_clarify"},
    )

    hints = tracey_turn["response_hints"]
    assert hints["ambiguity_posture"] == "blocking"
    assert hints["keep_ambiguity_open"] is False


def test_tracey_adapter_keeps_build_mode_exact_without_search_by_anxiety() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="Refactor the runtime shape but keep the kernel boundary intact.",
        live_state={"active_mode": "build"},
        monitor_summary={"recommended_intervention": "none"},
    )

    hints = tracey_turn["response_hints"]
    assert hints["build_mode_active"] is True
    assert hints["verification_before_completion"] is True
    assert hints["ambiguity_posture"] == "none"
    assert hints["search_posture"] == "none"


def test_tracey_adapter_explicit_verification_request_can_raise_search_posture() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="Please verify and confirm the latest result before we proceed.",
        live_state={"active_mode": "paper"},
        monitor_summary={"recommended_intervention": "none"},
    )

    hints = tracey_turn["response_hints"]
    assert hints["search_posture"] == "on_demand"
    assert hints["ambiguity_posture"] == "blocking"


def test_tracey_adapter_degraded_wake_keeps_ambiguity_open_and_reduces_recognition() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="Continue previous work thread.",
        live_state={"active_mode": "paper", "continuity_anchor": "state-agent-runtime-test build thread"},
        monitor_summary={"recommended_intervention": "none"},
        wake_hints={
            "resume_class": "degraded_resume",
            "wake_constraints_active": True,
            "requires_revalidation": ["tool_handles"],
            "forbidden_claims": ["exact continuity preserved"],
        },
    )

    hints = tracey_turn["response_hints"]
    patch = tracey_turn["state_patch"]
    assert hints["wake_resume_class"] == "degraded_resume"
    assert hints["recognition_active"] is False
    assert hints["keep_ambiguity_open"] is True
    assert hints["tone_constraint"] == "wake_degraded"
    assert patch["tracey_wake_resume_class"] == "degraded_resume"
    assert patch["tracey_wake_constraints_active"] is True


def test_tracey_adapter_blocked_wake_suppresses_false_continuity() -> None:
    adapter = TraceyAdapter()

    tracey_turn = adapter.inspect_turn(
        user_text="Continue exactly where we left off.",
        live_state={"active_mode": "paper", "continuity_anchor": "state-agent-runtime-test build thread"},
        monitor_summary={"recommended_intervention": "none"},
        wake_hints={
            "resume_class": "blocked",
            "wake_constraints_active": True,
            "requires_revalidation": [],
            "forbidden_claims": ["exact continuity preserved"],
        },
    )

    hints = tracey_turn["response_hints"]
    patch = tracey_turn["state_patch"]
    assert hints["wake_resume_class"] == "blocked"
    assert hints["recognition_active"] is False
    assert hints["keep_ambiguity_open"] is False
    assert hints["tone_constraint"] == "wake_blocked"
    assert patch["tracey_response_constraint"] == "wake_blocked"
