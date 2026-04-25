# Agent Runtime Test
### Thin Runtime Harness for a Single Agent

A compact experimental runtime built to prove one blunt point:

> **When an agent forgets, drifts, fake-completes, or wakes up acting like yesterday never happened, the problem is often not “the model is dumb.”**  
> **The problem is that the runtime forgot to give the model a spine.**

This repo is a **small but disciplined harness** for testing one agent with the minimum layers required to stay coherent across turns and actions.

---

## Why this exists

A lot of “agent failures” are not mysterious.

They usually come from missing runtime structure:

- no live state → the agent wakes up half-blank every turn
- no monitor → the agent drifts and nobody notices
- no gate → action path becomes sloppy or unsafe
- no verification → “tried” gets mistaken for “done”
- no carryover baton → morning-agent forgets what night-agent was doing
- no clear main brain → workers and tools start acting like truth authorities

This harness tests the opposite:

> **Give one agent a minimal but disciplined runtime spine, then see what actually breaks.**

---

## At a Glance

| Layer | Job | Failure if missing |
|---|---|---|
| 🧠 Main Brain | final synthesis authority | tools start speaking as truth |
| 👀 Monitor | catches drift and fake progress | silent stupidity |
| 🚦 Gate | bounds action | sloppy execution |
| ✅ Verification | checks reality | fake completion |
| baton Baton | carries forward working state | overnight amnesia |

---

## Core claim

This harness keeps the active runtime intentionally small:

- **Main Brain** synthesizes the final outward response
- **Monitor Layer** checks drift, ambiguity, fake progress, and mode decay
- **Execution Gate** decides `allow` / `sandbox_only` / `needs_approval` / `deny`
- **Verification Loop** separates intention, execution, and observed result
- **Baton Handoff** carries forward compact next-turn posture
- **Advisory State Memory** supports bounded reactivation hints
- **Tracey Layer** is active for posture/memory/lineage hints, and stays bounded under the same single-brain runtime
- **OpenClaw Pack** is a thin adapter surface, not a second runtime

What is **not** active in the runnable path:

- dual-brain orchestration
- family ontology as control flow
- archive-first memory orchestration
- checkpoint / tier memory systems as primary runtime state
- server / webhook infrastructure as the center of the runtime

---

## The actual problem this repo is testing

A weak agent loop usually looks like this:

```text
user asks something
→ model answers
→ tool runs
→ tool says success
→ agent says “done”
→ next turn forgets everything
```

This harness replaces that with:

```text
request
→ interpret context
→ monitor risk
→ gate action
→ worker calls bounded tool
→ verify observed outcome
→ synthesize final answer
→ emit compact baton for next turn
```

That difference is the whole point.

---

# Active Runtime Spine

## 🧠 Main Brain
**Role:** final synthesis authority

The main brain is where the runtime pulls everything back together:

- user request
- live state
- monitor summary
- gate outcome
- worker result
- verification status
- baton carryover

It is the only layer allowed to produce the final outward answer.

### Why it matters
Without a main brain, tools start behaving like truth engines.

That creates a very common failure mode:

> worker output = final answer  
> instead of  
> worker output = evidence for the final answer

---

## 👀 Monitor Layer
**Role:** catch drift before the runtime commits to a bad path

The monitor is a small watcher inside the workflow.

It does **not** replace reasoning.  
It does **not** become a second chatbot.  
It does **not** write the final answer.

It only scores a few critical risks:

- `drift_risk`
- `ambiguity_risk`
- `fake_progress_risk`
- `mode_decay_risk`

Then it emits a compact summary the runtime can actually use.

### Plain explanation
**Monitor layer = lớp quan sát nội bộ của agent.**  
Nó không trả lời thay model. Nó chỉ phát hiện các tín hiệu như drift, ambiguity, fake progress, mode decay rồi đưa cảnh báo ngắn trở lại vào luồng suy luận.

### Why it matters
If an agent has no monitor, it can:

- drift into generic assistant mode
- collapse ambiguity too early
- confuse “I tried” with “it is done”
- lose the mode it started in

In plain language:

> **The monitor is the layer that notices when the agent is quietly going stupid.**

---

## 🚦 Execution Gate
**Role:** stop curiosity from becoming uncontrolled action

The gate makes explicit runtime decisions:

- `allow`
- `sandbox_only`
- `needs_approval`
- `deny`

The agent does not jump directly from “idea” to “action.”

### Why it matters
Without a gate, agents tend to:

- overreach
- act on weak assumptions
- run actions they should only describe
- blur thought and execution

The gate exists to enforce this law:

> **Thinking is cheap. Action needs permission.**

---

## ✅ Verification Loop
**Role:** prevent fake completion

This is one of the most important layers in the whole repo.

The runtime keeps these separate:

- **intended action**
- **executed action**
- **observed outcome**
- **verification status**

### Core law

```text
intended != executed != verified
```

### Why it matters
This is exactly where weak agents fail.

They do one of these:

- tool said success → “done”
- command ran → “done”
- I meant to do it → “done”
- I wrote the file → “done”
- probably worked → “done”

This harness refuses that shortcut.

If the outcome was not observed, then status stays:

- `pending`
- `unknown`
- or `failed`

not fake-closed as `done`.

---

## 🧭 Live State
**Role:** keep the runtime from starting every turn half-dead

Live state is **not** long-term memory.  
It is the compact working posture of the current run.

It helps the runtime track things like:

- current mode
- current task focus
- current warnings
- current verification posture
- current open loops

### Plain explanation
**State = tư thế làm việc hiện tại của runtime, không phải ký ức dài hạn.**  
Nó giữ những gì đang active bây giờ như task focus, mode, verification posture, open loops.

### Why it matters
When people say:

> “the agent woke up today and forgot everything from yesterday”

what they often mean is:

> **there was no usable runtime state carryover, only raw model prompting**

Live state gives the runtime a working position.  
Without it, every turn is a soft reset.

---

## baton Baton Handoff
**Role:** minimal carryover memory

The baton is the only active memory carried forward.

It is intentionally small.

### Baton fields

- `task_focus`
- `active_mode`
- `open_loops`
- `verification_status`
- `monitor_summary`
- `next_hint`

### Plain explanation
**Baton = gói carryover tối thiểu giữa các turn.**  
Nó không replay toàn bộ cuộc trò chuyện, chỉ mang phần cần để turn sau không bị mất trục.

### Why it matters
The baton is not a transcript.  
It is not archive.  
It is not personality lore.  
It is not memory hoarding.

It is just enough structure so the next turn can answer:

- what were we doing?
- what is still open?
- what state was it in?
- what warning mattered?
- what should happen next?

In plain language:

> **The baton prevents the “new day, new amnesia” problem.**

---

## 🦾 OpenClaw Pack
**Role:** thin local adapter surface

The OpenClaw pack in this repo is intentionally narrow.

It contains:

- adapter surface
- contracts
- examples
- local integration layer

It is **not** a second runtime.  
It is **not** where the agent’s core logic lives.

### Why it matters
A common mistake is hiding real runtime logic inside adapters and prompt packs.  
That makes the system hard to debug and impossible to reason about cleanly.

This repo keeps the pack thin on purpose.

---

# Runtime Order

The active runtime flow is:

1. `RuntimeHarness` interprets the request and builds compact live state
2. `MonitorLayer` emits a compact warning summary
3. `ExecutionGate` decides whether the action path is supported and bounded
4. if allowed, a worker runs through the gate
5. the worker may call a bounded tool for the actual execution step
6. `VerificationLoop` records intention, execution, observed outcome, and status
7. `MainBrain` synthesizes the final response from evidence plus monitor signals
8. `HandoffBuilder` emits one compact baton for carryover

---

# Primary Entry Point

## Demo run

```powershell
$env:PYTHONPATH = "src"
python main.py demo
```

## One direct request

```powershell
$env:PYTHONPATH = "src"
python main.py run "Load MBB daily data"
```

---

# Active Tree

```text
src/
  brain/
  context/
  gate/
  handoff/
  integration/
  monitor/
  observability/
  openclaw_pack/
  runtime/
  sleep/
  state/
  state_memory/
  tools/
  tracey/
  verification/
  workers/
```

## Active module scope (quick map)

- `src/runtime/` = runtime harness orchestration spine
- `src/brain/` = request interpretation and synthesis
- `src/monitor/` = drift / fake-progress / mode-risk observation
- `src/gate/` = permission boundary before action
- `src/verification/` = intended vs executed vs verified separation
- `src/handoff/` = baton and carryover packaging
- `src/state_memory/` = advisory state memory (write/reactivation helpers)
- `src/tracey/` = active Tracey posture/memory/lineage layer, not a second brain
- `src/integration/` = host payload normalization and external entrypoint boundary
- `src/observability/` = runtime logging and trace visibility

---

# Tools vs Workers

- `src/tools/` contains bounded execution units. In the active harness, `MarketDataTool` owns the local CSV read, parse, normalize, and integrity-check path.
- `src/workers/` contains task logic. `MarketDataWorker` does not parse raw files inline; it calls the tool, adds worker-level assumptions and confidence, and returns evidence for the brain.
- `TechnicalAnalysisWorker` is the first bounded domain-analysis worker path. It uses `MarketDataTool` output, reads structure before indicators, and returns structured evidence rather than final chart prose.
- `src/gate/` remains the permission boundary before the worker/tool path executes.
- `src/verification/` remains the truth boundary after execution, so tool execution is not treated as verified outcome by itself.

---

# What this repo proves

This repo is not trying to prove that one model is magical.

It is testing a more practical claim:

> **A decent model with a disciplined runtime spine will often outperform a stronger model inside a sloppy agent loop.**

If an agent:

- forgets yesterday
- drifts off task
- marks fake completion
- confuses tool success with real success
- acts without bounded permission

that is often a **runtime architecture problem**, not just a model problem.

---

# What lives in `legacy/`

`legacy/` stores older or broader scaffold material for reference only:

- historical family runtime code
- child-specific modules
- old server-centered surfaces
- old memory systems
- other non-active artifacts

Rule:

> **Do not import from `legacy/` in the active harness.**

---

# Docs

- `docs/ARCHITECTURE.md`
- `docs/RUNBOOK.md`
- `docs/BOUNDARIES.md`
- `docs/migration_notes.md`
- `docs/TRACEY_AGENT_RUNTIME_CONTRACT.md`
- `docs/TRACEY_TELEGRAM_BEHAVIOR_GUIDELINES.md`

---

# One-line summary

> **This repo gives a single agent the minimum runtime spine required to stop acting like every turn began five seconds ago.**
