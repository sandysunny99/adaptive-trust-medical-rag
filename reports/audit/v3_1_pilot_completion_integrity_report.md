# Phase 2F.2 Pilot Completion & Integrity Report

## 1. Executive Summary

The "Candidate Verification Mode" review for the Phase 2F.2 Human Pilot is now **COMPLETE**. 
All surfaced candidates across the 10 pilot cases have been reviewed by a human annotator via the Decision-Helper workflow. 

Because the AI decision-helper facilitated the candidate presentation and some of the reviewed records were title-only, this process must formally be characterized as **AI-assisted human annotation** rather than fully independent, blinded annotation.

## 2. Current Phase Status

* **Phase 2F.2 surfaced-candidate review:** COMPLETE
* **Phase 2F.2 full row-level human annotation:** NOT COMPLETE
* **Phase 2F.4 ground-truth integrity:** BLOCKED
* **Phase 2F.5 F0 vs MedCPT confirmation:** LOCKED
* **Phase 2G Controlled Production Integration:** LOCKED

## 3. Pilot Scope & Unreviewed Rows

While candidate review for the 10 pilot cases is finished, the original validation specification explicitly requires a complete, 2,480-row ground-truth submission for Phase 2F.3/2F.4. 

* **Total Candidates Reviewed:** All explicitly surfaced candidates across the 10 cases have received a human decision (`DIRECT_SUPPORT`, `PARTIAL_SUPPORT`, `NOT_RELEVANT`, `NO_EVIDENCE`).
* **Unreviewed Rows:** The vast majority of the 248 documents per case (2,480 rows total) were *not* explicitly surfaced and thus *not* reviewed by the human annotator. They currently lack a `human_final_label`.
* **Action Required:** The pilot candidate-review exercise by itself does not satisfy the rigorous 2,480-row requirement. A formal scope approval (or protocol amendment) is required to resolve how to handle the remaining unreviewed rows before unlocking Phase 2F.4 (Ground-Truth Integrity Audit).

## 4. Next Steps

1. Review this integrity report and the previously submitted `v3_1_pilot_scope_proposal.md`.
2. Provide explicit approval or an amended protocol on whether the unreviewed rows can be bulk-labeled as `NOT_RELEVANT` based on the candidate-search exhaustiveness, or if a different procedure is required.
3. Once the scope is approved and the remaining rows are resolved, the final CSV ground-truth artifact can be compiled to unblock Phase 2F.4.
