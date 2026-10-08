# V1.2 METRIC DEFINITION AUDIT V2

## claim_support_rate
- Numerator: count of supported claims
- Denominator: count of total claims in generated answers
- Protocol/Impl Source: Evaluator
- Raw Recalculation: 0.00
- Limitation: Denominator is zero for Arm B, non-comparable.

## citation_validation_rate
- Numerator: count of valid citations
- Denominator: count of total citations
- Protocol/Impl Source: Evaluator
- Limitation: Zero for Arm B.

## unsupported_answer_rate
- Numerator: count of answers with unsupported claims
- Denominator: count of total GENERATED answers
- Protocol/Impl Source: Evaluator

## provider_failure_rate
- Numerator: count of provider failures
- Denominator: total requests

## abstention_rate
- Numerator: count of abstentions
- Denominator: total requests

