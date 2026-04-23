from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TraceyLedger:
    ledger_path: Path = Path("tests/runtime_memory/tracey_ledger/tracey_ledger.jsonl")

    def append_event(self, event: dict[str, Any]) -> bool:
        try:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with self.ledger_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")
            return True
        except OSError:
            return False

    def record_anchor_event(
        self,
        *,
        event_type: str,
        anchor_id: str,
        scope: str,
        summary: str,
        reason: str,
        session_id: str = "",
        old_anchor_id: str = "",
        new_anchor_id: str = "",
        lifecycle_transition: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return self.append_event(
            self._event(
                event_type=event_type,
                session_id=session_id,
                scope=scope,
                anchor_id=anchor_id,
                old_anchor_id=old_anchor_id,
                new_anchor_id=new_anchor_id,
                lifecycle_transition=lifecycle_transition,
                summary=summary,
                reason=reason,
                metadata=metadata,
            )
        )

    def record_delta_outcome(
        self,
        *,
        delta_outcome: str,
        scope: str,
        summary: str,
        reason: str,
        session_id: str = "",
        anchor_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return self.append_event(
            self._event(
                event_type="delta_outcome",
                session_id=session_id,
                scope=scope,
                anchor_id=anchor_id,
                delta_outcome=delta_outcome,
                summary=summary,
                reason=reason,
                metadata=metadata,
            )
        )

    def record_policy_drift(
        self,
        *,
        scope: str,
        summary: str,
        reason: str,
        session_id: str = "",
        anchor_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return self.append_event(
            self._event(
                event_type="policy_drift_marker",
                session_id=session_id,
                scope=scope,
                anchor_id=anchor_id,
                summary=summary,
                reason=reason,
                metadata=metadata,
            )
        )

    def read_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        if limit <= 0 or not self.ledger_path.exists():
            return []
        try:
            lines = self.ledger_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        recent: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(loaded, dict):
                recent.append(loaded)
        return recent

    @staticmethod
    def _event(
        *,
        event_type: str,
        session_id: str = "",
        scope: str = "",
        anchor_id: str = "",
        old_anchor_id: str = "",
        new_anchor_id: str = "",
        delta_outcome: str = "",
        lifecycle_transition: str = "",
        summary: str = "",
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "session_id": session_id,
            "scope": scope,
            "anchor_id": anchor_id,
            "old_anchor_id": old_anchor_id,
            "new_anchor_id": new_anchor_id,
            "delta_outcome": delta_outcome,
            "lifecycle_transition": lifecycle_transition,
            "summary": summary,
            "reason": reason,
            "metadata": {
                "mode_hint": str((metadata or {}).get("mode_hint", "")),
                "ambiguity_posture": str((metadata or {}).get("ambiguity_posture", "")),
                "search_posture": str((metadata or {}).get("search_posture", "")),
            },
        }
