from __future__ import annotations

from pathlib import Path

from state_memory.adapter import records_from_turn, records_from_wake_result
from state_memory.compression import compress_state_memories
from state_memory.contracts import StateMemoryRecord
from state_memory.reactivation import reactivate_state_memories
from state_memory.store import StateMemoryStore


def test_state_memory_store_round_trip(tmp_path: Path) -> None:
    store = StateMemoryStore(tmp_path / "state_memory.jsonl")
    record = StateMemoryRecord(
        event_type="wake_degraded",
        scope="runtime/wake",
        session_id="session_a",
        summary="wake degraded because handles must be revalidated",
        source="wake_sanity",
        tags=["wake", "degraded_resume"],
    )

    assert store.append(record) is True
    loaded = store.read_recent(limit=1)

    assert loaded[0]["event_type"] == "wake_degraded"
    assert loaded[0]["session_id"] == "session_a"


def test_records_from_wake_result_captures_degraded_resume() -> None:
    records = records_from_wake_result(
        wake_result={
            "resume_class": "degraded_resume",
            "summary": "wake continuity is usable but must be revalidated",
            "checks": {"handle_validity": "partial"},
            "constraints": {
                "requires_revalidation": ["tool_handles"],
                "forbidden_claims": ["exact continuity preserved"],
            },
        },
        session_id="session_a",
    )

    assert len(records) == 1
    payload = records[0].to_dict()
    assert payload["event_type"] == "wake_degraded"
    assert payload["evidence"]["resume_class"] == "degraded_resume"
    assert "tool_handles" in payload["evidence"]["requires_revalidation"]


def test_records_from_turn_collects_wake_delta_and_tracey() -> None:
    records = records_from_turn(
        wake_result={
            "resume_class": "blocked",
            "summary": "wake continuity is blocked",
            "checks": {},
            "constraints": {},
        },
        delta={
            "repair_event": True,
            "coherence_shift": -0.2,
            "mode_shift": "build->audit",
            "trigger_cue": "wake_check",
        },
        tracey_turn={
            "reactivated_anchors": [
                {"anchor_id": "brain_speaks_last", "kind": "invariant", "content": "brain speaks last"}
            ],
            "response_hints": {"tone_constraint": "wake_blocked", "resume_class": "blocked"},
        },
        session_id="session_a",
    )

    event_types = {record.event_type for record in records}
    assert "wake_blocked" in event_types
    assert "repair_event" in event_types
    assert "coherence_drop" in event_types
    assert "mode_shift" in event_types
    assert "anchor_reactivation" in event_types
    assert "verification_boundary" in event_types


def test_reactivation_ignores_invalidated_records() -> None:
    records = [
        StateMemoryRecord(
            event_type="wake_degraded",
            scope="runtime/wake",
            summary="wake degraded because tool handles must be revalidated",
            lifecycle_status="observed",
            tags=["wake", "tool_handles"],
        ).to_dict(),
        StateMemoryRecord(
            event_type="wake_blocked",
            scope="runtime/wake",
            summary="blocked stale branch",
            lifecycle_status="invalidated",
            tags=["wake", "blocked"],
        ).to_dict(),
    ]

    reactivated = reactivate_state_memories(records=records, cue_text="wake tool handles", limit=5)

    assert len(reactivated) == 1
    assert reactivated[0]["event_type"] == "wake_degraded"


def test_compression_prefers_canonical_duplicate() -> None:
    observed = StateMemoryRecord(
        event_type="state_invariant",
        scope="tracey/runtime",
        summary="brain speaks last",
        lifecycle_status="observed",
    ).to_dict()
    canonical = dict(observed)
    canonical["record_id"] = "sm_canonical"
    canonical["lifecycle_status"] = "canonical"

    compact = compress_state_memories([observed, canonical])

    assert len(compact) == 1
    assert compact[0]["record_id"] == "sm_canonical"
