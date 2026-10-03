# CLAIM VS ANSWER ABSTENTION
- Currently, the system does not surgically drop individual unsupported claims.
- If the `AnswerSafetyGate` detects a proportion of unsupported claims above its tolerance threshold, it ABSTAINS on the ENTIRE answer.
- If the proportion is extremely low (minor hallucination), it QUALIFIES the answer (prepends a warning).
