from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


VerificationStatus = Literal["pending", "passed", "failed", "unknown"]

_ALLOWED_STATUSES = {"pending", "passed", "failed", "unknown"}


@dataclass(slots=True)
class ActionIntent:
    intended_action: str
    expected_change: str
    notes: list[str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.intended_action, str) or not self.intended_action.strip():
            raise ValueError("intended_action must be a non-empty string")
        if not isinstance(self.expected_change, str):
            raise TypeError("expected_change must be a string")
        if self.notes is None:
            self.notes = []
        if not isinstance(self.notes, list) or not all(isinstance(item, str) for item in self.notes):
            raise TypeError("notes must be list[str]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ActionExecution:
    executed_action: str = ""
    evidence: list[str] | None = None
    notes: list[str] | None = None
    authoritative_evidence_present: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.executed_action, str):
            raise TypeError("executed_action must be a string")
        if self.evidence is None:
            self.evidence = []
        if self.notes is None:
            self.notes = []
        if not isinstance(self.evidence, list) or not all(isinstance(item, str) for item in self.evidence):
            raise TypeError("evidence must be list[str]")
        if not isinstance(self.notes, list) or not all(isinstance(item, str) for item in self.notes):
            raise TypeError("notes must be list[str]")
        if not isinstance(self.authoritative_evidence_present, bool):
            raise TypeError("authoritative_evidence_present must be a bool")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VerificationRecord:
    intended_action: str
    executed_action: str
    expected_change: str
    observed_outcome: str
    verification_status: VerificationStatus
    evidence: list[str] | None = None
    notes: list[str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.intended_action, str) or not self.intended_action.strip():
            raise ValueError("intended_action must be a non-empty string")
        if not isinstance(self.executed_action, str):
            raise TypeError("executed_action must be a string")
        if not isinstance(self.expected_change, str):
            raise TypeError("expected_change must be a string")
        if not isinstance(self.observed_outcome, str):
            raise TypeError("observed_outcome must be a string")
        if self.verification_status not in _ALLOWED_STATUSES:
            raise ValueError(f"verification_status must be one of: {sorted(_ALLOWED_STATUSES)}")
        if self.evidence is None:
            self.evidence = []
        if self.notes is None:
            self.notes = []
        if not isinstance(self.evidence, list) or not all(isinstance(item, str) for item in self.evidence):
            raise TypeError("evidence must be list[str]")
        if not isinstance(self.notes, list) or not all(isinstance(item, str) for item in self.notes):
            raise TypeError("notes must be list[str]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
