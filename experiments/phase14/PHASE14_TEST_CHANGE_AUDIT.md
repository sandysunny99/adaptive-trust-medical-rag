# Phase 14 Test Change Audit

## 1. 	ests/test_rag_orchestrator.py
**Original:** ssert len(resp.audit_log["steps"]) >= 2
**New:** ssert len(resp.audit_log) >= 2
**Reason:** The internal _log() format structure of the RAGOrchestrator changed from appending to a "steps" key to a direct array.
**Behavior Changed:** No, merely syntax matching.
**Phase 14 Requirement:** **A (Legitimate contract update)**

**Original:** Candidate(chunk_id="c-warf-001", metadata={"source": "pubmed"})
**New:** Candidate(chunk_id="c-warf-001", metadata={"provenance": {"source": "pubmed", "document_id": "c-warf-001"}})
**Reason:** The new RetrievalPoisoningDetector validates provenance structurally inside .metadata.get("provenance").
**Behavior Changed:** Yes, chunk now successfully passes the poisoning detector gate as safe.
**Phase 14 Requirement:** **B (Fixture update required by new schema)**

## 2. 	ests/security/test_phase14_integration.py
**Original:** Mocks PromptInjectionDetector returning block.
**New:** Passes a genuine hard-reject injection marker <script>alert(1)</script> into the request, drops the mock, and spies on the retriever execution.
**Reason:** To test actual execution boundaries rather than mocking out the entire detection structure, verifying true end-to-end cutoff.
**Behavior Changed:** Yes, test now runs the real payload detector end-to-end to prove the execution boundary stops prior to etrieve.
**Phase 14 Requirement:** **A (Legitimate contract update)**

**Original:** @pytest.mark.skip on 	est_retrieval_poisoning_excluded
**New:** Re-enabled and passing.
**Reason:** Skipped initially due to test fixture mismatches. Now unskipped as the schema update resolved the issue and proven working.
**Behavior Changed:** Yes, now correctly running.
**Phase 14 Requirement:** **E -> A (Fixed invalid test manipulation)**

## 3. 	ests/test_security_extensions.py
**Original:** InjectionDecision(is_safe=False)
**New:** SecurityDecision(decision=SecurityState.BLOCK)
**Reason:** Standardized on SecurityContext models.
**Behavior Changed:** No.
**Phase 14 Requirement:** **B (Fixture update required by new schema)**
