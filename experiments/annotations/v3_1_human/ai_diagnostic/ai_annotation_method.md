# AI Annotation Method (Diagnostic Only)

This track uses a simple diagnostic script to scan the 248-document corpus for 10 pilot cases.
It identifies potential candidates for `DIRECT_SUPPORT` and `PARTIAL_SUPPORT` based on explicit textual matches in the abstract/title.
It explicitly assigns `INSUFFICIENT_SOURCE_TEXT` when the corpus only provides a short string (e.g. title-only) preventing confident clinical judgment.

**WARNING:** This metadata records AI generation and MUST NOT be interpreted as human provenance.
