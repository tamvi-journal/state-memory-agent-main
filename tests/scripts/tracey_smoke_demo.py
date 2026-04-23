from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from tracey.tracey_adapter import TraceyAdapter
from tracey.tracey_ledger import TraceyLedger


LEDGER_PATH = REPO_ROOT / "tests" / "runtime_memory" / "tracey_smoke_demo" / "tracey_ledger.jsonl"
FALLBACK_LEDGER_PATH = REPO_ROOT / "runtime_memory_tracey_smoke_demo" / "tracey_ledger.jsonl"


@dataclass(slots=True)
class DemoCase:
    name: str
    user_text: str
    live_state: dict[str, Any]
    monitor_summary: dict[str, Any] | None = None
    optional: bool = False


def build_cases() -> list[DemoCase]:
    return [
        DemoCase(
            name="exploratory_ambiguity",
            user_text="Maybe we could explore two directions for Tracey memory next.",
            live_state={"active_mode": "paper", "active_project": "tracey-smoke-demo"},
            monitor_summary={"recommended_intervention": "none"},
        ),
        DemoCase(
            name="blocking_ambiguity",
            user_text="Which worker should run?",
            live_state={"active_mode": "paper", "active_project": "tracey-smoke-demo"},
            monitor_summary={"recommended_intervention": "ask_clarify"},
        ),
        DemoCase(
            name="explicit_verification_request",
            user_text="Please verify and confirm whether this is current.",
            live_state={"active_mode": "paper", "active_project": "tracey-smoke-demo"},
            monitor_summary={"recommended_intervention": "none"},
        ),
        DemoCase(
            name="build_mode_exactness",
            user_text="Map the smallest valid integration seam for Tracey policy.",
            live_state={"active_mode": "build", "active_project": "tracey-smoke-demo"},
            monitor_summary={"recommended_intervention": "none"},
        ),
        DemoCase(
            name="duplicate_noop",
            user_text="hello there",
            live_state={"active_mode": "paper", "active_project": "tracey-smoke-demo"},
            monitor_summary={"recommended_intervention": "none"},
        ),
        DemoCase(
            name="resurrection_risk",
            user_text="Please verify and confirm the latest result before we proceed.",
            live_state={"active_mode": "paper", "active_project": "tracey-smoke-demo"},
            monitor_summary={
                "recommended_intervention": "none",
                "tracey_resurrection_risk_detected": True,
            },
            optional=True,
        ),
    ]


def reset_demo_ledger() -> None:
    active_ledger_path, _warnings = resolve_demo_ledger_path(reset=True)
    _ = active_ledger_path


def resolve_demo_ledger_path(*, reset: bool = False) -> tuple[Path, list[str]]:
    warnings: list[str] = []
    for candidate in (LEDGER_PATH, FALLBACK_LEDGER_PATH):
        ledger_dir = candidate.parent
        try:
            if reset and ledger_dir.exists():
                shutil.rmtree(ledger_dir)
            ledger_dir.mkdir(parents=True, exist_ok=True)
            return candidate, warnings
        except OSError as exc:
            warnings.append(f"warning: ledger path unavailable at {candidate}: {exc}")
    return FALLBACK_LEDGER_PATH, warnings


def read_recent_ledger_lines(limit: int = 5) -> tuple[list[dict[str, Any]], str | None]:
    active_ledger_path, _warnings = resolve_demo_ledger_path(reset=False)
    try:
        if not active_ledger_path.exists():
            return [], None
        lines = active_ledger_path.read_text(encoding="utf-8").splitlines()
        recent: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            if not line.strip():
                continue
            recent.append(json.loads(line))
        return recent, None
    except (OSError, json.JSONDecodeError) as exc:
        return [], f"warning: ledger read failed: {exc}"


def run_case(case: DemoCase, adapter: TraceyAdapter, previous_count: int) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    runtime_notes: list[str] = []
    try:
        tracey_turn = adapter.inspect_turn(
            user_text=case.user_text,
            live_state=case.live_state,
            monitor_summary=case.monitor_summary,
        )
    except Exception as exc:
        runtime_notes.append(f"warning: Tracey inspection failed: {exc}")
        return None, [], runtime_notes

    ledger_lines, ledger_warning = read_recent_ledger_lines()
    if ledger_warning:
        runtime_notes.append(ledger_warning)
    ledger_appended = False
    active_ledger_path, ledger_path_warnings = resolve_demo_ledger_path(reset=False)
    runtime_notes.extend(ledger_path_warnings)
    try:
        current_count = len(active_ledger_path.read_text(encoding="utf-8").splitlines()) if active_ledger_path.exists() else 0
        ledger_appended = current_count > previous_count
    except OSError as exc:
        runtime_notes.append(f"warning: ledger append check failed: {exc}")

    if case.optional:
        resurrection_seen = any(
            line.get("event_type") == "delta_outcome" and line.get("delta_outcome") == "resurrection_risk"
            for line in ledger_lines
        )
        if not resurrection_seen:
            runtime_notes.append("optional case skipped: resurrection-risk was not recorded honestly")

    summary = {
        "case_name": case.name,
        "input": case.user_text,
        "mode_hint": case.live_state.get("active_mode", ""),
        "reactivated_anchor_ids": [item.get("anchor_id", "") for item in tracey_turn["reactivated_anchors"]],
        "response_hints": tracey_turn["response_hints"],
        "state_patch": tracey_turn["state_patch"],
        "runtime_notes": runtime_notes,
        "ledger_appended": ledger_appended,
    }
    return summary, ledger_lines, runtime_notes


def print_case(summary: dict[str, Any], ledger_lines: list[dict[str, Any]]) -> None:
    print(f"CASE: {summary['case_name']}")
    print(f"input: {summary['input']}")
    print(f"mode_hint: {summary['mode_hint']}")
    print(f"reactivated_anchor_ids: {summary['reactivated_anchor_ids']}")
    print("response_hints:")
    print(json.dumps(summary["response_hints"], ensure_ascii=True, sort_keys=True))
    print("state_patch:")
    print(json.dumps(summary["state_patch"], ensure_ascii=True, sort_keys=True))
    print(f"runtime_notes: {summary['runtime_notes']}")
    print(f"ledger_appended: {summary['ledger_appended']}")
    if ledger_lines:
        print("recent_ledger_lines:")
        for line in ledger_lines[-3:]:
            print(json.dumps(line, ensure_ascii=True, sort_keys=True))
    print("")


def main() -> int:
    active_ledger_path, setup_warnings = resolve_demo_ledger_path(reset=True)
    adapter = TraceyAdapter(ledger=TraceyLedger(ledger_path=active_ledger_path))

    for case in build_cases():
        try:
            previous_count = len(active_ledger_path.read_text(encoding="utf-8").splitlines()) if active_ledger_path.exists() else 0
        except OSError:
            previous_count = 0
        summary, ledger_lines, _runtime_notes = run_case(case, adapter, previous_count)
        if summary is None:
            print(f"CASE: {case.name}")
            print(f"input: {case.user_text}")
            print("runtime_notes: ['warning: Tracey inspection failed']")
            print("")
            continue
        if setup_warnings:
            summary["runtime_notes"] = list(summary["runtime_notes"]) + setup_warnings
        print_case(summary, ledger_lines)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
