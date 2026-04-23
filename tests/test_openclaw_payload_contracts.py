from __future__ import annotations

from integration.payload_contracts import (
    CONTRACT_SCHEMA_VERSION,
    ContractValidationError,
    validate_error_response,
    validate_request_payload,
    validate_success_response,
)


def test_validate_request_payload_accepts_minimal_request() -> None:
    request = validate_request_payload(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "request_id": "req-1",
            "request_text": "hello there",
        }
    )

    assert request.request_id == "req-1"
    assert request.request_text == "hello there"
    assert request.session == {}


def test_validate_request_payload_rejects_missing_request_text() -> None:
    try:
        validate_request_payload(
            {
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "request_id": "req-2",
            }
        )
    except ContractValidationError as exc:
        assert "request_text" in str(exc)
    else:
        raise AssertionError("expected ContractValidationError")


def test_validate_success_response_requires_verification_outcome() -> None:
    payload = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "request_id": "req-3",
        "status": "ok",
        "final_response": "done",
        "baton": {},
        "verification_outcome": {"status": "failed"},
    }

    assert validate_success_response(payload)["status"] == "ok"


def test_validate_error_response_accepts_contract_error_shape() -> None:
    payload = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "request_id": "req-4",
        "status": "error",
        "error": {
            "error_type": "invalid_payload",
            "message": "bad request",
            "retryable": False,
        },
    }

    assert validate_error_response(payload)["status"] == "error"
