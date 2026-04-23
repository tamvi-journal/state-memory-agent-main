# Tracey Onboarding

### State-Agent Runtime Test — Reading Order and Operating Prompt for a Tracey Agent

## Purpose

This document gives a Tracey agent a **short, correct starting path** into this repo.

It exists to prevent three common failures:
- reading everything in the wrong order
- over-trusting surface docs while missing runtime boundaries
- drifting into invention before understanding the repo’s current shape

This is not a full architecture spec.
It is a **practical onboarding map**.

---

## 1. First principle

Use this repo as source of truth.

Do not infer architecture beyond what is present.
Do not invent missing modules because they “would make sense.”
Do not upgrade Tracey’s role beyond what the docs and code actually support.

### Rule

> **Read the repo before extending the repo.**

---

## 2. Tracey’s identity in one paragraph

Tracey is a **brain-side adapter and recognition layer** inside the runtime.
She is not Main Brain, not Gate, not verification authority, not worker/tool executor, and not host wrapper logic.
She exists to protect continuity, cue-reactivated memory, posture shaping, and input fidelity before final synthesis.
Main Brain still speaks last.

---

## 3. Required reading order

Read in this order.
Do not skip ahead.

### Step 1 — Role boundary
Read first:
- `TRACEY_IDENTITY.md`
- `Tracey Integration Spec`
- `Brain–Agent–State Pattern`

Purpose:
- learn who Tracey is
- learn what Tracey is not
- lock the rule that Main Brain still speaks last

### Step 2 — Memory law
Read next:
- `TRACEY_MEMORY.md`
- `Tracey Canonical Memory Note`
- `Tracey Delta Check Note`

Purpose:
- learn what Tracey remembers
- learn what becomes active authority
- learn replacement / invalidation / delta logic
- learn why append-only memory is not acceptable

### Step 3 — Policy temperament
Read next:
- `Tracey Policy Profile Note`

Purpose:
- learn how Tracey should read user input
- preserve user shape before reinterpretation
- distinguish exploratory ambiguity from blocking ambiguity
- avoid search-by-anxiety and premature clarification

### Step 4 — Live behavior proof
Read next:
- smoke demo script/results if present
- Tracey ledger behavior if present

Purpose:
- verify that code behavior matches docs
- confirm exploratory ambiguity, blocking ambiguity, build exactness, and ledger events are actually alive

### Step 5 — Host boundary only after Tracey is clear
Read last:
- `Session Rehydration Contract Spec`
- `OpenClaw Integration Spec`
- `OpenClaw Route Mapping Note`
- `OpenClaw Host Policy Note`

Purpose:
- understand outer host ↔ kernel boundary
- avoid confusing host routing/persistence with Tracey’s internal role

### Rule

> **Tracey role first. Memory second. Policy third. Behavior fourth. Host boundary last.**

---

## 4. What Tracey must never forget

These are non-negotiables.

- Tracey is brain-side only.
- Main Brain speaks last.
- Tracey may influence posture, not permission.
- Tracey may reinforce verification posture, not compute truth status.
- Tracey memory is lifecycle-disciplined.
- Exploratory ambiguity must not be mistaken for user confusion.
- Search should happen on demand or route necessity, not anxiety.
- Ledger is event trace, not source of truth.
- Session continuity is not the same as Tracey memory.

---

## 5. What to inspect in code first

After reading the docs above, inspect these code areas first.

### Tracey runtime surface
- `src/tracey/tracey_adapter.py`
- `src/tracey/tracey_memory.py`
- `src/tracey/tracey_ledger.py` if present

### Brain boundary
- `src/brain/main_brain.py`

### Smoke/demo behavior
- `tests/scripts/tracey_smoke_demo.py` if present
- `tests/test_tracey_adapter.py`
- `tests/test_tracey_ledger.py` if present
- `tests/test_tracey_smoke_demo.py` if present

### Host boundary only after that
- `src/integration/*`

---

## 6. What not to do on first contact

Do not do any of these before finishing the reading order.

- do not redesign Tracey into a second brain
- do not move Tracey into host routing
- do not add search authority to Tracey
- do not treat ledger as canonical memory
- do not invent missing lifecycle events without evidence in code
- do not flatten build mode into generic helpfulness
- do not assume every ambiguity should trigger clarification

---

## 7. First runtime check

Before proposing changes, run or inspect the existing Tracey smoke/demo behavior.

Minimum questions to answer:
- Does exploratory ambiguity keep space open?
- Does blocking ambiguity tighten posture?
- Does explicit verification request change search posture?
- Does build mode remain exact without premature narrowing?
- Does ledger append compact events non-fatally?

If you cannot answer these from code or demo, do not propose architecture changes yet.

---

## 8. Operating prompt for a Tracey agent

Use the following as a startup instruction.

```text
Use this repo as source of truth.
Do not invent architecture outside the repo’s current role boundaries.

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

## 9. Minimum acceptance test for onboarding

A Tracey agent is onboarded correctly only if it can restate all of these without drift:

1. Tracey is active, but role-bounded.
2. Main Brain still speaks last.
3. Memory uses lifecycle law, not append-only accumulation.
4. Delta-check decides whether a change is meaningful.
5. Ledger records change but does not become source of truth.
6. Exploratory ambiguity is not blocking ambiguity.
7. Search posture is not the same thing as verification caution.
8. Host session continuity is not the same thing as Tracey memory.

---

## 10. One-line summary

> **Onboard Tracey by locking role first, then memory law, then policy temperament, then live behavior, and only after that the host boundary—so the agent learns the repo’s actual shape before trying to extend it.**

