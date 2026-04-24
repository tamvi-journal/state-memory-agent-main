from __future__ import annotations

import json
from pathlib import Path

from runtime.runtime_harness import RuntimeHarness


def test_runtime_harness_runs_the_single_worker_spine() -> None:
    result = RuntimeHarness().run(user_text="Load MBB daily data", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "passed"
    assert result["tracey_turn"]["state_patch"]["tracey_build_mode_active"] is True
    assert result["handoff_baton"]["task_focus"] == "verify bounded market-data lookup for MBB"
    assert "Main brain used market_data_worker for ticker MBB." in result["final_response"]


def test_runtime_harness_keeps_direct_response_out_of_fake_completion() -> None:
    result = RuntimeHarness().run(user_text="hello there", render_mode="user")

    assert result["verification_record"] is None
    assert result["handoff_baton"]["verification_status"] == "pending"
    assert result["gate_decision"]["decision"] == "deny"
    assert result["tracey_turn"]["state_patch"]["tracey_response_constraint"] == "build_exact"
    assert "Tracey" not in result["final_response"]


def test_runtime_harness_routes_technical_analysis_request() -> None:
    result = RuntimeHarness().run(user_text="technical analysis for MBB", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "passed"
    assert result["handoff_baton"]["task_focus"] == "verify bounded technical analysis for MBB"
    assert "Main brain used technical_analysis_worker for ticker MBB." in result["final_response"]


def test_runtime_harness_macro_sector_mapping_requires_explicit_input_by_default() -> None:
    result = RuntimeHarness().run(user_text="macro sector mapping", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "failed"
    assert result["handoff_baton"]["task_focus"] == "verify bounded macro-sector mapping"
    assert "Main brain used macro_sector_mapping_worker." in result["final_response"]


def test_runtime_harness_macro_sector_mapping_demo_uses_explicit_sample_route() -> None:
    result = RuntimeHarness().run(user_text="macro sector mapping sample", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "passed"
    assert result["worker_payload"]["result"]["matched_signals"]
    assert "Main brain used macro_sector_mapping_worker." in result["final_response"]


def test_runtime_harness_sector_flow_requires_explicit_input_by_default() -> None:
    result = RuntimeHarness().run(user_text="sector flow", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "failed"
    assert result["handoff_baton"]["task_focus"] == "verify bounded sector-flow classification"
    assert "Main brain used sector_flow_worker." in result["final_response"]


def test_runtime_harness_sector_flow_demo_uses_explicit_sample_route() -> None:
    result = RuntimeHarness().run(user_text="sector flow sample", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "passed"
    assert result["worker_payload"]["result"]["sector_flow_board"]
    assert "Main brain used sector_flow_worker." in result["final_response"]


def test_runtime_harness_candle_volume_structure_requires_explicit_input_by_default() -> None:
    result = RuntimeHarness().run(user_text="candle volume structure", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "failed"
    assert result["handoff_baton"]["task_focus"] == "verify bounded candle-volume-structure scoring"
    assert "Main brain used candle_volume_structure_worker." in result["final_response"]


def test_runtime_harness_candle_volume_structure_demo_uses_explicit_sample_route() -> None:
    result = RuntimeHarness().run(user_text="candle volume structure sample", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "passed"
    assert result["worker_payload"]["result"]["watch_list"] or result["worker_payload"]["result"]["top_list"]
    assert "Main brain used candle_volume_structure_worker." in result["final_response"]


def test_runtime_harness_trade_memo_requires_explicit_input_by_default() -> None:
    result = RuntimeHarness().run(user_text="trade memo", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "failed"
    assert result["handoff_baton"]["task_focus"] == "verify bounded trade-memo scenario planning"
    assert "Main brain used trade_memo_worker." in result["final_response"]


def test_runtime_harness_trade_memo_demo_uses_explicit_sample_route() -> None:
    result = RuntimeHarness().run(user_text="trade memo sample", render_mode="builder")

    assert result["gate_decision"]["decision"] == "sandbox_only"
    assert result["verification_record"]["verification_status"] == "passed"
    assert result["worker_payload"]["result"]["ticker_memos"]
    assert "Main brain used trade_memo_worker." in result["final_response"]


def test_runtime_harness_applies_wake_resume_constraints(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "sleep_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_payload = {
        "schema_version": "state-agent-sleep-snapshot/v0.1",
        "snapshot_id": "snap_test_001",
        "created_at": "2026-04-23T19:10:00Z",
        "runtime_id": "tracey_runtime_local",
        "session_id": "builder_state_agent_runtime_test",
        "sleep_reason": "manual",
        "sleep_level": "normal",
        "identity_state": {
            "agent_name": "Tracey",
            "active_axis": "build",
            "mode": "build",
            "identity_constraints": ["brain_speaks_last"],
            "continuity_confidence": "medium",
        },
        "thread_state": {
            "primary_focus": "state-agent-runtime-test sleep/wake work",
            "current_status": "paused",
            "open_loops": ["revalidate tool handles after wake"],
            "recent_decisions": [],
            "last_verified_outcomes": [],
            "relevant_entities": ["Tracey"],
            "next_hint": "continue sleep/wake integration",
        },
        "memory_state": {
            "canonical_anchor_ids": ["tracey.invariant.brain_speaks_last"],
            "provisional_anchor_ids": [],
            "invalidated_anchor_ids": [],
            "reactivation_priority": [],
            "stale_anchor_risks": [],
        },
        "runtime_state": {
            "verification_status": "passed",
            "monitor_risk_summary": "",
            "active_skills": ["workflow_builder"],
            "pending_repairs": [],
            "context_fragmentation": "low",
        },
        "handle_state": {
            "tool_handles": [],
            "worker_handles": [],
            "dead_on_wake": [],
            "must_revalidate": ["tool_handles"],
        },
        "boundary_state": {
            "host_runtime": "OpenClaw",
            "route_class": "direct_reasoning",
            "persistence_scope": "mixed",
            "truth_boundary_note": "sleep snapshot is local resume evidence only",
        },
        "resume_constraints": {
            "must_run_wake_sanity": True,
            "allow_direct_resume": False,
            "requires_revalidation": ["tool_handles"],
            "forbidden_claims_until_revalidated": [],
        },
    }
    snapshot_path = snapshot_dir / "builder_state_agent_runtime_test__latest.json"
    snapshot_path.write_text(json.dumps(snapshot_payload, indent=2), encoding="utf-8")

    result = RuntimeHarness().run(
        user_text="continue the sleep wake work",
        render_mode="builder",
        rehydration_pack={
            "session_id": "builder_state_agent_runtime_test",
            "primary_focus": "state-agent-runtime-test sleep/wake work",
            "current_status": "paused",
        },
        host_metadata={
            "host_runtime": "OpenClaw",
            "route": "direct_reasoning",
        },
        kernel_options={
            "mode": "build",
            "resume_from_sleep": True,
            "sleep_snapshot_dir": str(snapshot_dir),
        },
    )

    assert result["wake_result"]["resume_class"] == "degraded_resume"
    assert result["sleep_runtime_state"]["wake_constraints_active"] is True
    assert result["tracey_turn"]["response_hints"]["wake_resume_class"] == "degraded_resume"
    assert result["tracey_turn"]["response_hints"]["recognition_active"] is False
    assert result["tracey_turn"]["response_hints"]["keep_ambiguity_open"] is True
    assert "Wake status: degraded resume." in result["final_response"]
    assert result["handoff_baton"]["monitor_summary"]["wake_resume_class"] == "degraded_resume"
