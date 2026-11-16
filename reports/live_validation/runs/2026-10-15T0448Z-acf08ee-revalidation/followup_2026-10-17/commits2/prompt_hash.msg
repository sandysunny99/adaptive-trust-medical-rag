fix(annotation): verify frozen Track A prompts against their raw bytes

TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json was recorded by gen_final_v14.py, which hashes each
prompt file opened with "rb" on a Windows checkout, so the adjudication prompt's recorded hash is
of its CRLF bytes. The engine hashed the text it had read in text mode (CRLF turned into LF) and
rejected the genuine frozen file. It now hashes the raw bytes; the recorded hashes are unchanged.
An LF copy of a CRLF-frozen prompt is a different file and still fails closed.

track_a_annotation/decision_batches/.gitattributes pins the three V2 prompts (adjudication
eol=crlf, system and challenge eol=lf, as on claude/continue-blockers) so every checkout
reproduces the recorded bytes. The root .gitattributes is UTF-16, which git cannot read, so the
pin lives in the folder.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
