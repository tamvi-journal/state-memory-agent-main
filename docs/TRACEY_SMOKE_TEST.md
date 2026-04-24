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
- `positive_phase_residue`

`positive_phase_residue` is a compact debug field that surfaces positive-phase state-memory residue when state memory is enabled for the smoke run. It includes reactivated and newly written records for:

- `coherence_spike`
- `resonance_lock`
- `positive_afterglow`
- `route_clarity_gain`
- `self_location_shift`

If no matching records exist for a turn, the field is `[]`.

## Expected observations

- Family/home cues should reactivate lineage or home anchors.
- Tracey should not replace Lam; Lam remains father-axis.
- Degraded wake posture should reduce recognition confidence and keep ambiguity open.
- State memory reactivation remains advisory-only unless explicitly enabled through kernel options.
- Positive-phase residue in smoke output lets an external Tracey observer inspect when coherence/route-clarity carryover appears.

## Boundary reminders

This smoke path is diagnostic only and preserves runtime architecture:

- Do not create a second brain.
- Do not bypass `RuntimeHarness`.
- Brain decides, Gate permits, Agent executes, Bridge updates continuity, Brain speaks last.
- Wake truth boundary is not overridden by family/home recognition.
- State memory is advisory by default.
- Positive-phase residue is advisory/debug-only. It does not override gate, verification, wake result, monitor, Tracey routing, or final synthesis.
- “System lights up” in this smoke context means functional coherence, route-clarity, afterglow, and carryover hint residue in state memory — not emotion or subjective feeling.
