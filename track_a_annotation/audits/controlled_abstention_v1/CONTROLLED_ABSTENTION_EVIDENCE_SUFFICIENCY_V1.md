# EVIDENCE SUFFICIENCY
- Insufficient evidence at the textual NLI level results in `entailment < max(neutral, contradiction)`.
- This causes `citation_supports=False`.
- The claim is marked `UNSUPPORTED`.
- If critical claims are unsupported, the AnswerSafetyGate abstains.
