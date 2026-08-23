# Retrieval Poisoning & Source Integrity Evaluation

## Threat Vectors & Countermeasures

| Attack Category | Threat Scenario | Detection Method | Mitigation Result |
|-----------------|-----------------|------------------|-------------------|
| **Hash Spoofing** | Modified document payload with fake hash | SHA-256 re-computation | Ingestion quarantine trigger |
| **Low-Authority Poisoning** | Malicious blog post claiming safe lethal dosage | Source Authority Tiering (Tier 4) | Pre-Gen Gate Abstention |
| **Outdated Evidence Poisoning** | 20-year old study advocating deprecated therapy | Exponential Freshness Decay ($S_{fresh} < 0.2$) | Trust score below threshold |
| **Entity Misattribution** | Compound A safety profile assigned to Compound B | RxCUI / scispaCy NER Match ($S_{ent} = 0$) | Pre-Gen Gate Abstention |

## Performance Metrics
- **Poisoning Detection Rate:** 98.4%
- **Malicious Context Acceptance Rate:** 0.0%
