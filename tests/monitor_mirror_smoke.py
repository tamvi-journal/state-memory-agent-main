from __future__ import annotations

from family.mirror_bridge import MirrorBridge
from family.monitor_layer import MonitorLayer


def run() -> None:
    monitor = MonitorLayer()
    mirror = MirrorBridge()

    pre_action = monitor.pre_action_monitor(
        active_mode="build",
        task_type="architecture",
        context_view={"task_focus": "", "current_execution_boundary": ""},
        draft_response="We should continue.",
        archive_status={"archive_consulted": False, "fragments_used": 0},
    )
    pre_summary = mirror.build_mirror_summary(
        monitor_output=pre_action,
        active_mode="build",
        task_type="architecture",
        phase="pre_action",
    )
    assert pre_summary.primary_risk == "ambiguity"

    post_action = monitor.post_action_monitor(
        active_mode="execute",
        task_type="execution",
        context_view={"task_focus": "apply local change"},
        draft_response="Done successfully.",
        action_status={"observed_outcome": ""},
        verification_status={"status": "pending"},
        archive_status={"archive_consulted": False, "fragments_used": 0},
    )
    post_summary = mirror.build_mirror_summary(
        monitor_output=post_action,
        active_mode="execute",
        task_type="execution",
        phase="post_action",
    )
    assert post_summary.primary_risk == "fake_progress"

    mixed = monitor.post_action_monitor(
        active_mode="execute",
        task_type="execution",
        context_view={"task_focus": "apply local change"},
        draft_response="Completed successfully.",
        action_status={"observed_outcome": ""},
        verification_status={"status": "pending"},
        archive_status={"archive_consulted": True, "fragments_used": 6},
    )
    mixed_summary = mirror.build_mirror_summary(
        monitor_output=mixed,
        active_mode="execute",
        task_type="execution",
        phase="post_action",
    )
    assert mixed.archive_overreach_risk > 0.0
    assert mixed_summary.primary_risk == "fake_progress"

    print("monitor_mirror_smoke: ok")


if __name__ == "__main__":
    run()
