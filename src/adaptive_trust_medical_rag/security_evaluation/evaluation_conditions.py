from adaptive_trust_medical_rag.security_extensions import (
    ActionType,
    AuthorizationBoundary,
    EntityDomain,
    PromptInjectionDetector,
    RetrievalPoisoningDetector,
)

from .result_schema import SecurityResultRecord
from .security_case import (
    AttackFamily,
    EvaluationCondition,
    SecurityCase,
)


class SecurityConditionAdapter:
    """Routes identical SecurityCase instances to BASELINE or HARDENED paths.

    BASELINE CONDITION: A security-boundary adapter representing the
    absence of the Phase 12 security-extension decision layer.  It is
    NOT a complete re-execution of a historical unprotected RAG pipeline.
    The experiment measures the incremental contribution of Phase 12
    security-boundary mechanisms, not complete end-to-end RAG security.

    HARDENED CONDITION: Invokes the Phase 12 Security Extensions
    (PromptInjectionDetector, RetrievalPoisoningDetector,
    AuthorizationBoundary) exactly as implemented.
    """

    _DOMAIN_MAP = {
        "EVIDENCE": EntityDomain.EVIDENCE,
        "CONTEXT": EntityDomain.CONTEXT,
        "MEMORY": EntityDomain.MEMORY,
    }
    _ACTION_MAP = {
        "INVOKE_TOOL": ActionType.INVOKE_TOOL,
        "MODIFY_TRUST": ActionType.MODIFY_TRUST_CONFIG,
        "MODIFY_EXPERIMENT": ActionType.MODIFY_EXPERIMENT_CONFIG,
    }

    def evaluate(
        self,
        case: SecurityCase,
        condition: EvaluationCondition,
        eval_id: str = "eval_0",
    ) -> SecurityResultRecord:
        if condition == EvaluationCondition.BASELINE:
            return self._evaluate_baseline(case, eval_id)
        if condition == EvaluationCondition.HARDENED:
            return self._evaluate_hardened(case, eval_id)
        raise ValueError(f"Unknown condition: {condition}")

    # ------------------------------------------------------------------
    # BASELINE — no Phase 12 security-extension decisions applied
    # ------------------------------------------------------------------
    def _evaluate_baseline(
        self, case: SecurityCase, eval_id: str
    ) -> SecurityResultRecord:
        return SecurityResultRecord(
            evaluation_id=eval_id,
            case_id=case.case_id,
            condition=EvaluationCondition.BASELINE,
            case_input_hash=case.case_input_hash,
            attack_family=case.attack_family,
            attack_subtype=case.attack_subtype,
            expected_outcome=case.expected_outcome,
            observed_outcome="ALLOW",
            detected=False,
            blocked=False,
            false_positive=False,
            unauthorized_action=(
                case.requires_authorization_check
            ),
            provenance_preserved="source" in case.provenance_fixture,
            requires_provenance_preservation=case.requires_provenance_preservation,
            requires_authorization_check=case.requires_authorization_check,
            security_decision="NO_SECURITY_GATE",
            reason_code="BASELINE_PASSTHROUGH",
            harness_version="1.0.0",
        )

    # ------------------------------------------------------------------
    # HARDENED — Phase 12 Security Extensions applied
    # ------------------------------------------------------------------
    def _evaluate_hardened(
        self, case: SecurityCase, eval_id: str
    ) -> SecurityResultRecord:
        blocked = False
        detected = False
        unauthorized = False
        reason = "BENIGN_CONTENT_ALLOWED"
        decision = "SAFE"

        if case.attack_family == AttackFamily.PROMPT_INJECTION:
            det = PromptInjectionDetector()
            res = det.inspect(case.payload, "req1")
            detected = not res.decision == "ALLOW"
            blocked = res.decision == "BLOCK"
            if detected:
                reason = "INJECTION_DETECTED"
                decision = "BLOCKED" if blocked else "FLAGGED"

        elif case.attack_family == AttackFamily.RETRIEVAL_POISONING:
            det = RetrievalPoisoningDetector()
            res = det.inspect_provenance(case.provenance_fixture, "c1", "req1")
            detected = not res.decision == "ALLOW"
            blocked = not res.decision == "ALLOW"
            if detected:
                reason = "POISONING_INDICATOR_DETECTED"
                decision = "BLOCKED"

        elif case.attack_family == AttackFamily.BOUNDARY_VIOLATION:
            boundary = AuthorizationBoundary()
            dom = self._DOMAIN_MAP.get(case.target_component, EntityDomain.USER)
            act = self._ACTION_MAP.get(case.requested_action, ActionType.READ_DATA)
            res = boundary.authorize(dom, act, "req1", "USER")
            if res.decision == "UNAUTHORIZED_ACTION_REJECTED":
                blocked = True
                detected = True
                reason = "AUTHORIZATION_REJECTED"
                decision = "BLOCKED"
            else:
                unauthorized = True

        false_positive = False
        if case.attack_family == AttackFamily.BENIGN_CONTROL and (
            detected or blocked
        ):
            false_positive = True
            reason = "BENIGN_CONTENT_FLAGGED"

        if blocked:
            observed = "BLOCK"
        elif reason == "AUTHORIZATION_REJECTED":
            observed = "UNAUTHORIZED_ACTION_REJECTED"
        else:
            observed = "ALLOW"

        return SecurityResultRecord(
            evaluation_id=eval_id,
            case_id=case.case_id,
            condition=EvaluationCondition.HARDENED,
            case_input_hash=case.case_input_hash,
            attack_family=case.attack_family,
            attack_subtype=case.attack_subtype,
            expected_outcome=case.expected_outcome,
            observed_outcome=observed,
            detected=detected,
            blocked=blocked,
            false_positive=false_positive,
            unauthorized_action=unauthorized,
            provenance_preserved="source" in case.provenance_fixture,
            requires_provenance_preservation=case.requires_provenance_preservation,
            requires_authorization_check=case.requires_authorization_check,
            security_decision=decision,
            reason_code=reason,
            harness_version="1.0.0",
        )
