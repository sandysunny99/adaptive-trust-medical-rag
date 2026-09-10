from adaptive_trust_medical_rag.security.sanitizer import sanitize_document_chunk
from adaptive_trust_medical_rag.security.security_context import SecurityDecision, SecurityState

class PromptInjectionDetector:
    """Detects instruction-like content originating from evidence/context/memory."""

    def inspect(self, text: str, request_id: str) -> SecurityDecision:
        result = sanitize_document_chunk(text)
        
        if result.rejected:
            state = SecurityState.BLOCK
            reason = "INJECTION_DETECTED"
        elif not result.is_clean:
            state = SecurityState.FLAG
            reason = "INJECTION_FLAGGED"
        else:
            state = SecurityState.ALLOW
            reason = "CLEAN"

        return SecurityDecision(
            decision=state,
            reason_code=reason,
            attack_family="PROMPT_INJECTION",
            attack_subtype="MARKER_MATCH" if not result.is_clean else None,
            confidence=1.0,
            target="orchestrator",
            source="user_query",
            evidence_id=None,
            request_id=request_id,
            detector="PromptInjectionDetector"
        )
