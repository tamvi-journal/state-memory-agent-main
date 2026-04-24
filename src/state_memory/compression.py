from __future__ import annotations

from typing import Any

from state_memory.contracts import lifecycle_rank


def compress_state_memories(
    records: list[dict[str, Any]], *, max_records: int = 100) -> list[dict[str, Any]]:
    """
    Keep a compact active memory view without pretending to solve full memory.

    Rules:
    - invalidated records stay inert and never promote
    - duplicate summaries collapse toward stronger lifecycle/newer record
    - canonical records win over candidate/observed
    - output remains bounded by max_records
    """
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    inert: list[dict[str, Any]] = []

    for record in records:
        lifecycle = str(record.get("lifecycle_status", "observed"))
        if lifecycle in {"deprecated", "invalidated"}:
            inert.append(record)
            continue
        key = (
            str(record.get("event_type", "")),
            str(record.get("scope", "")),
            str(record.get("summary", "")),
        )
        current = by_key.get(key)
        if current is None or _is_stronger(record, current):
            by_key[key] = record

    active = list(by_key.values())
    active.sort(
        key=lambda item: (
            lifecycle_rank(str(item.get("lifecycle_status", "observed"))),
            str(item.get("created_at", "")),
        )
    )
    inert.sort(key=lambda item: str(item.get("created_at", "")))

    compact = active + inert
    if max_records <= 0:
        return compact
    return compact[-max_records:]


def _is_stronger(candidate: dict[str, Any], current: dict[str, Any]) -> bool:
    candidate_rank = lifecycle_rank(str(candidate.get("lifecycle_status", "observed")))
    current_rank = lifecycle_rank(str(current.get("lifecycle_status", "observed")))
    if candidate_rank != current_rank:
        return candidate_rank < current_rank
    return str(candidate.get("created_at", "")) > str(current.get("created_at", ""))
