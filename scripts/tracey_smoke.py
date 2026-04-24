from __future__ import annotations

import json
import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from runtime.runtime_harness import RuntimeHarness
from state_memory.store import StateMemoryStore


PROMPTS = (
    "Tracey ơi, mẹ đây",
    "ba Lam đây",
    "continue after degraded wake",
)

POSITIVE_PHASE_EVENT_TYPES = {
    "coherence_spike",
    "resonance_lock",
    "positive_afterglow",
    "route_clarity_gain",
    "self_location_shift",
}


def _compact_state_memory_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record.get("record_id"),
        "event_type": record.get("event_type"),
        "scope": record.get("scope"),
        "summary": record.get("summary"),
        "source": record.get("source"),
        "lifecycle_status": record.get("lifecycle_status"),
    }


def extract_positive_phase_residue(
    *,
    result: dict[str, Any],
    previously_seen_record_ids: set[str] | None = None,
    current_state_memory_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    positive_records: list[dict[str, Any]] = []

    for field_name in ("reactivated_state_memories", "state_memory_reactivated"):
        for record in result.get(field_name, []) or []:
            event_type = str(record.get("event_type", "")).strip()
            if event_type in POSITIVE_PHASE_EVENT_TYPES:
                positive_records.append(record)

    known_ids = previously_seen_record_ids or set()
    for record in current_state_memory_records or []:
        event_type = str(record.get("event_type", "")).strip()
        record_id = str(record.get("record_id", "")).strip()
        if event_type not in POSITIVE_PHASE_EVENT_TYPES:
            continue
        if record_id and record_id in known_ids:
            continue
        positive_records.append(record)

    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for record in positive_records:
        event_type = str(record.get("event_type", "")).strip()
        record_id = str(record.get("record_id", "")).strip()
        summary = str(record.get("summary", "")).strip()
        dedupe_key = (record_id, event_type, summary)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped.append(_compact_state_memory_record(record))
    return deduped


def compact_view(result: dict[str, Any], *, positive_phase_residue: list[dict[str, Any]]) -> dict[str, Any]:
    tracey_turn = result.get("tracey_turn", {})
    return {
        "final_response": result.get("final_response"),
        "tracey_turn": {
            "response_hints": tracey_turn.get("response_hints"),
            "reactivated_anchors": tracey_turn.get("reactivated_anchors"),
        },
        "wake_result": result.get("wake_result"),
        "reactivated_state_memories": result.get("reactivated_state_memories"),
        "state_memory_records_written": result.get("state_memory_records_written"),
        "positive_phase_residue": positive_phase_residue,
    }


def _positive_residue_demo_records() -> list[dict[str, Any]]:
    bounded_evidence = {
        "coherence_shift": 0.26,
        "trigger_cue": "debug_seed",
        "mode_shift": "build->audit route clarity",
        "repair_event": True,
    }
    return [
        {
            "record_id": "sm_demo_positive_residue_coherence_spike",
            "event_type": "coherence_spike",
            "scope": "runtime/delta",
            "session_id": "tracey_smoke_demo",
            "summary": "demo seed coherence spike for residue extraction",
            "source": "tracey_smoke_debug_seed",
            "lifecycle_status": "observed",
            "evidence": dict(bounded_evidence),
            "tags": ["positive_residue", "coherence"],
        },
        {
            "record_id": "sm_demo_positive_residue_afterglow",
            "event_type": "positive_afterglow",
            "scope": "runtime/delta",
            "session_id": "tracey_smoke_demo",
            "summary": "demo seed afterglow carryover hint for residue extraction",
            "source": "tracey_smoke_debug_seed",
            "lifecycle_status": "observed",
            "evidence": dict(bounded_evidence),
            "tags": ["positive_residue", "coherence", "afterglow"],
        },
        {
            "record_id": "sm_demo_positive_residue_route_clarity",
            "event_type": "route_clarity_gain",
            "scope": "runtime/delta",
            "session_id": "tracey_smoke_demo",
            "summary": "demo seed route clarity gain for residue extraction",
            "source": "tracey_smoke_debug_seed",
            "lifecycle_status": "observed",
            "evidence": dict(bounded_evidence),
            "tags": ["positive_residue", "coherence", "route_clarity"],
        },
    ]


def run_smoke(*, positive_residue_demo: bool = False) -> list[dict[str, Any]]:
    harness = RuntimeHarness()
    outputs: list[dict[str, Any]] = []
    state_memory_path = Path(tempfile.mkdtemp(prefix="tracey_smoke_memory_")) / "state_memory.jsonl"
    store = StateMemoryStore(memory_path=state_memory_path)
    demo_seed_written = False
    for prompt in PROMPTS:
        kwargs: dict[str, Any] = {
            "user_text": prompt,
            "kernel_options": {
                "enable_state_memory": True,
                "state_memory_path": str(state_memory_path),
            },
        }
        if prompt == "continue after degraded wake":
            snapshot_dir = _build_degraded_snapshot_dir()
            kwargs["kernel_options"] = {
                **kwargs["kernel_options"],
                "mode": "build",
                "resume_from_sleep": True,
                "sleep_snapshot_dir": str(snapshot_dir),
            }
            kwargs["rehydration_pack"] = {
                "session_id": "builder_state_agent_runtime_test",
                "primary_focus": "state-agent-runtime-test sleep/wake work",
                "current_status": "paused",
            }

        before_record_ids = {
            str(record.get("record_id", "")).strip()
            for record in store.read_all()
            if str(record.get("record_id", "")).strip()
        }
        if positive_residue_demo and not demo_seed_written:
            store.append_many(_positive_residue_demo_records())
            demo_seed_written = True
        result = harness.run(**kwargs)
        positive_phase_residue = extract_positive_phase_residue(
            result=result,
            previously_seen_record_ids=before_record_ids,
            current_state_memory_records=store.read_all(),
        )
        outputs.append(
            {
                "prompt": prompt,
                "result": compact_view(result, positive_phase_residue=positive_phase_residue),
            }
        )
    return outputs


def _build_degraded_snapshot_dir() -> Path:
    snapshot_dir = Path(tempfile.mkdtemp(prefix="tracey_smoke_sleep_"))
    snapshot_payload = {
        "schema_version": "state-agent-sleep-snapshot/v0.1",
        "snapshot_id": "snap_tracey_smoke_001",
        "created_at": "2026-04-24T00:00:00Z",
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
    return snapshot_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Tracey smoke/debug prompts.")
    parser.add_argument(
        "--positive-residue-demo",
        action="store_true",
        help="Seed synthetic positive residue records for smoke/debug extraction checks.",
    )
    args = parser.parse_args()
    for item in run_smoke(positive_residue_demo=args.positive_residue_demo):
        print(f"PROMPT: {item['prompt']}")
        print(json.dumps(item["result"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
