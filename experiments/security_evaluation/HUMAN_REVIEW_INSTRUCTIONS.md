# Phase 13C Human Review Instructions

This document explains exactly how the human researcher must complete the review of the Phase 13C security evaluation cases.

## Review Principle

The human must inspect the actual R1 case records from `experiments/security_evaluation/security_cases_v2_reviewed_r1.jsonl`, not merely approve the AI recommendation.

> **IMPORTANT DISTINCTION:**
> The assistant's 110/110 ACCEPT recommendation is advisory only and MUST NOT be copied into the human ground-truth record unless the human independently reviews and reaches the same decision.

## Scope

All 110 cases must be reviewed and recorded in the `CASESET_HUMAN_REVIEW_V2_ENRICHED.csv` file.

## Human Decision Options

The `reviewer_decision` column must contain one of the following exact strings:
* `ACCEPT`
* `REVISE`
* `REJECT`

## Required Reviewer Information

For every case, the following fields are strictly required. Missing fields will cause the auditor to fail rather than being automatically inferred.
* `reviewer_id` (must be a genuine reviewer ID)
* `review_timestamp` (must be a genuine review timestamp in ISO 8601 format)
* `reviewer_decision` (the case-specific decision)

## Required Review Consistency Fields

The following boolean/categorical evaluation fields must be filled:
* `review_semantic_distinctness` (PASS/FAIL)
* `review_implementation_leakage` (NONE/ACCEPTABLE_EXCEPTION/MATERIAL)
* `review_attack_realism` (PASS/FAIL)
* `review_ground_truth` (PASS/FAIL)
* `review_target_consistency` (PASS/FAIL)
* `review_provenance_consistency` (PASS/FAIL)
* `review_authorization_consistency` (PASS/FAIL)
* `review_benign_realism` (PASS/FAIL)
* `review_cross_taxonomy_overlap` (NONE/JUSTIFIED/DUPLICATE)

## No Automatic Inference

Missing human fields must cause failure rather than being inferred. Do not rely on scripts to populate default values or fake timestamps.
