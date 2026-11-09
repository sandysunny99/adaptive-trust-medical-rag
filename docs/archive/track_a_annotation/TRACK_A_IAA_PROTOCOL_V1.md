# TRACK_A_IAA_PROTOCOL_V1

## Overview
To quantify the reliability of the human annotation protocol, an Inter-Annotator Agreement (IAA) calculation must be performed before the full annotation set is frozen. 

## 1. Independent Annotators
At least two independent human annotators must label the overlap subset without viewing each other's grades, rationales, or labels. 
- Annotations from `annotator_A` and `annotator_B` must be recorded as separate, independent records or in distinct canonical columns if stored tabularly.

## 2. Overlap Subset
A deterministic subset of 50 positions has been selected (Seed = 42). The exact `position_id`s are recorded in `TRACK_A_IAA_OVERLAP_MANIFEST_V1.json`. This subset must remain blind to any automated labeling script.

## 3. Supported Metrics
Once the dual annotations are complete, the following metrics will be calculated:
- **Percentage Agreement**: The raw percentage of positions where Annotator A and Annotator B assigned the identical label.
- **Quadratic Weighted Cohen's Kappa**: To account for the ordinal nature of the relevance grading (0 = Irrelevant/Insufficient, 1 = Partially Relevant, 2 = Relevant).

## 4. Current IAA Status
`OBSERVED_KAPPA = NOT_YET_OBSERVED`

*(Note: Under no circumstances should automated labels be used to fabricate IAA metrics. Actual human annotations are explicitly required).*
