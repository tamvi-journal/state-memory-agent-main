from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from state_memory.contracts import StateMemoryRecord

DEFAULT_STATE_MEMORY_PATH = Path("runtime_state") / "state_memory" / "state_memory.jsonl"


class StateMemoryStore:
    def __init__(self, memory_path: str | Path | None = None) -> None:
        self.memory_path = Path(memory_path) if memory_path is not None else DEFAULT_STATE_MEMORY_PATH

    def append(self, record: StateMemoryRecord | dict[str, Any]) -> bool:
        try:
            normalized = record if isinstance(record, StateMemoryRecord) else StateMemoryRecord.from_dict(record)
            payload = normalized.to_dict()
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            with self.memory_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
            return True
        except (OSError, ValueError, TypeError):
            return False

    def read_all(self) -> list[dict[str, Any]]:
        if not self.memory_path.exists():
            return []
        try:
            lines = self.memory_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        records: list[dict[str, Any]] = []
        for line in lines:
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(loaded, dict):
                records.append(loaded)
        return records

    def read_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        return self.read_all()[-limit:]

    def query(
        self,
        *,
        scope: str | None = None,
        session_id: str | None = None,
        event_type: str | None = None,
        include_inert: bool = False,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        records = self.read_all()
        filtered: list[dict[str, Any]] = []
        for record in records:
            if scope and str(record.get("scope", "")) != scope:
                continue
            if session_id and str(record.get("session_id", "")) != session_id:
                continue
            if event_type and str(record.get("event_type", "")) != event_type:
                continue
            if not include_inert and str(record.get("lifecycle_status", "")) in {"archived", "deprecated", "invalidated"}:
                continue
            filtered.append(record)
        if limit <= 0:
            return filtered
        return filtered[-limit:]

    def append_many(self, records: list[StateMemoryRecord | dict[str, Any]]) -> int:
        count = 0
        for record in records:
            if self.append(record):
                count += 1
        return count
