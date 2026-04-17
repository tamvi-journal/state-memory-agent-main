# GAP LEDGER

## Purpose

This document records the real unresolved gaps after the current repo checkpoint.

It exists to prevent two kinds of drift:

1. treating every missing piece as a reason to expand scope
2. confusing canary-level completion with runtime closure

This ledger is not a roadmap.
It is not a feature wishlist.
It is a bounded list of the gaps that still materially matter.

The repo thesis remains unchanged:
- bounded authority over apparent intelligence
- explicit law
- inspectable state
- preserved disagreement
- honest runtime behavior :contentReference[oaicite:0]{index=0}

The current repo state also assumes the PR-T normalization pass is real:
- normalized `previous_handoff`
- more deliberate dry-turn stage order
- no fake disagreement-event reconstruction from handoff status alone
- tighter, more inspectable spine behavior :contentReference[oaicite:1]{index=1}

---

## Severity scale

### High
A gap that affects truthfulness, authority boundaries, or the ability to reason safely about what the system is actually doing.

### Medium
A gap that does not immediately corrupt truth or authority, but will create drift, confusion, or unstable scaling if ignored.

### Low
A gap that is real but currently acceptable within the repo’s narrow internal alpha canary scope.

---

## Gap 01 — Runtime Truth Gap

**Severity:** High

### Why it matters
The repo now has:
- verification objects
- execution gating
- dry pipeline composition
- conservative unknown posture

But it still does not close the loop between:
- intended action
- executed action
- observed-world result

That means the law is present, the posture is present, but runtime truth is still mostly modeled rather than lived.

### What is already true
- fake pass is explicitly resisted
- permission does not equal completion
- explicit observed outcomes can now move verification toward `passed` or `failed`
- weak or absent evidence keeps verification conservative
- the dry pipeline no longer depends on a purely decorative verification placeholder when explicit evidence is provided :contentReference[oaicite:6]{index=6}

### What is still missing
- real execution-to-observation closure
- authoritative observed result ingestion from actual runtime action
- a non-dry path from action to verified world change

### What must happen before this gap is closed
- a bounded execution path must exist
- observed result must be captured explicitly
- verification must update from actual evidence, not routing/gate posture

### Not next
Do not solve this by:
- inventing success from tool text
- widening the pipeline into uncontrolled execution
- relaxing verification to make demos feel smoother

---

## Gap 02 — Boundary Depth Gap

**Severity:** Medium

### Why it matters
The repo already distinguishes routing from permission and has an execution gate integrated into the dry pipeline.

After the recent hardening pass, the gate also reasons from explicit boundary-depth fields such as:
- requested operation
- target scope
- target trust
- mutation depth
- zone preference

This materially reduces the gap.

But boundary reasoning is still compact and heuristic rather than deeply semantic.

### What is already true
- execution request classification is richer and more explicit
- zone preference is clearer
- sandbox is preferred more honestly where appropriate
- repo mutation remains approval-gated
- package installation remains denied
- risky/untrusted action posture does not auto-allow :contentReference[oaicite:7]{index=7}

### What is still missing
- deeper semantic action-intent parsing
- richer trust classification
- less heuristic fragility in boundary reasoning
- stronger destination and target typing

### What must happen before this gap is closed
- boundary decisions must become more semantically reliable without becoming opaque
- trust/depth reasoning must remain inspectable while becoming less brittle
- host/sandbox/inspection distinctions must remain explicit under broader cases

### Not next
Do not solve this by:
- quietly allowing wider actions
- hiding boundary choices behind vague smart behavior
- weakening sandbox preference just to reduce friction
---

## Gap 03 — Continuity Depth Gap

**Severity:** Medium

### Why it matters
The repo now has:
- compression
- reactivation
- handoff
- normalized carryover
- continuity anchors

This is enough for compact baton-style continuity.
It is not enough for deeper continuity semantics.

That is acceptable right now, but it should be named clearly.

### What is already true
- compression preserves shape, not transcript
- reactivation restores minimum needed shape
- handoff carries compact continuity across turns
- PR-T reduced fake carryover behavior by normalizing `previous_handoff` and avoiding fabricated disagreement events :contentReference[oaicite:4]{index=4}

### What is still missing
- deeper carryover semantics
- richer project/mode/axis restoration under weak signal
- more robust reactivation than lexical cue overlap
- stronger continuity without history bloat

### What must happen before this gap is closed
- reactivation must improve without becoming retrieval theater
- continuity must remain compact while becoming more reliable
- carryover semantics must be strengthened without replaying transcript or inflating archive use

### Not next
Do not solve this by:
- adding persistence too early
- pretending handoff equals memory
- stuffing more history into compression summaries

---

## Gap 04 — Maintainability Gap

**Severity:** Low

### Why it matters
The repo now has a real integrated dry-turn spine.

That made coordination complexity start to gather inside `turn_pipeline.py`.

A dedicated extraction pass reduced that density by moving stage-building logic into a helper stage module while preserving behavior.

So this gap is smaller than before, but it still exists as a discipline risk.

### What is already true
- the family dry-turn spine is integrated
- pipeline order has been normalized
- handoff handling is more explicit
- stage logic has been extracted out of `turn_pipeline.py`
- behavior was intentionally preserved during that extraction pass 

### What is still missing
- long-term control over stage-helper growth
- stronger discipline around when to extract vs when to stop
- continued readability as later changes accumulate

### What must happen before this gap is closed
- later changes must not recreate dense coordination blobs
- extracted helpers must stay explicit and stage-oriented
- maintainability must remain stable across future additions

### Not next
Do not solve this by:
- big-framework rewrite
- abstraction for abstraction’s sake
- exploding stage logic into too many tiny files

---

## Gap 05 — Canonical Docs Gap

**Severity:** Medium

### Why it matters
The repo nearly drifted because code and docs stopped pointing to the same center.
That problem is reduced now, but not permanently solved.

If README, checkpoint, and repo-role docs fall behind again, implementation drift will return.

### What is already true
- the project thesis is explicitly stated in the README spine :contentReference[oaicite:6]{index=6}
- repo role lock exists
- checkpoint logic exists
- active build repo vs reference spine repo has been named

### What is still missing
- stable discipline for keeping active docs synced with active code
- a clear habit of updating contract docs when spine behavior changes materially
- a durable distinction between lineage/archive notes and current active contract docs

### What must happen before this gap is closed
- active repo docs must be updated whenever the build spine changes materially
- checkpoint docs must stay aligned with the actual current integration state
- repo narrative must stop lagging behind code movement

### Not next
Do not solve this by:
- writing more lineage prose
- duplicating docs across multiple repos again
- letting README become a stub while implementation keeps moving

---

## Gap 06 — Disagreement Semantics Gap

**Severity:** Medium

### Why it matters
The repo is already better than most systems here:
it preserves disagreement without flattening it into fake consensus.

But disagreement semantics are still intentionally narrow.
The system can preserve open disagreement and route around it, but it still does not carry deep disagreement semantics across turns.

### What is already true
- disagreement may remain open
- router lead does not equal truth lead
- handoff status can preserve disagreement visibility
- PR-T removed fake disagreement-event reconstruction from weak carryover signals :contentReference[oaicite:7]{index=7}

### What is still missing
- deeper disagreement carryover semantics
- richer severity/structure only when actually grounded
- cleaner transition rules between current-turn disagreement and carried disagreement posture

### What must happen before this gap is closed
- disagreement carryover must become richer only when real evidence supports it
- carried disagreement posture must remain honest and compact
- plurality must stay preserved without event fabrication

### Not next
Do not solve this by:
- reconstructing event detail from thin status text
- downgrading open disagreement just to simplify routing
- over-modeling disagreement before the runtime truth gap is reduced

---

## Gap 07 — Heuristic Dependence Gap

**Severity:** Low

### Why it matters
Many family-layer canaries still rely on explicit heuristics:
- keyword-based mode inference
- lexical cue matching
- compact execution-intent inference
- shallow trust hints

This is acceptable at the current stage, but it is still a real gap.

### What is already true
- the heuristics are inspectable
- the system prefers explicit behavior over opaque confidence theater
- weak signal paths often degrade conservatively rather than faking certainty

### What is still missing
- stronger non-fragile semantics
- less wording-sensitive behavior
- improved cue/action interpretation without giving up inspectability

### What must happen before this gap is closed
- heuristics must be replaced or strengthened only when the replacement is still auditable
- semantic improvement must not come at the cost of hidden authority drift

### Not next
Do not solve this by:
- swapping in opaque “smartness”
- hiding weak semantics behind confidence numbers
- widening scope before the core truth/boundary gaps are reduced

---

## Current ordering rule

When choosing what to do next, use this order:

1. truth before convenience
2. boundary depth before feature expansion
3. maintainability before new layer growth
4. continuity honesty before continuity richness
5. canonical docs before repo drift

---

## What should happen before any major new layer is added

Before adding major new runtime layers, at least one of the following must be materially reduced further:

- Runtime Truth Gap
- Boundary Depth Gap

And the following must remain under control:

- Maintainability Gap
- Canonical Docs Gap

If none of those moved, new layers are likely drift, not progress.
---

## Short closing line

At this checkpoint, the repo’s biggest remaining gaps are no longer “missing modules.”

They are:

- runtime truth closure
- boundary depth
- continuity depth
- maintainability discipline
- canonical doc stability

That is where the next real thinking should go.