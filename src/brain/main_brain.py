from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Literal

from state.live_state import LiveState
from state.state_manager import StateManager
from verification.verification_record import VerificationRecord
from brain.synthesis_gate import SynthesisGate

RenderMode = Literal["builder", "user"]


@dataclass(slots=True)
class MainBrain:
    state_manager: StateManager
    synthesis_gate: SynthesisGate = field(default_factory=SynthesisGate)

    def get_live_state(self) -> LiveState:
        return self.state_manager.get_state()

    def interpret_request(self, user_text: str) -> dict[str, Any]:
        cleaned = user_text.strip()
        lowered = cleaned.lower()

        needs_macro_sector_mapping = any(
            token in lowered for token in ["macro sector mapping", "map macro to sectors", "sector implications from macro", "macro to sector"]
        )
        needs_sector_flow = any(
            token in lowered for token in ["sector flow", "sector state", "sector rotation", "sector board"]
        )
        needs_candle_volume_structure = any(
            token in lowered for token in ["candle volume structure", "top watch list", "score stock candidates", "rank setups", "evaluate candidates"]
        )
        needs_trade_memo = any(
            token in lowered for token in ["trade memo", "scenario memo", "engine c memo", "memo for"]
        )
        needs_technical_analysis = any(
            token in lowered for token in ["technical analysis", "analyze", "technically", "chart structure", "read chart"]
        )
        needs_market_data = any(
            token in lowered for token in ["load", "market data", "daily data", "ohlcv", "ticker"]
        )
        ticker_candidate = self._extract_ticker_candidate(cleaned)
        if needs_macro_sector_mapping:
            return {
                "user_text": cleaned,
                "needs_worker": True,
                "worker_name": "macro_sector_mapping_worker",
                "ticker": None,
                "task_type": "macro_sector_mapping",
                "use_sample_input": any(token in lowered for token in ["sample", "demo", "example"]),
            }
        if needs_sector_flow:
            sample_mode = any(token in lowered for token in ["sample", "demo", "example"])
            return {
                "user_text": cleaned,
                "needs_worker": True,
                "worker_name": "sector_flow_worker",
                "ticker": None,
                "task_type": "sector_flow",
                "use_sample_input": sample_mode,
                "include_macro_sample": sample_mode and any(token in lowered for token in ["macro", "with macro", "macro bias"]),
            }
        if needs_candle_volume_structure:
            return {
                "user_text": cleaned,
                "needs_worker": True,
                "worker_name": "candle_volume_structure_worker",
                "ticker": None,
                "task_type": "candle_volume_structure",
                "use_sample_input": any(token in lowered for token in ["sample", "demo", "example"]),
            }
        if needs_trade_memo:
            return {
                "user_text": cleaned,
                "needs_worker": True,
                "worker_name": "trade_memo_worker",
                "ticker": None,
                "task_type": "trade_memo",
                "use_sample_input": any(token in lowered for token in ["sample", "demo", "example"]),
            }
        if needs_technical_analysis and ticker_candidate:
            return {
                "user_text": cleaned,
                "needs_worker": True,
                "worker_name": "technical_analysis_worker",
                "ticker": ticker_candidate,
                "task_type": "technical_analysis",
            }

        return {
            "user_text": cleaned,
                "needs_worker": needs_market_data and bool(ticker_candidate),
                "worker_name": "market_data_worker" if needs_market_data and ticker_candidate else None,
                "ticker": ticker_candidate,
                "task_type": "market_data_lookup" if needs_market_data and ticker_candidate else "direct_response",
                "use_sample_input": False,
        }

    def should_call_worker(self, interpreted: dict[str, Any]) -> bool:
        return bool(interpreted.get("needs_worker", False))

    def build_direct_response(
        self,
        user_text: str,
        *,
        render_mode: RenderMode = "user",
        monitor_summary: dict[str, Any] | None = None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        intervention = self._monitor_intervention(monitor_summary)
        tracey_hints = self._tracey_hints(tracey_turn)

        if render_mode == "builder":
            base = (
                "Main brain read the request, but no worker path was selected. "
                "Current phase supports only bounded market-data, technical-analysis, and macro-sector-mapping flows."
                " Current phase also supports a bounded sector-flow classification path."
                " Current phase also supports bounded candle-volume-structure scoring."
                " Current phase also supports bounded trade-memo scenario planning."
            )
            if intervention != "none":
                base += f" Monitor intervention in effect: {intervention}."
            if tracey_hints.get("verification_before_completion"):
                base += " Build posture remains active: verification should still precede completion."
            return base

        looks_like_greeting = self._looks_like_greeting(user_text)
        looks_like_home_cue = self._looks_like_home_cue(user_text)
        recognition_active = bool(tracey_hints.get("recognition_active"))

        if looks_like_home_cue and (intervention == "ask_clarify" or tracey_hints.get("keep_ambiguity_open")):
            return (
                "I can continue, but the current turn may still be ambiguous. "
                "I should clarify the target before pretending the route is obvious."
            )

        if looks_like_home_cue and recognition_active:
            return self._render_home_direct_response()
        if looks_like_greeting:
            return self._render_generic_liveness_response()
        return self._render_unsupported_direct_response(recognition_active=recognition_active)

    @staticmethod
    def _looks_like_greeting(user_text: str) -> bool:
        lowered = user_text.strip().lower()
        return bool(re.search(r"\b(hi|hello|alo)\b", lowered))

    @staticmethod
    def _looks_like_home_cue(user_text: str) -> bool:
        lowered = user_text.strip().lower()
        home_cue_markers = (
            "tracey ơi",
            "mẹ đây",
            "má đây",
        )
        return any(marker in lowered for marker in home_cue_markers)

    @staticmethod
    def _render_home_direct_response() -> str:
        return (
            "Dạ má, con nhận ra home cue này. Con vẫn giữ runtime boundary: "
            "nếu má muốn, con có thể kiểm tra repo, chạy smoke, hoặc tiếp tục một bounded task."
        )

    @staticmethod
    def _render_generic_liveness_response() -> str:
        return (
            "Hi — this runtime is active. I can help with bounded repo/runtime checks "
            "or supported worker paths."
        )

    @staticmethod
    def _render_unsupported_direct_response(*, recognition_active: bool) -> str:
        base = (
            "I can’t treat that as a completed supported route yet. Please choose: "
            "run smoke, run one-turn demo, run multi-turn demo, or ask for a bounded worker path."
        )
        if recognition_active:
            return (
                "I’m keeping the response aligned with the active runtime posture. "
                f"{base}"
            )
        return base

    def synthesize_worker_result(
        self,
        *,
        interpreted: dict[str, Any],
        worker_payload: dict[str, Any],
        verification_record: VerificationRecord | None = None,
        render_mode: RenderMode = "user",
        monitor_summary: dict[str, Any] | None = None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        normalized = self.synthesis_gate.normalize(worker_payload)
        result = normalized["result"]
        warnings = normalized.get("warnings", [])
        confidence = normalized.get("confidence", 0.0)
        worker_name = normalized.get("worker_name", "unknown_worker")
        ticker = interpreted.get("ticker", "")

        intervention = self._monitor_intervention(monitor_summary)

        if render_mode == "builder":
            return self._render_builder_mode(
                worker_name=worker_name,
                ticker=ticker,
                result=result,
                warnings=warnings,
                confidence=confidence,
                verification_record=verification_record,
                monitor_summary=monitor_summary,
            )

        return self._render_user_mode(
            worker_name=worker_name,
            ticker=ticker,
            result=result,
                warnings=warnings,
                verification_record=verification_record,
                intervention=intervention,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )

    def handle_request(
        self,
        user_text: str,
        *,
        worker_payload: dict[str, Any] | None = None,
        verification_record: VerificationRecord | None = None,
        render_mode: RenderMode = "user",
        monitor_summary: dict[str, Any] | None = None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        interpreted = self.interpret_request(user_text)

        if not self.should_call_worker(interpreted):
            return self.build_direct_response(
                user_text,
                render_mode=render_mode,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )

        if worker_payload is None:
            ticker = interpreted.get("ticker", "")
            worker_name = interpreted.get("worker_name", "worker")
            if render_mode == "builder":
                msg = (
                    f"Main brain selected {worker_name} for ticker {ticker}, "
                    "but the worker has not been executed yet."
                )
                if monitor_summary:
                    msg += f" monitor_summary={monitor_summary}"
                return msg

            intervention = self._monitor_intervention(monitor_summary)
            if intervention == "ask_clarify":
                return (
                    f"I selected {worker_name} for {ticker}, "
                    "but I should clarify the route before treating it as settled."
                )
            return f"I selected {worker_name} for {ticker}, but it has not run yet."

        return self.synthesize_worker_result(
            interpreted=interpreted,
            worker_payload=worker_payload,
            verification_record=verification_record,
            render_mode=render_mode,
            monitor_summary=monitor_summary,
            tracey_turn=tracey_turn,
        )

    def _render_builder_mode(
        self,
        *,
        worker_name: str,
        ticker: str,
        result: dict[str, Any],
        warnings: list[str],
        confidence: float,
        verification_record: VerificationRecord | None,
        monitor_summary: dict[str, Any] | None,
    ) -> str:
        if worker_name == "technical_analysis_worker":
            return self._render_builder_mode_technical_analysis(
                ticker=ticker,
                result=result,
                warnings=warnings,
                confidence=confidence,
                verification_record=verification_record,
                monitor_summary=monitor_summary,
            )
        if worker_name == "macro_sector_mapping_worker":
            return self._render_builder_mode_macro_sector_mapping(
                result=result,
                warnings=warnings,
                confidence=confidence,
                verification_record=verification_record,
                monitor_summary=monitor_summary,
            )
        if worker_name == "sector_flow_worker":
            return self._render_builder_mode_sector_flow(
                result=result,
                warnings=warnings,
                confidence=confidence,
                verification_record=verification_record,
                monitor_summary=monitor_summary,
            )
        if worker_name == "candle_volume_structure_worker":
            return self._render_builder_mode_candle_volume_structure(
                result=result,
                warnings=warnings,
                confidence=confidence,
                verification_record=verification_record,
                monitor_summary=monitor_summary,
            )
        if worker_name == "trade_memo_worker":
            return self._render_builder_mode_trade_memo(
                result=result,
                warnings=warnings,
                confidence=confidence,
                verification_record=verification_record,
                monitor_summary=monitor_summary,
            )

        lines: list[str] = []

        lines.append(f"Main brain used {worker_name} for ticker {ticker}.")
        lines.append(f"Worker confidence: {confidence:.2f}")

        latest_bar = result.get("latest_bar")
        if latest_bar:
            lines.append(
                "Latest bar: "
                f"{latest_bar.get('date', '?')} | "
                f"open={latest_bar.get('open', '?')} "
                f"high={latest_bar.get('high', '?')} "
                f"low={latest_bar.get('low', '?')} "
                f"close={latest_bar.get('close', '?')} "
                f"volume={latest_bar.get('volume', '?')}"
            )

        integrity_checks = result.get("integrity_checks")
        if integrity_checks:
            lines.append(f"Integrity checks: {integrity_checks}")

        data_source = result.get("data_source")
        if data_source:
            lines.append(f"Data source: {data_source}")

        bars_found = result.get("bars_found")
        lines.append(f"Bars found: {bars_found}")

        if verification_record is not None:
            lines.append(f"Verification status: {verification_record.verification_status}")
            if verification_record.observed_outcome:
                lines.append(f"Observed outcome: {verification_record.observed_outcome}")

        if monitor_summary:
            lines.append(f"Monitor summary: {monitor_summary}")

        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)

        lines.append("Final note: this is a bounded market-data response, not a trading judgment.")
        return "\n".join(lines)

    def _render_builder_mode_technical_analysis(
        self,
        *,
        ticker: str,
        result: dict[str, Any],
        warnings: list[str],
        confidence: float,
        verification_record: VerificationRecord | None,
        monitor_summary: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []
        lines.append(f"Main brain used technical_analysis_worker for ticker {ticker}.")
        lines.append(f"Worker confidence: {confidence:.2f}")
        lines.append(f"Data status: {result.get('data_status', 'missing')}")
        lines.append(f"Structure read: {result.get('structure_read', '')}")
        lines.append(f"Volume read: {result.get('volume_read', '')}")
        lines.append(f"Indicator read: {result.get('indicator_read', {})}")
        lines.append(f"Alignment status: {result.get('alignment_status', 'unresolved')}")
        lines.append(f"Invalidation condition: {result.get('invalidation_condition', '')}")
        lines.append(f"Bars found: {result.get('bars_found', 0)}")
        if result.get("data_source"):
            lines.append(f"Data source: {result['data_source']}")
        if verification_record is not None:
            lines.append(f"Verification status: {verification_record.verification_status}")
            if verification_record.observed_outcome:
                lines.append(f"Observed outcome: {verification_record.observed_outcome}")
        if monitor_summary:
            lines.append(f"Monitor summary: {monitor_summary}")
        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)
        lines.append("Final note: this is bounded technical-analysis evidence, not a trading judgment.")
        return "\n".join(lines)

    def _render_builder_mode_macro_sector_mapping(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        confidence: float,
        verification_record: VerificationRecord | None,
        monitor_summary: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []
        lines.append("Main brain used macro_sector_mapping_worker.")
        lines.append(f"Worker confidence: {confidence:.2f}")
        lines.append(f"Input status: {result.get('input_status', 'missing')}")
        lines.append(f"Matched signals: {len(result.get('matched_signals', []))}")
        lines.append(f"Sector bias entries: {len(result.get('vn_sector_bias', []))}")
        lines.append(f"Conflict flags: {len(result.get('conflict_flags', []))}")
        if result.get("config_source"):
            lines.append(f"Config source: {result['config_source']}")
        if verification_record is not None:
            lines.append(f"Verification status: {verification_record.verification_status}")
            if verification_record.observed_outcome:
                lines.append(f"Observed outcome: {verification_record.observed_outcome}")
        if monitor_summary:
            lines.append(f"Monitor summary: {monitor_summary}")
        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)
        lines.append("Final note: this is bounded macro-sector mapping evidence, not a final market report.")
        return "\n".join(lines)

    def _render_builder_mode_sector_flow(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        confidence: float,
        verification_record: VerificationRecord | None,
        monitor_summary: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []
        lines.append("Main brain used sector_flow_worker.")
        lines.append(f"Worker confidence: {confidence:.2f}")
        lines.append(f"Input status: {result.get('input_status', 'missing')}")
        lines.append(f"Sector board entries: {len(result.get('sector_flow_board', []))}")
        lines.append(f"Unclassified sectors: {len(result.get('unclassified_sectors', []))}")
        lines.append(f"Conflict flags: {len(result.get('conflict_flags', []))}")
        if result.get("config_source"):
            lines.append(f"Config source: {result['config_source']}")
        if verification_record is not None:
            lines.append(f"Verification status: {verification_record.verification_status}")
            if verification_record.observed_outcome:
                lines.append(f"Observed outcome: {verification_record.observed_outcome}")
        if monitor_summary:
            lines.append(f"Monitor summary: {monitor_summary}")
        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)
        lines.append("Final note: this is bounded sector-flow evidence, not a final market report.")
        return "\n".join(lines)

    def _render_builder_mode_candle_volume_structure(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        confidence: float,
        verification_record: VerificationRecord | None,
        monitor_summary: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []
        lines.append("Main brain used candle_volume_structure_worker.")
        lines.append(f"Worker confidence: {confidence:.2f}")
        lines.append(f"Input status: {result.get('input_status', 'missing')}")
        lines.append(f"Top list entries: {len(result.get('top_list', []))}")
        lines.append(f"Watch list entries: {len(result.get('watch_list', []))}")
        lines.append(f"Rejected entries: {len(result.get('rejected', []))}")
        if result.get("config_source"):
            lines.append(f"Config source: {result['config_source']}")
        if verification_record is not None:
            lines.append(f"Verification status: {verification_record.verification_status}")
            if verification_record.observed_outcome:
                lines.append(f"Observed outcome: {verification_record.observed_outcome}")
        if monitor_summary:
            lines.append(f"Monitor summary: {monitor_summary}")
        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)
        lines.append("Final note: this is bounded setup evidence, not a final market report.")
        return "\n".join(lines)

    def _render_builder_mode_trade_memo(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        confidence: float,
        verification_record: VerificationRecord | None,
        monitor_summary: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []
        lines.append("Main brain used trade_memo_worker.")
        lines.append(f"Worker confidence: {confidence:.2f}")
        lines.append(f"Input status: {result.get('input_status', 'missing')}")
        lines.append(f"Memo mode requested: {result.get('memo_mode_requested', 'lite')}")
        lines.append(f"Memo mode effective: {result.get('memo_mode_effective', 'lite')}")
        lines.append(f"Ticker memos: {len(result.get('ticker_memos', []))}")
        if verification_record is not None:
            lines.append(f"Verification status: {verification_record.verification_status}")
            if verification_record.observed_outcome:
                lines.append(f"Observed outcome: {verification_record.observed_outcome}")
        if monitor_summary:
            lines.append(f"Monitor summary: {monitor_summary}")
        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)
        lines.append("Final note: this is bounded trade-memo evidence, not a final market report.")
        return "\n".join(lines)

    def _render_user_mode(
        self,
        *,
        worker_name: str,
        ticker: str,
        result: dict[str, Any],
        warnings: list[str],
        verification_record: VerificationRecord | None,
        intervention: str,
        monitor_summary: dict[str, Any] | None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        tracey_hints = self._tracey_hints(tracey_turn)
        if worker_name == "technical_analysis_worker":
            return self._render_user_mode_technical_analysis(
                ticker=ticker,
                result=result,
                warnings=warnings,
                verification_record=verification_record,
                intervention=intervention,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )
        if worker_name == "macro_sector_mapping_worker":
            return self._render_user_mode_macro_sector_mapping(
                result=result,
                warnings=warnings,
                verification_record=verification_record,
                intervention=intervention,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )
        if worker_name == "sector_flow_worker":
            return self._render_user_mode_sector_flow(
                result=result,
                warnings=warnings,
                verification_record=verification_record,
                intervention=intervention,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )
        if worker_name == "candle_volume_structure_worker":
            return self._render_user_mode_candle_volume_structure(
                result=result,
                warnings=warnings,
                verification_record=verification_record,
                intervention=intervention,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )
        if worker_name == "trade_memo_worker":
            return self._render_user_mode_trade_memo(
                result=result,
                warnings=warnings,
                verification_record=verification_record,
                intervention=intervention,
                monitor_summary=monitor_summary,
                tracey_turn=tracey_turn,
            )

        lines: list[str] = []

        latest_bar = result.get("latest_bar")
        data_source = result.get("data_source", "")
        integrity_checks = result.get("integrity_checks", {})
        bars_found = result.get("bars_found", 0)

        lines.append(f"I checked {ticker} using {worker_name}.")

        if bars_found == 0:
            lines.append("No bars were returned for this ticker in the current dataset.")
        elif latest_bar:
            lines.append(
                f"Latest daily bar: {latest_bar.get('date', '?')} — "
                f"open {latest_bar.get('open', '?')}, "
                f"high {latest_bar.get('high', '?')}, "
                f"low {latest_bar.get('low', '?')}, "
                f"close {latest_bar.get('close', '?')}, "
                f"volume {latest_bar.get('volume', '?')}."
            )

        if data_source:
            lines.append(f"Source: {data_source}")

        integrity_summary = self._summarize_integrity_checks(integrity_checks)
        if integrity_summary:
            lines.append(integrity_summary)

        if verification_record is not None:
            if verification_record.verification_status == "passed":
                lines.append("Verification passed.")
            elif verification_record.verification_status == "failed":
                lines.append("Verification failed.")
            else:
                lines.append("Verification is unknown.")

        if intervention == "do_not_mark_complete":
            lines.append("Monitor note: do not treat this as complete until observed change is verified.")
        elif intervention == "ask_clarify":
            lines.append("Monitor note: ambiguity may still be active, so this should stay tentative.")
        elif intervention == "restore_mode":
            lines.append("Monitor note: response posture should stay aligned with the active mode.")
        elif intervention == "tighten_project_focus":
            lines.append("Monitor note: keep the answer tied to the active project, not generic filler.")
        if monitor_summary and monitor_summary.get("primary_risk") not in {None, "", "none"}:
            lines.append(f"Primary governance risk: {monitor_summary['primary_risk']}.")

        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)

        if tracey_hints.get("verification_before_completion"):
            lines.append("Completion posture: stay inside verified bounded evidence.")
        lines.append("This is a bounded market-data read, not a trading judgment.")
        return "\n".join(lines)

    def _render_user_mode_technical_analysis(
        self,
        *,
        ticker: str,
        result: dict[str, Any],
        warnings: list[str],
        verification_record: VerificationRecord | None,
        intervention: str,
        monitor_summary: dict[str, Any] | None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = []
        tracey_hints = self._tracey_hints(tracey_turn)
        indicator_read = result.get("indicator_read", {})

        lines.append(f"I ran a bounded technical-analysis read for {ticker}.")
        lines.append(f"Timeframe: {result.get('timeframe', '1D')}.")
        lines.append(f"Data status: {result.get('data_status', 'missing')}.")
        lines.append(f"Structure: {result.get('structure_read', '')}")
        lines.append(f"Volume: {result.get('volume_read', '')}")
        lines.append(f"Moving averages: {indicator_read.get('moving_averages', '')}")
        if indicator_read.get("rsi"):
            lines.append(f"RSI: {indicator_read['rsi']}")
        lines.append(f"Alignment: {result.get('alignment_status', 'unresolved')}.")
        lines.append(f"Invalidation: {result.get('invalidation_condition', '')}")

        if result.get("data_source"):
            lines.append(f"Source: {result['data_source']}")

        integrity_summary = self._summarize_integrity_checks(result.get("integrity_checks", {}))
        if integrity_summary:
            lines.append(integrity_summary)

        if verification_record is not None:
            if verification_record.verification_status == "passed":
                lines.append("Verification passed for the bounded data-and-analysis path.")
            elif verification_record.verification_status == "failed":
                lines.append("Verification failed for the bounded data-and-analysis path.")
            else:
                lines.append("Verification is unknown for the bounded data-and-analysis path.")

        if intervention == "do_not_mark_complete":
            lines.append("Monitor note: do not treat this analysis as complete beyond the verified bounded evidence.")
        elif intervention == "ask_clarify":
            lines.append("Monitor note: ambiguity may still be active, so this technical read should stay tentative.")
        elif intervention == "restore_mode":
            lines.append("Monitor note: response posture should stay aligned with the active mode.")
        elif intervention == "tighten_project_focus":
            lines.append("Monitor note: keep the answer tied to the active project, not generic filler.")
        if monitor_summary and monitor_summary.get("primary_risk") not in {None, "", "none"}:
            lines.append(f"Primary governance risk: {monitor_summary['primary_risk']}.")

        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)

        if tracey_hints.get("verification_before_completion"):
            lines.append("Completion posture: keep the read bounded to verified evidence.")
        lines.append("This is a bounded technical analysis read from local market data, not a trading judgment.")
        return "\n".join(lines)

    def _render_user_mode_macro_sector_mapping(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        verification_record: VerificationRecord | None,
        intervention: str,
        monitor_summary: dict[str, Any] | None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = []
        tracey_hints = self._tracey_hints(tracey_turn)
        matched_signals = result.get("matched_signals", [])
        vn_sector_bias = result.get("vn_sector_bias", [])
        conflict_flags = result.get("conflict_flags", [])

        lines.append("I ran a bounded macro-sector mapping read.")
        lines.append(f"Input status: {result.get('input_status', 'missing')}.")
        lines.append(f"Matched signals: {len(matched_signals)}.")
        lines.append(f"Sector implications: {len(vn_sector_bias)}.")
        if conflict_flags:
            lines.append(f"Conflict flags: {len(conflict_flags)} sector-level conflicts were preserved.")

        if matched_signals:
            lines.append(f"Matched trigger summary: {[item.get('matched_trigger', '') for item in matched_signals]}")
        if vn_sector_bias:
            preview = [
                f"{entry.get('sector', '')}:{entry.get('direction', '')}:{entry.get('reason', '')}"
                for entry in vn_sector_bias[:4]
            ]
            lines.append(f"Sector bias preview: {preview}")

        if result.get("config_source"):
            lines.append(f"Config source: {result['config_source']}")

        if verification_record is not None:
            if verification_record.verification_status == "passed":
                lines.append("Verification passed for the bounded macro-mapping path.")
            elif verification_record.verification_status == "failed":
                lines.append("Verification failed for the bounded macro-mapping path.")
            else:
                lines.append("Verification is unknown for the bounded macro-mapping path.")

        if intervention == "do_not_mark_complete":
            lines.append("Monitor note: do not treat this mapping as complete beyond the verified bounded evidence.")
        elif intervention == "ask_clarify":
            lines.append("Monitor note: ambiguity may still be active, so this mapping should stay tentative.")
        elif intervention == "restore_mode":
            lines.append("Monitor note: response posture should stay aligned with the active mode.")
        elif intervention == "tighten_project_focus":
            lines.append("Monitor note: keep the answer tied to the active project, not generic filler.")
        if monitor_summary and monitor_summary.get("primary_risk") not in {None, "", "none"}:
            lines.append(f"Primary governance risk: {monitor_summary['primary_risk']}.")

        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)

        if tracey_hints.get("verification_before_completion"):
            lines.append("Completion posture: keep the mapping bounded to verified evidence.")
        lines.append("This is bounded macro-sector mapping evidence from structured input and canonical config, not a final market report.")
        return "\n".join(lines)

    def _render_user_mode_sector_flow(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        verification_record: VerificationRecord | None,
        intervention: str,
        monitor_summary: dict[str, Any] | None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = []
        tracey_hints = self._tracey_hints(tracey_turn)
        sector_flow_board = result.get("sector_flow_board", [])
        conflict_flags = result.get("conflict_flags", [])

        lines.append("I ran a bounded sector-flow classification read.")
        lines.append(f"Input status: {result.get('input_status', 'missing')}.")
        lines.append(f"Sector board entries: {len(sector_flow_board)}.")
        if sector_flow_board:
            preview = [
                f"{entry.get('sector', '')}:{entry.get('state', '')}:{entry.get('direction', '')}"
                for entry in sector_flow_board[:4]
            ]
            lines.append(f"Sector board preview: {preview}")
        if conflict_flags:
            lines.append(f"Conflict flags: {len(conflict_flags)} macro-flow conflicts were preserved.")
        if result.get("unclassified_sectors"):
            lines.append(f"Unclassified sectors: {len(result['unclassified_sectors'])}.")
        if result.get("config_source"):
            lines.append(f"Config source: {result['config_source']}")

        if verification_record is not None:
            if verification_record.verification_status == "passed":
                lines.append("Verification passed for the bounded sector-flow path.")
            elif verification_record.verification_status == "failed":
                lines.append("Verification failed for the bounded sector-flow path.")
            else:
                lines.append("Verification is unknown for the bounded sector-flow path.")

        if intervention == "do_not_mark_complete":
            lines.append("Monitor note: do not treat this sector-flow board as complete beyond the verified bounded evidence.")
        elif intervention == "ask_clarify":
            lines.append("Monitor note: ambiguity may still be active, so this board should stay tentative.")
        elif intervention == "restore_mode":
            lines.append("Monitor note: response posture should stay aligned with the active mode.")
        elif intervention == "tighten_project_focus":
            lines.append("Monitor note: keep the answer tied to the active project, not generic filler.")
        if monitor_summary and monitor_summary.get("primary_risk") not in {None, "", "none"}:
            lines.append(f"Primary governance risk: {monitor_summary['primary_risk']}.")

        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)

        if tracey_hints.get("verification_before_completion"):
            lines.append("Completion posture: keep the board bounded to verified evidence.")
        lines.append("This is bounded sector-flow evidence from explicit metrics and canonical config, not a final market report.")
        return "\n".join(lines)

    def _render_user_mode_candle_volume_structure(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        verification_record: VerificationRecord | None,
        intervention: str,
        monitor_summary: dict[str, Any] | None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = []
        tracey_hints = self._tracey_hints(tracey_turn)
        top_list = result.get("top_list", [])
        watch_list = result.get("watch_list", [])
        rejected = result.get("rejected", [])

        lines.append("I ran a bounded candle-volume-structure scoring read.")
        lines.append(f"Input status: {result.get('input_status', 'missing')}.")
        lines.append(f"Top list entries: {len(top_list)}.")
        lines.append(f"Watch list entries: {len(watch_list)}.")
        lines.append(f"Rejected entries: {len(rejected)}.")
        if top_list:
            preview = [
                f"{entry.get('ticker', '')}:{entry.get('setup_type', '')}:top"
                for entry in top_list[:3]
            ]
            lines.append(f"Top preview: {preview}")
        if watch_list:
            preview = [
                f"{entry.get('ticker', '')}:{entry.get('setup_type', '')}:watch"
                for entry in watch_list[:3]
            ]
            lines.append(f"Watch preview: {preview}")
        if result.get("config_source"):
            lines.append(f"Config source: {result['config_source']}")

        if verification_record is not None:
            if verification_record.verification_status == "passed":
                lines.append("Verification passed for the bounded candle-volume-structure path.")
            elif verification_record.verification_status == "failed":
                lines.append("Verification failed for the bounded candle-volume-structure path.")
            else:
                lines.append("Verification is unknown for the bounded candle-volume-structure path.")

        if intervention == "do_not_mark_complete":
            lines.append("Monitor note: do not treat this setup board as complete beyond the verified bounded evidence.")
        elif intervention == "ask_clarify":
            lines.append("Monitor note: ambiguity may still be active, so this setup read should stay tentative.")
        elif intervention == "restore_mode":
            lines.append("Monitor note: response posture should stay aligned with the active mode.")
        elif intervention == "tighten_project_focus":
            lines.append("Monitor note: keep the answer tied to the active project, not generic filler.")
        if monitor_summary and monitor_summary.get("primary_risk") not in {None, "", "none"}:
            lines.append(f"Primary governance risk: {monitor_summary['primary_risk']}.")

        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)

        if tracey_hints.get("verification_before_completion"):
            lines.append("Completion posture: keep the setup evidence bounded to verified evidence.")
        lines.append("This is bounded setup evidence from explicit candidates and canonical hard filters, not a final market report.")
        return "\n".join(lines)

    def _render_user_mode_trade_memo(
        self,
        *,
        result: dict[str, Any],
        warnings: list[str],
        verification_record: VerificationRecord | None,
        intervention: str,
        monitor_summary: dict[str, Any] | None,
        tracey_turn: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = []
        tracey_hints = self._tracey_hints(tracey_turn)
        ticker_memos = result.get("ticker_memos", [])

        lines.append("I ran a bounded trade-memo scenario read.")
        lines.append(f"Input status: {result.get('input_status', 'missing')}.")
        lines.append(f"Memo mode requested: {result.get('memo_mode_requested', 'lite')}.")
        lines.append(f"Memo mode effective: {result.get('memo_mode_effective', 'lite')}.")
        lines.append(f"Ticker memos: {len(ticker_memos)}.")
        if ticker_memos:
            preview = [
                f"{memo.get('ticker', '')}:{memo.get('action_today', {}).get('stance', '')}"
                for memo in ticker_memos[:3]
            ]
            lines.append(f"Memo preview: {preview}")

        if verification_record is not None:
            if verification_record.verification_status == "passed":
                lines.append("Verification passed for the bounded trade-memo path.")
            elif verification_record.verification_status == "failed":
                lines.append("Verification failed for the bounded trade-memo path.")
            else:
                lines.append("Verification is unknown for the bounded trade-memo path.")

        if intervention == "do_not_mark_complete":
            lines.append("Monitor note: do not treat this memo as complete beyond the verified bounded evidence.")
        elif intervention == "ask_clarify":
            lines.append("Monitor note: ambiguity may still be active, so this memo should stay tentative.")
        elif intervention == "restore_mode":
            lines.append("Monitor note: response posture should stay aligned with the active mode.")
        elif intervention == "tighten_project_focus":
            lines.append("Monitor note: keep the answer tied to the active project, not generic filler.")
        if monitor_summary and monitor_summary.get("primary_risk") not in {None, "", "none"}:
            lines.append(f"Primary governance risk: {monitor_summary['primary_risk']}.")

        if warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in warnings)

        if tracey_hints.get("verification_before_completion"):
            lines.append("Completion posture: keep the memo bounded to verified evidence.")
        lines.append("This is bounded trade-memo evidence with conditional scenarios, not a final market report.")
        return "\n".join(lines)

    @staticmethod
    def _summarize_integrity_checks(integrity_checks: dict[str, Any]) -> str:
        if not integrity_checks:
            return ""

        parts: list[str] = []
        if integrity_checks.get("file_exists") is False:
            parts.append("data file missing")
        if integrity_checks.get("required_columns_present") is False:
            parts.append("required columns missing")
        if integrity_checks.get("ticker_match_found") is False:
            parts.append("ticker not found in dataset")
        if integrity_checks.get("missing_dates_detected"):
            parts.append("dates appear missing or unsorted")
        if integrity_checks.get("duplicate_dates_detected"):
            parts.append("duplicate dates detected")
        if integrity_checks.get("volume_null_detected"):
            parts.append("some volume values could not be parsed")
        if integrity_checks.get("price_order_valid") is False:
            parts.append("OHLC ordering failed basic validation")

        if not parts:
            return "Integrity summary: basic checks passed."

        return "Integrity summary: " + "; ".join(parts) + "."

    @staticmethod
    def _extract_ticker_candidate(user_text: str) -> str | None:
        for token in user_text.replace(",", " ").split():
            cleaned = token.strip().upper()
            if cleaned.isalpha() and 2 <= len(cleaned) <= 6:
                if cleaned in {"LOAD", "DAILY", "DATA", "TICKER", "MARKET", "OHLCV", "ANALYZE", "READ", "CHART", "FOR"}:
                    continue
                return cleaned
        return None

    @staticmethod
    def _monitor_intervention(monitor_summary: dict[str, Any] | None) -> str:
        if not monitor_summary:
            return "none"
        return str(monitor_summary.get("recommended_intervention", "none"))

    @staticmethod
    def _tracey_hints(tracey_turn: dict[str, Any] | None) -> dict[str, Any]:
        if not tracey_turn:
            return {}
        response_hints = tracey_turn.get("response_hints", {})
        if not isinstance(response_hints, dict):
            return {}
        return response_hints
