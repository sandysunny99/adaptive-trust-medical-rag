import sys
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
lines = p.read_text(encoding='utf-8').splitlines()

new_lines = []
for i, line in enumerate(lines):
    if line.strip() == "self._trust_scorer = AdaptiveTrustScorer()":
        new_lines.append(line)
        new_lines.append("        self._prompt_detector = PromptInjectionDetector()")
        new_lines.append("        self._poisoning_detector = RetrievalPoisoningDetector()")
        new_lines.append("        self._auth_boundary = AuthorizationBoundary()")
    elif line.strip() == "def evaluate(":
        # Patch EvidenceEligibilityGate to accept retrieval_security_states
        new_lines.append(line)
        continue
    elif line.strip() == "trust_scores: dict[str, float],":
        new_lines.append(line)
        new_lines.append("        retrieval_security_states: dict[str, SecurityDecision] | None = None,")
        continue
    elif line.strip() == "# Trust gate":
        # we are inside EvidenceEligibilityGate.evaluate
        new_lines.append("            # Security gate")
        new_lines.append("            if retrieval_security_states and cand.chunk_id in retrieval_security_states:")
        new_lines.append("                sec_state = retrieval_security_states[cand.chunk_id].decision")
        new_lines.append("                if sec_state == SecurityState.BLOCK:")
        new_lines.append("                    rejected_ids.append(cand.chunk_id)")
        new_lines.append("                    continue")
        new_lines.append(line)
    else:
        new_lines.append(line)

p.write_text("\n".join(new_lines), encoding='utf-8')
