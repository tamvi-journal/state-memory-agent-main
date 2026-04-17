from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from family.compression_layer import CompressionLayer
from family.context_view import ContextViewBuilder
from family.delta_log import DeltaLogBuilder
from family.disagreement_types import DisagreementEvent
from family.effort_allocator import EffortAllocator
from family.effort_types import EffortInput
from family.execution_gate import ExecutionGate
from family.execution_types import ExecutionRequest
from family.live_state import LiveStateBuilder
from family.mirror_bridge import MirrorBridge
from family.mode_inference import ModeInference
from family.monitor_layer import MonitorLayer
from family.reactivation_layer import ReactivationLayer
from family.router_decision import FamilyRouterDecision
from family.router_types import RouterInput
from family.turn_pipeline_types import FamilyTurnInput, FamilyTurnResult


@dataclass(slots=True)
class FamilyTurnPipeline:
    context_builder: ContextViewBuilder = field(default_factory=ContextViewBuilder)
    mode_inference: ModeInference = field(default_factory=ModeInference)
    live_state_builder: LiveStateBuilder = field(default_factory=LiveStateBuilder)
    monitor_layer: MonitorLayer = field(default_factory=MonitorLayer)
    mirror_bridge: MirrorBridge = field(default_factory=MirrorBridge)
    effort_allocator: EffortAllocator = field(default_factory=EffortAllocator)
    router: FamilyRouterDecision = field(default_factory=FamilyRouterDecision)
    execution_gate: ExecutionGate = field(default_factory=ExecutionGate)
    delta_builder: DeltaLogBuilder = field(default_factory=DeltaLogBuilder)
    compression_layer: CompressionLayer = field(default_factory=CompressionLayer)
    reactivation_layer: ReactivationLayer = field(default_factory=ReactivationLayer)

    def run(self, turn_input: FamilyTurnInput | dict[str, Any]) -> FamilyTurnResult:
        if isinstance(turn_input, dict):
            turn_input = FamilyTurnInput(**turn_input)

        disagreement_event = self._primary_disagreement_event(turn_input.disagreement_events)
        disagreement_open = bool(disagreement_event and disagreement_event.still_open)

        context_view = self.context_builder.build(
            {
                "active_project": turn_input.active_project,
                "active_mode": "",
                "current_task": turn_input.current_task,
                "current_environment_state": turn_input.current_environment_state or "dry family turn pipeline",
                "last_verified_result": turn_input.last_verified_result,
                "open_obligations": turn_input.open_obligations,
                "verification_status": turn_input.verification_status,
                "disagreement_events": turn_input.disagreement_events,
                "risk_hint": turn_input.monitor_hint,
                "monitor_summary": None,
                "recent_anchor_cue": turn_input.recent_anchor_cue,
            }
        ).to_dict()

        mode_result = self.mode_inference.infer(
            {
                "current_message": turn_input.current_message,
                "active_project": turn_input.active_project,
                "current_task": turn_input.current_task,
                "recent_anchor_cue": turn_input.recent_anchor_cue,
                "context_view_summary": self._context_summary(context_view),
                "action_required": turn_input.action_required,
                "disagreement_open": disagreement_open,
                "verification_status": turn_input.verification_status,
                "explicit_mode_hint": turn_input.explicit_mode_hint,
            }
        ).to_dict()

        monitor_output = self.monitor_layer.pre_action_monitor(
            active_mode=mode_result["active_mode"],
            task_type=self._task_type(turn_input.current_message, turn_input.current_task),
            context_view={
                "task_focus": context_view["task_focus"],
                "current_execution_boundary": turn_input.execution_intent or turn_input.current_task,
            },
            draft_response=turn_input.current_message,
            archive_status={
                "archive_consulted": turn_input.archive_consulted,
                "fragments_used": 1 if turn_input.archive_consulted else 0,
            },
            project_relevance_markers={
                "project_relevant": self._project_relevant(turn_input.current_message, turn_input.active_project),
            },
        ).to_dict()

        mirror_summary = self.mirror_bridge.build_mirror_summary(
            monitor_output=monitor_output,
            active_mode=mode_result["active_mode"],
            task_type=self._task_type(turn_input.current_message, turn_input.current_task),
            phase="pre_action",
        ).to_dict()

        live_state = self.live_state_builder.build(
            {
                "context_view": context_view,
                "mode_inference_result": mode_result,
                "verification_status": turn_input.verification_status,
                "active_project": turn_input.active_project,
                "recent_anchor_cue": turn_input.recent_anchor_cue,
                "disagreement_open": disagreement_open,
                "monitor_summary": mirror_summary,
                "current_axis_hint": "",
            }
        ).to_dict()

        effort_route = self.effort_allocator.route(
            EffortInput(
                task_type=self._task_type(turn_input.current_message, turn_input.current_task),
                domain=self._domain(turn_input.active_project, mode_result["active_mode"]),
                active_mode=mode_result["active_mode"],
                mode_confidence=float(mode_result["confidence"]),
                ambiguity_score=self._ambiguity_score(turn_input.current_message, disagreement_open, mirror_summary),
                risk_score=self._risk_score(turn_input.verification_status, disagreement_open, mirror_summary),
                stakes_signal=None,
                stakes_confidence=0.0,
                action_required=turn_input.action_required,
                memory_commit_possible=False,
                disagreement_likelihood=0.75 if disagreement_open else 0.10,
                cue_strength=self._cue_strength(turn_input.current_message, turn_input.recent_anchor_cue, turn_input.active_project),
                verification_gap_estimate=0.75 if turn_input.verification_status.lower() in {"pending", "failed", "unknown"} else 0.10,
                high_risk_domain=False,
                unanswerable_likelihood=0.65 if "not sure" in turn_input.current_message.lower() else 0.10,
            )
        ).to_dict()

        router_decision = self.router.decide(
            RouterInput(
                task_type=self._task_type(turn_input.current_message, turn_input.current_task),
                effort_route=self.effort_allocator.route(
                    EffortInput(
                        task_type=self._task_type(turn_input.current_message, turn_input.current_task),
                        domain=self._domain(turn_input.active_project, mode_result["active_mode"]),
                        active_mode=mode_result["active_mode"],
                        mode_confidence=float(mode_result["confidence"]),
                        ambiguity_score=self._ambiguity_score(turn_input.current_message, disagreement_open, mirror_summary),
                        risk_score=self._risk_score(turn_input.verification_status, disagreement_open, mirror_summary),
                        stakes_signal=None,
                        stakes_confidence=0.0,
                        action_required=turn_input.action_required,
                        memory_commit_possible=False,
                        disagreement_likelihood=0.75 if disagreement_open else 0.10,
                        cue_strength=self._cue_strength(turn_input.current_message, turn_input.recent_anchor_cue, turn_input.active_project),
                        verification_gap_estimate=0.75 if turn_input.verification_status.lower() in {"pending", "failed", "unknown"} else 0.10,
                        high_risk_domain=False,
                        unanswerable_likelihood=0.65 if "not sure" in turn_input.current_message.lower() else 0.10,
                    )
                ),
                disagreement_event=disagreement_event,
                mirror_summary=self.mirror_bridge.build_mirror_summary(
                    monitor_output=monitor_output,
                    active_mode=mode_result["active_mode"],
                    task_type=self._task_type(turn_input.current_message, turn_input.current_task),
                    phase="pre_action",
                ),
                verification_status=turn_input.verification_status,
                active_mode=mode_result["active_mode"],
                domain=self._domain(turn_input.active_project, mode_result["active_mode"]),
                action_required=turn_input.action_required,
            )
        ).to_dict()

        execution_request = {}
        execution_decision = {}
        approval_request = {}
        if turn_input.action_required:
            execution_request_obj = self._build_execution_request(turn_input)
            execution_request = execution_request_obj.to_dict()
            execution_decision_obj = self.execution_gate.assess(execution_request_obj)
            execution_decision = execution_decision_obj.to_dict()
            if execution_decision_obj.decision == "require_approval":
                approval_request = self.execution_gate.build_approval_request(
                    execution_request_obj,
                    execution_decision_obj,
                ).to_dict()

        verification_record = self._verification_placeholder(
            turn_input,
            execution_decision=execution_decision,
        )

        previous_live_state = (
            dict(turn_input.previous_live_state)
            if turn_input.previous_live_state
            else self._default_previous_live_state(turn_input, context_view, mode_result)
        )
        delta_log_event = self.delta_builder.build(
            {
                "previous_live_state": previous_live_state,
                "current_live_state": live_state,
                "recent_trigger_cue": turn_input.recent_anchor_cue or turn_input.current_task or "dry family turn",
                "archive_consulted": turn_input.archive_consulted,
                "verification_before": str(previous_live_state.get("verification_status", "")),
                "verification_after": live_state["verification_status"],
            }
        ).to_dict()

        compression_summary = self.compression_layer.build(
            {
                "context_view": context_view,
                "live_state": live_state,
                "delta_log_event": delta_log_event,
                "recent_anchor_cue": turn_input.recent_anchor_cue,
                "verification_status": turn_input.verification_status,
                "disagreement_open": disagreement_open,
                "current_question": "",
                "task_focus": turn_input.current_task,
            }
        ).to_dict()

        reactivation_result = self.reactivation_layer.build(
            {
                "current_message": turn_input.current_message,
                "detected_cues": self._detected_cues(turn_input.current_message, turn_input.recent_anchor_cue, turn_input.active_project),
                "active_project_hint": turn_input.active_project,
                "compression_summary": compression_summary,
                "context_view": context_view,
                "live_state": live_state,
                "recent_anchor_cue": turn_input.recent_anchor_cue,
                "disagreement_open": disagreement_open,
                "verification_status": turn_input.verification_status,
                "mode_hint": mode_result["active_mode"],
            }
        ).to_dict()

        notes = [
            "dry pipeline canary composed family-layer stages without real execution",
        ]
        if execution_decision:
            notes.append(
                f"execution gate result: {execution_decision['decision']} ({execution_decision['recommended_zone']})"
            )
            if execution_decision["decision"] == "require_approval":
                notes.append("runtime action remained approval-gated and was not executed")
            elif execution_decision["decision"] == "deny":
                notes.append("runtime action was denied, so verification remained non-passing")
            else:
                notes.append("execution posture was allowed in principle, but this dry canary still executed nothing")
        else:
            notes.append("no runtime action was requested, so execution objects remained empty")
        if disagreement_open:
            notes.append("open disagreement remained visible across context, live state, router, and compression")
        if turn_input.verification_status.lower() in {"pending", "failed", "unknown"}:
            notes.append("verification posture remained visible and was not auto-passed")

        return FamilyTurnResult(
            context_view=context_view,
            mode_inference=mode_result,
            live_state=live_state,
            monitor_output=monitor_output,
            mirror_summary=mirror_summary,
            effort_route=effort_route,
            router_decision=router_decision,
            execution_request=execution_request,
            execution_decision=execution_decision,
            approval_request=approval_request,
            verification_record=verification_record,
            delta_log_event=delta_log_event,
            compression_summary=compression_summary,
            reactivation_result=reactivation_result,
            notes=notes,
        )

    @staticmethod
    def _context_summary(context_view: dict[str, Any]) -> str:
        return " ".join(
            [
                str(context_view.get("task_focus", "")),
                str(context_view.get("current_risk", "")),
                str(context_view.get("shared_disagreement_status", "")),
            ]
        ).strip()

    @staticmethod
    def _task_type(message: str, current_task: str) -> str:
        haystack = f"{message} {current_task}".lower()
        if any(token in haystack for token in ("review", "debug", "correctness", "audit", "verify")):
            return "verify"
        if any(token in haystack for token in ("architecture", "build", "implementation", "code", "scaffold")):
            return "architecture"
        if any(token in haystack for token in ("research", "investigate")):
            return "research"
        if any(token in haystack for token in ("run", "apply", "perform", "update", "execute")):
            return "execution"
        return "chat"

    @staticmethod
    def _domain(active_project: str, active_mode: str) -> str:
        if active_project:
            return "build"
        if active_mode in {"care", "playful"}:
            return "relational"
        if active_mode == "audit":
            return "audit"
        return "generic"

    @staticmethod
    def _ambiguity_score(message: str, disagreement_open: bool, mirror_summary: dict[str, Any]) -> float:
        haystack = message.lower()
        if mirror_summary.get("primary_risk") == "ambiguity":
            return 0.80
        if disagreement_open or any(token in haystack for token in ("not sure", "either", "both", "ambiguous")):
            return 0.75
        return 0.20

    @staticmethod
    def _risk_score(verification_status: str, disagreement_open: bool, mirror_summary: dict[str, Any]) -> float:
        if verification_status.lower() in {"pending", "failed", "unknown"}:
            return 0.80
        if disagreement_open:
            return 0.65
        if mirror_summary.get("primary_risk") in {"fake_progress", "mode_decay"}:
            return 0.70
        return 0.20

    @staticmethod
    def _cue_strength(message: str, recent_anchor_cue: str, active_project: str) -> float:
        haystack = message.lower()
        supports = 0
        for cue in (recent_anchor_cue, active_project):
            tokens = [token for token in re.findall(r"[a-z0-9_]+", cue.lower()) if len(token) >= 3]
            if cue and any(token in haystack for token in tokens):
                supports += 1
        if supports >= 2:
            return 0.85
        if supports == 1:
            return 0.55
        return 0.10

    @staticmethod
    def _project_relevant(message: str, active_project: str) -> bool:
        if not active_project:
            return True
        return active_project.lower() in message.lower()

    @staticmethod
    def _primary_disagreement_event(disagreement_events: list[dict[str, Any]]) -> DisagreementEvent | None:
        for event in disagreement_events:
            if event.get("still_open", False):
                return DisagreementEvent(
                    event_id=str(event.get("event_id", "dg_pipeline")),
                    timestamp=str(event.get("timestamp", "2026-04-17T00:00:00Z")),
                    disagreement_type=str(event.get("disagreement_type", "action")),
                    tracey_position=str(event.get("tracey_position", "preserve local continuity line")),
                    seyn_position=str(event.get("seyn_position", "preserve verification-first line")),
                    severity=float(event.get("severity", 0.70)),
                    still_open=bool(event.get("still_open", True)),
                    later_resolution=str(event.get("later_resolution", "")),
                    house_law_implicated=str(event.get("house_law_implicated", "")),
                    action_lead_selected=event.get("action_lead_selected"),
                    epistemic_resolution_claimed=bool(event.get("epistemic_resolution_claimed", False)),
                )
        return None

    @staticmethod
    def _verification_placeholder(
        turn_input: FamilyTurnInput,
        *,
        execution_decision: dict[str, Any],
    ) -> dict[str, Any]:
        notes = ["dry pipeline canary: no real action executed, so verification is conservative"]
        if turn_input.verification_status:
            notes.append(f"incoming verification posture: {turn_input.verification_status}")
        if turn_input.last_verified_result:
            notes.append("last verified result is carried as compact context, not fresh verification")
        if execution_decision:
            notes.append(f"execution gate decision: {execution_decision['decision']}")
            if execution_decision["decision"] == "require_approval":
                notes.append("approval is required before any runtime action can occur")
            elif execution_decision["decision"] == "deny":
                notes.append("runtime action is denied, so no execution outcome exists")
            elif execution_decision["decision"] == "allow":
                notes.append("runtime posture is allowed, but the dry canary still did not execute the action")
        return {
            "intended_action": turn_input.current_task or turn_input.current_message[:80],
            "executed_action": "",
            "expected_change": turn_input.execution_intent or turn_input.current_task or "dry-run family turn progression",
            "observed_outcome": turn_input.last_verified_result,
            "verification_status": "unknown",
            "evidence": [],
            "notes": notes,
        }

    @staticmethod
    def _build_execution_request(turn_input: FamilyTurnInput) -> ExecutionRequest:
        haystack = f"{turn_input.current_message} {turn_input.current_task} {turn_input.execution_intent}".lower()

        if any(token in haystack for token in ("inspect", "read", "list", "metadata")):
            return ExecutionRequest(
                action_type="inspect",
                target_type="repo_metadata",
                target_path_or_ref=turn_input.active_project or turn_input.current_task,
                requested_zone="inspection",
                writes_state=False,
                executes_code=False,
                network_required=False,
                package_install_required=False,
                secret_access_required=False,
                source_trust_stage="reviewed",
                reason=turn_input.execution_intent or turn_input.current_task or turn_input.current_message,
            )

        if any(token in haystack for token in ("install", "package", "dependency", "pip", "pytest")):
            return ExecutionRequest(
                action_type="install",
                target_type="package",
                target_path_or_ref=turn_input.execution_intent or turn_input.current_task or "requested-package",
                requested_zone="host",
                writes_state=False,
                executes_code=False,
                network_required=False,
                package_install_required=True,
                secret_access_required=False,
                source_trust_stage="unknown",
                reason=turn_input.execution_intent or turn_input.current_task or turn_input.current_message,
            )

        if any(token in haystack for token in ("write", "patch", "apply", "update", "commit", "modify")):
            return ExecutionRequest(
                action_type="write_file",
                target_type="repo_file",
                target_path_or_ref=turn_input.execution_intent or turn_input.current_task or turn_input.active_project,
                requested_zone="host",
                writes_state=True,
                executes_code=False,
                network_required=False,
                package_install_required=False,
                secret_access_required=False,
                source_trust_stage="reviewed",
                reason=turn_input.execution_intent or turn_input.current_task or turn_input.current_message,
            )

        return ExecutionRequest(
            action_type="shell_execute",
            target_type="command",
            target_path_or_ref=turn_input.execution_intent or turn_input.current_task or turn_input.current_message,
            requested_zone="host",
            writes_state=False,
            executes_code=True,
            network_required=False,
            package_install_required=False,
            secret_access_required=False,
            source_trust_stage="reviewed",
            reason=turn_input.execution_intent or turn_input.current_task or turn_input.current_message,
        )

    @staticmethod
    def _default_previous_live_state(
        turn_input: FamilyTurnInput,
        context_view: dict[str, Any],
        mode_result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "active_mode": mode_result["active_mode"],
            "current_axis": context_view["task_focus"] or "maintain current state",
            "coherence_level": "mixed" if turn_input.verification_status.lower() in {"pending", "failed", "unknown"} else "stable",
            "tension_flags": [],
            "policy_pressure": "low",
            "active_project": turn_input.active_project,
            "continuity_anchor": turn_input.recent_anchor_cue or turn_input.active_project,
            "user_signal": context_view["task_focus"],
            "archive_needed": False,
            "verification_status": "passed" if turn_input.last_verified_result and not turn_input.verification_status else turn_input.verification_status,
        }

    @staticmethod
    def _detected_cues(message: str, recent_anchor_cue: str, active_project: str) -> list[str]:
        cues = []
        for cue in (recent_anchor_cue, active_project):
            if cue:
                cues.append(cue)
        cues.extend(token for token in re.findall(r"[a-z0-9_]+", message.lower()) if len(token) >= 5)
        compact: list[str] = []
        for cue in cues:
            if cue not in compact:
                compact.append(cue)
        return compact[:5]
