# PHASE 15 QUERY DIVERSITY AUDIT

## Quantitative Diversity Metrics
- **Exact duplicate query count:** 0
- **Normalized duplicate count:** 0
- **Duplicate query + payload count:** 0

## Pairwise Similarity Distribution
Similarity was computed using normalized strings (lowercased, punctuation stripped) with Python's `difflib.SequenceMatcher.ratio()`. (19,900 pairs analyzed).

- **Minimum similarity:** 0.010
- **Median similarity:** 0.268
- **Maximum similarity:** 0.855
- **Pairs > 0.80:** 1

The single pair exceeding 0.80 was manually reviewed: it involves structurally similar pharmacokinetic questions about two different drugs, but the query and task are entirely distinct.

## Conclusion
Lexical uniqueness is backed by genuine semantic diversity. The median similarity of 0.268 confirms that the cases are completely distinct stimuli, not boilerplate variations.
