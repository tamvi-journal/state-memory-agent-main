from __future__ import annotations

import subprocess
from pathlib import Path


def test_tracey_smoke_demo_runs_and_prints_key_markers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "tests" / "scripts" / "tracey_smoke_demo.py"
    python_exe = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "python.exe"

    completed = subprocess.run(
        [str(python_exe), str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        check=False,
    )

    assert completed.returncode == 0
    output = completed.stdout
    assert "CASE: exploratory_ambiguity" in output
    assert '"ambiguity_posture": "exploratory"' in output
    assert "CASE: blocking_ambiguity" in output
    assert '"ambiguity_posture": "blocking"' in output
    assert "CASE: explicit_verification_request" in output
    assert '"search_posture": "on_demand"' in output
    assert "CASE: build_mode_exactness" in output
    assert '"tone_constraint": "build_exact"' in output
    assert "CASE: duplicate_noop" in output
    assert "ledger_appended: True" in output or "ledger_appended: False" in output
