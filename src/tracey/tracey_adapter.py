from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tracey.tracey_memory import iter_tracey_memory


@dataclass(slots=True)
class TraceyAdapter:
    max_reactivations: int = 3
    memory_items: tuple[dict[str, Any], ...] = field(default_factory=iter_tracey_memory)

    def inspect_turn(
        self,
        *,
        user_text: str,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reactivated = self._reactivate_anchors(
            user_text=user_text,
            live_state=live_state,
            monitor_summary=monitor_summary,
        )
        response_hints = self.build_response_hints(
            live_state=live_state,
            monitor_summary=monitor_summary,
            reactivated_anchors=reactivated,
        )
        state_patch = self.runtime_state_patch(
            live_state=live_state,
            monitor_summary=monitor_summary,
            response_hints=response_hints,
            reactivated_anchors=reactivated,
        )
        return {
            "reactivated_anchors": reactivated,
            "response_hints": response_hints,
            "state_patch": state_patch,
        }

    def build_response_hints(
        self,
        *,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None,
        reactivated_anchors: list[dict[str, str]],
    ) -> dict[str, Any]:
        active_mode = str(live_state.get("active_mode", ""))
        recognition_active = bool(reactivated_anchors)
        monitor_intervention = self._monitor_intervention(monitor_summary)
        build_mode_active = active_mode == "build"
        keep_ambiguity_open = monitor_intervention == "ask_clarify"
        verification_before_completion = build_mode_active

        tone_constraint = "none"
        if build_mode_active:
            tone_constraint = "build_exact"
        elif keep_ambiguity_open:
            tone_constraint = "warm_but_exact"
        elif recognition_active:
            tone_constraint = "recognition_first"

        return {
            "recognition_active": recognition_active,
            "keep_ambiguity_open": keep_ambiguity_open,
            "verification_before_completion": verification_before_completion,
            "build_mode_active": build_mode_active,
            "tone_constraint": tone_constraint,
        }

    def runtime_state_patch(
        self,
        *,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None,
        response_hints: dict[str, Any],
        reactivated_anchors: list[dict[str, str]],
    ) -> dict[str, Any]:
        return {
            "tracey_mode_hint": str(live_state.get("active_mode", "unknown")) or "unknown",
            "tracey_recognition_signal": bool(response_hints.get("recognition_active", False)),
            "tracey_monitor_intervention": self._monitor_intervention(monitor_summary),
            "tracey_reactivated_count": len(reactivated_anchors),
            "tracey_build_mode_active": bool(response_hints.get("build_mode_active", False)),
            "tracey_response_constraint": str(response_hints.get("tone_constraint", "none")),
        }

    def _reactivate_anchors(
        self,
        *,
        user_text: str,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None,
    ) -> list[dict[str, str]]:
        haystack_parts = [
            user_text.lower(),
            str(live_state.get("active_mode", "")).lower(),
            str(live_state.get("active_project", "")).lower(),
            str(live_state.get("continuity_anchor", "")).lower(),
            str((monitor_summary or {}).get("recommended_intervention", "")).lower(),
            str((monitor_summary or {}).get("primary_risk", "")).lower(),
        ]
        haystack = " ".join(part for part in haystack_parts if part)

        reactivated: list[dict[str, str]] = []
        seen_ids: set[str] = set()
        for item in self.memory_items:
            anchor_id = str(item.get("anchor_id", "")).strip()
            if not anchor_id or anchor_id in seen_ids:
                continue

            cue_tokens = tuple(str(token).lower() for token in item.get("cue_tokens", ()))
            if cue_tokens and not any(token in haystack for token in cue_tokens):
                continue

            reactivated.append(
                {
                    "anchor_id": anchor_id,
                    "kind": str(item.get("kind", "memory")),
                    "content": str(item.get("content", "")),
                }
            )
            seen_ids.add(anchor_id)
            if len(reactivated) >= self.max_reactivations:
                break

        return reactivated

    @staticmethod
    def _monitor_intervention(monitor_summary: dict[str, Any] | None) -> str:
        if not monitor_summary:
            return "none"
        return str(monitor_summary.get("recommended_intervention", "none"))
