# V1.2 PROVIDER FAILURE FORENSIC ANALYSIS

Total Provider Failures: 80
- Arm A Failures: 72
- Arm B Failures: 8

## Distribution Analysis
Failures are heavily skewed towards Arm A. This is because in Arm B, the Adaptive Trust Scorer evaluated the retrieved evidence, and due to stringent thresholds, it abstained before calling the LLM API. Thus, Arm B largely avoided provider failures by failing the evidence gate early.

## Error Status
The predominant error was HTTP 429 Rate Limit from Groq for the `openai/gpt-oss-120b` model. This is an API availability limitation, completely independent of the medical logic.
