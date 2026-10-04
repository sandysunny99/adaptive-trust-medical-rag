# MANIFEST_HASH_CANONICALIZATION_V1

## Overview
This document formally defines the canonical hashing convention for the evidence manifest to prevent self-hashing inconsistencies.

## Canonical Hashing Rule
1. Load `data/evidence/manifest.json`.
2. Extract the `manifest_sha256` value (if present) and set the `manifest_sha256` key to `null`.
3. Serialize the dictionary to a JSON string using:
   - `separators=(',', ':')`
   - `sort_keys=True`
4. Compute the SHA-256 hash of the UTF-8 encoded serialized string.
5. Store the resulting hash as the new `manifest_sha256` value.
6. To verify, repeat steps 1-4 and compare the result against the stored `manifest_sha256` value.
