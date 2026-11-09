# V1.2 ANALYSIS CLAIM AUDIT

| Claim | Source Evidence | Classification | Correction Required | Final Wording |
|---|---|---|---|---|
| "Arm B largely avoided provider failures by failing the evidence gate early" | 72 Arm B abstentions vs 8 provider failures | PARTIALLY_SUPPORTED | Remove causal assumption | "Arm B produced 72 pre-generation abstentions and 8 provider failures. Provider availability and pre-generation gating interact." |
| "Arm A generated 8 answers, all of which contained unsupported claims." | 8 Arm A success records all show unsupported_answer_rate > 0 | SUPPORTED | None | "Arm A generated 8 answers, all of which contained unsupported claims." |
| "Arm B heavily preferred abstention, shielding the system from generating hallucinations" | Arm B had 0 generated answers and 72 abstentions | UNSUPPORTED | Remove "shielding from hallucinations" | "Arm B exhibited a high pre-generation abstention rate. Because Arm B generated no successful answers, the experiment cannot determine whether its abstention policy would produce fewer unsupported outputs." |
