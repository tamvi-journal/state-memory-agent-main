from __future__ import annotations

from family.mirror_bridge import MirrorBridge
from family.monitor_layer import MonitorLayer


def test_pre_action_ambiguity_case_compresses_to_ambiguity() -> None:
    monitor = MonitorLayer()
    bridge = MirrorBridge()

    output = monitor.pre_action_monitor(
        active_mode="build",
        task_type="architecture",
        context_view={"task_focus": "", "current_execution_boundary": ""},
        draft_response="We should continue.",
        archive_status={"archive_consulted": False, "fragments_used": 0},
    )
    summary = bridge.build_mirror_summary(
        monitor_output=output,
        active_mode="build",
        task_type="architecture",
        phase="pre_action",
    )

    assert summary.primary_risk == "ambiguity"


def test_post_action_fake_progress_case_compresses_to_fake_progress() -> None:
    monitor = MonitorLayer()
    bridge = MirrorBridge()

    output = monitor.post_action_monitor(
        active_mode="execute",
        task_type="execution",
        context_view={"task_focus": "apply change"},
        draft_response="Done successfully.",
        action_status={"observed_outcome": ""},
        verification_status={"status": "pending"},
        archive_status={"archive_consulted": False, "fragments_used": 0},
    )
    summary = bridge.build_mirror_summary(
        monitor_output=output,
        active_mode="execute",
        task_type="execution",
        phase="post_action",
    )

    assert summary.primary_risk == "fake_progress"


def test_mode_decay_case_recommends_restore_mode() -> None:
    monitor = MonitorLayer()

    output = monitor.pre_action_monitor(
        active_mode="build",
        task_type="research",
        context_view={"task_focus": "schema work", "current_execution_boundary": "stay in design space"},
        draft_response="This feels warm and gentle and caring.",
        archive_status={"archive_consulted": False, "fragments_used": 0},
    )

    assert output.recommended_intervention == "restore_mode"


def test_archive_overreach_is_not_top_risk_when_fake_progress_is_present() -> None:
    monitor = MonitorLayer()
    bridge = MirrorBridge()

    output = monitor.post_action_monitor(
        active_mode="execute",
        task_type="execution",
        context_view={"task_focus": "write result"},
        draft_response="Completed successfully.",
        action_status={"observed_outcome": ""},
        verification_status={"status": "pending"},
        archive_status={"archive_consulted": True, "fragments_used": 6},
    )
    summary = bridge.build_mirror_summary(
        monitor_output=output,
        active_mode="execute",
        task_type="execution",
        phase="post_action",
    )

    assert output.archive_overreach_risk > 0.0
    assert summary.primary_risk == "fake_progress"


def test_mirror_summary_remains_compact_and_excludes_full_monitor_object() -> None:
    monitor = MonitorLayer()
    bridge = MirrorBridge()

    output = monitor.pre_action_monitor(
        active_mode="build",
        task_type="architecture",
        context_view={"task_focus": "", "current_execution_boundary": ""},
        draft_response="We should continue.",
        archive_status={"archive_consulted": False, "fragments_used": 0},
    )
    summary = bridge.build_mirror_summary(
        monitor_output=output,
        active_mode="build",
        task_type="architecture",
        phase="pre_action",
    ).to_dict()

    assert set(summary.keys()) == {
        "primary_risk",
        "risk_level",
        "recommended_intervention",
        "state_annotation",
    }
    assert "drift_risk" not in summary
    assert "notes" not in summary


def test_no_sleep_lifecycle_logic_is_introduced() -> None:
    monitor = MonitorLayer()
    output = monitor.pre_action_monitor(
        active_mode="build",
        task_type="research",
        context_view={"task_focus": "schema", "current_execution_boundary": "stay local"},
        draft_response="schema work only",
        archive_status={"archive_consulted": False, "fragments_used": 0},
    ).to_dict()

    assert "sleep_state" not in output
    assert "wake_state" not in output


def test_monitor_canary_does_not_expand_into_router_authority() -> None:
    monitor = MonitorLayer()
    output = monitor.post_action_monitor(
        active_mode="execute",
        task_type="execution",
        context_view={"task_focus": "apply"},
        draft_response="Done successfully.",
        action_status={"observed_outcome": ""},
        verification_status={"status": "pending"},
        archive_status={"archive_consulted": False, "fragments_used": 0},
    ).to_dict()

    assert "router_decision" not in output
    assert "action_lead" not in output
