fix: make frozen artifact hashes reproduce on LF checkouts

Ported from d8e44c3 on claude/continue-blockers (BLK-010; the Cognee adapter changes in that
commit are not included). The root .gitattributes was UTF-16, which git cannot read, so none
of its rules applied. It is now UTF-8 and pins the 310 tracked files whose recorded SHA-256
only matches their CRLF form to eol=crlf, as on claude/continue-blockers. No artifact or
recorded hash is edited. scripts/audit_frozen_hash_line_endings.py regenerates and --checks the
list; tests/test_frozen_hash_reproducibility.py checks key frozen hashes and runs the audit.

experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt is recorded as its LF bytes. It is
pinned 'text eol=lf' rather than '-text': both give LF on a fresh checkout, but '-text' would
mark an existing CRLF working copy of it as modified. The Track A prompt pins move from the
folder .gitattributes into the root file.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
