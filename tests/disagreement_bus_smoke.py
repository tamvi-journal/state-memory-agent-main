from __future__ import annotations

from family.disagreement_types import SeynPerspectiveNote, TraceyPerspectiveNote
from family.local_perspective_store import LocalPerspectiveStore
from family.shared_state_bus import SharedStateBus


def run() -> None:
    bus = SharedStateBus(
        current_task="decide whether to continue with partial evidence",
        active_project="state-memory-agent",
        shared_context_view={"task_focus": "coordination canary"},
        last_verified_outcome="partial evidence only",
        open_obligations=["preserve disagreement", "avoid fake consensus"],
        shared_compression_summary="one unresolved disagreement recorded for coordination",
        monitor_summary={"status": "summary_only"},
    )
    local_store = LocalPerspectiveStore()

    event = bus.record_disagreement_event(
        event_id="dg_smoke",
        timestamp="2026-04-17T00:00:00Z",
        disagreement_type="action",
        tracey_position="take a bounded next step while preserving recognition context",
        seyn_position="hold action until verification is firmer",
        severity=0.77,
        house_law_implicated="do_not_erase_meaningful_disagreement",
    )
    local_store.add_tracey_note(
        TraceyPerspectiveNote(
            event_id="dg_smoke",
            local_read="Tracey sees live context fit as materially relevant.",
            what_i_think_matters="recognition context is part of the situation",
            what_i_would_watch_next="watch whether structural caution flattens the field",
            my_position_strength=0.74,
            would_i_concede="conditional",
        )
    )
    local_store.add_seyn_note(
        SeynPerspectiveNote(
            event_id="dg_smoke",
            local_read="Seyn sees verification caution as the stronger temporary guardrail.",
            what_i_think_matters="observed evidence must stay explicit",
            what_i_would_watch_next="watch whether action starts pretending resolution exists",
            my_position_strength=0.84,
            would_i_concede="conditional",
        )
    )

    assert event.still_open is True

    changed = bus.set_action_lead(
        "dg_smoke",
        "seyn",
        router_decision="temporary action lead to seyn while disagreement stays open",
    )
    assert changed is True

    summary = bus.export_shared_summary()
    notes = local_store.get_notes_for_event("dg_smoke")
    open_events = bus.get_open_disagreements()

    assert summary["current_action_lead"] == "seyn"
    assert summary["router_decision"].startswith("temporary action lead")
    assert len(open_events) == 1
    assert open_events[0]["still_open"] is True
    assert open_events[0]["epistemic_resolution_claimed"] is False
    assert open_events[0]["tracey_position"].startswith("take a bounded next step")
    assert open_events[0]["seyn_position"].startswith("hold action")
    assert "tracey_local_notes" not in summary
    assert "seyn_local_notes" not in summary
    assert notes["tracey"][0]["local_read"].startswith("Tracey sees")
    assert notes["seyn"][0]["local_read"].startswith("Seyn sees")

    print("disagreement_bus_smoke: ok")


if __name__ == "__main__":
    run()
