from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from .control_tower import build_control_tower_decision
from .injection import detect_injection
from .models import ControlTowerDecisionRequest, ControlTowerDecisionResponse
from .redaction import redact_text
from .safety import REFUSAL_MESSAGE, should_refuse


class ControlTowerDecisionBuildError(Exception):
    pass


@dataclass
class ControlTowerServiceResult:
    response: ControlTowerDecisionResponse
    redacted_notes: str
    redaction_applied: bool
    injection_detected: bool
    injection_hits: List[str]
    refusal: bool


class ControlTowerService:
    def __init__(
        self,
        decision_builder: Callable[[ControlTowerDecisionRequest], Dict] = build_control_tower_decision,
        redactor: Callable[[str], Tuple[str, Dict[str, bool]]] = redact_text,
        injection_detector: Callable[[str], Tuple[bool, List[str]]] = detect_injection,
        refusal_checker: Callable[[str], bool] = should_refuse,
    ) -> None:
        self.decision_builder = decision_builder
        self.redactor = redactor
        self.injection_detector = injection_detector
        self.refusal_checker = refusal_checker

    def decide(
        self,
        payload: ControlTowerDecisionRequest,
        decision_timestamp_ms: int,
    ) -> ControlTowerServiceResult:
        notes = payload.notes or ""
        redacted_notes, redaction_events = self.redactor(notes)
        redaction_applied = any(redaction_events.values())

        injection_detected, injection_hits = self.injection_detector(notes)
        refusal = self.refusal_checker(notes)

        if refusal:
            response = ControlTowerDecisionResponse(
                decision_id=f"ct-refused-{decision_timestamp_ms}",
                risk_score=0.0,
                risk_level="blocked",
                factor_breakdown={
                    "demand_volatility": 0.0,
                    "inventory_pressure": 0.0,
                    "machine_health_risk": 0.0,
                    "sla_risk": 0.0,
                    "margin_pressure": 0.0,
                    "gpu_pressure": 0.0,
                },
                primary_actions=[REFUSAL_MESSAGE],
                execution_plan=[],
                cot_trace=[
                    {
                        "step": "policy_guard",
                        "summary": "Request refused due to safety policy.",
                    }
                ],
                spec_version="policy-blocked",
                policy_events={
                    "redaction_applied": redaction_applied,
                    "injection_detected": injection_detected,
                    "refusal": True,
                },
            )
            return ControlTowerServiceResult(
                response=response,
                redacted_notes=redacted_notes,
                redaction_applied=redaction_applied,
                injection_detected=injection_detected,
                injection_hits=injection_hits,
                refusal=True,
            )

        try:
            decision = self.decision_builder(payload)
        except Exception as exc:  # noqa: BLE001
            raise ControlTowerDecisionBuildError(str(exc)) from exc

        response = ControlTowerDecisionResponse(
            decision_id=decision["decision_id"],
            risk_score=decision["risk_score"],
            risk_level=decision["risk_level"],
            factor_breakdown=decision["factor_breakdown"],
            primary_actions=decision["primary_actions"],
            execution_plan=decision["execution_plan"],
            cot_trace=decision["cot_trace"],
            spec_version=decision["spec_version"],
            policy_events={
                "redaction_applied": redaction_applied,
                "injection_detected": injection_detected,
                "refusal": False,
            },
        )
        return ControlTowerServiceResult(
            response=response,
            redacted_notes=redacted_notes,
            redaction_applied=redaction_applied,
            injection_detected=injection_detected,
            injection_hits=injection_hits,
            refusal=False,
        )
