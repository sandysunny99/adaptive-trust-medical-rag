# 2026-10-22 audit validation. Run from anywhere:
#   powershell -ExecutionPolicy Bypass -File "reports\live_validation\runs\2026-10-22-audit\run_audit.ps1"
# Writes logs and results next to this script. Prints no secrets. Changes no application file.
# Leaves the backend (port 8000) and frontend (port 5173) running at the end for the browser check;
# close their two windows when done.
$ErrorActionPreference = 'Continue'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $Here '..\..\..\..')).Path
Set-Location $Root
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Log = Join-Path $Here 'logs'
New-Item -ItemType Directory -Force -Path $Log | Out-Null
$Summary = [ordered]@{ started_at = (Get-Date).ToUniversalTime().ToString('o'); steps = [ordered]@{} }

function Step($name, [scriptblock]$cmd) {
    Write-Host "=== $name" -ForegroundColor Cyan
    $t0 = Get-Date
    & $cmd *>&1 | Tee-Object -FilePath (Join-Path $Log "$name.log")
    $code = $LASTEXITCODE
    $Summary.steps[$name] = [ordered]@{ exit = $code; seconds = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1) }
    Write-Host "=== $name exit=$code" -ForegroundColor Yellow
}

$Historical = @('experiments/runs/live-smoke-v1/case_results.jsonl','experiments/runs/live-smoke-v1/manifest.json',
  'experiments/runs/live-smoke-v1/summary.json','reports/audit/ablation_runtime_integrity_smoke.md',
  'reports/audit/canonical_r1_verification.md','reports/audit/five_case_validation.md','reports/audit/live_smoke_integrity.md',
  'data/live_medical/relationships/LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json',
  'data/live_medical/relationships/LIVE_RELATIONSHIP_RECORDS_V2.json',
  'data/live_medical/relationships/LIVE_RELATIONSHIP_EVIDENCE_V2.json','data/live_medical/LIVE_MEDICAL_CORPUS_V2.json')
function Hashes { $h = [ordered]@{}; foreach ($f in $Historical) { $h[$f] = (Get-FileHash -Algorithm SHA256 $f).Hash.ToLower() }; $h }
$Summary.hashes_before = Hashes

# 1. Backend suites with the test stubs (TESTING=1: stub embeddings and keyword NLI)
$env:TESTING = '1'
Step 'pytest_new_and_focused_TESTING1' { & $Py -m pytest -q -p no:cacheprovider tests/test_live_audit_regressions.py tests/test_live_provider_failover_policy.py tests/providers/test_vision_fallback_and_timeouts.py tests/e2e/test_live_evidence_provenance.py tests/test_canonical_identity.py tests/e2e/test_live_relationship_evidence_v2.py tests/e2e/test_live_source_links.py tests/providers/test_vision_backend.py }
Step 'pytest_full_TESTING1' { & $Py -m pytest -q -p no:cacheprovider -rs }
Remove-Item Env:TESTING -ErrorAction SilentlyContinue

# 2. The same provenance and regression tests with the real PubMedBERT-MNLI model (TESTING unset)
Step 'pytest_provenance_REAL_NLI' { & $Py -m pytest -q -p no:cacheprovider tests/e2e/test_live_evidence_provenance.py tests/test_live_audit_regressions.py tests/test_claim_verifier_v2.py }

# 3. Static analysis, integrity, line endings
Step 'ruff' { & $Py -m ruff check src/ tests/ }
Step 'bandit' { & $Py .agents/scripts/ci/run_bandit.py }
Step 'integrity_v3_1' { & $Py scripts/verify_v3_1_integrity.py }
Step 'integrity_v3_separation' { & $Py scripts/verify_v3_confirmed_separation.py }
Step 'line_endings' { & $Py scripts/audit_frozen_hash_line_endings.py --check }
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
    $changed = @(git diff --name-only) + @(git ls-files --others --exclude-standard -- src tests scripts frontend/src data/live_medical/relationships reports/live_validation/runs/2026-10-22-audit)
    $changed = $changed | Where-Object { $_ -and (Test-Path $_) -and ($_ -notmatch '^\.env') } | Sort-Object -Unique
    Step 'gitleaks_changed_files' { $rc = 0; foreach ($f in $changed) { gitleaks dir --no-banner --redact --config .gitleaks.toml $f; if ($LASTEXITCODE -ne 0) { $rc = $LASTEXITCODE } }; $global:LASTEXITCODE = $rc }
} else { $Summary.steps['gitleaks_changed_files'] = 'gitleaks not on PATH; not run' }

# 4. Frontend
Push-Location frontend
Step 'frontend_test' { npx vitest run --maxWorkers=2 }
Step 'frontend_build' { npm run build }
Step 'frontend_lint' { npm run lint }
Pop-Location

$Summary.hashes_after = Hashes
$Summary.hashes_unchanged = (($Summary.hashes_before | ConvertTo-Json) -eq ($Summary.hashes_after | ConvertTo-Json))

# 5. Live: start the real backend (no TESTING), then real inference, failover and HTTP/SSE scenarios
Write-Host '=== starting backend on 127.0.0.1:8000' -ForegroundColor Cyan
$backend = Start-Process -PassThru -FilePath $Py -WorkingDirectory $Root `
  -ArgumentList '-m','uvicorn','--app-dir','src','adaptive_trust_medical_rag.api.app:app','--host','127.0.0.1','--port','8000' `
  -RedirectStandardOutput (Join-Path $Log 'backend.out.log') -RedirectStandardError (Join-Path $Log 'backend.err.log')
$up = $false
for ($i = 0; $i -lt 90; $i++) { Start-Sleep 2; try { if ((Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 3).StatusCode -eq 200) { $up = $true; break } } catch {} }
$Summary.backend_up = $up
if ($up) {
    Step 'live_audit' { & $Py (Join-Path $Here 'live_audit.py') (Join-Path $Here 'live') 'http://127.0.0.1:8000' }
    Step 'live_summary' { & $Py claude-incoming/abc-kit/summarize_abc.py (Join-Path $Here 'live') }
}
$Summary.finished_at = (Get-Date).ToUniversalTime().ToString('o')
$Summary | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $Here 'SUMMARY_RUN.json')

# 6. Leave backend + frontend running for the browser check
if ($up) {
    Start-Process -FilePath 'cmd.exe' -WorkingDirectory (Join-Path $Root 'frontend') -ArgumentList '/k','npm run dev -- --host 127.0.0.1 --port 5173'
    Write-Host "Backend PID $($backend.Id) and the frontend window are still running for the browser check." -ForegroundColor Green
}
Write-Host "Done. Results: $Here" -ForegroundColor Green
