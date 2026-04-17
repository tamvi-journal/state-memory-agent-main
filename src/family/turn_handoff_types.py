from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class TurnHandoff:
    active_project: str = ""
    active_mode: str = ""
    continuity_anchor: str = ""
    compression_summary: dict[str, Any] | None = None
    verification_status: str = ""
    open_obligations: list[str] | None = None
    shared_disagreement_status: str = "none"
    current_axis: str = ""
    notes: list[str] | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "active_project",
            "active_mode",
            "continuity_anchor",
            "verification_status",
            "shared_disagreement_status",
            "current_axis",
        ):
            if not isinstance(getattr(self, field_name), str):
                raise TypeError(f"{field_name} must be a string")
        if self.compression_summary is None:
            self.compression_summary = {}
        if self.open_obligations is None:
            self.open_obligations = []
        if self.notes is None:
            self.notes = []
        if not isinstance(self.compression_summary, dict):
            raise TypeError("compression_summary must be dict[str, Any] | None")
        if not isinstance(self.open_obligations, list) or not all(isinstance(item, str) for item in self.open_obligations):
            raise TypeError("open_obligations must be list[str]")
        if not isinstance(self.notes, list) or not all(isinstance(item, str) for item in self.notes):
            raise TypeError("notes must be list[str]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
