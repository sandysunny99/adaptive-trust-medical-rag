from dataclasses import dataclass

@dataclass
class EvaluationResult:
    claim_support_rate: float
    citation_validation_rate: float
    unsupported_answer_rate: float
    abstention_rate: float
    provider_failure_rate: float

class DetachedCommonEvaluator:
    def __init__(self, claim_verifier):
        self.claim_verifier = claim_verifier

    def evaluate_output(self, generated_answer: str, evidence_chunks: list) -> EvaluationResult:
        # Applies identical logic regardless of ARM origin
        report = self.claim_verifier.verify(generated_answer, evidence_chunks)
        # Mock logic to represent standard verification mapping
        return EvaluationResult(
            claim_support_rate=report.get("support_rate", 0.0),
            citation_validation_rate=report.get("citation_rate", 0.0),
            unsupported_answer_rate=report.get("unsupported_rate", 0.0),
            abstention_rate=0.0, # Computed at runner level
            provider_failure_rate=0.0 # Computed at runner level
        )
