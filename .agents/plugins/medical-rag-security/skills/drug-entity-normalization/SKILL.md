---
name: drug-entity-normalization
description: Standard operating procedures for normalizing drug entities, brand-to-generic mapping, RxNorm RxCUI resolution, and scispaCy NER extraction.
---

# Drug Entity Normalization Skill

This skill ensures that queries and documents are mapped to standardized pharmacological identifiers to prevent entity misattribution.

## Objectives

1. Prevent attributing effects of Drug X to Drug Y (e.g., conflating Hydralazine vs Hydroxyzine, or Celecoxib vs Celexa).
2. Resolve brand names, international non-proprietary names (INN), and synonyms to canonical RxNorm identifiers (`RxCUI`).
3. Differentiate dosage forms, salts, and administration routes when clinically relevant (e.g., Metoprolol Tartrate vs Metoprolol Succinate).

## Resolution Pipeline

```
Raw Query / Text
   │
   ▼
[1] Extraction: Clinical NER (scispaCy / en_core_sci_md) identifies chemical/disease mentions
   │
   ▼
[2] Direct Lookup: Local Exact & Fuzzy Cache (Normalized brand/generic table)
   │
   ▼ (if cache miss)
[3] RxNorm REST API Query: `/REST/rxcui.json?name={entity}` or `/REST/approximateTerm.json?term={entity}`
   │
   ▼
[4] Disambiguation & Enrichment:
   ├── Canonical Generic Name
   ├── RxCUI (Concept Unique Identifier)
   ├── ATC Code / Pharmacological Class (e.g., Beta-blocker, ACE-inhibitor)
   └── Salt / Form disambiguation
```

## Attribution Validation Rules

- When evaluating an interaction between Drug A and Drug B, both entities must match their respective RxCUIs in the retrieved evidence snippet.
- If a document only mentions a drug class (e.g., "NSAIDs") and not the specific drug (e.g., "Ibuprofen"), the attribution score must be explicitly discounted unless class-level generalization is warranted by the risk class.
