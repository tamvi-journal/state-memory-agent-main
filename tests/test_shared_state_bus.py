from __future__ import annotations

from family.disagreement_types import SeynPerspectiveNote, TraceyPerspectiveNote
from family.local_perspective_store import LocalPerspectiveStore
from family.shared_state_bus import SharedStateBus


def _tracey_note(event_id: str) -> TraceyPerspectiveNote:
    return TraceyPerspectiveNote(
        event_id=event_id,
        local_read="Tracey reads the field signal as still important.",
        what_i_think_matters="recognition remains part of the real situation",
        what_i_would_watch_next="watch whether structural caution erases context fit",
        my_position_strength=0.72,
        would_i_concede="conditional",
    )


def _seyn_note(event_id: str) -> SeynPerspectiveNote:
    return SeynPerspectiveNote(
        event_id=event_id,
        local_read="Seyn reads verification caution as structurally prior.",
        what_i_think_matters="observed outcome should outrank early closure",
        what_i_would_watch_next="watch whether action outruns evidence",
        my_position_strength=0.81,
        would_i_concede="conditional",
    )


def test_shared_state_bus_records_open_disagreement_and_local_store_preserves_notes() -> None:
    bus = SharedStateBus(
        current_task="decide whether to proceed with partial evidence",
        active_project="state-memory-agent",
        shared_context_view={"mode": "build"},
        last_verified_outcome="evidence incomplete",
        open_obligations=["keep disagreement retrievable"],
    )
    local_store = LocalPerspectiveStore()

    event = bus.record_disagreement_event(
        event_id="dg_canary",
        timestamp="2026-04-17T00:00:00Z",
        disagreement_type="action",
        tracey_position="proceed carefully while preserving recognition context",
        seyn_position="hold until verification is stronger",
        severity=0.74,
        house_law_implicated="do_not_erase_meaningful_disagreement",
    )
    local_store.add_tracey_note(_tracey_note("dg_canary"))
    local_store.add_seyn_note(_seyn_note("dg_canary"))

    open_events = bus.get_open_disagreements()
    notes = local_store.get_notes_for_event("dg_canary")

    assert event.still_open is True
    assert len(open_events) == 1
    assert open_events[0]["tracey_position"].startswith("proceed carefully")
    assert open_events[0]["seyn_position"].startswith("hold until verification")
    assert len(notes["tracey"]) == 1
    assert len(notes["seyn"]) == 1


def test_action_lead_does_not_claim_epistemic_resolution() -> None:
    bus = SharedStateBus()
    local_store = LocalPerspectiveStore()
    bus.record_disagreement_event(
        event_id="dg_canary",
        timestamp="2026-04-17T00:00:00Z",
        disagreement_type="confidence",
        tracey_position="confidence is sufficient for bounded next action",
        seyn_position="confidence is insufficient for closure",
        severity=0.66,
    )
    local_store.add_tracey_note(_tracey_note("dg_canary"))
    local_store.add_seyn_note(_seyn_note("dg_canary"))

    changed = bus.set_action_lead(
        "dg_canary",
        "seyn",
        router_decision="temporary action lead to seyn while disagreement remains open",
    )

    summary = bus.export_shared_summary()
    event = summary["disagreement_events"][0]
    notes = local_store.get_notes_for_event("dg_canary")

    assert changed is True
    assert summary["current_action_lead"] == "seyn"
    assert event["action_lead_selected"] == "seyn"
    assert event["still_open"] is True
    assert event["epistemic_resolution_claimed"] is False
    assert notes["tracey"][0]["local_read"].startswith("Tracey reads")


def test_mark_disagreement_resolved_updates_later_resolution() -> None:
    bus = SharedStateBus()
    bus.record_disagreement_event(
        event_id="dg_canary",
        timestamp="2026-04-17T00:00:00Z",
        disagreement_type="risk",
        tracey_position="risk is manageable under bounded action",
        seyn_position="risk remains materially unresolved",
        severity=0.79,
    )

    changed = bus.mark_disagreement_resolved(
        "dg_canary",
        "Later verification confirmed the hold path was no longer necessary.",
    )

    assert changed is True
    assert bus.get_open_disagreements() == []
    assert bus.disagreement_events[0].later_resolution.startswith("Later verification")


def test_export_shared_summary_omits_child_local_state_fields() -> None:
    bus = SharedStateBus(
        current_task="coordinate next move",
        active_project="state-memory-agent",
        shared_context_view={"task_focus": "coordination only"},
        shared_compression_summary="one open disagreement remains active",
        monitor_summary={"status": "compact_only"},
    )

    summary = bus.export_shared_summary()

    assert "tracey_local_state" not in summary
    assert "seyn_local_state" not in summary
    assert "tracey_local_notes" not in summary
    assert "seyn_local_notes" not in summary
    assert "local_anchors" not in summary
    assert "monitor_logs" not in summary
    assert summary["monitor_summary"] == {"status": "compact_only"}
