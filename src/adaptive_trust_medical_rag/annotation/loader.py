"""Data loading and persistence for Track A annotation workflows.

Guarantees strict separation between human annotations and AI-assisted records.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adaptive_trust_medical_rag.annotation.schemas import (
    AIRecommendation,
    AnnotationPosition,
    ResearcherDecision,
)


def load_annotator_file(path: Path | str) -> list[AnnotationPosition]:
    """Load a JSONL annotator workspace or dataset file.

    Args:
        path: Path to the JSONL file.

    Returns:
        List of AnnotationPosition instances.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Annotator file not found: {path_obj}")

    positions: list[AnnotationPosition] = []
    with open(path_obj, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                pos = AnnotationPosition.model_validate(data)
                positions.append(pos)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse AnnotationPosition at {path_obj}:{line_no}: {e}"
                ) from e

    return positions


def load_unannotated(path: Path | str) -> list[AnnotationPosition]:
    """Load only UNANNOTATED positions from an annotator file.

    Args:
        path: Path to the JSONL file.

    Returns:
        List of UNANNOTATED AnnotationPosition instances.
    """
    all_positions = load_annotator_file(path)
    return [pos for pos in all_positions if pos.annotation_status == "UNANNOTATED"]


def _assert_not_human_annotation_file(output_path: Path) -> None:
    """Safeguard: Never overwrite human annotator files with AI recommendations."""
    path_str = str(output_path.resolve()).replace("\\", "/").lower()
    protected_patterns = [
        "annotator_a/track_a_annotator_a.jsonl",
        "human_annotations",
        "frozen_annotations",
    ]
    for pattern in protected_patterns:
        if pattern in path_str:
            raise PermissionError(
                f"Destructive write rejected: Cannot write AI recommendations to human file: {output_path}. "
                "AI recommendations must be saved to a separate recommendations file."
            )


def save_ai_recommendations(
    recommendations: list[tuple[AnnotationPosition, AIRecommendation]],
    output_path: Path | str,
    provenance_tag: str = "AI_ASSISTED_V1",
) -> None:
    """Save AI recommendations to a separate JSONL file.

    Guarantees non-destructive output and enforces AI provenance tagging.

    Args:
        recommendations: Pairs of (AnnotationPosition, AIRecommendation).
        output_path: Target JSONL path.
        provenance_tag: Provenance tag indicating AI assistance version.
    """
    out_file = Path(output_path)
    _assert_not_human_annotation_file(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        for pos, rec in recommendations:
            record: dict[str, Any] = {
                "position_id": pos.position_id,
                "query_id": pos.query_id,
                "query_text": pos.query_text,
                "chunk_id": pos.chunk_id,
                "document_id": pos.document_id,
                "retrieved_evidence": pos.retrieved_evidence,
                "abstract_available": pos.abstract_available,
                "abstract_enrichment_status": pos.abstract_enrichment_status,
                "provenance": provenance_tag,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "recommendation": rec.model_dump(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_researcher_decisions(
    decisions: list[ResearcherDecision],
    output_path: Path | str,
) -> None:
    """Save researcher-reviewed decisions to a JSONL file.

    Args:
        decisions: List of ResearcherDecision instances.
        output_path: Destination path for decisions file.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        for decision in decisions:
            f.write(json.dumps(decision.model_dump(), ensure_ascii=False) + "\n")
