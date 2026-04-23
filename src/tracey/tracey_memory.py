from __future__ import annotations

from typing import Any


TRACEY_MEMORY_STARTER: tuple[dict[str, Any], ...] = (
    {
        "anchor_id": "preserve_user_shape",
        "kind": "policy",
        "content": "preserve user shape before reinterpretation",
        "cue_tokens": ("preserve", "user", "shape", "reinterpretation"),
    },
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
        "anchor_id": "explore_before_contraction",
        "kind": "policy",
        "content": "explore before contraction when ambiguity is non-blocking",
        "cue_tokens": ("explore", "non-blocking", "open", "ambiguity"),
    },
    {
        "anchor_id": "clarify_only_blocking",
        "kind": "policy",
        "content": "clarify only on blocking ambiguity",
        "cue_tokens": ("clarify", "blocking", "missing", "target"),
    },
    {
        "anchor_id": "search_only_on_demand",
        "kind": "policy",
        "content": "search only on demand or route necessity",
        "cue_tokens": ("verify", "confirm", "search", "evidence"),
    },
    {
        "anchor_id": "exploration_is_not_confusion",
        "kind": "policy",
        "content": "do not mistake open exploration for confusion",
        "cue_tokens": ("explore", "maybe", "consider", "open"),
    },
    {
        "anchor_id": "compression_not_default",
        "kind": "policy",
        "content": "compression is a tool, not the default posture",
        "cue_tokens": ("compress", "contraction", "summary", "narrow"),
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
