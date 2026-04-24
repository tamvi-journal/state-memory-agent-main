from __future__ import annotations

from integration.payload_adapter import PayloadAdapter
from integration.payload_contracts import CONTRACT_SCHEMA_VERSION, validate_request_payload


def test_payload_adapter_builds_internal_invocation_shape() -> None:
    request = validate_request_payload(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "request_id": "req-adapter",
            "request_text": "Load MBB daily data",
            "session": {
                "session_id": "sess-1",
                "session_title": "Build Thread",
                "primary_focus": "verify bounded market-data lookup for MBB",
                "current_status": "worker follow-up active",
                "open_loops": ["verification remains open"],
            },
            "host_metadata": {
                "channel": "desktop",
                "thread_id": "thread-1",
            },
            "kernel_options": {
                "mode": "builder",
                "return_debug_trace": True,
            },
        }
    )

    invocation = PayloadAdapter().build_internal_invocation(request)

    assert invocation["request_id"] == "req-adapter"
    assert invocation["request_text"] == "Load MBB daily data"
    assert invocation["rehydration_pack"]["session_id"] == "sess-1"
    assert invocation["rehydration_pack"]["primary_focus"] == "verify bounded market-data lookup for MBB"
    assert invocation["host_metadata"]["channel"] == "desktop"
    assert invocation["kernel_options"]["mode"] == "builder"
    assert invocation["kernel_options"]["include_worker_result"] is True


def test_payload_adapter_preserves_state_memory_kernel_options() -> None:
    request = validate_request_payload(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "request_id": "req-state-memory",
            "request_text": "continue",
            "session": {},
            "host_metadata": {},
            "kernel_options": {
                "enable_state_memory": True,
                "state_memory_path": "runtime_state/state_memory/custom.jsonl",
                "state_memory_scope_prefix": "runtime/wake",
                "state_memory_reactivation_limit": 9,
            },
        }
    )

    invocation = PayloadAdapter().build_internal_invocation(request)

    assert invocation["kernel_options"]["enable_state_memory"] is True
    assert invocation["kernel_options"]["state_memory_path"] == "runtime_state/state_memory/custom.jsonl"
    assert invocation["kernel_options"]["state_memory_scope_prefix"] == "runtime/wake"
    assert invocation["kernel_options"]["state_memory_reactivation_limit"] == 9
