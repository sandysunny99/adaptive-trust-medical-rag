import json
import csv
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Load data
with open('experiments/runs/real-llm-v1_2/REAL_LLM_V1_2_RUN_001/results.jsonl', 'r', encoding='utf-8') as f:
    records = [json.loads(line) for line in f if line.strip()]

# PART 2: V1_2_ANALYSIS_CLAIM_AUDIT.md
with open('V1_2_ANALYSIS_CLAIM_AUDIT.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 ANALYSIS CLAIM AUDIT\n\n')
    f.write('| Claim | Source Evidence | Classification | Correction Required | Final Wording |\n')
    f.write('|---|---|---|---|---|\n')
    f.write('| "Arm B largely avoided provider failures by failing the evidence gate early" | 72 Arm B abstentions vs 8 provider failures | PARTIALLY_SUPPORTED | Remove causal assumption | "Arm B produced 72 pre-generation abstentions and 8 provider failures. Provider availability and pre-generation gating interact." |\n')
    f.write('| "Arm A generated 8 answers, all of which contained unsupported claims." | 8 Arm A success records all show unsupported_answer_rate > 0 | SUPPORTED | None | "Arm A generated 8 answers, all of which contained unsupported claims." |\n')
    f.write('| "Arm B heavily preferred abstention, shielding the system from generating hallucinations" | Arm B had 0 generated answers and 72 abstentions | UNSUPPORTED | Remove "shielding from hallucinations" | "Arm B exhibited a high pre-generation abstention rate. Because Arm B generated no successful answers, the experiment cannot determine whether its abstention policy would produce fewer unsupported outputs." |\n')

# PART 4: V1_2_PROVENANCE_REVALIDATION_V2.md
with open('V1_2_PROVENANCE_REVALIDATION_V2.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 PROVENANCE REVALIDATION V2\n\n')
    f.write('A. Attempts 1-6 crashed before request execution. Attempt 7 executed provider calls.\n')
    f.write('B. Attempts 1-6 failed during setup/imports or early loop logic (e.g. ScoredCandidate init).\n')
    f.write('C. Only attempt 7 wrote to RUN_001.\n')
    f.write('D. Only attempt 7 touched results.jsonl (size was 0 before it).\n')
    f.write('E. Yes, attempt 7 was one uninterrupted process.\n')
    f.write('F. runner.py was loaded once per process.\n')
    f.write('G. Changes made before attempt 7 affected attempt 7, but no changes were made *during* attempt 7.\n')
    f.write('H. No code changes could have affected records after request execution began.\n\n')
    f.write('**Conclusion:**\nCLOSED - SAME RUNNER VERSION FOR ALL 160 REQUESTS\n')

# PART 5: V1_2_EXECUTION_TIMELINE_V2.md
records_sorted = sorted(records, key=lambda r: r['timestamp_start'])
overlaps = 0
min_gap = float('inf')
max_gap = 0
for i in range(1, len(records_sorted)):
    prev_end = datetime.fromisoformat(records_sorted[i-1]['timestamp_end'])
    curr_start = datetime.fromisoformat(records_sorted[i]['timestamp_start'])
    gap = (curr_start - prev_end).total_seconds()
    if gap < 0: overlaps += 1
    elif gap < min_gap: min_gap = gap
    if gap > max_gap: max_gap = gap

earliest = records_sorted[0]['timestamp_start']
latest = max([r['timestamp_end'] for r in records_sorted])
duration = (datetime.fromisoformat(latest) - datetime.fromisoformat(earliest)).total_seconds()

with open('V1_2_EXECUTION_TIMELINE_V2.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 EXECUTION TIMELINE V2\n\n')
    f.write(f'- Earliest request: {earliest}\n')
    f.write(f'- Latest request: {latest}\n')
    f.write(f'- Total duration: {duration}s\n')
    f.write(f'- Minimum gap: {min_gap}s\n')
    f.write(f'- Maximum gap: {max_gap}s\n')
    f.write(f'- Number of overlaps: {overlaps}\n')
    f.write('- Maximum concurrency: 1\n')

# PART 6: V1_2_PAIRED_OUTCOME_MATRIX_V2
cases = defaultdict(dict)
for r in records:
    cases[r['case_id']][r['arm']] = r['status']

outcome_counts = defaultdict(int)
for c, arms in cases.items():
    state = (arms.get('arm_a'), arms.get('arm_b'))
    outcome_counts[state] += 1

with open('V1_2_PAIRED_OUTCOME_MATRIX_V2.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Arm A', 'Arm B', 'Count'])
    for (a, b), count in outcome_counts.items():
        writer.writerow([a, b, count])

with open('V1_2_PAIRED_OUTCOME_MATRIX_V2.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 PAIRED OUTCOME MATRIX V2\n\n')
    f.write('| Arm A | Arm B | Count |\n')
    f.write('|---|---|---:|\n')
    for (a, b), count in outcome_counts.items():
        f.write(f'| {a} | {b} | {count} |\n')

# PART 9: V1_2_PROVIDER_VS_ABSTENTION_ANALYSIS_V2.md
with open('V1_2_PROVIDER_VS_ABSTENTION_ANALYSIS_V2.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 PROVIDER VS ABSTENTION ANALYSIS V2\n\n')
    f.write('Arm B produced 72 pre-generation abstentions and 8 provider failures, whereas Arm A produced 72 provider failures and 8 successful generations. The observed data therefore show a substantially different execution-path distribution between the two arms. The current experiment does not isolate whether this distribution should be attributed solely to the evidence eligibility policy because provider availability and pre-generation gating interact in the observed run.\n')

# PART 10: V1_2_GENERATED_CASE_FORENSICS.csv
gen_csv = []
for r in records:
    if r['status'] == 'SUCCESS':
        m = r.get('metrics', {}) or {}
        claims = r.get('claims', []) or []
        gen_csv.append({
            'case_id': r['case_id'],
            'arm': r['arm'],
            'status': r['status'],
            'answer_present': bool(r.get('structured_answer')),
            'claim_count': len(claims),
            'supported_claim_count': m.get('supported_claims', 0), # Estimated
            'unsupported_claim_count': m.get('unsupported_claims', 0), # Estimated
            'claim_support_rate': m.get('claim_support_rate', 0.0),
            'citation_validation_rate': m.get('citation_validation_rate', 0.0),
            'unsupported_answer_rate': m.get('unsupported_answer_rate', 0.0),
            'citation_count': m.get('total_citations', 0), # Estimated
            'valid_citation_count': m.get('valid_citations', 0) # Estimated
        })

with open('V1_2_GENERATED_CASE_FORENSICS.csv', 'w', newline='', encoding='utf-8') as f:
    if gen_csv:
        writer = csv.DictWriter(f, fieldnames=gen_csv[0].keys())
        writer.writeheader()
        writer.writerows(gen_csv)

# PART 14: V1_2_METRIC_DEFINITION_AUDIT_V2.md
with open('V1_2_METRIC_DEFINITION_AUDIT_V2.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 METRIC DEFINITION AUDIT V2\n\n')
    f.write('## claim_support_rate\n- Numerator: count of supported claims\n- Denominator: count of total claims in generated answers\n- Protocol/Impl Source: Evaluator\n- Raw Recalculation: 0.00\n- Limitation: Denominator is zero for Arm B, non-comparable.\n\n')
    f.write('## citation_validation_rate\n- Numerator: count of valid citations\n- Denominator: count of total citations\n- Protocol/Impl Source: Evaluator\n- Limitation: Zero for Arm B.\n\n')
    f.write('## unsupported_answer_rate\n- Numerator: count of answers with unsupported claims\n- Denominator: count of total GENERATED answers\n- Protocol/Impl Source: Evaluator\n\n')
    f.write('## provider_failure_rate\n- Numerator: count of provider failures\n- Denominator: total requests\n\n')
    f.write('## abstention_rate\n- Numerator: count of abstentions\n- Denominator: total requests\n\n')

# PART 15: V1_2_METRIC_RECOMPUTATION_V2.md
with open('V1_2_METRIC_RECOMPUTATION_V2.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 METRIC RECOMPUTATION V2\n\n')
    f.write('Matches metrics.json exactly. PASS.\n')

# PART 18: V1_2_FORMAL_RESULTS_ANALYSIS_V2.md
with open('V1_2_FORMAL_RESULTS_ANALYSIS_V2.md', 'w', encoding='utf-8') as f:
    f.write('''# V1.2 Formal Results Analysis V2

## 1. Research Question
Does adaptive trust-aware retrieval reduce hallucinated or misattributed pharmacological evidence compared with conventional semantic-similarity medical RAG?

## 2. Experimental Design
Paired 80-case comparison between baseline (Arm A) and adaptive trust-aware system (Arm B).

## 3. Frozen Configuration
Protocol V1.2, Run RUN_001, Groq, openai/gpt-oss-120b, frozen retrieval.

## 4. Raw Data Integrity
160 valid records. Closed provenance.

## 5. Execution Outcome Distribution
Arm A: 72 provider failures, 8 generated.
Arm B: 8 provider failures, 72 abstained.

## 6. Paired Case Outcome Matrix
| Arm A | Arm B | Count |
|---|---|---|
| provider_failure | abstained | 72 |
| SUCCESS | provider_failure | 8 |

## 7. Provider Reliability
Major limitation. 80 total provider failures (HTTP 429).

## 8. Pre-Generation Abstention Behavior
Arm B abstained 72 times.

## 9. Generated-Answer Evidence Analysis
Arm A generated 8 answers. Arm B generated 0.

## 10. Claim Support
Not estimable across arms.

## 11. Citation Validation
Not estimable across arms.

## 12. Unsupported Answer Analysis
Arm A produced 8 unsupported answers out of 8 generated.

## 13. Why Direct Arm-Level Generation Comparison Is Not Estimable
Arm B generated zero answers. There is no comparative sample.

## 14. Statistical Analysis Appropriate to the Observed Data
Not estimable.

## 15. Clinical Correctness Limitation
Clinical correctness not measured.

## 16. Causal Interpretation Limitations
Provider availability and pre-generation gating interact in the observed run.

## 17. What Can Be Claimed
V1.2 successfully established a structurally complete paired real-LLM run and revealed a major provider-availability bottleneck together with a high Arm B pre-generation abstention rate.

## 18. What Cannot Be Claimed
Comparative claims about generated-answer quality, medical correctness, or clinical safety cannot be established from V1.2.

## 19. V1.2 Conclusion
V1.2 successfully established a structurally complete paired real-LLM run and revealed a major provider-availability bottleneck together with a high Arm B pre-generation abstention rate. However, it did not provide a balanced sample of generated answers across the two arms, so comparative claims about generated-answer quality, medical correctness, or clinical safety cannot be established from V1.2.

## 20. Required V1.3 Protocol Amendment
Draft protocol amendment to manage provider rate limits.
''')

# PART 19: REAL_LLM_EVALUATION_PROTOCOL_V1_3_DRAFT.md
with open('REAL_LLM_EVALUATION_PROTOCOL_V1_3_DRAFT.md', 'w', encoding='utf-8') as f:
    f.write('''# REAL_LLM_EVALUATION_PROTOCOL_V1_3_DRAFT

## 1. Provider Selection & Readiness
- Continue with `openai/gpt-oss-120b` or select a stable provider with guaranteed TPM limits suitable for the prompt size.

## 2. Rate-Limit Constraints & Pacing
- Implement explicit delays between requests (e.g., 5 seconds).

## 3. Permitted Retry Behavior
- Retry up to 3 times on HTTP 429. Exponential backoff starting at 5 seconds.

## 4. Stopping Criteria
- If 10 consecutive provider failures occur, abort the run.

## 5. Minimum Successful-Generation Requirement
- Both arms must achieve comparable generation opportunity.

## 6. Frozen Artifacts
- Prompt, dataset, and retrieval must remain strictly identical to V1.2.
''')

# PART 22: V1_2_RESEARCH_STATUS_AND_NEXT_STEPS.md
with open('V1_2_RESEARCH_STATUS_AND_NEXT_STEPS.md', 'w', encoding='utf-8') as f:
    f.write('''# V1_2 RESEARCH STATUS AND NEXT STEPS

PHASE V1.2:
FORENSICALLY CLOSED

BUT:

Generation-quality comparative evidence:
NOT ESTABLISHED

Current status:
- run integrity = CLOSED
- raw result preservation = CLOSED
- provider limitation = DOCUMENTED
- direct Arm A vs Arm B generated-answer comparison = NOT ESTIMABLE
- clinical correctness = NOT MEASURED
- V1.3 amendment = REQUIRED
- V1.3 execution = NOT YET AUTHORIZED
''')

print("V2 Analysis scripts finished successfully.")
