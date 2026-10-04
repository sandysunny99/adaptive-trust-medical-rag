# REAL_LLM_EVALUATION_PROTOCOL_V1_2

## 1. Overview
The **V1.2 Formal Real-LLM Evaluation Protocol** replaces the historical V1.1 protocol. The primary reason for V1.2 is that V1.1 lacked programmatic prompt reproducibility (manual prompt hashing). V1.2 introduces a strictly versioned, hashed prompt source and freezes all execution configurations to guarantee reproducibility.

**Objective:** Compare the clinical evidence-grounding performance of Baseline Medical RAG against Adaptive Trust-Aware Medical RAG across 80 complex pharmacological cases.

---

## 2. Dataset Definition
- **Source File:** `experiments/manifests/v3_1_human_cases.json`
- **Case Count:** 80
- **Dataset SHA-256:** `db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc`
- **Case ID SHA-256:** `bb47d3c18a0c9bf5488437bc0bca873c4cd5ee4a2d6c7f8ce133ac6cd505da2f`

---

## 3. Retrieval Artifacts (Frozen)
Retrieval execution is explicitly frozen. The protocol strictly prohibits rerunning the live retrieval step to obtain new evidence. Historical V1 retrieval candidate outputs and rankings will be injected exactly as previously retrieved to isolate the LLM reasoning, gating, and verification layer.

---

## 4. Prompt Architecture
- **Prompt Template Path:** `experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt`
- **Programmatic Prompt Hash:** `e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c`
- **Implementation Note:** The prompt strictly segregates `<patient_context>` and `<evidence_block>` from instruction tuning to prevent prompt injection and guarantee template symmetry across arms.

---

## 5. Arm Definitions (Treatment Symmetry)
The evaluation executes 160 total requests (80 cases × 2 arms).

### **Arm A (Baseline RAG)**
- Standard prompt + retrieved evidence.
- Answer Safety Gate (Claim/Citation Verification) **disabled**.
- Evidence Eligibility Gate (Trust Scoring/Abstention) **disabled**.

### **Arm B (Adaptive Trust-Aware RAG)**
- Standard prompt + retrieved evidence.
- Answer Safety Gate **enabled** (Claims unsupported by the retrieved evidence trigger fallback/qualifications).
- Evidence Eligibility Gate **enabled** (Low-trust sources or severe contradictions trigger controlled abstention).

---

## 6. Execution Configuration
- **Provider:** Groq
- **Model:** `openai/gpt-oss-120b`
- **Temperature:** 0.0
- **Max Tokens:** None
- **Seed Support:** NOT_SUPPORTED
- **Retry Policy:** Disabled (provider timeouts mark the request as `FAILED`).
- **Fallback Policy:** Disabled (no silent provider switching).
- **Imputation Policy:** Disabled.

---

## 7. Metrics Definition
V1.2 defines the following programmatic metrics. *Note: Medical Ground Truth for absolute clinical correctness is NOT available. Metrics strictly evaluate adherence to the provided evidence.*

1. **Claim Support Rate:** `sum(verified_claims) / sum(total_generated_claims)`
2. **Citation Validation Rate:** `sum(validated_citations) / sum(total_generated_citations)`
3. **Unsupported Answer Rate:** `count(answers_containing_unsupported_claims) / count(total_generated_answers)`
4. **Abstention Rate:** `count(abstained_requests) / count(total_requests)`
5. **Provider Failure Rate:** `count(failed_provider_requests) / count(total_requests)`

---

## 8. Research Authorization Guard
To prevent accidental medical LLM execution and pollution of application metrics:
Execution is blocked unless the environment variable `RESEARCH_EVAL_AUTHORIZED=1` is explicitly set.

---

## 9. Output Structure
Generated artifacts will be placed in `experiments/runs/real-llm-v1_2/`.
They must conform to the defined V1.2 schema containing `case_id`, `arm`, `provider`, `model`, `prompt_hash`, `claims`, `citations`, and `safety_status`. 

V1.1 historical artifacts remain preserved and untouched in their original directories.
