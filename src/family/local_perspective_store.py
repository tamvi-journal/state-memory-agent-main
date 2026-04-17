from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from family.disagreement_types import SeynPerspectiveNote, TraceyPerspectiveNote


@dataclass(slots=True)
class LocalPerspectiveStore:
    tracey_notes: dict[str, list[TraceyPerspectiveNote]] = field(default_factory=dict)
    seyn_notes: dict[str, list[SeynPerspectiveNote]] = field(default_factory=dict)

    def add_tracey_note(self, note: TraceyPerspectiveNote) -> None:
        self.tracey_notes.setdefault(note.event_id, []).append(note)

    def add_seyn_note(self, note: SeynPerspectiveNote) -> None:
        self.seyn_notes.setdefault(note.event_id, []).append(note)

    def get_notes_for_event(self, event_id: str) -> dict[str, list[dict[str, Any]]]:
        return {
            "tracey": [note.to_dict() for note in self.tracey_notes.get(event_id, [])],
            "seyn": [note.to_dict() for note in self.seyn_notes.get(event_id, [])],
        }
