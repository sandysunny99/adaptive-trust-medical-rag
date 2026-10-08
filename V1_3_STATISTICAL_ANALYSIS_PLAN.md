# V1.3 STATISTICAL ANALYSIS PLAN

## Primary Outcomes
1. **Successful Generation Rate** (Binary per request)
2. **Unsupported-Answer Rate** (Binary per generated answer)
3. **Abstention Rate** (Binary per request)
4. **Provider Reliability** (Binary per request)

## Secondary Outcomes
1. Claim Support Rate (Continuous per generated answer)
2. Citation Validation Rate (Continuous per generated answer)

## Paired Unit
N = 80 case IDs.

## Statistical Tests
- **Unsupported-Answer Rate**: McNemar's test on paired generated outputs (if both arms generated an answer).
- **Abstention Rate**: McNemar's test (N=80).

## Provider-Failure Treatment
Treated as missing data for generation quality outcomes. Do not conflate with abstention.
