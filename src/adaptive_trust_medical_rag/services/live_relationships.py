"""Approved drug-relationship records for the live application.

A record links two canonical medications (RxCUI) by a predicate and a severity, and names the
live-corpus chunk, content hash and verbatim evidence span it was taken from. Records are read
from a versioned file whose manifest must be APPROVED by a named person and whose SHA-256 must
match. A candidate, a hash mismatch or an invalid record is ignored, so nothing unapproved can
raise a risk tier or give a claim a relationship identity.

Records only ever raise the risk tier. They never create evidence: a pairwise claim still needs
an eligible chunk carrying the record's identity and passing claim verification.

A record with a symmetric predicate (a contraindicated combination, an interaction) may be
BIDIRECTIONAL: the relationship then holds in both drug orders, and a claim naming the two
drugs in the other order is checked against the record in that order. Directional predicates
(inhibition, induction, increases, ...) keep their recorded direction.

V1 records must cite a chunk of the frozen live corpus. V2 records may also cite a chunk of
their own versioned evidence file (for example exact label text captured from DailyMed), so a
source can be added without changing the frozen corpus. V2 has its own manifest, which must be
APPROVED by a named person and must match the SHA-256 of both the records file and the evidence
file. An evidence chunk becomes retrievable only when an accepted V2 record cites it, and it then
goes through the same provenance-hash, trust, eligibility and claim-verification gates as a
corpus chunk.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

from adaptive_trust_medical_rag.trust_scoring.trust_scorer import RISK_CLASSES, classify_query_risk
from adaptive_trust_medical_rag.verification.canonical_identity import (
    NORMALIZED_PREDICATES,
    CanonicalDirection,
    CanonicalRelationshipIdentity,
)

log = logging.getLogger(__name__)

RELATIONSHIP_DATASET = "LIVE_RELATIONSHIP_RECORDS_V1"
RELATIONSHIP_DATASET_V2 = "LIVE_RELATIONSHIP_RECORDS_V2"
RELATIONSHIP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "live_medical", "relationships"
)

SEVERITIES = frozenset({"CONTRAINDICATED", "MAJOR", "MODERATE", "MINOR", "NONE"})
SEVERE = frozenset({"CONTRAINDICATED", "MAJOR"})
_PREDICATES = frozenset(NORMALIZED_PREDICATES.values())
# "A is contraindicated with B" states the same thing as "B is contraindicated with A".
SYMMETRIC_PREDICATES = frozenset({"CONTRAINDICATION", "INTERACTION"})


@dataclass(frozen=True)
class RelationshipRecord:
    record_id: str
    subject_rxcui: str
    subject_name: str
    object_rxcui: str
    object_name: str
    predicate: str
    direction: CanonicalDirection
    severity: str
    source_chunk_id: str
    source_content_hash: str
    evidence_span: str

    def links(self, a: str, b: str) -> bool:
        return {self.subject_rxcui, self.object_rxcui} == {a, b}

    @property
    def symmetric(self) -> bool:
        return self.direction == CanonicalDirection.BIDIRECTIONAL and self.predicate in SYMMETRIC_PREDICATES

    def identity(self, claim_order: tuple[str, str] | None = None) -> CanonicalRelationshipIdentity:
        """The record's identity. For a symmetric record and a claim naming the same two drugs,
        the identity is given in the claim's order (first-named drug as subject, A_TO_B, the
        convention the claim side uses): the relationship holds that way round too. The
        predicate is never changed, and a directional record is always given as recorded."""
        if claim_order and self.symmetric and set(claim_order) == {self.subject_rxcui, self.object_rxcui}:
            subject, obj = claim_order
            return CanonicalRelationshipIdentity(
                subject_rxcui=subject,
                object_rxcui=obj,
                predicate=self.predicate,
                direction=CanonicalDirection.A_TO_B,
                provenance_chunk_id=self.source_chunk_id,
            )
        return CanonicalRelationshipIdentity(
            subject_rxcui=self.subject_rxcui,
            object_rxcui=self.object_rxcui,
            predicate=self.predicate,
            direction=self.direction,
            provenance_chunk_id=self.source_chunk_id,
        )


@dataclass(frozen=True)
class RelationshipStore:
    """The approved records, or none with the reason they were not loaded."""

    records: tuple[RelationshipRecord, ...] = ()
    status: str = "NOT_LOADED"
    reason: str = "no relationship dataset was loaded"
    rejected: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    # Approved V2 evidence chunks (corpus item schema) that an accepted V2 record cites.
    evidence: tuple[dict[str, Any], ...] = ()

    def between(self, rxcuis: list[str]) -> list[RelationshipRecord]:
        """Records linking any two different requested medications."""
        wanted = set(rxcuis)
        return [r for r in self.records
                if r.subject_rxcui in wanted and r.object_rxcui in wanted and r.subject_rxcui != r.object_rxcui]

    def identity_for_chunk(self, chunk_id: str, text: str, rxcuis: list[str],
                           claim_order: tuple[str, str] | None = None) -> CanonicalRelationshipIdentity | None:
        """The relationship identity an eligible chunk carries for this request, if exactly one applies.

        The record must name this chunk and its current content hash. Several records on the
        chunk, or records that disagree about whether the pair interacts at all, give no identity.
        ``claim_order`` is the (subject, object) RxCUI order of the claim being verified; only a
        symmetric record uses it.
        """
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        on_chunk = [r for r in self.between(rxcuis)
                    if r.source_chunk_id == chunk_id and r.source_content_hash == text_hash]
        if len(on_chunk) != 1:
            return None
        record = on_chunk[0]
        pair = self.between([record.subject_rxcui, record.object_rxcui])
        if record.severity == "NONE" or any(r.severity == "NONE" for r in pair):
            return None
        return record.identity(claim_order)


def _records_hash(raw: bytes) -> str:
    # Line endings are normalised so a Windows (CRLF) checkout hashes the same as Linux.
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _whole_word(name: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(name.lower())}\b", text.lower()) is not None


def validate_record(raw: dict[str, Any], chunks_by_id: dict[str, dict[str, Any]]) -> tuple[RelationshipRecord | None, str]:
    """A record is valid only if it is fully specified and grounded in a corpus chunk verbatim."""
    try:
        subject, obj = raw["subject"], raw["object"]
        record = RelationshipRecord(
            record_id=str(raw["record_id"]),
            subject_rxcui=str(subject["rxcui"]).strip(),
            subject_name=str(subject["name"]).strip(),
            object_rxcui=str(obj["rxcui"]).strip(),
            object_name=str(obj["name"]).strip(),
            predicate=str(raw["predicate"]),
            direction=CanonicalDirection(raw["direction"]),
            severity=str(raw["severity"]),
            source_chunk_id=str(raw["source_chunk_id"]),
            source_content_hash=str(raw["source_content_hash"]),
            evidence_span=str(raw["evidence_span"]),
        )
    except (KeyError, TypeError, ValueError) as e:
        return None, f"incomplete record ({type(e).__name__}: {e})"

    if not all([record.subject_rxcui, record.object_rxcui, record.subject_name, record.object_name]):
        return None, "unresolved medication identity"
    if record.subject_rxcui == record.object_rxcui:
        return None, "a record must link two different medications"
    if record.predicate not in _PREDICATES:
        return None, f"predicate {record.predicate} is not in the bounded predicate set"
    if record.direction == CanonicalDirection.UNKNOWN:
        return None, "direction is unknown"
    if record.direction == CanonicalDirection.BIDIRECTIONAL and record.predicate not in SYMMETRIC_PREDICATES:
        return None, f"predicate {record.predicate} is directional, so it cannot be BIDIRECTIONAL"
    if record.severity not in SEVERITIES:
        return None, f"severity {record.severity} is not one of {sorted(SEVERITIES)}"

    chunk = chunks_by_id.get(record.source_chunk_id)
    if chunk is None:
        return None, f"source chunk {record.source_chunk_id} is not in the live corpus"
    text = chunk.get("text", "")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != record.source_content_hash:
        return None, "source content hash does not match the corpus chunk"
    if record.evidence_span not in text:
        return None, "evidence span is not verbatim in the source chunk"
    if not (_whole_word(record.subject_name, record.evidence_span) and _whole_word(record.object_name, record.evidence_span)):
        return None, "evidence span does not name both medications"
    return record, "valid"


def load_relationship_store(corpus_items: list[dict[str, Any]], directory: str | None = None) -> RelationshipStore:
    """Load the approved V1 and V2 records; a dataset short of approved and hash-matching loads nothing.

    Without a V2 manifest the result is exactly the V1 store.
    """
    directory = RELATIONSHIP_DIR if directory is None else directory
    v1 = _load_v1(corpus_items, directory)
    v2 = _load_v2(corpus_items, directory)
    if v2 is None:
        return v1
    return RelationshipStore(
        records=v1.records + v2.records,
        status="APPROVED" if "APPROVED" in (v1.status, v2.status) else v1.status,
        reason=f"{v1.reason}; {v2.reason}",
        rejected=v1.rejected + v2.rejected,
        evidence=v2.evidence,
    )


def _load_v1(corpus_items: list[dict[str, Any]], directory: str) -> RelationshipStore:
    """Load the approved V1 records; anything short of an approved, hash-matching dataset loads nothing."""
    manifest_path = os.path.join(directory, f"{RELATIONSHIP_DATASET}_MANIFEST.json")
    if not os.path.exists(manifest_path):
        return RelationshipStore(status="MISSING", reason=f"{RELATIONSHIP_DATASET} manifest not found")
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        approval = manifest.get("approval") or {}
        status = str(manifest.get("status", "UNKNOWN"))
        if status != "APPROVED" or not approval.get("approved_by") or not approval.get("approved_at"):
            return RelationshipStore(status=status, reason=f"{RELATIONSHIP_DATASET} is {status}, not approved")

        records_path = os.path.join(directory, manifest["records_file"])
        with open(records_path, "rb") as f:
            raw = f.read()
        if _records_hash(raw) != manifest.get("records_sha256"):
            return RelationshipStore(status="HASH_MISMATCH", reason="records file does not match the manifest SHA-256")
        dataset = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as e:
        return RelationshipStore(status="UNREADABLE", reason=f"{RELATIONSHIP_DATASET} could not be read ({type(e).__name__})")

    chunks_by_id = {item.get("chunk_id"): item for item in corpus_items}
    accepted, rejected = [], []
    for raw_record in dataset.get("records", []):
        record, why = validate_record(raw_record, chunks_by_id)
        if record is None:
            rejected.append((str(raw_record.get("record_id", "?")), why))
            log.warning("Relationship record %s rejected: %s", raw_record.get("record_id", "?"), why)
        else:
            accepted.append(record)
    return RelationshipStore(records=tuple(accepted), status="APPROVED",
                             reason=f"{len(accepted)} approved record(s) loaded", rejected=tuple(rejected))


def validate_evidence_chunk(item: Any, frozen_ids: set[Any], embedding_dims: set[int]) -> str:
    """'valid', or why a V2 evidence chunk cannot be used. It must be complete, keep its own
    content hash, never replace a frozen corpus chunk, carry an https source URL and an embedding
    of the corpus's dimension."""
    if not isinstance(item, dict):
        return "evidence chunk is not an object"
    missing = [k for k in ("chunk_id", "document_id", "document_url", "source_type", "text", "content_hash",
                           "authority", "freshness", "embedding", "provenance") if item.get(k) in (None, "")]
    if missing:
        return f"evidence chunk is missing {', '.join(missing)}"
    if item["chunk_id"] in frozen_ids:
        return "evidence chunk id is already a frozen corpus chunk"
    text = item["text"]
    if not isinstance(text, str) or hashlib.sha256(text.encode("utf-8")).hexdigest() != item["content_hash"]:
        return "evidence chunk content hash does not match its text"
    prov = item["provenance"]
    if not isinstance(prov, dict) or not prov.get("source") or prov.get("content_hash") != item["content_hash"]:
        return "evidence chunk provenance must name its source and carry its content hash"
    if not str(item["document_url"]).lower().startswith("https://"):
        return "evidence chunk source URL is not https"
    if not all(isinstance(item[k], (int, float)) and 0.0 <= item[k] <= 1.0 for k in ("authority", "freshness")):
        return "evidence chunk authority and freshness must be numbers in [0, 1]"
    emb = item["embedding"]
    if not isinstance(emb, list) or not all(isinstance(x, (int, float)) for x in emb) or (
            embedding_dims and {len(emb)} != embedding_dims):
        return "evidence chunk embedding does not match the corpus embedding dimension"
    return "valid"


def _load_v2(corpus_items: list[dict[str, Any]], directory: str) -> RelationshipStore | None:
    """Load approved V2 records and the evidence chunks they cite; None when no V2 manifest exists."""
    name = RELATIONSHIP_DATASET_V2
    manifest_path = os.path.join(directory, f"{name}_MANIFEST.json")
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        approval = manifest.get("approval") or {}
        status = str(manifest.get("status", "UNKNOWN"))
        if status != "APPROVED" or not approval.get("approved_by") or not approval.get("approved_at"):
            return RelationshipStore(status=status, reason=f"{name} is {status}, not approved")
        with open(os.path.join(directory, manifest["records_file"]), "rb") as f:
            records_raw = f.read()
        with open(os.path.join(directory, manifest["evidence_file"]), "rb") as f:
            evidence_raw = f.read()
        if _records_hash(records_raw) != manifest.get("records_sha256"):
            return RelationshipStore(status="HASH_MISMATCH", reason=f"{name} records file does not match the manifest SHA-256")
        if _records_hash(evidence_raw) != manifest.get("evidence_sha256"):
            return RelationshipStore(status="HASH_MISMATCH", reason=f"{name} evidence file does not match the manifest SHA-256")
        dataset = json.loads(records_raw.decode("utf-8"))
        evidence_items = json.loads(evidence_raw.decode("utf-8"))
        if not isinstance(evidence_items, list):
            raise ValueError("evidence file is not a list")
    except (OSError, ValueError, KeyError, TypeError) as e:
        return RelationshipStore(status="UNREADABLE", reason=f"{name} could not be read ({type(e).__name__})")

    frozen_ids = {item.get("chunk_id") for item in corpus_items}
    dims = {len(item["embedding"]) for item in corpus_items if isinstance(item.get("embedding"), list)}
    evidence, rejected = {}, []
    for item in evidence_items:
        why = validate_evidence_chunk(item, frozen_ids, dims)
        chunk_id = item.get("chunk_id", "?") if isinstance(item, dict) else "?"
        if why != "valid" or chunk_id in evidence:
            why = why if why != "valid" else "duplicate evidence chunk id"
            rejected.append((f"evidence {chunk_id}", why))
            log.warning("%s evidence chunk %s rejected: %s", name, chunk_id, why)
        else:
            evidence[chunk_id] = item

    chunks_by_id = {item.get("chunk_id"): item for item in corpus_items} | evidence
    accepted = []
    for raw_record in dataset.get("records", []):
        record, why = validate_record(raw_record, chunks_by_id)
        if record is None:
            rejected.append((str(raw_record.get("record_id", "?")), why))
            log.warning("Relationship record %s rejected: %s", raw_record.get("record_id", "?"), why)
        else:
            accepted.append(record)
    cited = {r.source_chunk_id for r in accepted}
    usable = tuple(item for chunk_id, item in evidence.items() if chunk_id in cited)
    return RelationshipStore(records=tuple(accepted), status="APPROVED",
                             reason=f"{name}: {len(accepted)} approved record(s), {len(usable)} evidence chunk(s) loaded",
                             rejected=tuple(rejected), evidence=usable)


def aligned_medications(text: str, medications: list[dict[str, Any]]) -> list[str]:
    """Canonical names of the requested medications that the chunk names as whole words.

    The live corpus carries no per-chunk RxCUI metadata, so the RxNorm canonical name in the
    chunk text is the entity mapping available. A chunk that names none of them is unrelated.
    """
    names = {(m.get("canonical_name") or m["raw_text"]).lower() for m in medications}
    return sorted(n for n in names if _whole_word(n, text))


def live_risk_tier(medications: list[dict[str, Any]], store: RelationshipStore | None) -> tuple[str, str]:
    """The risk tier for a live analysis and the basis for it.

    Two or more medications are analysed for their interactions, so that question, not the bare
    names, goes through the keyword classifier ("drug interaction" is R2). An approved record of
    a contraindicated or major interaction between two of them raises the tier to R3. Nothing
    lowers a tier, and no interaction is inferred from the names alone.
    """
    names = [(m.get("canonical_name") or m["raw_text"]) for m in medications]
    rxcuis = [str(m["rxcui"]) for m in medications if m.get("rxcui")]
    if len(medications) >= 2:
        tier = classify_query_risk("drug interaction between " + " and ".join(names))
        basis = "a multi-drug interaction question with no approved severe relationship record"
    else:
        tier = classify_query_risk(" ".join(names))
        basis = "keyword classification of the medication name"

    records = (store or RelationshipStore()).between(rxcuis)
    severe = [r for r in records if r.severity in SEVERE]
    if severe and RISK_CLASSES.index(tier) < RISK_CLASSES.index("R3"):
        tier = "R3"
    if severe:
        record = severe[0]
        basis = (f"approved relationship record {record.record_id}: {record.subject_name} and "
                 f"{record.object_name} {record.severity.lower()} (source {record.source_chunk_id})")
        if any(r.severity == "NONE" for r in records):
            basis += "; another approved record says no interaction, so the higher tier is kept"
    return tier, basis
