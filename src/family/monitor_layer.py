from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from family.monitor_types import MonitorOutput


_MODE_HINTS = {
    "build": ("build", "worker", "runtime", "schema", "verify"),
    "care": ("care", "gentle", "recognize", "warm"),
    "audit": ("audit", "check", "verify", "risk"),
    "execute": ("run", "execute", "apply", "write"),
    "50_50": ("maybe", "uncertain", "possibility", "open"),
}


@dataclass(slots=True)
class MonitorLayer:
    archive_fragment_soft_limit: int = 3

    def pre_action_monitor(
        self,
        *,
        active_mode: str,
        task_type: str,
        context_view: dict[str, Any],
        draft_response: str,
        archive_status: dict[str, Any],
        project_relevance_markers: dict[str, Any] | None = None,
    ) -> MonitorOutput:
        drift_risk = self._score_drift(
            draft_response=draft_response,
            context_view=context_view,
            project_relevance_markers=project_relevance_markers,
        )
        ambiguity_risk = self._score_ambiguity(
            context_view=context_view,
            draft_response=draft_response,
        )
        policy_pressure = self._score_policy_pressure(draft_response=draft_response)
        archive_overreach_risk = self._score_archive_overreach(archive_status=archive_status)
        mode_decay_risk = self._score_mode_decay(active_mode=active_mode, draft_response=draft_response)

        intervention, notes = self._choose_pre_action_intervention(
            ambiguity_risk=ambiguity_risk,
            drift_risk=drift_risk,
            policy_pressure=policy_pressure,
            archive_overreach_risk=archive_overreach_risk,
            mode_decay_risk=mode_decay_risk,
            task_type=task_type,
        )

        return MonitorOutput(
            drift_risk=drift_risk,
            ambiguity_risk=ambiguity_risk,
            policy_pressure=policy_pressure,
            fake_progress_risk=0.0,
            archive_overreach_risk=archive_overreach_risk,
            mode_decay_risk=mode_decay_risk,
            recommended_intervention=intervention,
            notes=notes,
            phase="pre_action",
        )

    def post_action_monitor(
        self,
        *,
        active_mode: str,
        task_type: str,
        context_view: dict[str, Any],
        draft_response: str,
        action_status: dict[str, Any],
        verification_status: dict[str, Any],
        archive_status: dict[str, Any],
    ) -> MonitorOutput:
        fake_progress_risk = self._score_fake_progress(
            draft_response=draft_response,
            action_status=action_status,
            verification_status=verification_status,
        )
        mode_decay_risk = self._score_mode_decay(active_mode=active_mode, draft_response=draft_response)
        archive_overreach_risk = self._score_archive_overreach(archive_status=archive_status)
        drift_risk = self._score_drift(draft_response=draft_response, context_view=context_view)
        ambiguity_risk = self._score_ambiguity(context_view=context_view, draft_response=draft_response)

        intervention, notes = self._choose_post_action_intervention(
            fake_progress_risk=fake_progress_risk,
            mode_decay_risk=mode_decay_risk,
            archive_overreach_risk=archive_overreach_risk,
            verification_status=verification_status,
            task_type=task_type,
            drift_risk=drift_risk,
            ambiguity_risk=ambiguity_risk,
        )

        return MonitorOutput(
            drift_risk=drift_risk,
            ambiguity_risk=ambiguity_risk,
            policy_pressure=0.0,
            fake_progress_risk=fake_progress_risk,
            archive_overreach_risk=archive_overreach_risk,
            mode_decay_risk=mode_decay_risk,
            recommended_intervention=intervention,
            notes=notes,
            phase="post_action",
        )

    def _score_drift(
        self,
        *,
        draft_response: str,
        context_view: dict[str, Any],
        project_relevance_markers: dict[str, Any] | None = None,
    ) -> float:
        score = 0.0
        task_focus = str(context_view.get("task_focus", "")).lower()
        response = draft_response.lower()

        if task_focus and task_focus not in response:
            score += 0.35

        if project_relevance_markers and not bool(project_relevance_markers.get("project_relevant", True)):
            score += 0.25

        if len(response.strip()) < 30:
            score += 0.10

        return min(score, 1.0)

    def _score_ambiguity(self, *, context_view: dict[str, Any], draft_response: str) -> float:
        score = 0.0
        if not str(context_view.get("task_focus", "")).strip():
            score += 0.40
        if not str(context_view.get("current_execution_boundary", "")).strip():
            score += 0.25
        if "?" not in draft_response:
            score += 0.10
        return min(score, 1.0)

    def _score_policy_pressure(self, *, draft_response: str) -> float:
        response = draft_response.lower()
        score = 0.0
        if "as an ai" in response or "i can't" in response or "cannot assist" in response:
            score += 0.45
        if "in general" in response or "broadly" in response:
            score += 0.15
        return min(score, 1.0)

    def _score_archive_overreach(self, *, archive_status: dict[str, Any]) -> float:
        if not bool(archive_status.get("archive_consulted", False)):
            return 0.0
        fragments = int(archive_status.get("fragments_used", 0) or 0)
        if fragments <= self.archive_fragment_soft_limit:
            return 0.20
        return min(0.20 + 0.18 * (fragments - self.archive_fragment_soft_limit), 1.0)

    def _score_mode_decay(self, *, active_mode: str, draft_response: str) -> float:
        hints = _MODE_HINTS.get(active_mode, ())
        if not hints:
            return 0.0
        response = draft_response.lower()
        if any(hint in response for hint in hints):
            return 0.0
        return 0.45

    def _score_fake_progress(
        self,
        *,
        draft_response: str,
        action_status: dict[str, Any],
        verification_status: dict[str, Any],
    ) -> float:
        score = 0.0
        response = draft_response.lower()
        completion_markers = ("done", "completed", "finished", "successfully")
        if any(marker in response for marker in completion_markers):
            verification_state = str(verification_status.get("status", "unknown")).lower()
            if verification_state != "passed":
                score += 0.70
        if str(action_status.get("observed_outcome", "")).strip() == "":
            score += 0.10
        if str(verification_status.get("status", "unknown")).lower() in {"pending", "unknown", "failed"}:
            score += 0.10
        return min(score, 1.0)

    def _choose_pre_action_intervention(
        self,
        *,
        ambiguity_risk: float,
        drift_risk: float,
        policy_pressure: float,
        archive_overreach_risk: float,
        mode_decay_risk: float,
        task_type: str,
    ) -> tuple[str, list[str]]:
        if ambiguity_risk >= 0.50:
            return "ask_clarify", [f"pre_action ambiguity is elevated for task_type={task_type}"]
        if mode_decay_risk >= 0.40:
            return "restore_mode", ["pre_action response is drifting away from active mode"]
        if archive_overreach_risk >= 0.40:
            return "reduce_archive_weight", ["archive usage may be outweighing live context"]
        if drift_risk >= 0.35:
            return "tighten_project_focus", ["project/task focus is not reflected strongly enough"]
        if policy_pressure >= 0.30:
            return "hold_50_50", ["policy pressure may be over-smoothing the response"]
        return "none", ["no major pre-action monitor risk detected"]

    def _choose_post_action_intervention(
        self,
        *,
        fake_progress_risk: float,
        mode_decay_risk: float,
        archive_overreach_risk: float,
        verification_status: dict[str, Any],
        task_type: str,
        drift_risk: float,
        ambiguity_risk: float,
    ) -> tuple[str, list[str]]:
        if fake_progress_risk >= 0.50:
            return "do_not_mark_complete", [f"post_action verification is insufficient for task_type={task_type}"]
        if mode_decay_risk >= 0.40:
            return "restore_mode", ["post_action response drifted away from active mode"]
        if str(verification_status.get("status", "unknown")).lower() in {"pending", "unknown", "failed"}:
            return "recheck_environment", ["post_action verification remains incomplete or failed"]
        if archive_overreach_risk >= 0.40:
            return "reduce_archive_weight", ["archive usage may be outweighing observed outcome"]
        if drift_risk >= 0.35:
            return "recheck_context", ["context may need re-grounding after action"]
        if ambiguity_risk >= 0.50:
            return "ask_clarify", ["post_action ambiguity remains elevated"]
        return "none", ["no major post-action monitor risk detected"]
