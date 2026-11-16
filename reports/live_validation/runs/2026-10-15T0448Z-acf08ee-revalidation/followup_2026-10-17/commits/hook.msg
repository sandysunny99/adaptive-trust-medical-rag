fix(ci): run the secret-scan hook's gitleaks step with flags gitleaks 8.30 accepts

The CI write hook passed --quiet to gitleaks detect. gitleaks 8.30 rejects it (exit 126),
and the hook read any non-zero exit as a found secret, so it denied every file. It now
passes --no-banner --log-level error --redact --exit-code 1. Exit 1 is a found secret; any
other non-zero exit is reported as a scan that could not run, and still blocks.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
