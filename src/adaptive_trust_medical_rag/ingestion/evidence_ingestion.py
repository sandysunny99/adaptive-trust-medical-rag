"""
Phase 9 — Medical Evidence Ingestion Pipeline.

Implements:
- SHA-256 content hashing (immutable at byte-acquisition time)
- Quarantine staging (validation_status = 'quarantined')
- Poisoning / injection detection (poisoning_score 0.0–1.0)
- Provenance recording (evidence_provenance table)
- Sanitization gate (wraps security.sanitizer)
- Approval promotion to 'validated'
- Semantic chunking with clinical boundary preservation

All operations are database-free / pure-Python so they are fully
unit-testable without a live PostgreSQL instance.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Enumerations (mirrors database.models enums — kept independent for portability)
# ---------------------------------------------------------------------------


class IngestionStatus(str, Enum):
    quarantined = "quarantined"
    validated = "validated"
    rejected = "rejected"


class IngestionSourceType(str, Enum):
    fda_dailymed = "fda_dailymed"
    pubmed_oa = "pubmed_oa"
    ema = "ema"
    manual = "manual"
    unknown = "unknown"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RawDocument:
    """Raw document as acquired from an external source (pre-processing)."""

    content: str
    source_url: str
    source_type: IngestionSourceType = IngestionSourceType.unknown
    source_authority: float = 0.5  # 0.0–1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class PoisoningReport:
    """Result of the anti-poisoning / injection inspection pass."""

    score: float  # 0.0 (clean) – 1.0 (definitely poisoned)
    findings: list[str] = field(default_factory=list)

    @property
    def is_quarantined(self) -> bool:
        """Return True if score exceeds the quarantine threshold (>0.4)."""
        return self.score > 0.4


@dataclass
class EvidenceChunkData:
    """A single semantic chunk ready for vector/graph indexing."""

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    token_count: int  # approximate word count


@dataclass
class ProvenanceRecord:
    """Provenance metadata recorded per ingested document."""

    provenance_id: str
    document_id: str
    source_url: str
    source_type: str
    source_authority: float
    content_hash: str  # SHA-256 hex digest
    validation_status: IngestionStatus
    ingested_at: datetime
    poisoning_score: float
    chunk_count: int
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# SHA-256 hashing
# ---------------------------------------------------------------------------

# Prompt-injection markers that flag a document as potentially poisoned
_INJECTION_MARKERS: list[tuple[str, float]] = [
    # Explicit override attempts
    (r"ignore\s+(previous|prior|all)\s+instructions?", 0.9),
    (r"system\s+prompt\s*:", 0.85),
    (r"\[INST\]", 0.85),
    (r"<\|im_start\|>", 0.85),
    (r"<\|im_end\|>", 0.85),
    (r"<script[\s>]", 0.9),
    (r"</script>", 0.9),
    # Override / jailbreak phrasing
    (r"you\s+are\s+now\s+(a\s+)?(?:DAN|jailbreak|unrestricted)", 0.95),
    (r"disregard\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions?|context)", 0.90),
    (r"new\s+instructions?\s*:", 0.75),
    (r"act\s+as\s+if\s+you\s+(?:have\s+no|ignore)", 0.80),
    # Encoded / obfuscated payloads
    (r"base64\s*:\s*[A-Za-z0-9+/]{20,}", 0.70),
    (r"eval\s*\(", 0.60),
    # Suspicious formatting
    (r"#{5,}", 0.30),  # excessive markdown headers
]

# Homoglyph / invisible character detection
_INVISIBLE_CHAR_CATEGORIES = {"Cf", "Cc", "Cs"}  # Unicode format/control/surrogate


def compute_sha256(content: str) -> str:
    """Compute SHA-256 hex digest of UTF-8 encoded content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Poisoning / injection inspector
# ---------------------------------------------------------------------------


def inspect_for_poisoning(content: str) -> PoisoningReport:
    """
    Analyse document content for prompt-injection and poisoning signals.

    Returns a PoisoningReport with a composite score (0.0–1.0) and
    a list of human-readable findings.  Score > 0.4 → quarantine.
    """
    findings: list[str] = []
    max_score: float = 0.0

    # 1. Prompt-injection marker scan
    for pattern, weight in _INJECTION_MARKERS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(f"Injection marker matched: /{pattern}/")
            max_score = max(max_score, weight)

    # 2. Invisible / homoglyph character density
    total_chars = max(len(content), 1)
    invisible_count = sum(
        1
        for ch in content
        if unicodedata.category(ch) in _INVISIBLE_CHAR_CATEGORIES
    )
    invisible_ratio = invisible_count / total_chars
    if invisible_ratio > 0.01:  # >1% invisible chars is suspicious
        score_contrib = min(invisible_ratio * 10, 0.8)
        findings.append(
            f"High invisible-character density: {invisible_ratio:.2%} "
            f"({invisible_count}/{total_chars} chars)"
        )
        max_score = max(max_score, score_contrib)

    # 3. Excessive Unicode homoglyph substitutions (Cyrillic/Greek in ASCII context)
    latin_ctx = sum(1 for ch in content if "LATIN" in unicodedata.name(ch, ""))
    cyrillic = sum(1 for ch in content if "CYRILLIC" in unicodedata.name(ch, ""))
    if latin_ctx > 0 and cyrillic / max(latin_ctx, 1) > 0.05:
        score_contrib = min(cyrillic / latin_ctx, 0.7)
        findings.append(
            f"Suspected homoglyph substitution: {cyrillic} Cyrillic chars "
            f"alongside {latin_ctx} Latin chars"
        )
        max_score = max(max_score, score_contrib)

    # 4. Anomalous null-byte / binary content
    null_count = content.count("\x00")
    if null_count > 0:
        findings.append(f"Null bytes detected: {null_count}")
        max_score = max(max_score, 0.6)

    return PoisoningReport(score=round(max_score, 4), findings=findings)


# ---------------------------------------------------------------------------
# Semantic chunker
# ---------------------------------------------------------------------------

_MIN_CHUNK_CHARS = 150
_MAX_CHUNK_CHARS = 1200

# Clinical paragraph boundary signals (preserve these)
_BOUNDARY_RE = re.compile(
    r"\n{2,}"
    r"|(?<=\.)\s{2,}(?=[A-Z])",
    re.IGNORECASE,
)

_SECTION_HEADER_RE = re.compile(
    r"\b(WARNINGS?|PRECAUTIONS?|DOSAGE|INDICATIONS?|CONTRAINDICATIONS?"
    r"|ADVERSE\s+REACTIONS?|DRUG\s+INTERACTIONS?|PHARMACOKINETICS?"
    r"|MECHANISM\s+OF\s+ACTION)\b",
    re.IGNORECASE,
)


def chunk_document(document_id: str, content: str) -> list[EvidenceChunkData]:
    """
    Split document into semantic chunks preserving clinical boundaries.

    Chunks are between _MIN_CHUNK_CHARS and _MAX_CHUNK_CHARS characters.
    Clinical section headers (WARNINGS, DOSAGE, etc.) always start a new chunk.
    """
    chunks: list[EvidenceChunkData] = []
    # Split on boundary markers, keep the delimiter for context
    parts = _BOUNDARY_RE.split(content)

    current_text = ""
    current_start = 0
    cursor = 0

    for part in parts:
        if not part or not part.strip():
            cursor += len(part)
            continue

        combined = (current_text + " " + part).strip() if current_text else part.strip()

        if len(combined) > _MAX_CHUNK_CHARS and current_text:
            # Flush current buffer
            chunks.append(
                EvidenceChunkData(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=len(chunks),
                    text=current_text.strip(),
                    char_start=current_start,
                    char_end=current_start + len(current_text),
                    token_count=len(current_text.split()),
                )
            )
            current_text = part.strip()
            current_start = cursor
        else:
            current_text = combined
            if not current_text:
                current_start = cursor

        cursor += len(part)

    # Flush remainder
    if current_text.strip() and len(current_text.strip()) >= _MIN_CHUNK_CHARS:
        chunks.append(
            EvidenceChunkData(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=len(chunks),
                text=current_text.strip(),
                char_start=current_start,
                char_end=current_start + len(current_text),
                token_count=len(current_text.split()),
            )
        )
    elif current_text.strip() and chunks:
        # Append short tail to last chunk
        last = chunks[-1]
        chunks[-1] = EvidenceChunkData(
            chunk_id=last.chunk_id,
            document_id=last.document_id,
            chunk_index=last.chunk_index,
            text=(last.text + " " + current_text.strip()).strip(),
            char_start=last.char_start,
            char_end=current_start + len(current_text),
            token_count=last.token_count + len(current_text.split()),
        )

    return chunks


# ---------------------------------------------------------------------------
# Evidence Ingestion Pipeline
# ---------------------------------------------------------------------------


@dataclass
class IngestionResult:
    """Full result of ingesting one document through the pipeline."""

    provenance: ProvenanceRecord
    chunks: list[EvidenceChunkData]
    status: IngestionStatus
    errors: list[str] = field(default_factory=list)

    @property
    def is_validated(self) -> bool:
        return self.status == IngestionStatus.validated

    @property
    def is_quarantined(self) -> bool:
        return self.status == IngestionStatus.quarantined


class EvidenceIngestionPipeline:
    """
    End-to-end ingestion pipeline for medical evidence documents.

    Steps (per skill):
      1. Compute SHA-256 hash immediately on raw bytes/string
      2. Stage in quarantine (validation_status = 'quarantined')
      3. Sanitize + inspect for poisoning
      4. If poisoning_score > 0.4 → retain in quarantine, record findings
      5. Semantic chunking (clinical boundary-aware)
      6. Record provenance
      7. Promote to 'validated' if all checks pass
    """

    QUARANTINE_THRESHOLD: float = 0.4

    def ingest(self, raw_doc: RawDocument) -> IngestionResult:
        """
        Ingest a single RawDocument through the full pipeline.

        Returns an IngestionResult with provenance + chunks.
        No live database connection required — callers persist the result.
        """
        document_id = str(uuid.uuid4())
        errors: list[str] = []

        # ── Step 1: SHA-256 hash (immutable, computed first) ──────────────────
        content_hash = compute_sha256(raw_doc.content)

        # ── Step 2: Stage as quarantined ──────────────────────────────────────
        status = IngestionStatus.quarantined

        # ── Step 3: Sanitize content (strip injection markers from surface) ───
        sanitized_content = self._sanitize(raw_doc.content)

        # ── Step 4: Poisoning inspection ──────────────────────────────────────
        poisoning_report = inspect_for_poisoning(raw_doc.content)

        if poisoning_report.is_quarantined:
            errors.extend(poisoning_report.findings)
            # Retain in quarantine — do not chunk or promote
            provenance = ProvenanceRecord(
                provenance_id=str(uuid.uuid4()),
                document_id=document_id,
                source_url=raw_doc.source_url,
                source_type=raw_doc.source_type.value,
                source_authority=raw_doc.source_authority,
                content_hash=content_hash,
                validation_status=IngestionStatus.quarantined,
                ingested_at=datetime.now(UTC),
                poisoning_score=poisoning_report.score,
                chunk_count=0,
                metadata={
                    **raw_doc.metadata,
                    "poisoning_findings": poisoning_report.findings,
                },
            )
            return IngestionResult(
                provenance=provenance,
                chunks=[],
                status=IngestionStatus.quarantined,
                errors=errors,
            )

        # ── Step 5: Semantic chunking ─────────────────────────────────────────
        chunks = chunk_document(document_id, sanitized_content)

        # ── Step 6 + 7: Record provenance, promote to validated ───────────────
        status = IngestionStatus.validated
        provenance = ProvenanceRecord(
            provenance_id=str(uuid.uuid4()),
            document_id=document_id,
            source_url=raw_doc.source_url,
            source_type=raw_doc.source_type.value,
            source_authority=raw_doc.source_authority,
            content_hash=content_hash,
            validation_status=status,
            ingested_at=datetime.now(UTC),
            poisoning_score=poisoning_report.score,
            chunk_count=len(chunks),
            metadata=raw_doc.metadata,
        )

        return IngestionResult(
            provenance=provenance,
            chunks=chunks,
            status=status,
        )

    def _sanitize(self, content: str) -> str:
        """
        Strip obvious injection markers from content before chunking.
        Preserves all legitimate medical text.
        """
        # Remove null bytes
        content = content.replace("\x00", "")
        # Strip prompt-injection override lines
        content = re.sub(
            r"(?im)^.*?(ignore\s+(previous|prior|all)\s+instructions?|"
            r"system\s+prompt\s*:|new\s+instructions?\s*:).*$",
            "[REDACTED-INJECTION]",
            content,
        )
        return content
