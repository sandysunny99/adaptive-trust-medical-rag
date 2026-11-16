docs: describe the current live application, setup and tests; update the blocker register

- README: current implementation status (implemented / pending approval / blocked), the live
  pipeline, evidence sources and their real status, providers as registered, local setup,
  tests, limitations. The A-F scorecard is replaced by a caveat: those numbers come from a
  simulation profile (MockVariantPipeline), not live runs or human labels.
- docs/ARCHITECTURE.md: the live pipeline as implemented (endpoints, stages, modules, SSE
  events, error codes, relationship records), the research harness as a separate path, and
  where the earlier version differed from the code.
- docs/CONFIGURATION.md (new): requirements, install, environment variable names from the
  source, run commands, troubleshooting.
- docs/TESTING.md (new): every suite and scan, exact-build and LF-checkout checks, browser
  scenarios and the latest verified results.
- docs/architecture/INTEGRATION_ROADMAP.md: marked historical, pointing to the register.
- reports/audit/blocked_issue_register.md: entries from 2026-10-15 to 2026-10-19 (fixes,
  local validation, commits now pushed). REL-LIVE-0001/0002 stay pending; no freeze declared.

Documentation only; no code, data or test changes.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
