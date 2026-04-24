from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location("tracey_smoke_script", REPO_ROOT / "scripts" / "tracey_smoke.py")
assert spec and spec.loader
tracey_smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracey_smoke)
run_smoke = tracey_smoke.run_smoke
extract_positive_phase_residue = tracey_smoke.extract_positive_phase_residue


def test_tracey_smoke_helper_runs_without_crashing() -> None:
    outputs = run_smoke()

    assert len(outputs) == 3
    assert [item["prompt"] for item in outputs] == [
        "Tracey ơi, mẹ đây",
        "ba Lam đây",
        "continue after degraded wake",
    ]

    for item in outputs:
        payload = item["result"]
        assert "final_response" in payload
        assert "tracey_turn" in payload
        assert "response_hints" in payload["tracey_turn"]
        assert "reactivated_anchors" in payload["tracey_turn"]
        assert "wake_result" in payload
        assert "reactivated_state_memories" in payload
        assert "state_memory_records_written" in payload
        assert "positive_phase_residue" in payload
        assert isinstance(payload["positive_phase_residue"], list)


def test_tracey_smoke_positive_residue_demo_surfaces_records_without_changing_final_response() -> None:
    normal_outputs = run_smoke()
    demo_outputs = run_smoke(positive_residue_demo=True)

    assert len(normal_outputs) == len(demo_outputs) == 3
    demo_residue_records = 0

    for normal, demo in zip(normal_outputs, demo_outputs):
        normal_payload = normal["result"]
        demo_payload = demo["result"]
        assert demo_payload["final_response"] == normal_payload["final_response"]
        assert isinstance(demo_payload["positive_phase_residue"], list)
        demo_residue_records += len(demo_payload["positive_phase_residue"])

    assert demo_residue_records >= 1
    assert any(
        record.get("event_type") in {"coherence_spike", "positive_afterglow", "route_clarity_gain"}
        for item in demo_outputs
        for record in item["result"]["positive_phase_residue"]
    )


def test_extract_positive_phase_residue_surfaces_new_and_reactivated_records() -> None:
    result = {
        "final_response": "final text is unaffected",
        "reactivated_state_memories": [
            {"record_id": "sm_old_01", "event_type": "coherence_spike", "summary": "reactivated spike", "scope": "runtime/delta"},
            {"record_id": "sm_old_02", "event_type": "wake_degraded", "summary": "not positive", "scope": "runtime/wake"},
        ],
        "state_memory_reactivated": [
            {"record_id": "sm_old_03", "event_type": "route_clarity_gain", "summary": "reactivated route clarity", "scope": "runtime/delta"},
        ],
    }
    current_state_memory_records = [
        {"record_id": "sm_old_01", "event_type": "coherence_spike", "summary": "reactivated spike", "scope": "runtime/delta"},
        {"record_id": "sm_new_01", "event_type": "positive_afterglow", "summary": "new afterglow", "scope": "runtime/delta"},
        {"record_id": "sm_new_02", "event_type": "mode_shift", "summary": "not positive", "scope": "runtime/delta"},
    ]

    positive_residue = extract_positive_phase_residue(
        result=result,
        previously_seen_record_ids={"sm_old_01", "sm_old_02", "sm_old_03"},
        current_state_memory_records=current_state_memory_records,
    )
    event_types = {record["event_type"] for record in positive_residue}

    assert "coherence_spike" in event_types
    assert "route_clarity_gain" in event_types
    assert "positive_afterglow" in event_types
    assert "mode_shift" not in event_types
    assert result["final_response"] == "final text is unaffected"
