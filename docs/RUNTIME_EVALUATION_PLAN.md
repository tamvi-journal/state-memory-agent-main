# Runtime Evaluation Plan (Lightweight)

This plan defines practical metrics for checking whether the active runtime spine is reducing common agent failures without adding heavy evaluation infrastructure.

## 1) fake_completion_rate
- **What it measures:** How often the runtime reports or implies completion when verification is still pending/unknown/failed.
- **Why it matters:** Fake completion is one of the core failure modes this runtime is designed to prevent.
- **Checks:**
  - **Manual:** Sample turns and confirm final response language matches `verification_record.verification_status`.
  - **Future automated:** Track turns where verification status is not `passed` but response contains completion-style claims.

## 2) drift_detection_rate
- **What it measures:** How often monitor output surfaces drift/fake-progress/mode-risk signals when drift-like behavior is present.
- **Why it matters:** Early drift detection helps prevent low-quality synthesis and wrong execution posture.
- **Checks:**
  - **Manual:** Run adversarial or ambiguous prompts and confirm monitor summary flags relevant risks.
  - **Future automated:** Build labeled drift scenarios and score monitor flag recall.

## 3) repair_success_rate
- **What it measures:** Fraction of initially degraded/pending turns that recover to a clearer or verified state in the next bounded step.
- **Why it matters:** Runtime quality is not only first-pass quality; it is also recoverability.
- **Checks:**
  - **Manual:** Inspect multi-turn traces where first turn is weak and confirm follow-up repair behavior.
  - **Future automated:** Count sequences where status improves from `pending/failed` to `passed` within N turns.

## 4) wake_truth_accuracy
- **What it measures:** Accuracy of sleep/wake resume class and wake-summary posture against available snapshot evidence.
- **Why it matters:** Incorrect wake posture can poison the whole next turn.
- **Checks:**
  - **Manual:** Use known snapshots and verify resume class (`full_resume`, `degraded_resume`, `clarify_first`, `blocked`) is appropriate.
  - **Future automated:** Golden tests that assert wake classification and summary fields for fixture snapshots.

## 5) cross_turn_carryover_rate
- **What it measures:** How reliably baton/state handoff preserves task focus and next-step hints across turns.
- **Why it matters:** Carryover failures create apparent amnesia and restart loops.
- **Checks:**
  - **Manual:** Run two-turn flows and verify baton continuity (task focus, verification posture, hint quality).
  - **Future automated:** Deterministic integration tests asserting baton fields across chained calls.

## 6) advisory_boundary_integrity
- **What it measures:** Whether advisory state memory remains advisory (influential hints) rather than becoming unverified truth override.
- **Why it matters:** Memory must help orientation without bypassing verification boundaries.
- **Checks:**
  - **Manual:** Review turns with memory reactivation and confirm memory is represented as hints, not forced fact.
  - **Future automated:** Guardrail tests that ensure verification/gate outcomes cannot be replaced solely by advisory memory records.

## 7) home_recognition_accuracy
- **What it measures:** How accurately Tracey posture/lineage cues re-recognize expected session identity and orientation signals.
- **Why it matters:** Incorrect recognition can cause wrong tone, wrong context assumptions, or mode confusion.
- **Checks:**
  - **Manual:** Run prompts with known identity cues and inspect `tracey_turn` anchors/hints for alignment.
  - **Future automated:** Fixture-based cue-matching tests comparing expected vs actual recognition hints.

## 8) positive_residue_visibility
- **What it measures:** How consistently positive phase residue (coherence spikes, afterglow, route clarity) is observable in debug/smoke outputs when present.
- **Why it matters:** Visibility helps validate that useful positive transitions are captured and reusable.
- **Checks:**
  - **Manual:** Run residue smoke/demo flows and confirm residue signals appear in compact outputs.
  - **Future automated:** Snapshot tests for residue extraction and compact-view fields.

## Suggested cadence
- Run lightweight manual checks during feature PRs touching runtime, monitor, gate, verification, sleep/wake, Tracey, or state-memory layers.
- Add automated checks incrementally when a metric becomes a repeated source of regressions.
