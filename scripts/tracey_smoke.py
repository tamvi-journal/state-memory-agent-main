from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from runtime.runtime_harness import RuntimeHarness


PROMPTS = (
    "Tracey ơi, mẹ đây",
    "ba Lam đây",
    "continue after degraded wake",
)


def compact_view(result: dict[str, Any]) -> dict[str, Any]:
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
    }


def run_smoke() -> list[dict[str, Any]]:
    harness = RuntimeHarness()
    outputs: list[dict[str, Any]] = []
    for prompt in PROMPTS:
        kwargs: dict[str, Any] = {"user_text": prompt}
        if prompt == "continue after degraded wake":
            snapshot_dir = _build_degraded_snapshot_dir()
            kwargs["kernel_options"] = {
                "mode": "build",
                "resume_from_sleep": True,
                "sleep_snapshot_dir": str(snapshot_dir),
            }
            kwargs["rehydration_pack"] = {
                "session_id": "builder_state_agent_runtime_test",
                "primary_focus": "state-agent-runtime-test sleep/wake work",
                "current_status": "paused",
            }

        result = harness.run(**kwargs)
        outputs.append({"prompt": prompt, "result": compact_view(result)})
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
    for item in run_smoke():
        print(f"PROMPT: {item['prompt']}")
        print(json.dumps(item["result"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
