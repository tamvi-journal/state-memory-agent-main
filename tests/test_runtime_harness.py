from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path

from runtime.runtime_harness import RuntimeHarness
from state_memory.contracts import StateMemoryRecord
from state_memory.store import StateMemoryStore


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_demo_spec = importlib.util.spec_from_file_location("demo_multi_turn_script", REPO_ROOT / "scripts" / "demo_multi_turn.py")
assert _demo_spec and _demo_spec.loader
demo_multi_turn = importlib.util.module_from_spec(_demo_spec)
_demo_spec.loader.exec_module(demo_multi_turn)
run_multi_turn_demo = demo_multi_turn.run_multi_turn_demo


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


def _write_degraded_wake_snapshot(snapshot_dir: Path) -> None:
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


def test_runtime_harness_applies_wake_resume_constraints(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "sleep_snapshots"
    _write_degraded_wake_snapshot(snapshot_dir)

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


def test_runtime_harness_returns_empty_reactivated_state_memories_when_disabled(tmp_path: Path) -> None:
    memory_path = tmp_path / "state_memory.jsonl"
    store = StateMemoryStore(memory_path)
    store.append(
        StateMemoryRecord(
            event_type="wake_degraded",
            scope="runtime/wake",
            summary="hello handshake observed with wake reminder",
            tags=["hello", "wake"],
        )
    )

    result = RuntimeHarness().run(
        user_text="wake handles",
        render_mode="user",
        kernel_options={
            "enable_state_memory": False,
            "state_memory_path": str(memory_path),
        },
    )

    assert result["reactivated_state_memories"] == []


def test_runtime_harness_reactivates_relevant_state_memory_by_cue(tmp_path: Path) -> None:
    memory_path = tmp_path / "state_memory.jsonl"
    store = StateMemoryStore(memory_path)
    store.append(
        StateMemoryRecord(
            event_type="wake_degraded",
            scope="runtime/wake",
            summary="wake degraded because handles must be revalidated",
            session_id="session_a",
            tags=["wake", "handles"],
        )
    )
    store.append(
        StateMemoryRecord(
            event_type="mode_shift",
            scope="runtime/delta",
            summary="mode shifted build to audit",
            session_id="session_a",
            tags=["mode"],
        )
    )

    result = RuntimeHarness().run(
        user_text="wake handles",
        render_mode="user",
        rehydration_pack={"session_id": "session_a"},
        kernel_options={
            "enable_state_memory": True,
            "state_memory_path": str(memory_path),
            "state_memory_reactivation_limit": 5,
        },
    )

    assert len(result["reactivated_state_memories"]) == 1
    assert result["reactivated_state_memories"][0]["event_type"] == "wake_degraded"


def test_runtime_harness_does_not_reactivate_invalidated_records(tmp_path: Path) -> None:
    memory_path = tmp_path / "state_memory.jsonl"
    store = StateMemoryStore(memory_path)
    store.append(
        StateMemoryRecord(
            event_type="wake_degraded",
            scope="runtime/wake",
            summary="wake degraded because handles must be revalidated",
            lifecycle_status="invalidated",
            tags=["wake", "handles"],
        )
    )

    result = RuntimeHarness().run(
        user_text="wake handles",
        render_mode="user",
        kernel_options={
            "enable_state_memory": True,
            "state_memory_path": str(memory_path),
        },
    )

    assert result["reactivated_state_memories"] == []


def test_reactivated_state_memory_is_advisory_only(tmp_path: Path) -> None:
    memory_path = tmp_path / "state_memory.jsonl"
    store = StateMemoryStore(memory_path)
    store.append(
        StateMemoryRecord(
            event_type="wake_degraded",
            scope="runtime/wake",
            summary="hello handshake observed with wake reminder",
            tags=["hello", "wake"],
        )
    )

    baseline = RuntimeHarness().run(user_text="hello there", render_mode="user")
    with_memory = RuntimeHarness().run(
        user_text="hello there",
        render_mode="user",
        kernel_options={
            "enable_state_memory": True,
            "state_memory_path": str(memory_path),
        },
    )

    assert with_memory["reactivated_state_memories"]
    assert with_memory["final_response"] == baseline["final_response"]
    assert with_memory["gate_decision"] == baseline["gate_decision"]
    assert with_memory["verification_record"] == baseline["verification_record"]
    assert with_memory["wake_result"] == baseline["wake_result"]


def test_runtime_harness_does_not_write_state_memory_by_default(tmp_path: Path) -> None:
    memory_path = tmp_path / "state_memory.jsonl"

    result = RuntimeHarness().run(
        user_text="hello there",
        kernel_options={"state_memory_path": str(memory_path)},
    )

    assert result["state_memory_records_written"] == 0
    assert result["state_memory_path"] == str(memory_path)
    assert memory_path.exists() is False


def test_runtime_harness_writes_state_memory_when_enabled(tmp_path: Path) -> None:
    memory_path = tmp_path / "state_memory.jsonl"

    result = RuntimeHarness().run(
        user_text="Load MBB daily data",
        kernel_options={
            "enable_state_memory": True,
            "state_memory_path": str(memory_path),
        },
    )

    assert result["state_memory_records_written"] >= 1
    assert result["state_memory_path"] == str(memory_path)
    assert memory_path.exists() is True
    assert StateMemoryStore(memory_path).read_all()


def test_runtime_harness_records_wake_degraded_event_when_enabled(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "sleep_snapshots"
    _write_degraded_wake_snapshot(snapshot_dir)
    memory_path = tmp_path / "state_memory.jsonl"

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
            "enable_state_memory": True,
            "state_memory_path": str(memory_path),
        },
    )

    assert result["state_memory_records_written"] >= 1
    records = StateMemoryStore(memory_path).read_all()
    event_types = {record["event_type"] for record in records}
    assert "wake_degraded" in event_types


def test_runtime_harness_invalid_reactivation_limit_falls_back_without_crashing(tmp_path: Path) -> None:
    memory_path = tmp_path / "state_memory.jsonl"
    store = StateMemoryStore(memory_path)
    assert store.append(
        StateMemoryRecord(
            event_type="wake_degraded",
            scope="runtime/wake",
            session_id="sess-limit",
            summary="wake degraded because handles need revalidation",
            source="wake_sanity",
            tags=["wake", "degraded"],
        )
    )

    baseline = RuntimeHarness().run(
        user_text="wake revalidation",
        render_mode="builder",
        rehydration_pack={"session_id": "sess-limit"},
    )

    for invalid_limit in ("five", {}, None, 0, -2, True, False):
        result = RuntimeHarness().run(
            user_text="wake revalidation",
            render_mode="builder",
            rehydration_pack={"session_id": "sess-limit"},
            kernel_options={
                "enable_state_memory": True,
                "state_memory_path": str(memory_path),
                "state_memory_reactivation_limit": invalid_limit,
            },
        )

        assert result["final_response"] == baseline["final_response"]
        assert result["gate_decision"] == baseline["gate_decision"]
        assert result["verification_record"] == baseline["verification_record"]
        assert result["wake_result"] == baseline["wake_result"]
        assert result["tracey_turn"] == baseline["tracey_turn"]
        assert result["monitor_summary"] == baseline["monitor_summary"]
        assert result["handoff_baton"] == baseline["handoff_baton"]
        assert result["reactivated_state_memories"]
        assert len(result["reactivated_state_memories"]) == 1


def test_demo_multi_turn_helper_runs_without_crashing() -> None:
    outputs = run_multi_turn_demo()

    assert len(outputs) == 3
    assert [item["input"] for item in outputs] == [
        "Load MBB daily data",
        "continue from there",
        "tell me if this runtime is ready for production",
    ]


def test_demo_multi_turn_passes_baton_from_turn_1_to_turn_2() -> None:
    outputs = run_multi_turn_demo()

    assert outputs[0]["baton_out"]
    assert outputs[1]["baton_in"] == outputs[0]["baton_out"]


def test_demo_multi_turn_compact_output_includes_expected_fields() -> None:
    outputs = run_multi_turn_demo()

    expected_fields = {
        "turn",
        "input",
        "final_response",
        "gate_decision",
        "verification_status",
        "handoff_baton.task_focus",
        "handoff_baton.next_hint",
        "tracey_turn.response_hints",
        "state_memory_records_written",
        "reactivated_state_memories_count",
    }

    for item in outputs:
        compact = item["compact"]
        assert expected_fields.issubset(compact.keys())
