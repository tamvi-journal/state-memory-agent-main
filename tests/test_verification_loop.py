from __future__ import annotations

from family.verification_loop import VerificationLoop
from family.verification_types import ActionExecution, ActionIntent


def _intent(expected_change: str = "config file now includes memory_tiers block") -> ActionIntent:
    return ActionIntent(
        intended_action="wire config-backed memory tiers",
        expected_change=expected_change,
        notes=["canary fixture"],
    )


def _execution(
    *,
    executed_action: str = "",
    evidence: list[str] | None = None,
    authoritative_evidence_present: bool = False,
) -> ActionExecution:
    return ActionExecution(
        executed_action=executed_action,
        evidence=[] if evidence is None else evidence,
        notes=["execution fixture"] if executed_action else [],
        authoritative_evidence_present=authoritative_evidence_present,
    )


def test_intention_only_yields_unknown() -> None:
    loop = VerificationLoop()
    record = loop.post_action_review(_intent())

    assert record.verification_status == "unknown"
    assert "no observed outcome is available yet" in record.notes


def test_executed_action_with_no_observed_outcome_yields_unknown() -> None:
    loop = VerificationLoop()
    record = loop.post_action_review(
        _intent(),
        _execution(executed_action="Applied the patch successfully."),
    )

    assert record.verification_status == "unknown"
    assert "execution text alone does not verify completion" in record.notes


def test_observed_expected_change_yields_passed() -> None:
    loop = VerificationLoop()
    record = loop.post_action_review(
        _intent(expected_change="memory tiers block present in config"),
        _execution(
            executed_action="Updated config and verified file contents.",
            evidence=["authoritative:file_read:config.yaml"],
            authoritative_evidence_present=True,
        ),
        observed_outcome="config now shows memory tiers block present in config",
    )

    assert record.verification_status == "passed"


def test_observed_mismatch_yields_failed() -> None:
    loop = VerificationLoop()
    record = loop.post_action_review(
        _intent(expected_change="router decision smoke prints ok"),
        _execution(executed_action="Ran smoke command."),
        observed_outcome="router decision smoke still fails",
    )

    assert record.verification_status == "failed"


def test_tool_success_like_text_alone_does_not_force_passed() -> None:
    loop = VerificationLoop()
    record = loop.post_action_review(
        _intent(expected_change="shared bus export contains disagreement event"),
        _execution(executed_action="Success: command completed cleanly."),
    )

    assert record.verification_status == "unknown"
    assert "success-like execution text is not treated as authoritative evidence" in record.notes


def test_export_stays_compact_and_explicit() -> None:
    loop = VerificationLoop()
    record = loop.post_action_review(_intent())
    exported = loop.export_review_event(record)

    assert set(exported.keys()) == {
        "intended_action",
        "executed_action",
        "expected_change",
        "observed_outcome",
        "verification_status",
        "evidence",
        "notes",
    }


def test_no_sleep_logic_is_introduced() -> None:
    loop = VerificationLoop()
    exported = loop.export_review_event(loop.post_action_review(_intent()))

    assert "sleep_state" not in exported
    assert "wake_state" not in exported


def test_no_broad_runtime_authority_creep_is_introduced() -> None:
    loop = VerificationLoop()
    exported = loop.export_review_event(
        loop.post_action_review(
            _intent(),
            _execution(executed_action="Ran checks."),
            observed_outcome="",
        )
    )

    assert "tool_call" not in exported
    assert "orchestration_plan" not in exported
    assert "persistence_write" not in exported
