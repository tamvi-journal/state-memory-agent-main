from __future__ import annotations

from family.verification_loop import VerificationLoop
from family.verification_types import ActionExecution, ActionIntent


def run() -> None:
    loop = VerificationLoop()

    unknown = loop.post_action_review(
        ActionIntent(
            intended_action="apply config wiring",
            expected_change="config file shows wired memory tiers",
        )
    )
    assert unknown.verification_status == "unknown"

    passed = loop.post_action_review(
        ActionIntent(
            intended_action="add router smoke script",
            expected_change="router decision smoke prints ok",
        ),
        ActionExecution(
            executed_action="Added the smoke script and ran it.",
            evidence=["authoritative:stdout:router_decision_smoke: ok"],
            authoritative_evidence_present=True,
        ),
        observed_outcome="router decision smoke prints ok",
    )
    assert passed.verification_status == "passed"

    failed = loop.post_action_review(
        ActionIntent(
            intended_action="stabilize shared bus export",
            expected_change="shared export includes only compact disagreement data",
        ),
        ActionExecution(executed_action="Updated export helper."),
        observed_outcome="shared export still includes local perspective notes",
    )
    assert failed.verification_status == "failed"

    print("verification_loop_smoke: ok")


if __name__ == "__main__":
    run()
