# Phase 14 Security Execution Trace

request_id = s1

USER QUERY
   ↓
PromptInjectionDetector.inspect()
   ↓
ALLOW
   ↓
Drug Normalizer
   ↓
RxNorm Normalization
   ↓
Risk Classification
   ↓
Hybrid Retrieval
   ↓
RetrievalPoisoningDetector.inspect_provenance()
   ↓
Provenance Extraction -> ALLOW
   ↓
Integrity Validation -> ALLOW
   ↓
Trust Scoring
   ↓
Evidence Eligibility Gate
   ↓
Evidence Pack
   ↓
LLM.generate()
   ↓
Structured Output
   ├───────────────┐
   ↓               ↓
CLAIM            ACTION
   ↓               ↓
Verification   AuthorizationBoundary.authorize()
   ↓               ↓
Answer Gate    _execute_tool()
   ↓               ↓
FINAL ANSWER   TOOL RESULT
