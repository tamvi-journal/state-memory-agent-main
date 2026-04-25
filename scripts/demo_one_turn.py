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


def compact_demo_view(*, user_text: str, result: dict[str, Any]) -> dict[str, Any]:
    verification_record = result.get("verification_record") or {}
    tracey_turn = result.get("tracey_turn") or {}
    reactivated_state_memories = result.get("reactivated_state_memories") or []

    return {
        "input": user_text,
        "final_response": result.get("final_response"),
        "gate_decision": result.get("gate_decision"),
        "verification_status": verification_record.get("verification_status"),
        "tracey_turn_response_hints": tracey_turn.get("response_hints"),
        "handoff_baton": result.get("handoff_baton"),
        "state_memory_records_written": result.get("state_memory_records_written"),
        "reactivated_state_memories_count": len(reactivated_state_memories),
    }


def main() -> None:
    user_text = "Give me a compact status check for this runtime harness."
    result = RuntimeHarness().run(user_text=user_text)
    print(json.dumps(compact_demo_view(user_text=user_text, result=result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
