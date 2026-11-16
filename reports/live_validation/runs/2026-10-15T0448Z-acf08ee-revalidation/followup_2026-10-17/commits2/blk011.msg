fix(cli): stop test and simulation runs overwriting committed run evidence

Ported from e41cae2 on claude/continue-blockers. research-run wrote reports/audit/* and
experiments/runs/live-smoke-v1/* to fixed paths regardless of --output-dir, so every pytest
run replaced the committed live-smoke artifacts with simulation output. Add --audit-dir and
--run-dir (defaults unchanged), point the tests at temporary directories, and add a test that
fails if a run modifies any of the seven committed run and audit files.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
