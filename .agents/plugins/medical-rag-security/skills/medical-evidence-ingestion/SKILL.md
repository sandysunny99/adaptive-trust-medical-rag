---
name: medical-evidence-ingestion
description: Guidelines and procedures for ingesting medical literature, FDA drug labels, and pharmacology sources with SHA-256 validation and quarantine checks.
---

# Medical Evidence Ingestion Skill

This skill defines the data ingestion pipeline ensuring data integrity, provenance tracking, and poisoning defense.

## Ingestion Workflow

1. **Document Fetching:** Acquire raw documents from approved medical repositories (FDA DailyMed, PubMed Central Open Access, DailyMed XML/SPL, EMA).
2. **SHA-256 Checksum Calculation:** Compute immutable SHA-256 hash immediately upon byte acquisition.
3. **Quarantine Staging:** Place incoming raw text/XML in quarantined status in the database (`validation_status = 'quarantined'`).
4. **Sanitization & Poisoning Inspection:**
   - Detect prompt injection markers, invisible characters, excessive unicode homoglyphs, or anomalous formatting.
   - Calculate `poisoning_score` (0.0 to 1.0). If `poisoning_score > 0.4`, retain in quarantine and flag for review.
5. **Entity Annotation & Chunking:**
   - Extract pharmacological entities (Drugs, Dosages, Conditions, ADEs).
   - Use semantic chunking preserving clinical paragraph boundaries.
6. **Provenance Recording:**
   - Record document metadata in `evidence_provenance`:
     - `provenance_id`, `document_id`, `source_id`, `source_url`, `content_hash`, `source_authority`, `validation_status`.
7. **Approval & Indexing:**
   - Upon successful automated validation, promote status to `'validated'` and trigger vector/graph indexing.
