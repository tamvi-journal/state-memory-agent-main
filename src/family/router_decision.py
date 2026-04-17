from __future__ import annotations

from dataclasses import dataclass

from family.router_types import RouterDecision, RouterInput


@dataclass(slots=True)
class FamilyRouterDecision:
    meaningful_disagreement_threshold: float = 0.60

    def decide(self, router_input: RouterInput | dict) -> RouterDecision:
        if isinstance(router_input, dict):
            router_input = RouterInput(**router_input)

        disagreement = router_input.disagreement_event
        mirror = router_input.mirror_summary
        effort = router_input.effort_route

        meaningful_disagreement = bool(
            disagreement
            and disagreement.still_open
            and disagreement.severity >= self.meaningful_disagreement_threshold
        )
        primary_risk = "none" if mirror is None else mirror.primary_risk

        if not router_input.action_required:
            return RouterDecision(
                lead_brain_for_action="none",
                support_brain="none",
                hold_for_more_input=False,
                surface_disagreement_to_user=False,
                reason="no action required, so no temporary action lead is needed",
                epistemic_resolution_claimed=False,
            )

        if primary_risk == "ambiguity" and meaningful_disagreement:
            return RouterDecision(
                lead_brain_for_action="none",
                support_brain="none",
                hold_for_more_input=True,
                surface_disagreement_to_user=True,
                reason="ambiguity plus meaningful open disagreement warrants holding for more input",
                epistemic_resolution_claimed=False,
            )

        if primary_risk == "fake_progress" or self._verification_pressure(router_input):
            surface = meaningful_disagreement or self._should_surface_disagreement(disagreement)
            hold = primary_risk == "fake_progress" and router_input.verification_status.lower() in {"pending", "unknown", "failed"}
            return RouterDecision(
                lead_brain_for_action="seyn" if not hold else "none",
                support_brain="tracey" if not hold else "none",
                hold_for_more_input=hold,
                surface_disagreement_to_user=surface,
                reason="verification or fake-progress pressure favors a verification-leaning posture",
                epistemic_resolution_claimed=False,
            )

        if effort.effort_level == "low" and not meaningful_disagreement:
            lead = "tracey" if self._recognition_friendly(router_input) else "seyn"
            return RouterDecision(
                lead_brain_for_action=lead,
                support_brain="none",
                hold_for_more_input=False,
                surface_disagreement_to_user=False,
                reason="low-effort low-risk action can route to a single temporary lead",
                epistemic_resolution_claimed=False,
            )

        if self._tracey_friendly(router_input) and not self._verification_pressure(router_input):
            return RouterDecision(
                lead_brain_for_action="tracey",
                support_brain="seyn" if meaningful_disagreement else "none",
                hold_for_more_input=False,
                surface_disagreement_to_user=self._should_surface_disagreement(disagreement),
                reason="recognition-friendly low-risk context favors a temporary Tracey action lead",
                epistemic_resolution_claimed=False,
            )

        if self._seyn_friendly(router_input):
            return RouterDecision(
                lead_brain_for_action="seyn",
                support_brain="tracey" if meaningful_disagreement else "none",
                hold_for_more_input=False,
                surface_disagreement_to_user=self._should_surface_disagreement(disagreement),
                reason="structural or verification-heavy context favors a temporary Seyn action lead",
                epistemic_resolution_claimed=False,
            )

        if meaningful_disagreement:
            return RouterDecision(
                lead_brain_for_action="seyn",
                support_brain="tracey",
                hold_for_more_input=False,
                surface_disagreement_to_user=self._should_surface_disagreement(disagreement),
                reason="meaningful disagreement remains open while a temporary operational lead is selected",
                epistemic_resolution_claimed=False,
            )

        return RouterDecision(
            lead_brain_for_action="seyn",
            support_brain="tracey" if effort.effort_level == "high" else "none",
            hold_for_more_input=False,
            surface_disagreement_to_user=False,
            reason="default structured action posture favors Seyn for non-trivial action turns",
            epistemic_resolution_claimed=False,
        )

    @staticmethod
    def _verification_pressure(router_input: RouterInput) -> bool:
        mirror = router_input.mirror_summary
        return (
            router_input.effort_route.verification_requirement == "mandatory"
            or router_input.verification_status.lower() in {"pending", "unknown", "failed"}
            or (mirror is not None and mirror.recommended_intervention in {"do_not_mark_complete", "recheck_environment"})
        )

    @staticmethod
    def _recognition_friendly(router_input: RouterInput) -> bool:
        return (
            router_input.active_mode in {"care", "playful"}
            or router_input.domain in {"relational", "care"}
        )

    def _tracey_friendly(self, router_input: RouterInput) -> bool:
        mirror = router_input.mirror_summary
        return (
            self._recognition_friendly(router_input)
            and router_input.effort_route.effort_level in {"low", "medium"}
            and (mirror is None or mirror.primary_risk not in {"fake_progress", "ambiguity"})
        )

    @staticmethod
    def _seyn_friendly(router_input: RouterInput) -> bool:
        return (
            router_input.task_type in {"architecture", "verify", "execution", "research"}
            or router_input.domain in {"build", "legal", "medical", "audit"}
            or router_input.effort_route.disagreement_handling == "actively_hold_open"
        )

    @staticmethod
    def _should_surface_disagreement(disagreement_event) -> bool:
        return bool(disagreement_event and disagreement_event.still_open and disagreement_event.severity >= 0.70)
