feat(annotation): add the Track A AI-assisted annotation package, scripts and tests

Adds the researcher's AI-assisted annotation work: the annotation package (schemas, loader,
engine, reviewer, commit), its CLI scripts and its tests. The generated dry-run session record
(track_a_annotation/ai_assisted/SESSION_CONFIG_V1.json) is not included.

Bandit B110 in the engine: a failed HuggingFace/FreeLLMAPI adapter initialization was swallowed
silently. It is now logged with the provider and exception type only (never the message, which
can carry a key or URL); the method still returns no backend, so annotation still fails safely
with the missing-credentials error. tests/test_annotation_engine_backend_init.py covers success,
a failed initialization and the safe failure.

Three engine tests still fail on Windows checkouts with a prompt-hash mismatch; the next commit
fixes how the prompt bytes are hashed.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
