# Phase 14 Integration Test Matrix

| Security Layer      | Test Type   | Real Component  | Downstream Cutoff | Status |
| ------------------- | ----------- | --------------- | ----------------- | ------ |
| Prompt Injection    | Integration | Real detector   | Retrieval + LLM   | PASS   |
| Retrieval Poisoning | Integration | Real detector   | Evidence pack     | PASS   |
| Provenance          | Integration | Real validator  | Eligibility       | PASS   |
| Integrity           | Integration | SHA-256         | Eligibility       | PASS   |
| Trust               | Integration | Real scorer     | Gate 1            | PASS   |
| Authorization       | Integration | Real boundary   | Tool execution    | PASS   |
| Claim Verification  | Integration | Real verifier   | Answer            | PASS   |
| Citation Support    | Integration | Real verifier   | Answer            | PASS   |
| Contradiction       | Integration | Real analyzer   | Answer            | PASS   |
| Answer Safety       | Integration | Real gate       | Final response    | PASS   |
| Audit               | Integration | Real audit path | Traceability      | PASS   |
