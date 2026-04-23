from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .payload_contracts import OpenClawRequestContract


@dataclass(slots=True)
class PayloadAdapter:
    def build_internal_invocation(
        self,
        request: OpenClawRequestContract,
    ) -> dict[str, Any]:
        session = dict(request.session)
        host_metadata = self._normalize_host_metadata(request.host_metadata)
        kernel_options = self._normalize_kernel_options(request.kernel_options)
        rehydration_pack = self._build_rehydration_pack(session=session)

        return {
            "request_id": request.request_id,
            "request_text": request.request_text,
            "rehydration_pack": rehydration_pack,
            "host_metadata": host_metadata,
            "kernel_options": kernel_options,
        }

    @staticmethod
    def _build_rehydration_pack(*, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": str(session.get("session_id", "")),
            "session_kind": str(session.get("session_kind", "")),
            "session_title": str(session.get("session_title", "")),
            "primary_focus": str(session.get("primary_focus", "")),
            "current_status": str(session.get("current_status", "")),
            "open_loops": PayloadAdapter._coerce_str_list(session.get("open_loops", [])),
            "last_verified_outcomes": PayloadAdapter._coerce_dict_list(session.get("last_verified_outcomes", [])),
            "recent_decisions": PayloadAdapter._coerce_dict_list(session.get("recent_decisions", [])),
            "relevant_entities": PayloadAdapter._coerce_str_list(session.get("relevant_entities", [])),
            "active_skills": PayloadAdapter._coerce_str_list(session.get("active_skills", [])),
            "risk_notes": PayloadAdapter._coerce_str_list(session.get("risk_notes", [])),
            "next_hint": str(session.get("next_hint", "")),
        }

    @staticmethod
    def _normalize_host_metadata(host_metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "channel": str(host_metadata.get("channel", "")),
            "thread_id": str(host_metadata.get("thread_id", "")),
            "route": str(host_metadata.get("route", "")),
            "user_scope": str(host_metadata.get("user_scope", "")),
            "host_message_id": str(host_metadata.get("host_message_id", "")),
        }

    @staticmethod
    def _normalize_kernel_options(kernel_options: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": str(kernel_options.get("mode", "default")),
            "allow_tool_paths": bool(kernel_options.get("allow_tool_paths", True)),
            "return_debug_trace": bool(kernel_options.get("return_debug_trace", False)),
            "include_worker_result": bool(kernel_options.get("include_worker_result", True)),
            "include_snapshot_candidates": bool(kernel_options.get("include_snapshot_candidates", True)),
        }

    @staticmethod
    def _coerce_str_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item)]

    @staticmethod
    def _coerce_dict_list(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [dict(item) for item in value if isinstance(item, dict)]
