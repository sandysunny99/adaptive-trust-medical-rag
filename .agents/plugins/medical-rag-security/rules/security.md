---
name: security-rules
description: Security guidelines and defense against prompt injection, poisoned documents, and secret leakage.
trigger: always_on
---

# Security & Threat Model Rules

## 1. Input Sanitization & Indirect Injection Defense
- Every incoming user query and retrieved document chunk must undergo deterministic regex and semantic sanitization.
- Prompt injection markers (e.g., `Ignore previous instructions`, `SYSTEM PROMPT:`, `[INST]`, `<|im_start|>`, `<script>`) must be escaped or stripped.
- Injected documents must never alter the LLM system prompt framing or bypass safety gates.

## 2. Retrieval Poisoning & Provenance
- All evidence documents must have a computed SHA-256 content hash and recorded provenance metadata in `evidence_provenance`.
- Source validation status must be `validated` before documents enter vector or graph retrieval indices.
- Documents flagged with high anomaly or poisoning scores must be quarantined immediately.

## 3. Secret Management & Tool Execution Policy
- Never store API keys, connection strings, private keys, or passwords in source code, configuration files (unless loaded via env vars), or commit history.
- Run pre-commit secret scans on all staged changes.
- Terminal commands must adhere to strict least-privilege standards; destructive filesystem or database commands are prohibited.
