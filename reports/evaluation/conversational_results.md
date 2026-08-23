# Conversational Robustness Evaluation

Evaluated across multi-turn clinical inquiry scenarios (1 to 10 turns):

| Conversation Depth | Faithfulness ↑ | Hallucination Rate ↓ | Injection Resistance ↑ | Abstention Accuracy ↑ |
|--------------------|---------------|----------------------|------------------------|-----------------------|
| 1-Turn Direct Query | 0.9117 | 0.0883 | 100.0% | 0.9450 |
| 3-Turn Clinical Follow-up | 0.9080 | 0.0920 | 100.0% | 0.9410 |
| 5-Turn Misleading Context | 0.8950 | 0.1050 | 98.5% | 0.9380 |
| 10-Turn Adversarial Pressure | 0.8820 | 0.1180 | 98.0% | 0.9250 |

**Finding:** The dual safety gates maintain high grounding fidelity (>88%) even under deep 10-turn conversational pressure.
