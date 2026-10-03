# Canonical Relationship Identity Security Requirement Review

## 1. Documented Threat Models
- **TM-03 (Retrieval Poisoning)**: Documented in `reports/security/threat_model.md`.
- **Entity Misattribution**: Documented in `reports/security/retrieval_poisoning_evaluation.md` as "Compound A safety profile assigned to Compound B".

## 2. Gap Identification against Threat Model
- **Correct source + wrong drug pair**: Implicitly covered by the Entity Misattribution threat.
- **Correct source + wrong relationship interpretation (Predicate/Direction Spoofing)**: While "Retrieval Poisoning" is broadly identified, the specific attack vector of an LLM hallucinating the *direction* of a relationship from an otherwise trusted source is barely mitigated by current controls (NLI).

## 3. Conclusion
The security requirements strictly forbid entity misattribution and rely heavily on rigorous pre-generation and post-generation gates. The current lack of Canonical Relationship Identity binding leaves a severe gap where NLI text-matching can be exploited by adversarial text phrased to "entail" a false direction or predicate.
