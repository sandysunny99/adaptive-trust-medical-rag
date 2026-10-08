content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('log.info("Lazy loading ClaimVerifierV2 (heavy model download)")', '''log.info("Lazy loading ClaimVerifierV2 (heavy model download)")
        print("DEBUG: ABOUT TO LOAD ClaimVerifierV2")''')
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
