# TRUST P0 MISSING DATA REGRESSION MATRIX V1

| Case | Object Representation | Missing-State | Aggregate Score Behavior | Gate State |
|---|---|---|---|---|
| All factors present | All float | [] | Full calculation | Normal |
| `query_relevance` missing | `None` | `['query_relevance']` | Re-weighted calculation | Normal |
| `evidence_quality` missing | `None` | `['evidence_quality']` | Re-weighted calculation | Normal |
| `population_match` missing | `None` | `['population_match']` | Re-weighted calculation | Normal |
| `freshness` missing | `None` | `['freshness']` | Re-weighted calculation | Normal |
| Explicit Zero vs Missing | `0.0` | [] | Drags score down | Fails gate |
| Explicit One vs Missing | `1.0` | [] | Drags score up | Passes gate |
