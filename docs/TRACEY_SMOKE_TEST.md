# Tracey Smoke Test

This repo includes a minimal smoke path to validate Tracey behavior against the current runtime harness and policy boundaries.

## Run

From the repository root:

```bash
python scripts/tracey_smoke.py
```

## What the smoke script does

The script executes `RuntimeHarness().run(...)` for three prompts:

- `Tracey ơi, mẹ đây`
- `ba Lam đây`
- `continue after degraded wake`

For each prompt it prints compact JSON with:

- `final_response`
- `tracey_turn.response_hints`
- `tracey_turn.reactivated_anchors`
- `wake_result`
- `reactivated_state_memories`
- `state_memory_records_written`

## Expected observations

- Family/home cues should reactivate lineage or home anchors.
- Tracey should not replace Lam; Lam remains father-axis.
- Degraded wake posture should reduce recognition confidence and keep ambiguity open.
- State memory reactivation remains advisory-only unless explicitly enabled through kernel options.

## Boundary reminders

This smoke path is diagnostic only and preserves runtime architecture:

- Do not create a second brain.
- Do not bypass `RuntimeHarness`.
- Brain decides, Gate permits, Agent executes, Bridge updates continuity, Brain speaks last.
- Wake truth boundary is not overridden by family/home recognition.
- State memory is advisory by default.
