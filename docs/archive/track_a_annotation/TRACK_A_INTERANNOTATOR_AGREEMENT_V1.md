# TRACK_A_INTERANNOTATOR_AGREEMENT_V1

## Overview
This document records the inter-annotator agreement statistics for the Track A Retrieval Relevance dataset.

## Agreement Statistic Design
Since the annotation schema utilizes graded relevance (0, 1, 2) to support nDCG calculations, a simple percentage agreement or standard Cohen's Kappa is insufficient because it treats all disagreements equally (e.g., disagreeing between 1 and 2 is penalized the same as 0 and 2).

Therefore, the appropriate agreement statistic is **Cohen's Weighted Kappa (Quadratic)**, which appropriately penalizes disagreements based on the ordinal distance between the grades.

## Current Status
**Status:** PENDING ANNOTATION COMPLETION

- **Total independently dual-annotated positions:** 0
- **Agreement Rate (Weighted Kappa):** TBD
- **Disagreement Count:** TBD
- **Ambiguous Count (pre-adjudication):** TBD
- **Adjudicated Count:** TBD
