# CANONICAL_MEDICAL_RAG_ARCHITECTURE_V1

## 1. Research objective
Mitigating Prompt Injection and Retrieval Hallucinations in medical RAG systems, focusing on evidence-based pharmacology (DDI, ADE, medication safety).

## 2. Research contribution
The core contribution is the **Adaptive Trust-Aware Evidence Control Layer**. Cognee provides infrastructure; the custom research layer provides validation, qualification, security, verification, and abstention.

## 3. End-to-end architecture
`mermaid
flowchart TD
    U[User Pharmacology Query] --> RO[RAG Orchestrator]
    RO --> RN[RxNorm Entity Layer]
    RN --> ESR[Evidence Source Router]
    
    ESR --> SRC_PUB[PubMed / NCBI]
    ESR --> SRC_EPMC[Europe PMC]
    ESR --> SRC_FDA[openFDA]
    ESR --> SRC_CT[ClinicalTrials.gov]
    
    SRC_PUB --> RA[Retrieval Abstraction]
    SRC_EPMC --> RA
    SRC_FDA --> RA
    SRC_CT --> RA
    
    RA -->|BM25 + Dense + Graph| RRF[RRF Fusion k=60]
    RA -->|Cognee add/cognify/search| EM[Cognee Adapter / Evidence Mapper]
    
    RRF --> RERANK[Cross-Encoder MedCPT]
    RERANK --> EM
    
    EM -->|Untrusted Candidate| TRUST[Adaptive Trust-Aware Evidence Control]
    
    TRUST --> SEC[Security / Grounding]
    SEC --> EEG[Evidence Eligibility Gate]
    
    EEG -->|FAIL| ABSTAIN[Block / Abstain]
    EEG -->|PASS| E_PACK[Qualified Evidence Pack]
    
    E_PACK --> LLM[LLM Generation]
    LLM --> ASG[Answer Safety Gate / Claim Verification]
    ASG --> FINAL[Response / Abstention Trace]
`

## 4. Technology stack
| Layer | Technology | Exact Version | Role | Code Location | Runtime Used | Validation State |
|---|---|---|---|---|---|---|
| Application | Python | 3.12+ | Main logic | src/ | YES | A |
| Env | uv | latest | Deps | pyproject.toml | YES | A |
| Interface | FastAPI | N/A | API | N/A | NO | CONCEPTUAL |
| Identity | RxNorm | REST API | Drug Identity | src/ | YES | A |
| Source | NCBI / PMC / FDA | REST APIs | Literature/Data | src/ | YES | A |
| Retrieval | BM25 / PubMedBERT | HuggingFace | Dense Retrieval | src/ | YES | A |
| Infrastructure | Cognee | latest | Graph/Vector | src/ | YES | B (POC) |
| Database | AIOSQLite/LanceDB | local | Storage POC | .cognee/ | YES | B (POC) |
| Security | Integrity/Injection | native | Detectors | src/ | YES | B |
| Trust | AdaptiveTrustScorer | native | Trust Gating | src/ | YES | B |
| LLM | requests / Groq / CF | OpenAI-compat | Provider Transport | src/ | YES | B (Deterministic) |

## 5. Medical evidence sources
- **PubMed / NCBI**: E-utilities (ESearch/EFetch) for DDI/ADE literature.
- **Europe PMC**: REST API for full-text biomedical publications.
- **openFDA**: JSON endpoints for regulatory labels and warnings (explicitly untrusted raw).
- **ClinicalTrials.gov**: Trial interventions and safety outcomes.

## 6. API architecture
APIs are integrated via REST (
equests). Capabilities are currently CODE_SUPPORTED and DOCUMENTATION_SUPPORTED but remain strictly NOT_VERIFIED for live transport.

## 7. RxNorm
Provides **Canonical identity control** (drug normalization, RxCUI resolution). It is not a medical truth engine.

## 8. Retrieval
Combines BM25, S-PubMedBERT, and Graph extraction, fused with RRF (k=60), and reranked via MedCPT cross-encoder.

## 9. Cognee
Provides graph/vector knowledge-representation.
`mermaid
flowchart TD
    I[Ingestion] --> V[Vectors]
    I --> G[Graph]
    V --> S[Search]
    G --> S
    S --> CA[Cognee Adapter]
    CA --> EM[Evidence Mapper]
    EM --> EC[EvidenceCandidate]
    EC --> TRUST[Trust/Security Layer]
`

## 10. Cognee trust boundary
Cognee output is strictly **UNTRUSTED** until validated by the research layer (trust, authority, provenance, integrity).

## 11. Provenance
`mermaid
flowchart LR
    S[Source ID] --> D[Document ID]
    D --> C[Chunk ID]
    C --> N[Cognee Node/Edge]
    N --> EC[EvidenceCandidate]
    EC --> CL[Claim]
    CL --> FA[Final Answer]
`

## 12. Trust scoring
Calculates risk-adjusted scores using: Source Authority, Provenance, Freshness, Entity Alignment, Retrieval Relevance, Evidence Quality, Population Match. Missing values do NOT silently equal zero.

## 13. Security guardrails
`mermaid
flowchart TD
    U[Untrusted Candidate] --> INJ[Prompt Injection Detector]
    INJ --> POI[Retrieval Poisoning Detector]
    POI --> INT[Integrity Validator / SHA-256]
    INT --> RG[Relationship Grounding]
    RG --> EEG[Eligibility Gate]
`

## 14. Relationship grounding
Validates if retrieved graph edges are truly supported by evidence text (SUPPORTED, UNSUPPORTED, CONTRADICTED, NO_RELEVANT_RELATION, AMBIGUOUS). NO_RELEVANT_RELATION blocks.

## 15. Integrity
Compares recomputed SHA-256 against a trusted manifest.

## 16. Contradiction handling
Identifies and weighs contradicting claims based on source authority and trust tier before LLM exposure.

## 17. Claim verification
Post-generation check aligning LLM claims strictly against exact retrieved evidence spans.

## 18. Controlled abstention
Hard safety path. If gates fail (e.g., trust below threshold, MISSING_PROVENANCE, INTEGRITY_MISMATCH), system abstains.

## 19. LLM provider abstraction
`mermaid
flowchart TD
    LA[LLM ADAPTER] --> G[Groq]
    LA --> C[Cloudflare]
    LA --> H[Hugging Face]
    LA --> F[FreeLLMAPI Gateway]
`

## 20. Track A structured adjudication
`mermaid
flowchart TD
    RESP[LLM Response] --> JSON[JSON Parsing]
    JSON --> SCH[JSON Schema Validation]
    SCH --> LG[Label/Grade Consistency Check]
    LG --> ES[Exact Evidence Span Check]
    ES --> CS[Evidence Claim Span Check]
    CS --> FIN[Accepted / Rejected]
`

## 21. Audit/reproducibility
Full cryptographic hashing of prompts, schemas, and configurations. Execution context recorded (STATIC vs DETERMINISTIC vs REAL).

## 22. Experimental status
Code implemented and deterministically tested via mocks. **REAL PROVIDER EXECUTION IS NOT EXECUTED.** Medical pilot is BLOCKED.

## 23. Known limitations
E2E generative security is technically unverified until live LLM inference loop is executed.
