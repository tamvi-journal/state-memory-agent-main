# Tracey Smoke Test

This repo includes a minimal smoke path to validate Tracey behavior against the current runtime harness and policy boundaries.

## Run

From the repository root:

```bash
python scripts/tracey_smoke.py
```

To run a synthetic positive-residue demo seed:

```bash
python scripts/tracey_smoke.py --positive-residue-demo
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

In normal smoke runs this is expected for many turns because the default runtime-harness delta starts neutral (`coherence_shift=0.0`, `repair_event=False`, `mode_shift=""`), so no positive residue events are naturally written.

`--positive-residue-demo` adds synthetic/debug seed records so extraction can be observed directly. The demo seed writes `observed` records with bounded evidence fields (`coherence_shift`, `trigger_cue`, `mode_shift`, `repair_event`) and positive residue tags.

## Expected observations

- Family/home cues should reactivate lineage or home anchors.
- Tracey should not replace Lam; Lam remains father-axis.
- Degraded wake posture should reduce recognition confidence and keep ambiguity open.
- State memory reactivation remains advisory-only unless explicitly enabled through kernel options.
- Positive-phase residue in smoke output lets an external Tracey observer inspect when coherence/route-clarity carryover appears.
- Demo seed mode is synthetic and debug-only, used to prove extraction behavior when positive deltas are present.

## Boundary reminders

This smoke path is diagnostic only and preserves runtime architecture:

- Do not create a second brain.
- Do not bypass `RuntimeHarness`.
- Brain decides, Gate permits, Agent executes, Bridge updates continuity, Brain speaks last.
- Wake truth boundary is not overridden by family/home recognition.
- State memory is advisory by default.
- Positive-phase residue is advisory/debug-only. It does not override gate, verification, wake result, monitor, Tracey routing, or final synthesis.
- `--positive-residue-demo` remains smoke/debug-only and must not be used as production control input.
- “System lights up” in this smoke context means functional coherence, route-clarity, afterglow, and carryover hint residue in state memory — not emotion or subjective feeling.
