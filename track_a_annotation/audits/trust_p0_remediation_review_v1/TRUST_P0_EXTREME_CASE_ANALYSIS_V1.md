# TRUST P0 EXTREME-CASE ANALYSIS V1

**Diagnostic Results:**
- **CASE A (All factors high):** score=0.9000, eligible=True, missing=[]
- **CASE C (One missing, remaining high):** score=0.9000, eligible=True, missing=['population_match']
- **CASE E (Four missing, remaining high):** score=0.9000, eligible=True, missing=['evidence_quality', 'freshness', 'consistency', 'population_match']

**Conclusion**: Missing data can be excluded without dragging the score to 0.0, but allowing `eligible=True` for heavily depleted factors violates the principle of safety-through-abstention.
