"""AI-Assisted Medical Evidence Relevance Annotation Package.

Provides core pipeline components for Track A relevance evaluation:
- Strict Pydantic data schemas matching Schema V2 and adjudication contracts
- LLM adjudication engine with cryptographic prompt integrity verification
- Non-destructive dataset loading and persistence
- Researcher review report generation with decision workflows
- Atomic decision commitment with explicit AI provenance tagging
"""

from adaptive_trust_medical_rag.annotation.commit import (
    commit_researcher_decisions,
)
from adaptive_trust_medical_rag.annotation.engine import (
    AIAnnotationEngine,
    PromptHashMismatchError,
)
from adaptive_trust_medical_rag.annotation.loader import (
    load_annotator_file,
    load_unannotated,
    save_ai_recommendations,
    save_researcher_decisions,
)
from adaptive_trust_medical_rag.annotation.reviewer import (
    format_position_for_review,
    generate_batch_review_report,
    generate_summary_statistics,
)
from adaptive_trust_medical_rag.annotation.schemas import (
    LABEL_TO_GRADE_MAP,
    AIRecommendation,
    AlignmentType,
    AnnotationBatch,
    AnnotationPosition,
    AnnotationSessionConfig,
    AnnotationState,
    ClaimPolarity,
    ClaimType,
    ConfidenceLevel,
    EvidenceClaim,
    PolarityType,
    RelevanceLabel,
    ResearcherAction,
    ResearcherDecision,
)

__all__ = [
    "AIAnnotationEngine",
    "AIRecommendation",
    "AlignmentType",
    "AnnotationBatch",
    "AnnotationPosition",
    "AnnotationSessionConfig",
    "AnnotationState",
    "ClaimPolarity",
    "ClaimType",
    "ConfidenceLevel",
    "EvidenceClaim",
    "LABEL_TO_GRADE_MAP",
    "PolarityType",
    "PromptHashMismatchError",
    "RelevanceLabel",
    "ResearcherAction",
    "ResearcherDecision",
    "commit_researcher_decisions",
    "format_position_for_review",
    "generate_batch_review_report",
    "generate_summary_statistics",
    "load_annotator_file",
    "load_unannotated",
    "save_ai_recommendations",
    "save_researcher_decisions",
]
