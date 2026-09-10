# V3.1 Confirmed Metric Provenance

| Metric | Raw File | Calculation Description | Denominator | Script | Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Recall@5** | `case_results.jsonl` | Cases where first relevant rank <= 5 | 75 positive cases | `run_v3_confirmed.py` | Verified independently via `verify_v3_confirmed_metrics.py` |
| **MRR@20** | `case_results.jsonl` | Mean 1/(first relevant rank) for rank <= 20 | 75 positive cases | `run_v3_confirmed.py` | Verified independently |
| **nDCG@5** | `case_results.jsonl` | Binary formulation using first relevant rank | 75 positive cases | `analyze_v3_confirmed.py` | Verified independently |
| **Candidate-Pool Recall@20** | `case_results.jsonl` | Cases where first relevant rank <= 20 | 75 positive cases | `analyze_v3_confirmed.py` | Verified independently |
| **Recovery/Regression** | `case_results.jsonl` | Rank transition across the 5 threshold | 75 positive cases | `analyze_v3_confirmed.py` | Verified independently |