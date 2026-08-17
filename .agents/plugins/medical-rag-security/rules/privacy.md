---
name: privacy-rules
description: Privacy protection and HIPAA-alignment rules preventing PHI leakage and ensuring synthetic data isolation.
trigger: always_on
---

# Privacy & Data Governance Rules

## 1. Zero PHI Policy
- Under no circumstances should real patient records, Protected Health Information (PHI), or identifiable personal health data be processed, stored, or committed to this repository.
- All testing, benchmarking, and example queries must use strictly synthetic or fully anonymized public datasets.

## 2. PII / PHI Detection & Scrubbing
- Any input text containing patterns resembling names, social security numbers, medical record numbers (MRNs), phone numbers, or dates of birth linked to identities must be sanitized and rejected or scrubbed immediately.

## 3. Telemetry & Log Sanitization
- Audit logs and experiment traces must only record query hashes, normalized entity CUIs, document IDs, trust scores, and model metadata—never raw unredacted personal identifiers.
