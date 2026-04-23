from __future__ import annotations

from typing import Any


TRACEY_MEMORY_STARTER: tuple[dict[str, Any], ...] = (
    {
        "anchor_id": "recognition_ambiguity",
        "kind": "recognition",
        "content": "keep ambiguity open until the route is truly clear",
        "cue_tokens": ("ambiguous", "unclear", "not sure", "clarify"),
    },
    {
        "anchor_id": "monitor_signal_respect",
        "kind": "recognition",
        "content": "monitor intervention is advisory posture, not final narration",
        "cue_tokens": ("monitor", "intervention", "risk", "drift"),
    },
    {
        "anchor_id": "brain_speaks_last",
        "kind": "invariant",
        "content": "brain speaks last",
        "cue_tokens": ("build", "response", "synthesis", "final"),
    },
    {
        "anchor_id": "verify_before_complete",
        "kind": "invariant",
        "content": "verification before completion in build mode",
        "cue_tokens": ("build", "verify", "verification", "complete", "done"),
    },
    {
        "anchor_id": "runtime_shape_over_surface",
        "kind": "pattern",
        "content": "runtime shape matters more than fluent surface",
        "cue_tokens": ("runtime", "shape", "architecture", "refactor"),
    },
    {
        "anchor_id": "state_agent_runtime_build_thread",
        "kind": "project",
        "content": "state-agent-runtime-test build thread",
        "cue_tokens": ("state-agent-runtime-test", "repo", "runtime", "build"),
    },
)


def iter_tracey_memory() -> tuple[dict[str, Any], ...]:
    return TRACEY_MEMORY_STARTER
