# V3.1 Candidate Discovery Report

## Overview
This diagnostic pass surfaces evidence candidates based strictly on keyword, synonym, and biomedical concept matching within the frozen corpus. It does NOT generate final human relevance labels and does NOT use retrieval ranking models (F0/F3/MedCPT are locked).

## Discovery Counts per Case
| Case | Candidate Count | Title-Only Limited |
|------|-----------------|--------------------|
| v3.1h-001 | 14 | 2 |
| v3.1h-002 | 9 | 4 |
| v3.1h-021 | 11 | 4 |
| v3.1h-022 | 7 | 2 |
| v3.1h-023 | 7 | 2 |
| v3.1h-046 | 12 | 3 |
| v3.1h-047 | 8 | 0 |
| v3.1h-066 | 15 | 4 |
| v3.1h-067 | 4 | 0 |
| v3.1h-069 | 3 | 0 |

## Limitations
This list provides a starting point for human annotation but is not exhaustive. The human reviewer retains access to the full frozen corpus to identify missing evidence and must independently verify the actual textual support for each surfaced candidate.