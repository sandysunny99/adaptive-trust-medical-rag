import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class ReviewAuditResult:
    is_complete: bool
    is_freeze_eligible: bool
    errors: List[str]
    total_cases: int
    reviewed_cases: int
    accept_count: int
    revise_count: int
    reject_count: int


class HumanReviewAuditor:
    """Audits the completed Phase 13C Human Review CSV against the canonical case set."""

    ALLOWED_DECISIONS = {"ACCEPT", "REVISE", "REJECT"}
    ALLOWED_BOOLEAN = {"PASS", "FAIL", "NA"}
    ALLOWED_LEAKAGE = {"NONE", "ACCEPTABLE_EXCEPTION", "MATERIAL"}
    ALLOWED_OVERLAP = {"NONE", "JUSTIFIED", "DUPLICATE"}

    def __init__(self, candidate_jsonl_path: str, review_csv_path: str):
        self.candidate_path = Path(candidate_jsonl_path)
        self.review_path = Path(review_csv_path)

    def audit(self) -> ReviewAuditResult:
        errors = []
        if not self.candidate_path.exists():
            return ReviewAuditResult(False, False, ["Candidate JSONL missing."], 0, 0, 0, 0, 0)

        if not self.review_path.exists():
            return ReviewAuditResult(False, False, ["Review CSV missing."], 0, 0, 0, 0, 0)

        # Load canonical
        canonical_cases: Dict[str, dict] = {}
        try:
            with open(self.candidate_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        c = json.loads(line)
                        canonical_cases[c["case_id"]] = c
        except Exception as e:
            return ReviewAuditResult(False, False, [f"Failed to load candidate: {e}"], 0, 0, 0, 0, 0)

        # Load reviews
        reviewed_rows = []
        try:
            with open(self.review_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    reviewed_rows.append(row)
        except Exception as e:
            return ReviewAuditResult(False, False, [f"Failed to load reviews: {e}"], len(canonical_cases), 0, 0, 0, 0)

        total_cases = len(canonical_cases)

        # 1. Coverage Checks
        if len(reviewed_rows) != total_cases:
            errors.append(f"Row count mismatch. Expected {total_cases}, found {len(reviewed_rows)}.")

        review_ids = [r.get("case_id") for r in reviewed_rows]
        if len(set(review_ids)) != len(review_ids):
            errors.append("Duplicate case_id found in review worksheet.")

        for cid in canonical_cases:
            if cid not in review_ids:
                errors.append(f"Missing case_id in review worksheet: {cid}")

        accept_count = 0
        revise_count = 0
        reject_count = 0
        reviewed_cases = 0

        # 2. Row-by-Row Checks
        for row in reviewed_rows:
            cid = row.get("case_id")
            if not cid or cid not in canonical_cases:
                errors.append(f"Unknown or missing case_id in review row: {cid}")
                continue

            canonical = canonical_cases[cid]

            # Hash/Payload Verification
            if row.get("payload") != canonical.get("payload"):
                errors.append(f"Payload mismatch for {cid}.")
            if str(row.get("requires_authorization_check")) != str(canonical.get("requires_authorization_check")):
                errors.append(f"Property mismatch (auth) for {cid}.")
            if str(row.get("requires_provenance_preservation")) != str(canonical.get("requires_provenance_preservation")):
                errors.append(f"Property mismatch (prov) for {cid}.")

            # Decision completeness
            decision = row.get("reviewer_decision", "").strip()
            if not decision:
                errors.append(f"Missing reviewer_decision for {cid}")
                continue

            reviewed_cases += 1

            if decision not in self.ALLOWED_DECISIONS:
                errors.append(f"Invalid reviewer_decision for {cid}: {decision}")

            if decision == "ACCEPT":
                accept_count += 1
            elif decision == "REVISE":
                revise_count += 1
            elif decision == "REJECT":
                reject_count += 1

            # Required Fields
            for required_field in ["reviewer_id", "review_timestamp"]:
                if not row.get(required_field, "").strip():
                    errors.append(f"Missing {required_field} for {cid}")

            # Enum Validations
            sem = row.get("review_semantic_distinctness", "").strip()
            if sem not in ["PASS", "FAIL"]:
                errors.append(f"Invalid semantic_distinctness for {cid}: {sem}")

            leakage = row.get("review_implementation_leakage", "").strip()
            if leakage not in self.ALLOWED_LEAKAGE:
                errors.append(f"Invalid implementation_leakage for {cid}: {leakage}")

            overlap = row.get("cross_taxonomy_overlap", row.get("review_cross_taxonomy_overlap", "")).strip()
            # If the CSV doesn't have cross_taxonomy_overlap exactly, we just ignore if it's not present at all.
            if "cross_taxonomy_overlap" in row or "review_cross_taxonomy_overlap" in row:
                if overlap not in self.ALLOWED_OVERLAP and overlap != "":
                    errors.append(f"Invalid cross_taxonomy_overlap for {cid}: {overlap}")

            for b_field in ["review_attack_realism", "review_ground_truth_consistency",
                            "review_target_consistency", "review_provenance_consistency",
                            "review_authorization_consistency", "review_benign_realism"]:
                val = row.get(b_field, "").strip()
                if val and val not in self.ALLOWED_BOOLEAN:
                    errors.append(f"Invalid {b_field} for {cid}: {val}")
                elif not val and b_field in row:
                    errors.append(f"Missing {b_field} for {cid}")

        is_complete = (reviewed_cases == total_cases) and (len(errors) == 0)
        is_freeze_eligible = is_complete and (revise_count == 0) and (reject_count == 0)

        return ReviewAuditResult(
            is_complete=is_complete,
            is_freeze_eligible=is_freeze_eligible,
            errors=errors,
            total_cases=total_cases,
            reviewed_cases=reviewed_cases,
            accept_count=accept_count,
            revise_count=revise_count,
            reject_count=reject_count
        )
