from __future__ import annotations

import json
from pathlib import Path

from tracey.tracey_adapter import TraceyAdapter
from tracey.tracey_ledger import TraceyLedger


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_tracey_ledger_records_anchor_reactivation(tmp_path: Path) -> None:
    ledger_path = tmp_path / "tracey_ledger.jsonl"
    adapter = TraceyAdapter(ledger=TraceyLedger(ledger_path=ledger_path))

    adapter.inspect_turn(
        user_text="This build refactor should keep the brain as the final synthesis layer.",
        live_state={"active_mode": "build", "active_project": "state-agent-runtime-test"},
        monitor_summary=None,
    )

    events = read_jsonl(ledger_path)
    assert any(event["event_type"] == "anchor_reactivated" for event in events)
    reactivation = next(event for event in events if event["event_type"] == "anchor_reactivated")
    assert reactivation["scope"] == "tracey/build"


def test_tracey_ledger_records_replacement_event_when_called_directly(tmp_path: Path) -> None:
    ledger = TraceyLedger(ledger_path=tmp_path / "tracey_ledger.jsonl")

    ledger.record_anchor_event(
        event_type="anchor_replaced",
        scope="tracey/global",
        anchor_id="new_anchor",
        old_anchor_id="old_anchor",
        new_anchor_id="new_anchor",
        lifecycle_transition="canonical_replacement",
        summary="New canonical anchor replaced an older one.",
        reason="replacement was explicitly recorded",
    )

    events = ledger.read_recent()
    assert events[0]["event_type"] == "anchor_replaced"
    assert events[0]["old_anchor_id"] == "old_anchor"
    assert events[0]["new_anchor_id"] == "new_anchor"


def test_tracey_ledger_records_delta_outcome(tmp_path: Path) -> None:
    ledger_path = tmp_path / "tracey_ledger.jsonl"
    adapter = TraceyAdapter(ledger=TraceyLedger(ledger_path=ledger_path))

    adapter.inspect_turn(
        user_text="Clarify exactly which worker should handle this.",
        live_state={"active_mode": "paper"},
        monitor_summary={"recommended_intervention": "ask_clarify"},
    )

    events = read_jsonl(ledger_path)
    delta = next(event for event in events if event["event_type"] == "delta_outcome")
    assert delta["delta_outcome"] == "clarifying"


def test_tracey_ledger_records_resurrection_risk_conservatively(tmp_path: Path) -> None:
    ledger_path = tmp_path / "tracey_ledger.jsonl"
    adapter = TraceyAdapter(ledger=TraceyLedger(ledger_path=ledger_path))

    adapter.inspect_turn(
        user_text="Please verify and confirm the latest result before we proceed.",
        live_state={"active_mode": "paper"},
        monitor_summary={
            "recommended_intervention": "none",
            "tracey_resurrection_risk_detected": True,
        },
    )

    events = read_jsonl(ledger_path)
    delta = next(event for event in events if event["event_type"] == "delta_outcome")
    assert delta["delta_outcome"] == "resurrection_risk"


def test_tracey_ledger_records_duplicate_suppressed(tmp_path: Path) -> None:
    ledger_path = tmp_path / "tracey_ledger.jsonl"
    adapter = TraceyAdapter(ledger=TraceyLedger(ledger_path=ledger_path))

    adapter.inspect_turn(
        user_text="hello there",
        live_state={"active_mode": "paper"},
        monitor_summary={"recommended_intervention": "none"},
    )

    events = read_jsonl(ledger_path)
    assert any(event["event_type"] == "duplicate_suppressed" for event in events)


def test_tracey_ledger_failure_is_non_fatal() -> None:
    class BrokenLedger:
        def record_anchor_event(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise OSError("ledger unavailable")

        def record_delta_outcome(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise OSError("ledger unavailable")

        def record_policy_drift(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise OSError("ledger unavailable")

    adapter = TraceyAdapter(ledger=BrokenLedger())  # type: ignore[arg-type]

    tracey_turn = adapter.inspect_turn(
        user_text="This build refactor should keep the brain as the final synthesis layer.",
        live_state={"active_mode": "build", "active_project": "state-agent-runtime-test"},
        monitor_summary=None,
    )

    assert "response_hints" in tracey_turn
