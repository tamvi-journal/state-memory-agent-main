from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tracey.tracey_ledger import TraceyLedger
from tracey.tracey_memory import iter_tracey_memory


@dataclass(slots=True)
class TraceyAdapter:
    max_reactivations: int = 3
    ledger: TraceyLedger = field(default_factory=TraceyLedger)
    memory_items: tuple[dict[str, Any], ...] = field(default_factory=iter_tracey_memory)

    def inspect_turn(
        self,
        *,
        user_text: str,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None = None,
        wake_hints: dict[str, Any] | None = None,
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
            wake_hints=wake_hints,
        )
        state_patch = self.runtime_state_patch(
            live_state=live_state,
            monitor_summary=monitor_summary,
            response_hints=response_hints,
            reactivated_anchors=reactivated,
            wake_hints=wake_hints,
        )
        self._record_ledger_events(
            live_state=live_state,
            monitor_summary=monitor_summary,
            reactivated_anchors=reactivated,
            response_hints=response_hints,
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
        wake_hints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        lowered = user_text.strip().lower()
        active_mode = str(live_state.get("active_mode", ""))
        wake_guidance = self._wake_guidance(wake_hints)
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

        if wake_guidance["resume_class"] == "degraded_resume":
            recognition_active = False
            keep_ambiguity_open = True
            ambiguity_posture = "exploratory"

        if wake_guidance["resume_class"] == "clarify_first":
            recognition_active = False
            keep_ambiguity_open = True
            ambiguity_posture = "blocking"

        if wake_guidance["resume_class"] == "blocked":
            recognition_active = False
            keep_ambiguity_open = False
            ambiguity_posture = "blocking"

        tone_constraint = "none"
        if wake_guidance["resume_class"] == "blocked":
            tone_constraint = "wake_blocked"
        elif wake_guidance["resume_class"] == "clarify_first":
            tone_constraint = "wake_clarify_first"
        elif wake_guidance["resume_class"] == "degraded_resume":
            tone_constraint = "wake_degraded"
        elif build_mode_active:
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
            "wake_resume_class": wake_guidance["resume_class"],
            "wake_constraints_active": wake_guidance["wake_constraints_active"],
            "requires_revalidation": wake_guidance["requires_revalidation"],
            "forbidden_claims": wake_guidance["forbidden_claims"],
        }

    def runtime_state_patch(
        self,
        *,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None,
        response_hints: dict[str, Any],
        reactivated_anchors: list[dict[str, str]],
        wake_hints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        wake_guidance = self._wake_guidance(wake_hints)
        return {
            "tracey_mode_hint": str(live_state.get("active_mode", "unknown")) or "unknown",
            "tracey_recognition_signal": bool(response_hints.get("recognition_active", False)),
            "tracey_monitor_intervention": self._monitor_intervention(monitor_summary),
            "tracey_reactivated_count": len(reactivated_anchors),
            "tracey_build_mode_active": bool(response_hints.get("build_mode_active", False)),
            "tracey_response_constraint": str(response_hints.get("tone_constraint", "none")),
            "tracey_wake_resume_class": wake_guidance["resume_class"],
            "tracey_wake_constraints_active": wake_guidance["wake_constraints_active"],
            "tracey_wake_requires_revalidation": wake_guidance["requires_revalidation"],
            "tracey_wake_forbidden_claims": wake_guidance["forbidden_claims"],
        }

    @staticmethod
    def _wake_guidance(wake_hints: dict[str, Any] | None) -> dict[str, Any]:
        hints = dict(wake_hints or {})
        resume_class = str(hints.get("resume_class", "full_resume"))
        constraints_active = bool(hints.get("wake_constraints_active", resume_class != "full_resume"))
        return {
            "resume_class": resume_class,
            "wake_constraints_active": constraints_active,
            "requires_revalidation": list(hints.get("requires_revalidation", [])),
            "forbidden_claims": list(hints.get("forbidden_claims", [])),
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

    def _record_ledger_events(
        self,
        *,
        live_state: dict[str, Any],
        monitor_summary: dict[str, Any] | None,
        reactivated_anchors: list[dict[str, str]],
        response_hints: dict[str, Any],
    ) -> None:
        scope = self._ledger_scope(live_state)
        session_id = str(live_state.get("session_id", ""))
        metadata = self._ledger_metadata(live_state=live_state, response_hints=response_hints)

        try:
            for anchor in reactivated_anchors:
                self.ledger.record_anchor_event(
                    event_type="anchor_reactivated",
                    session_id=session_id,
                    scope=scope,
                    anchor_id=str(anchor.get("anchor_id", "")),
                    lifecycle_transition="active_turn_reactivation",
                    summary=f"Anchor {anchor.get('anchor_id', '')} reactivated for current turn.",
                    reason="cue-triggered reactivation matched current turn context",
                    metadata=metadata,
                )

            delta_outcome = self._delta_outcome(
                monitor_summary=monitor_summary,
                reactivated_anchors=reactivated_anchors,
                response_hints=response_hints,
            )
            if delta_outcome != "none":
                self.ledger.record_delta_outcome(
                    session_id=session_id,
                    scope=scope,
                    anchor_id=str(reactivated_anchors[0].get("anchor_id", "")) if reactivated_anchors else "",
                    delta_outcome=delta_outcome,
                    summary=f"Tracey delta outcome recorded as {delta_outcome}.",
                    reason=self._delta_reason(delta_outcome=delta_outcome, response_hints=response_hints),
                    metadata=metadata,
                )
            elif not reactivated_anchors:
                self.ledger.record_anchor_event(
                    event_type="duplicate_suppressed",
                    session_id=session_id,
                    scope=scope,
                    anchor_id="",
                    lifecycle_transition="no_meaningful_delta",
                    summary="No meaningful Tracey memory delta was recorded for this turn.",
                    reason="no anchors reactivated and no meaningful delta outcome detected",
                    metadata=metadata,
                )

            drift_marker = str((monitor_summary or {}).get("tracey_policy_drift_marker", "")).strip()
            if drift_marker:
                self.ledger.record_policy_drift(
                    session_id=session_id,
                    scope=scope,
                    summary=f"Tracey policy drift marker recorded: {drift_marker}.",
                    reason="thin advisory drift marker provided by runtime context",
                    metadata=metadata,
                )
        except Exception:
            return

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

    @staticmethod
    def _ledger_scope(live_state: dict[str, Any]) -> str:
        active_mode = str(live_state.get("active_mode", "")).strip().lower()
        if active_mode == "build":
            return "tracey/build"
        if active_mode == "paper":
            return "tracey/runtime"
        if active_mode:
            return f"tracey/{active_mode}"
        return "tracey/global"

    @staticmethod
    def _ledger_metadata(*, live_state: dict[str, Any], response_hints: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode_hint": str(live_state.get("active_mode", "")),
            "ambiguity_posture": str(response_hints.get("ambiguity_posture", "")),
            "search_posture": str(response_hints.get("search_posture", "")),
        }

    @staticmethod
    def _delta_outcome(
        *,
        monitor_summary: dict[str, Any] | None,
        reactivated_anchors: list[dict[str, str]],
        response_hints: dict[str, Any],
    ) -> str:
        if bool((monitor_summary or {}).get("tracey_resurrection_risk_detected", False)):
            return "resurrection_risk"
        if str(response_hints.get("ambiguity_posture", "")) == "blocking":
            return "clarifying"
        if reactivated_anchors:
            return "structural"
        return "none"

    @staticmethod
    def _delta_reason(*, delta_outcome: str, response_hints: dict[str, Any]) -> str:
        if delta_outcome == "resurrection_risk":
            return "explicit resurrection-risk marker detected in runtime context"
        if delta_outcome == "clarifying":
            return "blocking ambiguity created a clarification-relevant delta"
        if delta_outcome == "structural":
            return "reactivated anchors changed active memory posture for the turn"
        return "no meaningful Tracey delta detected"
