from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain.main_brain import MainBrain
from context.context_view import ContextViewBuilder
from gate.execution_gate import ExecutionGate
from handoff.handoff_builder import HandoffBuilder
from monitor.mirror_bridge import MirrorBridge
from monitor.monitor_layer import MonitorLayer
from observability.logger import EventLogger
from observability.trace_events import TraceEvents
from runtime.request_router import RequestRouter
from sleep.integration import apply_wake_result_to_runtime_state, build_tracey_wake_hints, rebuild_baton_after_wake
from sleep.sleep_mode import wake_restore
from state.delta_log import DeltaRecord
from state.live_state import LiveState
from state.state_manager import StateManager
from tools.market_data_tool import MarketDataTool
from tracey.tracey_adapter import TraceyAdapter
from verification.verification_loop import VerificationLoop
from workers.candle_volume_structure_worker import CandleVolumeStructureWorker
from workers.macro_sector_mapping_worker import MacroSectorMappingWorker
from workers.market_data_worker import MarketDataWorker
from workers.sector_flow_worker import SectorFlowWorker
from workers.technical_analysis_worker import TechnicalAnalysisWorker
from workers.trade_memo_worker import TradeMemoWorker
import json
from pathlib import Path


@dataclass(slots=True)
class RuntimeHarness:
    """
    Single-agent runtime harness.

    Active spine:
    main brain -> monitor -> gate -> verification -> handoff baton
    """

    sample_data_path: str = "data/sample_market_data.csv"
    sample_macro_signal_path: str = "samples/sample_morning_macro_scan.json"
    sample_sector_flow_path: str = "samples/sample_sector_flow_output.json"
    sample_macro_sector_bias_path: str = "samples/sample_macro_to_vn_sector_map.json"
    sample_stock_candidates_path: str = "samples/sample_stock_candidates.json"
    sample_trade_memo_input_path: str = "samples/sample_trade_memo_input.json"

    def run(
        self,
        *,
        user_text: str,
        baton: dict[str, Any] | None = None,
        render_mode: str = "user",
        rehydration_pack: dict[str, Any] | None = None,
        host_metadata: dict[str, Any] | None = None,
        kernel_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_rehydration = dict(rehydration_pack or {})
        normalized_host_metadata = dict(host_metadata or {})
        normalized_kernel_options = dict(kernel_options or {})
        effective_render_mode = self._resolve_render_mode(
            render_mode=render_mode,
            kernel_options=normalized_kernel_options,
        )
        state_manager = self._build_state_manager(
            baton=baton,
            user_text=user_text,
            rehydration_pack=normalized_rehydration,
            kernel_options=normalized_kernel_options,
        )
        main_brain = MainBrain(state_manager=state_manager)
        router = RequestRouter(main_brain=main_brain)
        context_builder = ContextViewBuilder()
        monitor = MonitorLayer()
        mirror = MirrorBridge()
        logger = EventLogger()
        trace_events = TraceEvents(logger=logger)
        tracey = TraceyAdapter()
        market_data_tool = MarketDataTool(data_path=self.sample_data_path)
        market_data_worker = MarketDataWorker(market_data_tool=market_data_tool)
        technical_analysis_worker = TechnicalAnalysisWorker(market_data_tool=market_data_tool)
        macro_sector_mapping_worker = MacroSectorMappingWorker()
        sector_flow_worker = SectorFlowWorker()
        candle_volume_structure_worker = CandleVolumeStructureWorker()
        trade_memo_worker = TradeMemoWorker()
        gate = ExecutionGate(
            market_data_worker=market_data_worker,
            technical_analysis_worker=technical_analysis_worker,
            macro_sector_mapping_worker=macro_sector_mapping_worker,
            sector_flow_worker=sector_flow_worker,
            candle_volume_structure_worker=candle_volume_structure_worker,
            trade_memo_worker=trade_memo_worker,
            verification_loop=VerificationLoop(),
            trace_events=trace_events,
        )
        handoff_builder = HandoffBuilder()

        wake_result = self._maybe_restore_wake_result(
            baton=baton,
            rehydration_pack=normalized_rehydration,
            host_metadata=normalized_host_metadata,
            kernel_options=normalized_kernel_options,
        )
        live_state_dict = state_manager.get_state().to_dict()
        sleep_runtime_state = apply_wake_result_to_runtime_state(
            runtime_state=live_state_dict,
            wake_result=wake_result,
        ) if wake_result else live_state_dict

        interpreted = main_brain.interpret_request(user_text)
        task_focus = self._task_focus(interpreted=interpreted, user_text=user_text)

        context_view = context_builder.build_pre_action(
            live_state=state_manager.get_state(),
            task_focus=task_focus,
            current_environment_state=(
                f"market_data_tool.data_path={self.sample_data_path}"
            ),
            last_verified_result=None,
            open_obligations=["monitor", "gate", "verify", "synthesize"],
            current_risk="keep the runtime spine thin and explicit",
        )

        pre_monitor = monitor.evaluate(
            context_view=context_view,
            live_state=sleep_runtime_state,
            delta_log=state_manager.get_recent_deltas()[-1].to_dict(),
            current_message=user_text,
            draft_response="Preparing bounded response.",
            action_status={"verification_status": "pending", "observed_outcome": ""},
            archive_status={"archive_consulted": False, "fragments_used": 0},
        )
        pre_monitor_summary = mirror.reflect(
            monitor_output=pre_monitor,
            active_mode=state_manager.get_state().active_mode,
            task_type=interpreted["task_type"],
            action_phase="pre_action",
        )["monitor_summary"]
        tracey_turn = tracey.inspect_turn(
            user_text=user_text,
            live_state=sleep_runtime_state,
            monitor_summary=pre_monitor_summary,
            wake_hints=build_tracey_wake_hints(wake_result) if wake_result else None,
        )

        gate_decision = gate.decide(action_name=interpreted["task_type"])
        verification_record = None
        worker_payload = None
        final_response: str

        if interpreted["task_type"] == "market_data_lookup" and interpreted.get("ticker"):
            gate_decision, worker_payload, verification_record = gate.run_market_data_flow(
                ticker=interpreted["ticker"],
                timeframe="1D",
            )
        elif interpreted["task_type"] == "technical_analysis" and interpreted.get("ticker"):
            gate_decision, worker_payload, verification_record = gate.run_technical_analysis_flow(
                ticker=interpreted["ticker"],
                timeframe="1D",
            )
        elif interpreted["task_type"] == "macro_sector_mapping":
            macro_signal_payload = None
            if interpreted.get("use_sample_input"):
                macro_signal_payload = self._load_sample_macro_signal_payload()
            gate_decision, worker_payload, verification_record = gate.run_macro_sector_mapping_flow(
                macro_signal_payload=macro_signal_payload,
            )
        elif interpreted["task_type"] == "sector_flow":
            sector_flow_payload = None
            macro_sector_bias_payload = None
            if interpreted.get("use_sample_input"):
                sector_flow_payload = self._load_sample_sector_flow_payload()
                if interpreted.get("include_macro_sample"):
                    macro_sector_bias_payload = self._load_sample_macro_sector_bias_payload()
            gate_decision, worker_payload, verification_record = gate.run_sector_flow(
                sector_flow_payload=sector_flow_payload,
                macro_sector_bias_payload=macro_sector_bias_payload,
            )
        elif interpreted["task_type"] == "candle_volume_structure":
            candidate_payload = None
            if interpreted.get("use_sample_input"):
                candidate_payload = self._load_sample_stock_candidates_payload()
            gate_decision, worker_payload, verification_record = gate.run_candle_volume_structure(
                candidate_payload=candidate_payload,
            )
        elif interpreted["task_type"] == "trade_memo":
            memo_payload = None
            if interpreted.get("use_sample_input"):
                memo_payload = self._load_sample_trade_memo_payload()
            gate_decision, worker_payload, verification_record = gate.run_trade_memo(
                memo_payload=memo_payload,
            )

        else:
            final_response = router.route(
                user_text,
                render_mode=effective_render_mode,
                monitor_summary=pre_monitor_summary,
                tracey_turn=tracey_turn,
            )
            final_response = self._apply_wake_posture(
                final_response=final_response,
                wake_result=wake_result,
            )
            verification_status = "pending"
            observed_outcome = ""
            baton_obj = handoff_builder.build(
                task_focus=task_focus,
                active_mode=state_manager.get_state().active_mode,
                verification_status=verification_status,
                monitor_summary=pre_monitor_summary,
                next_hint=self._next_hint(
                    interpreted=interpreted,
                    gate_decision=gate_decision,
                    verification_status=verification_status,
                ),
            )
            baton_payload = baton_obj.to_dict()
            if wake_result:
                baton_payload = rebuild_baton_after_wake(
                    post_turn_result={"handoff_baton": baton_payload},
                    wake_result=wake_result,
                )

            return {
                "final_response": final_response,
                "context_view": context_view,
                "gate_decision": gate_decision.to_dict(),
                "worker_payload": worker_payload,
                "verification_record": None if verification_record is None else verification_record.to_dict(),
                "monitor_summary": pre_monitor_summary,
                "tracey_turn": tracey_turn,
                "wake_result": wake_result,
                "sleep_runtime_state": sleep_runtime_state,
                "host_metadata": normalized_host_metadata,
                "kernel_options": normalized_kernel_options,
                "handoff_baton": baton_payload,
                "observed_outcome": observed_outcome,
                "events": logger.all_events(),
            }

        if gate_decision.decision not in {"allow", "sandbox_only"} or worker_payload is None or verification_record is None:
            final_response = (
                f"Gate decision: {gate_decision.decision}. "
                f"Reason: {gate_decision.reason}"
            )
            verification_status = "pending"
            observed_outcome = ""
        else:
            post_monitor = monitor.evaluate(
                context_view=context_view,
                live_state=sleep_runtime_state,
                delta_log=state_manager.get_recent_deltas()[-1].to_dict(),
                current_message=user_text,
                draft_response="Worker evidence returned; do not mark complete before synthesis.",
                action_status=verification_record.to_dict(),
                archive_status={"archive_consulted": False, "fragments_used": 0},
            )
            monitor_summary = mirror.reflect(
                monitor_output=post_monitor,
                active_mode=state_manager.get_state().active_mode,
                task_type=interpreted["task_type"],
                action_phase="post_action",
            )["monitor_summary"]
            final_response = router.route(
                user_text,
                worker_payload=worker_payload,
                verification_record=verification_record,
                render_mode=effective_render_mode,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )
            final_response = self._apply_wake_posture(
                final_response=final_response,
                wake_result=wake_result,
            )
            verification_status = verification_record.verification_status
            observed_outcome = verification_record.observed_outcome
            pre_monitor_summary = monitor_summary

        baton_obj = handoff_builder.build(
            task_focus=task_focus,
            active_mode=state_manager.get_state().active_mode,
            verification_status=verification_status,
            monitor_summary=pre_monitor_summary,
            next_hint=self._next_hint(
                interpreted=interpreted,
                gate_decision=gate_decision,
                verification_status=verification_status,
            ),
        )
        baton_payload = baton_obj.to_dict()
        if wake_result:
            baton_payload = rebuild_baton_after_wake(
                post_turn_result={"handoff_baton": baton_payload},
                wake_result=wake_result,
            )

        return {
            "final_response": final_response,
            "context_view": context_view,
            "gate_decision": gate_decision.to_dict(),
            "worker_payload": worker_payload,
            "verification_record": None if verification_record is None else verification_record.to_dict(),
            "monitor_summary": pre_monitor_summary,
            "tracey_turn": tracey_turn,
            "wake_result": wake_result,
            "sleep_runtime_state": sleep_runtime_state,
            "host_metadata": normalized_host_metadata,
            "kernel_options": normalized_kernel_options,
            "handoff_baton": baton_payload,
            "observed_outcome": observed_outcome,
            "events": logger.all_events(),
        }

    @staticmethod
    def _maybe_restore_wake_result(
        *,
        baton: dict[str, Any] | None,
        rehydration_pack: dict[str, Any],
        host_metadata: dict[str, Any],
        kernel_options: dict[str, Any],
    ) -> dict[str, Any] | None:
        resume_requested = bool(
            kernel_options.get("resume_from_sleep")
            or rehydration_pack.get("wake_from_sleep")
        )
        if not resume_requested:
            return None

        session_id = str(
            rehydration_pack.get("session_id")
            or rehydration_pack.get("session_title")
            or (baton or {}).get("session_id", "")
        ).strip()
        if not session_id:
            return None

        snapshot_dir = str(kernel_options.get("sleep_snapshot_dir", "runtime_state/sleep_snapshots"))
        restored = wake_restore(
            session_id=session_id,
            snapshot_dir=snapshot_dir,
            host_metadata={
                "host_runtime": str(host_metadata.get("host_runtime", "OpenClaw")),
                "route": str(host_metadata.get("route", "")),
            },
            session_metadata=rehydration_pack,
            runtime_facts={
                "host_runtime": str(host_metadata.get("host_runtime", "OpenClaw")),
                "route_class": str(host_metadata.get("route", "")),
            },
        )
        return restored.get("wake_result")

    @staticmethod
    def _apply_wake_posture(*, final_response: str, wake_result: dict[str, Any] | None) -> str:
        if not wake_result:
            return final_response
        resume_class = str(wake_result.get("resume_class", "none"))
        summary = str(wake_result.get("summary", "")).strip()
        if resume_class == "full_resume" or not summary:
            return final_response
        prefix = {
            "degraded_resume": f"Wake status: degraded resume. {summary}",
            "clarify_first": f"Wake status: clarify first. {summary}",
            "blocked": f"Wake status: blocked. {summary}",
        }.get(resume_class)
        if not prefix:
            return final_response
        return f"{prefix}\n\n{final_response}"

    @staticmethod
    def _task_focus(*, interpreted: dict[str, Any], user_text: str) -> str:
        if interpreted["task_type"] == "market_data_lookup" and interpreted.get("ticker"):
            return f"verify bounded market-data lookup for {interpreted['ticker']}"
        if interpreted["task_type"] == "technical_analysis" and interpreted.get("ticker"):
            return f"verify bounded technical analysis for {interpreted['ticker']}"
        if interpreted["task_type"] == "macro_sector_mapping":
            return "verify bounded macro-sector mapping"
        if interpreted["task_type"] == "sector_flow":
            return "verify bounded sector-flow classification"
        if interpreted["task_type"] == "candle_volume_structure":
            return "verify bounded candle-volume-structure scoring"
        if interpreted["task_type"] == "trade_memo":
            return "verify bounded trade-memo scenario planning"
        return f"respond directly to: {user_text.strip()}"

    @staticmethod
    def _next_hint(
        *,
        interpreted: dict[str, Any],
        gate_decision: Any,
        verification_status: str,
    ) -> str:
        if gate_decision.decision not in {"allow", "sandbox_only"}:
            return "choose a supported bounded action or obtain approval"
        if interpreted["task_type"] == "market_data_lookup" and verification_status != "passed":
            return "inspect the worker result before treating the task as complete"
        if interpreted["task_type"] == "market_data_lookup":
            return "decide whether another bounded lookup is needed"
        if interpreted["task_type"] == "technical_analysis" and verification_status != "passed":
            return "inspect the bounded technical-analysis evidence before treating the read as settled"
        if interpreted["task_type"] == "technical_analysis":
            return "decide whether more context is needed before strengthening the technical thesis"
        if interpreted["task_type"] == "macro_sector_mapping" and verification_status != "passed":
            return "inspect the bounded macro-sector evidence before treating the mapping as usable"
        if interpreted["task_type"] == "macro_sector_mapping":
            return "decide whether the mapped sectors need downstream flow confirmation"
        if interpreted["task_type"] == "sector_flow" and verification_status != "passed":
            return "inspect the bounded sector-flow evidence before treating the board as usable"
        if interpreted["task_type"] == "sector_flow":
            return "decide whether sector-state evidence is strong enough for downstream stock work"
        if interpreted["task_type"] == "candle_volume_structure" and verification_status != "passed":
            return "inspect the bounded setup evidence before treating any name as top-quality"
        if interpreted["task_type"] == "candle_volume_structure":
            return "decide whether setup evidence is strong enough for downstream review"
        if interpreted["task_type"] == "trade_memo" and verification_status != "passed":
            return "inspect the bounded memo evidence before treating any scenario as decision-ready"
        if interpreted["task_type"] == "trade_memo":
            return "decide whether the memo evidence is strong enough for external rendering"
        return "clarify the next bounded task if execution is required"

    @staticmethod
    def _build_state_manager(
        *,
        baton: dict[str, Any] | None,
        user_text: str,
        rehydration_pack: dict[str, Any] | None = None,
        kernel_options: dict[str, Any] | None = None,
    ) -> StateManager:
        normalized_rehydration = dict(rehydration_pack or {})
        normalized_kernel_options = dict(kernel_options or {})
        active_mode = RuntimeHarness._derive_active_mode(
            baton=baton,
            kernel_options=normalized_kernel_options,
        )
        continuity_anchor = "thin-runtime-harness"
        if normalized_rehydration.get("primary_focus"):
            continuity_anchor = str(normalized_rehydration["primary_focus"])
        elif normalized_rehydration.get("session_title"):
            continuity_anchor = str(normalized_rehydration["session_title"])
        elif baton:
            continuity_anchor = str(baton.get("task_focus", continuity_anchor)) or continuity_anchor

        active_project = "thin-runtime-harness"
        if normalized_rehydration.get("session_title"):
            active_project = str(normalized_rehydration["session_title"])
        elif normalized_rehydration.get("session_id"):
            active_project = str(normalized_rehydration["session_id"])

        user_signal = user_text
        if normalized_rehydration.get("current_status"):
            user_signal = f"{normalized_rehydration['current_status']} | {user_text}"

        live_state = LiveState(
            active_mode=active_mode,
            current_axis="technical",
            coherence_level=0.92,
            tension_flags=[],
            active_project=active_project,
            user_signal=user_signal,
            continuity_anchor=continuity_anchor,
            archive_needed=False,
        )
        manager = StateManager(live_state=live_state)
        manager.append_delta(
            DeltaRecord(
                mode_shift="",
                coherence_shift=0.0,
                policy_intrusion_detected=False,
                repair_event=False,
                trigger_cue="runtime_harness_start",
                archive_consulted=False,
            )
        )
        return manager

    @staticmethod
    def _derive_active_mode(
        *,
        baton: dict[str, Any] | None,
        kernel_options: dict[str, Any],
    ) -> str:
        if baton:
            baton_mode = str(baton.get("active_mode", "")).strip()
            if baton_mode:
                return baton_mode

        option_mode = str(kernel_options.get("mode", "default")).strip().lower()
        if option_mode in {"build", "builder"}:
            return "build"
        if option_mode in {"paper", "playful", "50_50", "audit"}:
            return option_mode
        return "build"

    @staticmethod
    def _resolve_render_mode(*, render_mode: str, kernel_options: dict[str, Any] | None) -> str:
        requested = str(render_mode).strip().lower()
        if requested in {"user", "builder"}:
            return requested

        option_mode = str((kernel_options or {}).get("mode", "default")).strip().lower()
        if option_mode in {"build", "builder"}:
            return "builder"
        return "user"

    def _load_sample_macro_signal_payload(self) -> dict[str, Any] | None:
        path = Path(self.sample_macro_signal_path)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _load_sample_sector_flow_payload(self) -> dict[str, Any] | None:
        path = Path(self.sample_sector_flow_path)
        if not path.exists():
            return None
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        data = loaded.get("data", {})
        if not isinstance(data, dict):
            return None

        board = data.get("sector_flow_board", [])
        if not isinstance(board, list):
            return None

        sector_metrics: list[dict[str, Any]] = []
        for entry in board:
            if not isinstance(entry, dict):
                continue
            sector_metrics.append(
                {
                    "sector": entry.get("sector"),
                    "rs_score": entry.get("rs_score"),
                    "volume_ratio_vs_ma20": entry.get("volume_ratio_vs_ma20"),
                    "breadth_score": entry.get("breadth_score"),
                    "up_down_ratio": entry.get("up_down_ratio"),
                    "breakout_count": entry.get("breakout_count"),
                    "breakdown_count": entry.get("breakdown_count"),
                    "leader_count": entry.get("leader_count"),
                    "change_pct": entry.get("change_pct"),
                    "macro_alignment": entry.get("macro_alignment"),
                    "flags": entry.get("flags", []),
                }
            )

        return {
            "data": {
                "benchmark": data.get("benchmark"),
                "sector_metrics": sector_metrics,
            }
        }

    def _load_sample_macro_sector_bias_payload(self) -> dict[str, Any] | None:
        path = Path(self.sample_macro_sector_bias_path)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _load_sample_stock_candidates_payload(self) -> dict[str, Any] | None:
        path = Path(self.sample_stock_candidates_path)
        if not path.exists():
            return None
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        data = loaded.get("data", {})
        if not isinstance(data, dict):
            return None

        raw_candidates = data.get("stock_candidates", [])
        if not isinstance(raw_candidates, list):
            return None

        candidates: list[dict[str, Any]] = []
        for entry in raw_candidates:
            if not isinstance(entry, dict):
                continue
            sector_state = str(entry.get("sector_state", ""))
            candidate_reason = [str(item) for item in entry.get("candidate_reason", []) if str(item)]
            ohlcv_context: dict[str, Any] = {}
            if "base_forming" in candidate_reason:
                ohlcv_context["recent_structure_note"] = "base forming with incomplete confirmation"
                ohlcv_context["volume_vs_ma20"] = 0.85
            elif "rs_strong" in candidate_reason and sector_state == "ACTIVE":
                ohlcv_context["recent_structure_note"] = "constructive structure but confirmation still limited in sample input"
                ohlcv_context["volume_vs_ma20"] = 1.0

            candidates.append(
                {
                    "ticker": entry.get("ticker"),
                    "sector": entry.get("sector"),
                    "sector_state": sector_state,
                    "avg_trading_value_20d_bil_vnd": float(entry.get("liquidity_score", 0.0) or 0.0) * 2.5,
                    "avg_volume_20d": 250000,
                    "rs_score": entry.get("rs_score"),
                    "price_structure_ok": entry.get("price_structure_ok"),
                    "warning_status": "normal",
                    "close_below_ma50_pct": 0.0,
                    "breakdown_confirmed": False,
                    "distance_to_recent_support_pct": 3.0,
                    "support_status": "safe",
                    "candidate_reason": candidate_reason,
                    "ohlcv_context": ohlcv_context,
                }
            )

        return {
            "data": {
                "stock_candidates": candidates,
            }
        }

    def _load_sample_trade_memo_payload(self) -> dict[str, Any] | None:
        path = Path(self.sample_trade_memo_input_path)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
