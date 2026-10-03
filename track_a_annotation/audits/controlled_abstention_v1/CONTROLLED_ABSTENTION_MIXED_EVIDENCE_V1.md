# MIXED EVIDENCE ANALYSIS
- If context contains Evidence 1 (Support) and Evidence 2 (Neutral).
- Claim citing `[Source 1][Source 2]` evaluates `max(neutral)` across both.
- If Neutral is 1.0 on Source 2, `citation_supports` fails.
- Thus, over-citing dilutes the claim support and causes it to fail securely.
