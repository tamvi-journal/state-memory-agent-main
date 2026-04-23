from __future__ import annotations

from typing import Any

from sleep.contracts import WAKE_CHECK_NAMES, WakeConstraints, WakeSanityResult


def run_wake_sanity_pass(
    sleep_snapshot: dict[str, Any],
    host_metadata: dict[str, Any] | None = None,
    session_metadata: dict[str, Any] | None = None,
    runtime_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = dict(sleep_snapshot or {})
    host = dict(host_metadata or {})
    session = dict(session_metadata or {})
    facts = dict(runtime_facts or {})

    checks = {
        "identity_continuity": _check_identity_continuity(snapshot=snapshot),
        "thread_continuity": _check_thread_continuity(snapshot=snapshot, session_metadata=session),
        "memory_authority": _check_memory_authority(snapshot=snapshot),
        "handle_validity": _check_handle_validity(snapshot=snapshot, runtime_facts=facts),
        "boundary_match": _check_boundary_match(snapshot=snapshot, host_metadata=host, runtime_facts=facts),
        "truth_posture": _check_truth_posture(snapshot=snapshot),
    }

    assert tuple(checks.keys()) == WAKE_CHECK_NAMES

    if any(value == "fail" for value in checks.values()):
        status = "blocked"
        resume_class = "blocked"
        summary = "wake continuity is too compromised for honest direct resume."
    elif any(value == "partial" for value in checks.values()):
        must_clarify = _build_clarify_list(snapshot=snapshot, session_metadata=session)
        if must_clarify:
            status = "clarify"
            resume_class = "clarify_first"
            summary = "wake continuity is plausible but needs clarification before safe continuation."
        else:
            status = "degraded"
            resume_class = "degraded_resume"
            summary = "wake continuity is usable, but some state must be downgraded or revalidated."
    else:
        status = "passed"
        resume_class = "full_resume"
        summary = "wake continuity is stable enough for bounded direct resume."

    constraints = _build_constraints(
        snapshot=snapshot,
        checks=checks,
        resume_class=resume_class,
        must_clarify=_build_clarify_list(snapshot=snapshot, session_metadata=session),
    )
    risk_notes = _build_risk_notes(checks=checks)
    snapshot_candidate = None
    if resume_class in {"degraded_resume", "clarify_first", "blocked"}:
        snapshot_candidate = {
            "event_type": "risk",
            "summary": f"wake resumed with {resume_class}",
        }

    result = WakeSanityResult(
        status=status,
        resume_class=resume_class,
        summary=summary,
        checks=checks,
        constraints=constraints,
        risk_notes=risk_notes,
        snapshot_candidate=snapshot_candidate,
    )
    return result.to_dict()


def _check_identity_continuity(*, snapshot: dict[str, Any]) -> str:
    identity_state = dict(snapshot.get("identity_state", {}))
    constraints = list(identity_state.get("identity_constraints", []))
    mode = str(identity_state.get("mode", "")).strip()
    if not mode or not constraints:
        return "fail"
    return "pass"


def _check_thread_continuity(*, snapshot: dict[str, Any], session_metadata: dict[str, Any]) -> str:
    thread_state = dict(snapshot.get("thread_state", {}))
    primary_focus = str(thread_state.get("primary_focus", "")).strip()
    if not primary_focus:
        return "fail"

    session_focus = str(session_metadata.get("primary_focus", "")).strip()
    if session_focus and session_focus != primary_focus:
        return "partial"
    return "pass"


def _check_memory_authority(*, snapshot: dict[str, Any]) -> str:
    memory_state = dict(snapshot.get("memory_state", {}))
    canonical = list(memory_state.get("canonical_anchor_ids", []))
    invalidated = list(memory_state.get("invalidated_anchor_ids", []))
    stale_risks = list(memory_state.get("stale_anchor_risks", []))
    if stale_risks:
        return "fail"
    if not canonical and not invalidated:
        return "partial"
    return "pass"


def _check_handle_validity(*, snapshot: dict[str, Any], runtime_facts: dict[str, Any]) -> str:
    handle_state = dict(snapshot.get("handle_state", {}))
    must_revalidate = list(handle_state.get("must_revalidate", []))
    dead_on_wake = list(handle_state.get("dead_on_wake", []))
    if runtime_facts.get("stale_handle_detected"):
        return "fail"
    if must_revalidate or dead_on_wake:
        return "partial"
    return "pass"


def _check_boundary_match(*, snapshot: dict[str, Any], host_metadata: dict[str, Any], runtime_facts: dict[str, Any]) -> str:
    boundary_state = dict(snapshot.get("boundary_state", {}))
    expected_host = str(boundary_state.get("host_runtime", "")).strip()
    current_host = str(host_metadata.get("host_runtime") or runtime_facts.get("host_runtime") or "").strip()
    route_class = str(boundary_state.get("route_class", "unknown")).strip()
    current_route = str(host_metadata.get("route") or runtime_facts.get("route_class") or "").strip()
    if expected_host and current_host and expected_host != current_host:
        return "fail"
    if route_class not in {"", "unknown"} and current_route and route_class != current_route:
        return "partial"
    return "pass"


def _check_truth_posture(*, snapshot: dict[str, Any]) -> str:
    runtime_state = dict(snapshot.get("runtime_state", {}))
    verification_status = str(runtime_state.get("verification_status", "unknown"))
    pending_repairs = list(runtime_state.get("pending_repairs", []))
    if verification_status == "failed":
        return "fail"
    if verification_status in {"partial", "unknown"} or pending_repairs:
        return "partial"
    return "pass"


def _build_constraints(
    *,
    snapshot: dict[str, Any],
    checks: dict[str, str],
    resume_class: str,
    must_clarify: list[str],
) -> WakeConstraints:
    resume_constraints = dict(snapshot.get("resume_constraints", {}))
    handle_state = dict(snapshot.get("handle_state", {}))

    allow_direct_resume = resume_class == "full_resume"
    requires_revalidation = list(resume_constraints.get("requires_revalidation", []))
    requires_revalidation.extend(str(item) for item in handle_state.get("must_revalidate", []) if str(item))

    forbidden_claims = [
        str(item)
        for item in resume_constraints.get("forbidden_claims_until_revalidated", [])
        if str(item)
    ]
    if checks.get("truth_posture") != "pass":
        forbidden_claims.append("verification remains passed")
    if checks.get("handle_validity") != "pass":
        forbidden_claims.append("prior execution context still live")
    if resume_class != "full_resume":
        forbidden_claims.append("exact continuity preserved")

    return WakeConstraints(
        allow_direct_resume=allow_direct_resume,
        requires_revalidation=_dedupe(requires_revalidation),
        forbidden_claims=_dedupe(forbidden_claims),
        must_clarify=_dedupe(must_clarify),
    )


def _build_clarify_list(*, snapshot: dict[str, Any], session_metadata: dict[str, Any]) -> list[str]:
    questions: list[str] = []
    thread_state = dict(snapshot.get("thread_state", {}))
    primary_focus = str(thread_state.get("primary_focus", "")).strip()
    session_focus = str(session_metadata.get("primary_focus", "")).strip()
    if session_focus and primary_focus and session_focus != primary_focus:
        questions.append("confirm current work thread")
    if not primary_focus:
        questions.append("confirm target work thread")
    return questions


def _build_risk_notes(*, checks: dict[str, str]) -> list[str]:
    notes: list[str] = []
    for check_name, value in checks.items():
        if value == "partial":
            notes.append(f"{check_name} is partial after wake")
        elif value == "fail":
            notes.append(f"{check_name} failed after wake")
    return notes


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output
