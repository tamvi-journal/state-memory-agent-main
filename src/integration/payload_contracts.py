from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CONTRACT_SCHEMA_VERSION = "openclaw-state-agent/v0.1"
SUPPORTED_SCHEMA_VERSIONS = {CONTRACT_SCHEMA_VERSION}
ALLOWED_RESPONSE_STATUS = {"ok", "error"}
ALLOWED_ERROR_TYPES = {
    "invalid_payload",
    "entrypoint_failure",
    "runtime_failure",
    "serialization_failure",
}


class ContractValidationError(ValueError):
    def __init__(self, message: str, *, request_id: str = "") -> None:
        super().__init__(message)
        self.request_id = request_id


@dataclass(slots=True)
class OpenClawRequestContract:
    schema_version: str
    request_id: str
    request_text: str
    session: dict[str, Any] = field(default_factory=dict)
    host_metadata: dict[str, Any] = field(default_factory=dict)
    kernel_options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "request_text": self.request_text,
            "session": dict(self.session),
            "host_metadata": dict(self.host_metadata),
            "kernel_options": dict(self.kernel_options),
        }


def validate_request_payload(payload: Any) -> OpenClawRequestContract:
    if not isinstance(payload, dict):
        raise ContractValidationError("request payload must be a JSON object")

    schema_version = payload.get("schema_version")
    request_id = payload.get("request_id", "")
    request_text = payload.get("request_text")
    session = payload.get("session", {})
    host_metadata = payload.get("host_metadata", {})
    kernel_options = payload.get("kernel_options", {})

    if not isinstance(schema_version, str) or schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ContractValidationError(
            f"unsupported schema_version={schema_version!r}",
            request_id=str(request_id) if isinstance(request_id, str) else "",
        )
    if not isinstance(request_id, str) or not request_id.strip():
        raise ContractValidationError("request_id must be a non-empty string")
    if not isinstance(request_text, str) or not request_text.strip():
        raise ContractValidationError("request_text must be a non-empty string", request_id=request_id)
    if session is None:
        session = {}
    if host_metadata is None:
        host_metadata = {}
    if kernel_options is None:
        kernel_options = {}
    if not isinstance(session, dict):
        raise ContractValidationError("session must be an object", request_id=request_id)
    if not isinstance(host_metadata, dict):
        raise ContractValidationError("host_metadata must be an object", request_id=request_id)
    if not isinstance(kernel_options, dict):
        raise ContractValidationError("kernel_options must be an object", request_id=request_id)

    return OpenClawRequestContract(
        schema_version=schema_version,
        request_id=request_id.strip(),
        request_text=request_text.strip(),
        session=session,
        host_metadata=host_metadata,
        kernel_options=kernel_options,
    )


def validate_success_response(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ContractValidationError("response payload must be an object")

    required_fields = {
        "schema_version",
        "request_id",
        "status",
        "final_response",
        "baton",
        "verification_outcome",
    }
    missing = required_fields - set(payload.keys())
    if missing:
        raise ContractValidationError(f"success response missing fields: {sorted(missing)}")

    if payload.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        raise ContractValidationError("success response has unsupported schema_version")
    if payload.get("status") != "ok":
        raise ContractValidationError("success response status must be 'ok'")
    if not isinstance(payload.get("request_id"), str):
        raise ContractValidationError("success response request_id must be string")
    if not isinstance(payload.get("final_response"), str):
        raise ContractValidationError("success response final_response must be string")
    if not isinstance(payload.get("baton"), dict):
        raise ContractValidationError("success response baton must be object")
    if not isinstance(payload.get("verification_outcome"), dict):
        raise ContractValidationError("success response verification_outcome must be object")
    if "status" not in payload["verification_outcome"]:
        raise ContractValidationError("verification_outcome must include status")
    if not isinstance(payload["verification_outcome"]["status"], str):
        raise ContractValidationError("verification_outcome.status must be string")

    optional_object_fields = {"session_status_metadata", "worker_result"}
    optional_list_fields = {"snapshot_candidates", "debug_trace"}
    for field_name in optional_object_fields:
        if field_name in payload and not isinstance(payload[field_name], dict):
            raise ContractValidationError(f"{field_name} must be an object")
    for field_name in optional_list_fields:
        if field_name in payload and not isinstance(payload[field_name], list):
            raise ContractValidationError(f"{field_name} must be a list")

    return payload


def validate_error_response(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ContractValidationError("error response payload must be an object")

    required_fields = {"schema_version", "request_id", "status", "error"}
    missing = required_fields - set(payload.keys())
    if missing:
        raise ContractValidationError(f"error response missing fields: {sorted(missing)}")
    if payload.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        raise ContractValidationError("error response has unsupported schema_version")
    if payload.get("status") != "error":
        raise ContractValidationError("error response status must be 'error'")
    if not isinstance(payload.get("request_id"), str):
        raise ContractValidationError("error response request_id must be string")
    error = payload.get("error")
    if not isinstance(error, dict):
        raise ContractValidationError("error response error must be an object")
    if error.get("error_type") not in ALLOWED_ERROR_TYPES:
        raise ContractValidationError("error.error_type is invalid")
    if not isinstance(error.get("message"), str):
        raise ContractValidationError("error.message must be string")
    if not isinstance(error.get("retryable"), bool):
        raise ContractValidationError("error.retryable must be bool")

    return payload
