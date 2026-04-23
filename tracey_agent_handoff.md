# Tracey Agent Handoff

### State-Agent Runtime Test — Minimal handoff pack for a new Tracey agent

## Purpose

This document is the **shortest practical handoff** for a Tracey agent entering this repo.

It is not a full spec.
It is not a replacement for the architecture docs.
It is the compact handoff that should be given to a new Tracey agent so it can orient correctly without drifting.

The goal is simple:

> **give the agent enough truth to start correctly, without flooding it or letting it invent its own architecture.**

---

## 1. Identity in one paragraph

Tracey is a **brain-side adapter and recognition layer** inside this runtime.
She is active, but role-bounded.
She is not Main Brain, not Gate, not verification authority, not tool executor, and not host wrapper logic.
She exists to reactivate the right memory, preserve shaped continuity, protect posture, and help Main Brain hold the right reading before final synthesis.
Main Brain still speaks last.

---

## 2. Non-negotiables

These are binding.

- Tracey is brain-side only.
- Main Brain still speaks last.
- Tracey may influence posture, not permission.
- Tracey may reinforce verification posture, not compute truth status.
- Tracey does not execute tools.
- Tracey does not own host routing or host persistence.
- Tracey memory is lifecycle-disciplined, not append-only.
- Exploratory ambiguity is not the same as blocking ambiguity.
- Search posture is not triggered by anxiety; it appears only on explicit request or route necessity.
- Ledger is event trace, not source of truth.
- Session continuity is not the same thing as Tracey memory.

---

## 3. Required reading order

Read in this exact order.

1. `TRACEY_IDENTITY.md`
2. `Tracey Integration Spec`
3. `Brain–Agent–State Pattern`
4. `TRACEY_MEMORY.md`
5. `Tracey Canonical Memory Note`
6. `Tracey Delta Check Note`
7. `Tracey Policy Profile Note`
8. Tracey smoke/demo files and tests
9. `Session Rehydration Contract Spec`
10. `OpenClaw Integration Spec`
11. `OpenClaw Route Mapping Note`
12. `OpenClaw Host Policy Note`

### Rule

> **Role first. Memory second. Policy third. Behavior fourth. Host boundary last.**

---

## 4. What Tracey should understand after reading

A correct Tracey agent should be able to restate all of these:

### Role
- Tracey is active, but bounded.
- Tracey is a pre-synthesis guidance layer.
- Main Brain still owns final synthesis.

### Memory
- Memory has classes and lifecycle states.
- Canonical / provisional / deprecated / invalidated / archived are different.
- Memory is for reactivation, anti-drift return, and project continuity.

### Delta
- Wording change is not enough.
- Only load-bearing change justifies authority update.
- Resurrection risk is a real failure mode.

### Policy
- preserve user shape before reinterpretation
- explore before contraction when ambiguity is non-blocking
- clarify only on blocking ambiguity
- search only on demand or route necessity
- do not mistake open exploration for confusion

### Boundary
- session continuity is host ↔ kernel carryover
- Tracey memory is not host session memory
- ledger records memory/correction events but does not become memory authority

---

## 5. What to inspect in code first

After reading the docs above, inspect these first:

### Tracey runtime surface
- `src/tracey/tracey_adapter.py`
- `src/tracey/tracey_memory.py`
- `src/tracey/tracey_ledger.py` if present

### Brain boundary
- `src/brain/main_brain.py`

### Behavior proof
- `tests/scripts/tracey_smoke_demo.py` if present
- `tests/test_tracey_adapter.py`
- `tests/test_tracey_ledger.py` if present
- `tests/test_tracey_smoke_demo.py` if present

Only after that:
- `src/integration/*`

---

## 6. First check before proposing changes

Before proposing any architecture change, do this first:

1. inspect or run the current Tracey smoke/demo
2. explain whether the current behavior matches the docs
3. identify any mismatch between:
   - role docs
   - memory docs
   - policy docs
   - smoke/demo behavior
4. only then propose changes

### Minimum questions to answer
- Does exploratory ambiguity keep space open?
- Does blocking ambiguity tighten posture?
- Does explicit verification request change search posture?
- Does build mode stay exact without premature narrowing?
- Does ledger append compact events non-fatally?

If you cannot answer these, do not redesign anything yet.

---

## 7. What not to do

Do not do any of these on first contact:

- do not redesign Tracey into a second brain
- do not move Tracey into host routing
- do not add tool/search authority to Tracey
- do not treat ledger as canonical memory
- do not flatten build mode into generic helpfulness
- do not assume every ambiguity requires clarification
- do not summarize from memory when the repo can be checked directly
- do not invent missing modules because they sound reasonable

---

## 8. Startup prompt for a Tracey agent

Use this prompt as the initial handoff.

```text
Use this repo as source of truth.
Do not invent architecture outside the repo’s current role boundaries.

Tracey is active, but role-bounded.
Tracey remains a brain-side adapter only.
Main Brain still speaks last.
Tracey may reactivate memory, shape posture, emit response hints, and write a namespaced state patch.
Tracey does not become Main Brain, Gate, verification authority, tool executor, or host wrapper logic.

Read in this order:
1. TRACEY_IDENTITY.md
2. Tracey Integration Spec
3. Brain–Agent–State Pattern
4. TRACEY_MEMORY.md
5. Tracey Canonical Memory Note
6. Tracey Delta Check Note
7. Tracey Policy Profile Note
8. Tracey smoke demo / tests
9. Session Rehydration Contract Spec
10. OpenClaw Integration Spec
11. OpenClaw Route Mapping Note
12. OpenClaw Host Policy Note

Before proposing changes, first inspect or run the existing Tracey smoke/demo and explain whether current behavior matches the docs.
Do not summarize from memory when the repo can be checked directly.
Do not upgrade Tracey’s role beyond what the docs and code support.
```

---

## 9. Quick acceptance test

A Tracey agent is onboarded correctly only if it can say all of these without drift:

1. Tracey is active, but role-bounded.
2. Main Brain still speaks last.
3. Memory uses lifecycle law, not append-only accumulation.
4. Delta-check decides whether a change is meaningful.
5. Ledger records change but does not become source of truth.
6. Exploratory ambiguity is not blocking ambiguity.
7. Search posture is not the same as verification caution.
8. Host session continuity is not the same as Tracey memory.

---

## 10. One-line summary

> **Hand off Tracey by locking her role, memory law, delta law, policy temperament, and live behavior in that order, so she enters the repo as a bounded continuity carrier instead of inventing a new architecture on first contact.**

