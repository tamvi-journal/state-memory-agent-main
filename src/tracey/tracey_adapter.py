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
            user_text=user_text,
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
        user_text: str,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None,
        reactivated_anchors: list[dict[str, str]],
    ) -> dict[str, Any]:
        lowered = user_text.strip().lower()
        active_mode = str(live_state.get("active_mode", ""))
        recognition_active = bool(reactivated_anchors)
        monitor_intervention = self._monitor_intervention(monitor_summary)
        build_mode_active = active_mode == "build"
        ambiguity_posture = self._ambiguity_posture(
            user_text=lowered,
            monitor_intervention=monitor_intervention,
        )
        keep_ambiguity_open = ambiguity_posture == "exploratory"
        verification_before_completion = build_mode_active
        search_posture = self._search_posture(
            user_text=lowered,
        )

        tone_constraint = "none"
        if build_mode_active:
            tone_constraint = "build_exact"
        elif ambiguity_posture == "exploratory":
            tone_constraint = "warm_but_exact"
        elif ambiguity_posture == "blocking":
            tone_constraint = "recognition_first"
        elif recognition_active:
            tone_constraint = "recognition_first"

        return {
            "recognition_active": recognition_active,
            "keep_ambiguity_open": keep_ambiguity_open,
            "ambiguity_posture": ambiguity_posture,
            "search_posture": search_posture,
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

    @staticmethod
    def _ambiguity_posture(*, user_text: str, monitor_intervention: str) -> str:
        explicit_precision = any(token in user_text for token in ("clarify", "exactly", "precise", "which one"))
        explicit_verification = any(token in user_text for token in ("verify", "confirm", "search", "look up"))
        blocked_action = (
            ("continue" in user_text and "previous" in user_text)
            or ("which worker" in user_text)
            or ("missing target" in user_text)
        )
        if explicit_precision or explicit_verification or blocked_action or monitor_intervention == "ask_clarify":
            return "blocking"

        exploratory_markers = ("maybe", "could", "might", "consider", "explore", "what if")
        if any(marker in user_text for marker in exploratory_markers):
            return "exploratory"

        return "none"

    @staticmethod
    def _search_posture(*, user_text: str) -> str:
        if any(token in user_text for token in ("verify", "confirm", "search", "look up", "check")):
            return "on_demand"
        if any(token in user_text for token in ("latest", "current", "today", "source", "evidence-bound")):
            return "route_necessary"
        return "none"
