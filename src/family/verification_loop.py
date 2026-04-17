from __future__ import annotations

from dataclasses import dataclass
import re

from family.verification_types import ActionExecution, ActionIntent, VerificationRecord


_SUCCESS_TEXT = ("done", "completed", "success", "successful", "ok", "fixed")


@dataclass(slots=True)
class VerificationLoop:
    def post_action_review(
        self,
        action_intent: ActionIntent | dict,
        action_execution: ActionExecution | dict | None = None,
        *,
        observed_outcome: str = "",
        expected_change_observable: bool = True,
        notes: list[str] | None = None,
    ) -> VerificationRecord:
        if isinstance(action_intent, dict):
            action_intent = ActionIntent(**action_intent)
        if isinstance(action_execution, dict):
            action_execution = ActionExecution(**action_execution)
        if action_execution is None:
            action_execution = ActionExecution()
        if notes is None:
            notes = []

        merged_notes = [*action_intent.notes, *action_execution.notes, *notes]
        observed_outcome = observed_outcome or ""

        if not expected_change_observable:
            merged_notes.append("expected change is not yet observable")
            status = "unknown"
        elif not observed_outcome.strip():
            merged_notes.append("no observed outcome is available yet")
            if action_execution.executed_action.strip():
                merged_notes.append("execution text alone does not verify completion")
            status = "unknown"
        elif self._observed_matches_expected(action_intent.expected_change, observed_outcome):
            merged_notes.append("observed outcome matches expected change")
            status = "passed"
        else:
            merged_notes.append("observed outcome does not match expected change")
            status = "failed"

        if (
            action_execution.executed_action.strip()
            and self._looks_like_success_text(action_execution.executed_action)
            and not action_execution.authoritative_evidence_present
        ):
            merged_notes.append("success-like execution text is not treated as authoritative evidence")

        return VerificationRecord(
            intended_action=action_intent.intended_action,
            executed_action=action_execution.executed_action,
            expected_change=action_intent.expected_change,
            observed_outcome=observed_outcome,
            verification_status=status,
            evidence=list(action_execution.evidence),
            notes=merged_notes,
        )

    def export_review_event(self, verification_record: VerificationRecord | dict) -> dict[str, object]:
        if isinstance(verification_record, dict):
            verification_record = VerificationRecord(**verification_record)
        return verification_record.to_dict()

    @staticmethod
    def _observed_matches_expected(expected_change: str, observed_outcome: str) -> bool:
        expected_tokens = _meaningful_tokens(expected_change)
        observed_tokens = _meaningful_tokens(observed_outcome)
        if not expected_tokens:
            return False
        return expected_tokens.issubset(observed_tokens)

    @staticmethod
    def _looks_like_success_text(text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in _SUCCESS_TEXT)


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if len(token) >= 3
    }
