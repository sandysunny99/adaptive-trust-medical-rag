# TRUST R3 MISSING DATA SEMANTICS V1

**R3 Risk Class Definition**: 
High-Risk scenarios involving lethal dosage, severe drug-drug contraindications, black box warnings. 
- Threshold: 0.75
- Meaning: Highest level of verified evidence required to allow the LLM to generate an answer.
- Missing required evidence: "Query involves High-Risk (R3) scenarios ... without verified high-authority evidence" -> Must abstain.

**R3_CODE_SPECIFICATION_MISMATCH**:
The current remediation re-weights the trust score based only on available data. An R3 query missing `population_match` and `evidence_quality` might still yield a `1.0` score if the remaining factors are strong. The code bypasses the requirement that High-Risk scenarios *must* have sufficient verified evidence, as missing evidence simply drops out of the denominator instead of failing the gate.
