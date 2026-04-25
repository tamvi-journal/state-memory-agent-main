from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from runtime.runtime_harness import RuntimeHarness

PROMPTS = (
    "Load MBB daily data",
    "continue from there",
    "tell me if this runtime is ready for production",
)


def compact_turn_view(*, turn_number: int, user_text: str, result: dict[str, Any]) -> dict[str, Any]:
    verification_record = result.get("verification_record") or {}
    handoff_baton = result.get("handoff_baton") or {}
    tracey_turn = result.get("tracey_turn") or {}
    reactivated_state_memories = result.get("reactivated_state_memories") or []

    return {
        "turn": turn_number,
        "input": user_text,
        "final_response": result.get("final_response"),
        "gate_decision": (result.get("gate_decision") or {}).get("decision"),
        "verification_status": verification_record.get("verification_status"),
        "handoff_baton.task_focus": handoff_baton.get("task_focus"),
        "handoff_baton.next_hint": handoff_baton.get("next_hint"),
        "tracey_turn.response_hints": tracey_turn.get("response_hints"),
        "state_memory_records_written": result.get("state_memory_records_written"),
        "reactivated_state_memories_count": len(reactivated_state_memories),
    }


def run_multi_turn_demo() -> list[dict[str, Any]]:
    harness = RuntimeHarness()
    baton: dict[str, Any] | None = None
    outputs: list[dict[str, Any]] = []

    for turn_number, user_text in enumerate(PROMPTS, start=1):
        result = harness.run(user_text=user_text, baton=baton)
        outputs.append(
            {
                "turn": turn_number,
                "input": user_text,
                "baton_in": baton,
                "baton_out": result.get("handoff_baton"),
                "compact": compact_turn_view(
                    turn_number=turn_number,
                    user_text=user_text,
                    result=result,
                ),
            }
        )
        baton = result.get("handoff_baton")

    return outputs


def main() -> None:
    for item in run_multi_turn_demo():
        print(json.dumps(item["compact"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
