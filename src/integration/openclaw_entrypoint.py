from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .payload_adapter import PayloadAdapter
from .payload_contracts import (
    CONTRACT_SCHEMA_VERSION,
    ContractValidationError,
    validate_error_response,
    validate_request_payload,
    validate_success_response,
)


def _load_runtime_harness_class() -> type:
    src_root = Path(__file__).resolve().parents[1]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from runtime.runtime_harness import RuntimeHarness

    return RuntimeHarness


@dataclass(slots=True)
class OpenClawEntrypoint:
    adapter: PayloadAdapter = field(default_factory=PayloadAdapter)

    def handle_raw_json(
        self,
        raw_input: str,
        *,
        harness: Any = None,
    ) -> tuple[int, dict[str, Any]]:
        request_id = ""
        debug_trace: list[str] = []
        try:
            payload = json.loads(raw_input.lstrip("\ufeff"))
        except json.JSONDecodeError as exc:
            error_response = self._error_response(
                request_id="",
                error_type="invalid_payload",
                message=f"invalid JSON payload: {exc.msg}",
                retryable=False,
            )
            return 1, validate_error_response(error_response)

        try:
            request = validate_request_payload(payload)
            request_id = request.request_id
            debug_trace.append("payload_validated")
            invocation = self.adapter.build_internal_invocation(request)
            debug_trace.append("rehydration_pack_built")

            kernel_options = invocation["kernel_options"]
            runtime_harness = harness or _load_runtime_harness_class()()
            runtime_result = runtime_harness.run(
                user_text=invocation["request_text"],
                rehydration_pack=invocation["rehydration_pack"],
                host_metadata=invocation["host_metadata"],
                kernel_options=kernel_options,
            )
            debug_trace.append("runtime_invoked")
            response = self._normalize_success_response(
                request_id=request_id,
                runtime_result=runtime_result,
                kernel_options=kernel_options,
                debug_trace=debug_trace,
            )
            debug_trace.append("response_normalized")
            if kernel_options.get("return_debug_trace"):
                response["debug_trace"] = list(debug_trace)
            validate_success_response(response)
            return 0, response
        except ContractValidationError as exc:
            error_response = self._error_response(
                request_id=exc.request_id or request_id,
                error_type="invalid_payload",
                message=str(exc),
                retryable=False,
            )
            return 1, validate_error_response(error_response)
        except Exception as exc:
            error_response = self._error_response(
                request_id=request_id,
                error_type="runtime_failure",
                message=str(exc),
                retryable=False,
            )
            return 1, validate_error_response(error_response)

    def main(self, *, stdin: Any = None, stdout: Any = None) -> int:
        input_stream = stdin or sys.stdin
        output_stream = stdout or sys.stdout
        raw_input = input_stream.read()
        exit_code, payload = self.handle_raw_json(raw_input)

        try:
            serialized = json.dumps(payload, ensure_ascii=True)
        except (TypeError, ValueError) as exc:
            fallback = self._error_response(
                request_id=str(payload.get("request_id", "")) if isinstance(payload, dict) else "",
                error_type="serialization_failure",
                message=str(exc),
                retryable=False,
            )
            serialized = json.dumps(validate_error_response(fallback), ensure_ascii=True)
            output_stream.write(serialized)
            return 1

        output_stream.write(serialized)
        return exit_code

    @staticmethod
    def _normalize_success_response(
        *,
        request_id: str,
        runtime_result: dict[str, Any],
        kernel_options: dict[str, Any],
        debug_trace: list[str],
    ) -> dict[str, Any]:
        verification_record = runtime_result.get("verification_record") or {}
        baton = runtime_result.get("handoff_baton") or {}
        response = {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "request_id": request_id,
            "status": "ok",
            "final_response": str(runtime_result.get("final_response", "")),
            "baton": dict(baton),
            "session_status_metadata": OpenClawEntrypoint._build_session_status_metadata(runtime_result=runtime_result),
            "snapshot_candidates": [],
            "verification_outcome": {
                "status": str(verification_record.get("verification_status", baton.get("verification_status", "pending"))),
                "observed_outcome": str(runtime_result.get("observed_outcome", "")),
                "record": dict(verification_record),
            },
            "worker_result": {},
            "debug_trace": list(debug_trace) if kernel_options.get("return_debug_trace") else [],
        }

        if kernel_options.get("include_worker_result"):
            response["worker_result"] = dict(runtime_result.get("worker_payload") or {})
        if kernel_options.get("include_snapshot_candidates"):
            response["snapshot_candidates"] = OpenClawEntrypoint._build_snapshot_candidates(runtime_result=runtime_result)

        return response

    @staticmethod
    def _build_session_status_metadata(*, runtime_result: dict[str, Any]) -> dict[str, Any]:
        baton = runtime_result.get("handoff_baton") or {}
        if not isinstance(baton, dict):
            baton = {}

        observed_outcome = str(runtime_result.get("observed_outcome", "")).strip()
        verification_status = str(baton.get("verification_status", "")).strip()
        last_verified_outcomes: list[str] = []
        if observed_outcome and verification_status == "passed":
            last_verified_outcomes.append(observed_outcome)

        next_hint = str(baton.get("next_hint", "")).strip()
        open_loops = baton.get("open_loops", [])
        if not isinstance(open_loops, list):
            open_loops = []

        risk_notes: list[str] = []
        for loop in open_loops:
            if isinstance(loop, str) and loop.startswith("monitor:"):
                risk_notes.append(loop.removeprefix("monitor:"))

        recent_decisions: list[str] = []
        if next_hint:
            recent_decisions.append(next_hint)

        return {
            "current_status": verification_status,
            "primary_focus": str(baton.get("task_focus", "")),
            "open_loops": [str(item) for item in open_loops if isinstance(item, str)],
            "last_verified_outcomes": last_verified_outcomes,
            "recent_decisions": recent_decisions,
            "relevant_entities": [],
            "active_skills": [],
            "risk_notes": risk_notes,
            "next_hint": next_hint,
        }

    @staticmethod
    def _build_snapshot_candidates(*, runtime_result: dict[str, Any]) -> list[dict[str, Any]]:
        baton = runtime_result.get("handoff_baton") or {}
        if not isinstance(baton, dict) or not baton:
            return []
        return [
            {
                "candidate_type": "handoff_baton",
                "task_focus": str(baton.get("task_focus", "")),
                "verification_status": str(baton.get("verification_status", "")),
                "next_hint": str(baton.get("next_hint", "")),
            }
        ]

    @staticmethod
    def _error_response(
        *,
        request_id: str,
        error_type: str,
        message: str,
        retryable: bool,
    ) -> dict[str, Any]:
        return {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "request_id": request_id,
            "status": "error",
            "error": {
                "error_type": error_type,
                "message": message,
                "retryable": retryable,
            },
        }


def main() -> int:
    return OpenClawEntrypoint().main()


if __name__ == "__main__":
    raise SystemExit(main())
