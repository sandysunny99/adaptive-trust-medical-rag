import json
from pathlib import Path

def main():
    run_dir = Path("experiments/runs/real-llm-v1_2/REAL_LLM_V1_2_RUN_001")
    
    with open(run_dir / "metrics.json", "r") as f:
        metrics = json.load(f)
        
    summary_md = f"""# V1.2 Evaluation Summary
    
## Execution
- Total Cases: {metrics['n_cases']}
- Arm A (Baseline): {metrics['n_arm_a']}
- Arm B (Adaptive Trust-Aware): {metrics['n_arm_b']}
- Total Requests: {metrics['n_total']}

## Results
### Arm A (Baseline)
- Claim Support Rate: {metrics['arm_a_metrics']['claim_support']:.2%}
- Citation Validation Rate: {metrics['arm_a_metrics']['citation_val']:.2%}
- Unsupported Answer Rate: {metrics['arm_a_metrics']['unsupported']:.2%}
- Abstention Rate: {metrics['arm_a_metrics']['abstention']:.2%}
- Provider Failures: {metrics['arm_a_metrics']['provider_failures']}

### Arm B (Adaptive Trust-Aware)
- Claim Support Rate: {metrics['arm_b_metrics']['claim_support']:.2%}
- Citation Validation Rate: {metrics['arm_b_metrics']['citation_val']:.2%}
- Unsupported Answer Rate: {metrics['arm_b_metrics']['unsupported']:.2%}
- Abstention Rate: {metrics['arm_b_metrics']['abstention']:.2%}
- Provider Failures: {metrics['arm_b_metrics']['provider_failures']}
"""

    with open(run_dir / "summary.md", "w") as f:
        f.write(summary_md)
        
    with open("REAL_LLM_EVALUATION_V1_2_RESULTS.md", "w") as f:
        f.write("# REAL_LLM_EVALUATION_V1_2_RESULTS\n\n" + summary_md)
        
    print("Reports generated.")

if __name__ == "__main__":
    main()
