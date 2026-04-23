from __future__ import annotations

import json

from integration.openclaw_entrypoint import OpenClawEntrypoint
from integration.payload_contracts import CONTRACT_SCHEMA_VERSION


class DummyHarness:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[dict] = []

    def run(self, **kwargs: object) -> dict:
        self.calls.append(dict(kwargs))
        return self.result


def test_openclaw_entrypoint_returns_ok_and_preserves_verification() -> None:
    harness = DummyHarness(
        {
            "final_response": "I checked MBB using market_data_worker.",
            "handoff_baton": {
                "task_focus": "verify bounded market-data lookup for MBB",
                "active_mode": "build",
                "open_loops": [],
                "verification_status": "failed",
                "monitor_summary": {"primary_risk": "none"},
                "next_hint": "inspect bounded evidence",
            },
            "verification_record": {
                "verification_status": "failed",
                "observed_outcome": "ticker not found",
            },
            "observed_outcome": "ticker not found",
            "gate_decision": {"decision": "sandbox_only", "reason": "bounded flow"},
            "monitor_summary": {"primary_risk": "none"},
            "tracey_turn": {},
            "worker_payload": {"result": {"bars_found": 0}},
        }
    )
    payload = json.dumps(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "request_id": "req-entry-1",
            "request_text": "Load MBB daily data",
            "kernel_options": {
                "return_debug_trace": True,
            },
        }
    )

    exit_code, response = OpenClawEntrypoint().handle_raw_json(payload, harness=harness)

    assert exit_code == 0
    assert response["status"] == "ok"
    assert response["verification_outcome"]["status"] == "failed"
    assert set(response["session_status_metadata"].keys()) == {
        "current_status",
        "primary_focus",
        "open_loops",
        "last_verified_outcomes",
        "recent_decisions",
        "relevant_entities",
        "active_skills",
        "risk_notes",
        "next_hint",
    }
    assert "tracey_turn" not in response["session_status_metadata"]
    assert "gate_decision" not in response["session_status_metadata"]
    assert "monitor_summary" not in response["session_status_metadata"]
    assert harness.calls and len(harness.calls) == 1


def test_openclaw_entrypoint_rejects_invalid_payload() -> None:
    exit_code, response = OpenClawEntrypoint().handle_raw_json(
        json.dumps(
            {
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "request_id": "req-entry-2",
            }
        )
    )

    assert exit_code != 0
    assert response["status"] == "error"
    assert response["error"]["error_type"] == "invalid_payload"


def test_openclaw_entrypoint_rejects_invalid_json() -> None:
    exit_code, response = OpenClawEntrypoint().handle_raw_json("{not valid json")

    assert exit_code != 0
    assert response["status"] == "error"
    assert response["error"]["error_type"] == "invalid_payload"
