from __future__ import annotations

from typing import Any

from sleep.contracts import build_default_sleep_patch, normalize_sleep_level
from sleep.sleep_snapshot import build_sleep_snapshot, read_sleep_snapshot, write_sleep_snapshot
from sleep.wake_sanity import run_wake_sanity_pass


def sleep_prepare(
    runtime_state: dict[str, Any],
    session_state: dict[str, Any],
    tracey_memory_state: dict[str, Any],
    boundary_state: dict[str, Any],
    sleep_reason: str,
    sleep_level: str,
) -> dict[str, Any]:
    snapshot = build_sleep_snapshot(
        runtime_state=runtime_state,
        session_state=session_state,
        tracey_memory_state=tracey_memory_state,
        boundary_state=boundary_state,
        sleep_reason=sleep_reason,
        sleep_level=sleep_level,
    )
    return {
        "sleep_state": "sleep_prepare",
        "sleep_reason": str(sleep_reason or "unknown"),
        "sleep_level": normalize_sleep_level(sleep_level),
        "snapshot": snapshot,
        "pending_repairs": list(dict(runtime_state or {}).get("pending_repairs", [])),
    }


def enter_sleep_mode(prepared_state: dict[str, Any], snapshot_dir: str) -> dict[str, Any]:
    snapshot = dict(prepared_state.get("snapshot", {}))
    snapshot_path = write_sleep_snapshot(snapshot=snapshot, base_dir=snapshot_dir)
    return {
        "sleep_state": "sleeping",
        "sleep_level": prepared_state.get("sleep_level", "unknown"),
        "snapshot_path": snapshot_path,
        "session_id": snapshot.get("session_id", "unknown_session"),
    }


def wake_restore(
    session_id: str,
    snapshot_dir: str,
    host_metadata: dict[str, Any] | None = None,
    session_metadata: dict[str, Any] | None = None,
    runtime_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = read_sleep_snapshot(session_id=session_id, base_dir=snapshot_dir)
    if snapshot is None:
        return {
            "sleep_state": "blocked",
            "snapshot": None,
            "wake_result": {
                "status": "blocked",
                "resume_class": "blocked",
                "summary": "no sleep snapshot was available for wake restore.",
                "checks": {
                    "identity_continuity": "fail",
                    "thread_continuity": "fail",
                    "memory_authority": "fail",
                    "handle_validity": "fail",
                    "boundary_match": "fail",
                    "truth_posture": "fail",
                },
                "constraints": {
                    "allow_direct_resume": False,
                    "requires_revalidation": [],
                    "forbidden_claims": ["exact continuity preserved"],
                    "must_clarify": ["confirm target work thread"],
                },
                "risk_notes": ["missing sleep snapshot on wake"],
                "snapshot_candidate": {
                    "event_type": "risk",
                    "summary": "wake blocked because no snapshot was found",
                },
            },
        }

    wake_result = run_wake_sanity_pass(
        sleep_snapshot=snapshot,
        host_metadata=host_metadata,
        session_metadata=session_metadata,
        runtime_facts=runtime_facts,
    )
    return {
        "sleep_state": "wake_restore",
        "snapshot": snapshot,
        "wake_result": wake_result,
    }


def build_sleep_runtime_patch(wake_result: dict[str, Any] | None = None) -> dict[str, Any]:
    patch = build_default_sleep_patch()
    if not wake_result:
        return patch

    resume_class = str(wake_result.get("resume_class", "none"))
    constraints = dict(wake_result.get("constraints", {}))
    patch.update(
        {
            "sleep_state": {
                "full_resume": "resumed",
                "degraded_resume": "degraded_resume",
                "clarify_first": "clarify_first",
                "blocked": "blocked",
            }.get(resume_class, "wake_sanity"),
            "resume_class": resume_class,
            "wake_constraints_active": resume_class != "full_resume",
            "wake_requires_revalidation": list(constraints.get("requires_revalidation", [])),
            "wake_forbidden_claims": list(constraints.get("forbidden_claims", [])),
            "wake_summary": str(wake_result.get("summary", "")),
        }
    )
    return patch
