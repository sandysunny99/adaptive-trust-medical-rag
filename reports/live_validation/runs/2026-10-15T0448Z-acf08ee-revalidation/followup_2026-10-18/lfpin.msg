fix: pin the LF-hashed Phase 2f5 runner so its frozen hash reproduces on Windows

tests/test_frozen_hash_reproducibility.py records runner_real_hardened.py as its LF bytes
(774c9d65...). The file had no line-ending rule, so a Windows checkout with core.autocrlf=true
wrote CRLF and the test failed there (it passes on LF checkouts). Pin it text eol=lf, like the
REAL_LLM prompt. No file or recorded hash changes.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
