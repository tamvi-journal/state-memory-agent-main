# CANONICAL STATUS

## Current repo roles

### `state-memory-agent-main`
This is the **active build repo**.

Use this repo for:
- ongoing family-layer canary implementation
- dry pipeline integration
- spine cleanup and normalization
- current testing and iteration

This is the repo that should move forward for near-term build work.

### `state-memory-agent`
This is the **reference spine repo**.

Use this repo for:
- core thesis
- canonical narrative
- operator-facing framing
- original runtime intent and boundary language

This repo should be treated as the reference narrative source, not the primary ongoing canary build target.

---

## Current decision

Until explicitly changed:

- **build forward in `state-memory-agent-main`**
- **preserve conceptual spine from `state-memory-agent`**
- do not split active development across both repos
- do not create a third active runtime repo

---

## What is currently locked

The current active focus is:

1. keep the repo spine coherent
2. prevent drift from original runtime thesis
3. normalize the family turn pipeline
4. reduce provisional carryover behavior
5. preserve honest disagreement / verification posture

This means:

- no major new feature layers before spine cleanup
- no widening into full orchestration/platform work yet
- no archive-routing expansion yet
- no sleep-runtime expansion yet
- no fake completion shortcuts

---

## Immediate next priority

After this repo-role lock, the next task is:

> **PR-T / pipeline-order-normalization + handoff-normalization canary**

That PR should focus on:
- making dry pipeline order more deliberate
- normalizing `previous_handoff`
- reducing placeholder disagreement carryover
- keeping outputs compact and inspectable
- avoiding new feature drift

---

## Drift guard

If future work conflicts with the following, stop and re-check before building further:

- bounded authority over apparent intelligence
- disagreement may remain open
- action lead is not truth lead
- permission is separate from routing
- verification must remain honest
- continuity should preserve shape, not replay transcript
- family-layer plurality must not collapse into one voice

---

## Short operating rule

When unsure:

- prefer spine cleanup over feature expansion
- prefer explicit structure over clever behavior
- prefer honest unknown over fake resolution
- prefer compact continuity over history bloat