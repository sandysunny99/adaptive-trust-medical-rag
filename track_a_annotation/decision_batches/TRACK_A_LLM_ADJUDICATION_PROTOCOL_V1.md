# TRACK_A_LLM_ADJUDICATION_PROTOCOL_V1

## Research Control Requirement
Before executing any semantic annotation on P11-P60, the following parameters MUST be explicitly defined and frozen to ensure reproducible research:

| Parameter | Value |
|---|---|
| **1. Provider** | TBD |
| **2. Exact Model Name** | TBD |
| **3. Exact Model Revision/Version** | TBD |
| **4. Local Path / Provider Endpoint** | TBD |
| **5. Inference Framework** | TBD |
| **6. System Prompt** | TBD |
| **7. Adjudication Prompt** | TBD |
| **8. Challenge Prompt** | TBD |
| **9. Temperature** | TBD (Recommend 0.0 for reproducibility) |
| **10. Top P** | TBD |
| **11. Max Tokens** | TBD |
| **12. Random Seed** | TBD |
| **13. Structured-Output Format** | JSON (Defined Schema) |
| **14. Retry Policy** | TBD (e.g., 3 retries on parsing failure) |
| **15. Failure Policy** | TBD (e.g., Log as BLOCKED, do not hallucinate labels) |

*Note: The model must NOT use outside medical knowledge to compensate for missing evidence. It is evaluating retrieved evidence relevance, not clinical safety.*
