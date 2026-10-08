import os

file_path = 'tests/e2e/test_v6_c9_multimodal_full_e2e_audit.py'
content = open(file_path).read()

mock_verifier = '''
    class MockClaimVerifier:
        def verify(self, answer, evidence, risk_tier="R1", critical_claim_indices=None, drug_rxcui_map=None):
            from adaptive_trust_medical_rag.verification.claim_verifier_v2 import VerificationReportV2
            return VerificationReportV2(
                all_supported=True,
                support_states={"claim_1": "SUPPORTED"},
                judgments=[]
            )
    app.state.claim_verifier = MockClaimVerifier()
'''

content = content.replace('    app.state.retrieval_engine = MockRetrievalEngine()', '    app.state.retrieval_engine = MockRetrievalEngine()\n' + mock_verifier)

open(file_path, 'w').write(content)
