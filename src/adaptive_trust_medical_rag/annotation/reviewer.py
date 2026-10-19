"""Researcher review interface and reporting for AI-assisted annotations.

Provides formatted markdown reports with structured decision checkboxes
and batch summary statistics.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adaptive_trust_medical_rag.annotation.schemas import (
    AIRecommendation,
    AnnotationPosition,
    RelevanceLabel,
)


def format_position_for_review(
    position: AnnotationPosition,
    recommendation: AIRecommendation,
    evidence_snippet_length: int = 350,
) -> str:
    """Format a single position + AI recommendation for researcher review in Markdown.

    Args:
        position: AnnotationPosition metadata and evidence text.
        recommendation: 21-field AIRecommendation from LLM adjudication.
        evidence_snippet_length: Maximum characters of evidence snippet to show.

    Returns:
        Formatted markdown string with review checkboxes.
    """
    evidence_text = position.retrieved_evidence
    if len(evidence_text) > evidence_snippet_length:
        evidence_snippet = f"{evidence_text[:evidence_snippet_length]}..."
    else:
        evidence_snippet = evidence_text

    span_str = (
        f'`"{recommendation.best_supporting_span}"`'
        if recommendation.best_supporting_span
        else "*None (Empty)*"
    )

    claims_block = ""
    if recommendation.evidence_claims:
        claim_lines = [
            f'- [{c.claim_type.value} | {c.polarity.value}] {c.claim_text} *(Span: "{c.evidence_span[:50]}...")*'
            if len(c.evidence_span) > 50
            else f'- [{c.claim_type.value} | {c.polarity.value}] {c.claim_text} *(Span: "{c.evidence_span}")*'
            for c in recommendation.evidence_claims[:5]
        ]
        claims_block = "\n**Extracted Claims**:\n" + "\n".join(claim_lines) + "\n"

    alt_str = (
        recommendation.alternative_label_considered.value
        if recommendation.alternative_label_considered
        else "None"
    )

    return f"""### Position: `{position.position_id}`
- **Chunk ID**: `{position.chunk_id}` | **Document ID**: `{position.document_id}`
- **Query**: {position.query_text}

**Retrieved Evidence**:
> {evidence_snippet}

**AI Recommendation**:
- **Proposed Label**: **{recommendation.proposed_label.value}** (Grade: `{recommendation.proposed_grade}`)
- **Confidence**: `{recommendation.confidence.value}` | **Alternative Considered**: `{alt_str}`
- **Alignments**: Entity: `{recommendation.entity_alignment.value}`, Relation: `{recommendation.relationship_alignment.value}`, Outcome: `{recommendation.outcome_alignment.value}`
- **Supporting Span**: {span_str}
- **Proposed Rationale**: {recommendation.proposed_rationale}
{claims_block}
**Researcher Decision**:
- [ ] **APPROVE** (Accept {recommendation.proposed_label.value}, Grade {recommendation.proposed_grade})
- [ ] **OVERRIDE**: [ ] RELEVANT (2)  [ ] PARTIALLY_RELEVANT (1)  [ ] IRRELEVANT (0)  [ ] INSUFFICIENT (0)  [ ] AMBIGUOUS (null)
- [ ] **DEFER** (Secondary Adjudication)
- [ ] **REJECT**
- **Researcher Rationale**: __________________________________________________
- **Reviewer ID**: ____________  **Date**: ____________

---
"""


def generate_summary_statistics(recommendations: list[AIRecommendation]) -> dict[str, Any]:
    """Generate statistical summary of AI recommendations.

    Calculates label distribution, confidence distribution, and alignment metrics.

    Args:
        recommendations: List of AIRecommendation objects.

    Returns:
        Dictionary containing counts and percentages for all key metrics.
    """
    total = len(recommendations)
    if total == 0:
        return {
            "total_count": 0,
            "label_distribution": {},
            "grade_distribution": {},
            "confidence_distribution": {},
            "entity_alignment_distribution": {},
            "relationship_alignment_distribution": {},
            "outcome_alignment_distribution": {},
            "spans_present_count": 0,
            "claims_total_count": 0,
        }

    label_counts = Counter(r.proposed_label.value for r in recommendations)
    grade_counts = Counter(str(r.proposed_grade) for r in recommendations)
    conf_counts = Counter(r.confidence.value for r in recommendations)
    ent_counts = Counter(r.entity_alignment.value for r in recommendations)
    rel_counts = Counter(r.relationship_alignment.value for r in recommendations)
    out_counts = Counter(r.outcome_alignment.value for r in recommendations)

    spans_present = sum(1 for r in recommendations if bool(r.best_supporting_span.strip()))
    total_claims = sum(len(r.evidence_claims) for r in recommendations)

    return {
        "total_count": total,
        "label_distribution": {
            lbl: {"count": count, "pct": round(count / total * 100, 2)}
            for lbl, count in label_counts.items()
        },
        "grade_distribution": dict(grade_counts),
        "confidence_distribution": {
            conf: {"count": count, "pct": round(count / total * 100, 2)}
            for conf, count in conf_counts.items()
        },
        "entity_alignment_distribution": {
            align: {"count": count, "pct": round(count / total * 100, 2)}
            for align, count in ent_counts.items()
        },
        "relationship_alignment_distribution": {
            align: {"count": count, "pct": round(count / total * 100, 2)}
            for align, count in rel_counts.items()
        },
        "outcome_alignment_distribution": {
            align: {"count": count, "pct": round(count / total * 100, 2)}
            for align, count in out_counts.items()
        },
        "spans_present_count": spans_present,
        "claims_total_count": total_claims,
    }


def generate_batch_review_report(
    batch: list[tuple[AnnotationPosition, AIRecommendation]],
    output_path: Path | str,
) -> None:
    """Generate a comprehensive Markdown report of all AI recommendations for researcher review.

    Groups records by query and formats each with decision checkboxes.

    Args:
        batch: List of (AnnotationPosition, AIRecommendation) tuples.
        output_path: Destination path for the Markdown report.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    recommendations = [rec for _, rec in batch]
    stats = generate_summary_statistics(recommendations)

    # Group pairs by query text
    grouped: dict[str, list[tuple[AnnotationPosition, AIRecommendation]]] = {}
    for pos, rec in batch:
        grouped.setdefault(pos.query_text, []).append((pos, rec))

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build Header and Summary Table
    md_lines = [
        "# Track A Medical Evidence Relevance Review Report",
        f"*Generated at: {timestamp}*",
        f"*Total Positions in Batch: {len(batch)}*",
        "",
        "## Batch Summary Statistics",
        "",
        "### Label Distribution",
        "| Label | Count | Percentage |",
        "| :--- | :--- | :--- |",
    ]

    for lbl in [lbl.value for lbl in RelevanceLabel]:
        lbl_info = stats["label_distribution"].get(lbl, {"count": 0, "pct": 0.0})
        md_lines.append(f"| `{lbl}` | {lbl_info['count']} | {lbl_info['pct']}% |")

    md_lines.extend(
        [
            "",
            "### Confidence Distribution",
            "| Confidence | Count | Percentage |",
            "| :--- | :--- | :--- |",
        ]
    )
    for conf, data in stats["confidence_distribution"].items():
        md_lines.append(f"| `{conf}` | {data['count']} | {data['pct']}% |")

    md_lines.extend(
        [
            "",
            "### Entity Alignment Distribution",
            "| Alignment | Count | Percentage |",
            "| :--- | :--- | :--- |",
        ]
    )
    for align, data in stats["entity_alignment_distribution"].items():
        md_lines.append(f"| `{align}` | {data['count']} | {data['pct']}% |")

    md_lines.extend(
        [
            "",
            f"- **Best Supporting Spans Present**: {stats['spans_present_count']} / {stats['total_count']}",
            f"- **Total Evidence Claims Extracted**: {stats['claims_total_count']}",
            "",
            "---",
            "",
            "## Evidence Adjudication Review",
            "",
        ]
    )

    # Append grouped queries
    for query_text, items in grouped.items():
        md_lines.append(f"## Query: {query_text} ({len(items)} positions)\n")
        for pos, rec in items:
            md_lines.append(format_position_for_review(pos, rec))

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
