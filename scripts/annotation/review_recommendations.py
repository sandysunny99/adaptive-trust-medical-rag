#!/usr/bin/env python3
"""Interactive CLI for researcher review of AI-assisted annotation recommendations.

Loads AI recommendations from track_a_annotation/ai_assisted/AI_RECOMMENDATIONS_V1.jsonl,
presents each recommendation to the researcher for human adjudication (Approve, Override,
Defer, or Reject), and writes authoritative researcher decisions to
track_a_annotation/ai_assisted/RESEARCHER_DECISIONS_V1.jsonl with strict provenance marking.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

# Ensure repo root and script directory are accessible
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.annotation.common import (
    DEFAULT_DECISIONS_FILE,
    DEFAULT_RECOMMENDATIONS_FILE,
    LABEL_TO_GRADE,
    PROVENANCE_AI_ASSISTED_CONFIRMED,
    PROVENANCE_AI_ASSISTED_OVERRIDDEN,
    PROVENANCE_DEFERRED,
    PROVENANCE_REJECTED,
    VALID_LABELS,
    load_jsonl,
    normalize_label,
    verify_span_substring,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Researcher Review CLI for AI-assisted annotation recommendations.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--recommendations-file",
        type=str,
        default=str(DEFAULT_RECOMMENDATIONS_FILE),
        help="Path to AI recommendations JSONL file.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=str(DEFAULT_DECISIONS_FILE),
        help="Path to researcher decisions JSONL output file.",
    )
    parser.add_argument(
        "--researcher-id",
        type=str,
        default="RESEARCHER_CONFIRMED",
        help="Identifier for reviewing researcher or clinical adjudicator.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Skip positions that already have researcher decisions recorded.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_false",
        dest="resume",
        help="Do not skip existing positions; re-evaluate from beginning.",
    )
    parser.add_argument(
        "--filter-confidence",
        choices=["HIGH", "MEDIUM", "LOW"],
        default=None,
        help="Review only recommendations matching a specific confidence level.",
    )
    parser.add_argument(
        "--filter-label",
        type=str,
        default=None,
        help="Review only recommendations matching a specific proposed label (e.g. AMBIGUOUS).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of recommendations to review in this session.",
    )
    parser.add_argument(
        "--auto-approve-high-confidence",
        action="store_true",
        help="Batch-approve all HIGH confidence recommendations without interactive prompts.",
    )
    parser.add_argument(
        "--batch-approve-all",
        action="store_true",
        help="Batch-approve all pending recommendations (useful for test fixtures or automated pipelines).",
    )
    return parser.parse_args()


def display_recommendation_card(rec: dict[str, Any], index: int, total: int) -> None:
    """Print structured presentation of evidence and AI recommendation."""
    pid = rec.get("position_id", "UNKNOWN")
    qid = rec.get("query_id", "UNKNOWN")
    qtext = rec.get("query_text", qid)
    doc_id = rec.get("document_id", "N/A")
    chunk_id = rec.get("chunk_id", "N/A")
    evidence = rec.get("retrieved_evidence", "")
    rec_lbl = rec.get("recommended_label", "UNKNOWN")
    rec_grd = rec.get("recommended_grade")
    conf = rec.get("confidence", "UNKNOWN")
    span = rec.get("recommended_evidence_span") or rec.get("evidence_span") or ""
    rationale = rec.get("recommended_rationale") or rec.get("rationale") or "N/A"
    alt_lbl = rec.get("alternative_label") or "None"

    print("\n" + "=" * 80)
    print(f" Position: {pid}  [{index}/{total}] | Confidence: {conf} | Doc: {doc_id} | Chunk: {chunk_id}")
    print("=" * 80)
    print(f"Query: {qtext}")
    print("-" * 80)
    print("Evidence Preview:")
    preview_len = 280
    if len(evidence) <= preview_len:
        print(f"  {evidence}")
    else:
        print(f"  {evidence[:preview_len]}...")
        print(f"  [... {len(evidence)} total characters - press 'V' to view full text]")
    print("-" * 80)
    print(f"AI Recommendation : {rec_lbl} (Grade: {rec_grd})")
    if span:
        print(f"Supporting Span   : \"{span[:160]}{'...' if len(span) > 160 else ''}\"")
    else:
        print("Supporting Span   : [EMPTY / NOT APPLICABLE]")
    print(f"Alternative Label : {alt_lbl}")
    print(f"AI Rationale      : {rationale}")
    print("-" * 80)


def prompt_for_override(rec: dict[str, Any]) -> tuple[str, int | None, str, str]:
    """Prompt researcher for override label, rationale, and exact evidence span."""
    evidence = rec.get("retrieved_evidence", "")
    print("\n--- Override Options ---")
    print("  [1] RELEVANT                 (Grade 2)")
    print("  [2] PARTIALLY_RELEVANT       (Grade 1)")
    print("  [3] IRRELEVANT               (Grade 0)")
    print("  [4] INSUFFICIENT_INFORMATION (Grade 0)")
    print("  [5] AMBIGUOUS                (Grade null)")

    choice_map = {
        "1": "RELEVANT",
        "2": "PARTIALLY_RELEVANT",
        "3": "IRRELEVANT",
        "4": "INSUFFICIENT_INFORMATION",
        "5": "AMBIGUOUS",
    }

    new_label = ""
    while new_label not in choice_map.values():
        sel = input("Select new label [1-5]: ").strip()
        if sel in choice_map:
            new_label = choice_map[sel]
        elif sel.upper() in VALID_LABELS:
            new_label = sel.upper()
        else:
            print("Invalid choice. Please select 1 through 5.")

    new_grade = LABEL_TO_GRADE.get(new_label)

    # Rationale
    default_rat = f"Researcher override: reassessed relevance as {new_label}."
    rat_in = input(f"Enter rationale (press Enter for '{default_rat}'): ").strip()
    override_rationale = rat_in if rat_in else default_rat

    # Evidence Span (Required for RELEVANT / PARTIALLY_RELEVANT)
    final_span = ""
    if new_label in {"RELEVANT", "PARTIALLY_RELEVANT"}:
        while True:
            span_in = input("Enter exact supporting evidence span (substring from evidence): ").strip()
            if not span_in:
                print("Evidence span is required for RELEVANT and PARTIALLY_RELEVANT annotations!")
                continue
            is_valid, matched_span = verify_span_substring(span_in, evidence)
            if is_valid:
                final_span = matched_span
                print(f"✓ Exact span confirmed ({len(final_span)} chars).")
                break
            else:
                print(f"[ERROR] {matched_span}")
                retry = input("Try again? [y/N]: ").strip().lower()
                if retry != "y":
                    final_span = span_in
                    break

    return new_label, new_grade, override_rationale, final_span


def record_decision(
    output_path: Path,
    rec: dict[str, Any],
    action: str,
    researcher_id: str,
    final_label: str | None,
    final_grade: int | None,
    final_rationale: str,
    final_span: str,
    provenance: str,
    human_confirmation: bool,
) -> dict[str, Any]:
    """Persist reviewed decision to JSONL with full provenance markings."""
    now_iso = datetime.now(timezone.utc).isoformat()
    decision_record = {
        "position_id": rec.get("position_id"),
        "query_id": rec.get("query_id"),
        "query_text": rec.get("query_text"),
        "chunk_id": rec.get("chunk_id"),
        "document_id": rec.get("document_id"),
        "retrieved_evidence": rec.get("retrieved_evidence"),
        "ai_recommended_label": rec.get("recommended_label"),
        "ai_recommended_grade": rec.get("recommended_grade"),
        "ai_confidence": rec.get("confidence"),
        "ai_recommended_span": rec.get("recommended_evidence_span", ""),
        "action": action,
        "final_label": final_label,
        "final_grade": final_grade,
        "final_rationale": final_rationale,
        "final_evidence_span": final_span,
        "researcher_id": researcher_id,
        "provenance": provenance,
        "human_confirmation": human_confirmation,
        "llm_assistance": "RESEARCH_CONTROL_LLM_ASSISTED",
        "timestamp": now_iso,
        # Direct schema compatibility fields
        "label": final_label,
        "relevance_grade": final_grade,
        "rationale": final_rationale,
        "evidence_span": final_span,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(decision_record, ensure_ascii=False) + "\n")
        f.flush()

    return decision_record


def main() -> None:
    args = parse_args()
    recs_path = Path(args.recommendations_file)
    output_path = Path(args.output_file)

    if not recs_path.is_file():
        print(f"[ERROR] Recommendations file not found: {recs_path}")
        print("Please run `scripts/annotation/run_ai_annotation.py` first to generate recommendations.")
        sys.exit(1)

    all_recs = load_jsonl(recs_path)
    if not all_recs:
        print(f"[WARNING] No recommendation records found in {recs_path}.")
        sys.exit(0)

    # Check already reviewed decisions
    existing_decisions = load_jsonl(output_path) if output_path.is_file() else []
    existing_pids = {d.get("position_id") for d in existing_decisions if d.get("position_id")}

    if args.resume and existing_pids:
        pending_recs = [r for r in all_recs if r.get("position_id") not in existing_pids]
        print(f"Resuming: {len(existing_pids)} already reviewed; {len(pending_recs)} pending.")
    else:
        pending_recs = all_recs

    # Apply filters
    if args.filter_confidence:
        pending_recs = [r for r in pending_recs if r.get("confidence") == args.filter_confidence]
        print(f"Applied confidence filter [{args.filter_confidence}]: {len(pending_recs)} matching.")

    if args.filter_label:
        norm_filter = normalize_label(args.filter_label)
        pending_recs = [r for r in pending_recs if r.get("recommended_label") == norm_filter]
        print(f"Applied label filter [{norm_filter}]: {len(pending_recs)} matching.")

    if args.limit:
        pending_recs = pending_recs[: args.limit]
        print(f"Applied limit: reviewing {len(pending_recs)} positions.")

    if not pending_recs:
        print("No pending recommendations to review.")
        sys.exit(0)

    counts = {"APPROVE": 0, "OVERRIDE": 0, "DEFER": 0, "REJECT": 0}

    # BATCH APPROVAL SHORTCUTS
    if args.batch_approve_all or args.auto_approve_high_confidence:
        print(f"\nProcessing in batch mode for {len(pending_recs)} recommendations...")
        for r in pending_recs:
            pid = r.get("position_id")
            conf = r.get("confidence", "MEDIUM")
            if args.auto_approve_high_confidence and conf != "HIGH":
                continue

            rec_lbl = r.get("recommended_label")
            rec_grd = r.get("recommended_grade")
            rec_rat = r.get("recommended_rationale") or "Human confirmed recommendation."
            rec_span = r.get("recommended_evidence_span", "")

            record_decision(
                output_path=output_path,
                rec=r,
                action="APPROVE",
                researcher_id=args.researcher_id,
                final_label=rec_lbl,
                final_grade=rec_grd,
                final_rationale=f"Human confirmed: {rec_rat}",
                final_span=rec_span,
                provenance=PROVENANCE_AI_ASSISTED_CONFIRMED,
                human_confirmation=True,
            )
            counts["APPROVE"] += 1
            print(f"✓ Approved {pid} [{rec_lbl} | {conf}]")

        print(f"\nBatch processing complete. Total Approved: {counts['APPROVE']}")
        print(f"Saved decisions to: {output_path}")
        return

    # INTERACTIVE REVIEW LOOP
    total_review = len(pending_recs)
    print(f"\nStarting interactive researcher review of {total_review} recommendations.")
    print("Commands: [A]pprove | [O]verride | [D]efer | [R]eject | [V]iew full evidence | [Q]uit & Save")

    try:
        for idx, rec in enumerate(pending_recs, 1):
            pid = rec.get("position_id")
            rec_lbl = rec.get("recommended_label")
            rec_grd = rec.get("recommended_grade")
            rec_rat = rec.get("recommended_rationale") or ""
            rec_span = rec.get("recommended_evidence_span", "")

            while True:
                display_recommendation_card(rec, idx, total_review)
                choice = input("\nAction: [A]pprove / [O]verride / [D]efer / [R]eject / [V]iew full / [Q]uit? ").strip().upper()

                if choice in {"A", "APPROVE"}:
                    record_decision(
                        output_path=output_path,
                        rec=rec,
                        action="APPROVE",
                        researcher_id=args.researcher_id,
                        final_label=rec_lbl,
                        final_grade=rec_grd,
                        final_rationale=f"Human confirmed: {rec_rat}",
                        final_span=rec_span,
                        provenance=PROVENANCE_AI_ASSISTED_CONFIRMED,
                        human_confirmation=True,
                    )
                    counts["APPROVE"] += 1
                    print(f"✓ [APPROVED] {pid} -> {rec_lbl}")
                    break

                elif choice in {"O", "OVERRIDE"}:
                    ov_lbl, ov_grd, ov_rat, ov_span = prompt_for_override(rec)
                    record_decision(
                        output_path=output_path,
                        rec=rec,
                        action="OVERRIDE",
                        researcher_id=args.researcher_id,
                        final_label=ov_lbl,
                        final_grade=ov_grd,
                        final_rationale=ov_rat,
                        final_span=ov_span,
                        provenance=PROVENANCE_AI_ASSISTED_OVERRIDDEN,
                        human_confirmation=True,
                    )
                    counts["OVERRIDE"] += 1
                    print(f"✓ [OVERRIDDEN] {pid} -> {ov_lbl}")
                    break

                elif choice in {"D", "DEFER"}:
                    record_decision(
                        output_path=output_path,
                        rec=rec,
                        action="DEFER",
                        researcher_id=args.researcher_id,
                        final_label=None,
                        final_grade=None,
                        final_rationale="Deferred for secondary panel adjudication",
                        final_span="",
                        provenance=PROVENANCE_DEFERRED,
                        human_confirmation=False,
                    )
                    counts["DEFER"] += 1
                    print(f"✓ [DEFERRED] {pid}")
                    break

                elif choice in {"R", "REJECT"}:
                    record_decision(
                        output_path=output_path,
                        rec=rec,
                        action="REJECT",
                        researcher_id=args.researcher_id,
                        final_label=None,
                        final_grade=None,
                        final_rationale="AI recommendation rejected by researcher",
                        final_span="",
                        provenance=PROVENANCE_REJECTED,
                        human_confirmation=False,
                    )
                    counts["REJECT"] += 1
                    print(f"✓ [REJECTED] {pid}")
                    break

                elif choice in {"V", "VIEW"}:
                    print("\n--- FULL RETRIEVED EVIDENCE ---")
                    print(rec.get("retrieved_evidence", ""))
                    print("-" * 80)
                    continue

                elif choice in {"Q", "QUIT"}:
                    print("\nExiting session. Progress has been saved.")
                    return

                else:
                    print("Invalid input. Please choose A, O, D, R, V, or Q.")

    except KeyboardInterrupt:
        print("\n\nSession interrupted by researcher. All prior decisions saved safely.")

    finally:
        total_session = sum(counts.values())
        print("\n=================================================================")
        print("                  Review Session Summary                         ")
        print("=================================================================")
        print(f"Total Reviewed This Session : {total_session}")
        print(f"  - Approved                : {counts['APPROVE']}")
        print(f"  - Overridden              : {counts['OVERRIDE']}")
        print(f"  - Deferred                : {counts['DEFER']}")
        print(f"  - Rejected                : {counts['REJECT']}")
        print(f"Decisions saved to: {output_path}")


if __name__ == "__main__":
    main()
