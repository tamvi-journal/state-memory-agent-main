# Runtime demos

This repo includes small runnable scripts to validate runtime behavior from the command line.

## Run commands

```bash
python scripts/demo_one_turn.py
python scripts/demo_multi_turn.py
python scripts/tracey_smoke.py
```

## What each demo covers

- `scripts/demo_one_turn.py`: single-turn compact runtime pass.
- `scripts/demo_multi_turn.py`: three-turn sequence that demonstrates baton carryover, ambiguity follow-up, and unsupported/broad request handling.
- `scripts/tracey_smoke.py`: Tracey smoke workflow with wake/rehydration and state-memory surfaces.
