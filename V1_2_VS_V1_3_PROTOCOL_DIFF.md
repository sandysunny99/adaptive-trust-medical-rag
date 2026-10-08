# V1.2 vs V1.3 PROTOCOL DIFF

| Element | V1.2 | V1.3 | Changed? | Scientific Reason |
|---|---|---|---|---|
| Dataset | v3.1_human | v3.1_human | NO | Preserve consistency |
| Prompt | V1.2 Prompt | V1.2 Prompt | NO | Preserve consistency |
| Retrieval | Frozen | Frozen | NO | Preserve consistency |
| Provider/Model | Groq/120b | Groq/120b | NO | Preserve consistency |
| Retry Policy | None | 3x (HTTP 429) | YES | Mitigate execution bottleneck |
| Pacing | None | 5s delay | YES | Mitigate rate limit |
| Acceptance | 160 finished | >60 generations | YES | Ensure statistical viability |
